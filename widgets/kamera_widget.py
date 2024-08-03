import sys
import cv2
import numpy as np

from PyQt5 import QtWidgets, QtGui, QtCore


# Funkcije za obradu slike
def detect_color(tile):
    avg_color = tile.mean(axis=0).mean(axis=0)
    return avg_color

# Funkcija za provjeru preklapanja čelija kontura
def is_overlapping(box1, box2):
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    return not (x1 > x2 + w2 or x2 > x1 + w1 or y1 > y2 + h2 or y2 > y1 + h1)

# Funkcija za filtriranje čelija kontura koje se preklapaju 
def filter_overlapping_contours(contours):
    bounding_boxes = [cv2.boundingRect(contour) for contour in contours]
    filtered_contours = []
    
    for i, box1 in enumerate(bounding_boxes):
        keep = True
        for j, box2 in enumerate(bounding_boxes):
            if i != j and is_overlapping(box1, box2):
                if cv2.contourArea(contours[i]) < cv2.contourArea(contours[j]):
                    keep = False
                    break
        if keep:
            filtered_contours.append(contours[i])
    
    return filtered_contours

# preset_colors_rgb = {
#     'U': [235,235,235], #[255, 255, 255],
#     'D': [195,195,60], #[175, 200, 10],
#     'R': [240,0,0], #[255, 0, 0],
#     'L': [200,110,10], #[200, 100, 10],
#     'F': [50,210,65], #[0, 255, 0],
#     'B': [30,95,255] #[0, 0, 255]
# }

preset_sides = [U, D, R, L, F, B]
preset_colors_rgb = {}


# Layout polja kocke, redoslijed snimanja stranica 
cube_layout = [
    ['U1', 'U2', 'U3', 'U4', 'U5', 'U6', 'U7', 'U8', 'U9'],  # Gornja str
    ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9'],  # Prednja str
    ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9'],  # Desna str
    ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9'],  # Zadnja str
    ['L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8', 'L9'],  # Lijeva str
    ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9'],  # Donja str

]


# Funkcija za usporedbu i postavljanje detektirane boje s preset bojama  
def closest_color(color, preset_colors):
    min_distance = float('inf')
    closest_color_name = None
    for name, preset_color in preset_colors.items():
        distance = np.linalg.norm(color - preset_color)
        if color[0] > 160 and color[1] < 80:
            closest_color_name = 'R'
        elif distance < min_distance:
            min_distance = distance
            closest_color_name = name
    return closest_color_name

# Funkcija za obradu slika (Frame-a) i detekciju boja
def process_frame(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    adjusted = cv2.convertScaleAbs(gray, alpha=1.2, beta=10)
    blurred = cv2.GaussianBlur(adjusted, (9, 9), 0)
    edges = cv2.Canny(blurred, 40, 30)   # lower, upper threshold 20, 25 
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    cube_contours = []
    for contour in contours:
        epsilon = 0.15 * cv2.arcLength(contour, True)  # 0.15
        approx = cv2.approxPolyDP(contour, epsilon, True)
        if len(approx) == 4:
            cube_contours.append(approx)
    
    cube_contours = filter_overlapping_contours(cube_contours)
    
    tiles = []
    colors = []
    positions = []
    for contour in cube_contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w > 60 and h > 60:
            tile = frame[y:y+h, x:x+w]
            tiles.append(tile)
            color = detect_color(tile)
            colors.append(color)
            positions.append((x, y, w, h))
            start_x = int(x + 0.05*w)
            start_y = int(y + 0.05*h)
            end_x = int(x+w - 0.05*w)
            end_y = int(y+h - 0.05*h)
            cv2.rectangle(frame, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)
    
    # Sortiranje polja po vertikali-y (gore prema dolje)
    positions_colors = sorted(zip(positions, colors), key=lambda b: b[0][1])

    # Dijeljenje u redove (uzimajuči 3x3 raspored)
    rows = [positions_colors[i:i+3] for i in range(0, len(positions_colors), 3)]

    # Sortiranje svakog reda po horizontali-x (lijevo prema desno)
    sorted_positions_colors = [sorted(row, key=lambda b: b[0][0]) for row in rows]

     # Spajanje sortiranih redova u jednu listu
    sorted_positions_colors = [color for row in sorted_positions_colors for _, color in row]
    
    # Pretvorba detektiranih BGR boja u RGB
    colors_rgb = [cv2.cvtColor(np.uint8([[color]]), cv2.COLOR_BGR2RGB)[0][0] for color in sorted_positions_colors]

    if colors_rgb == 9:
        preset_colors_rgb[preset_sides[len(preset_colors_rgb)]] = colors_rgb[4]

    # Postavljanje detektirane boje s najbližom preset bojom
    #closest_colors = [preset_colors_rgb[closest_color(color, preset_colors_rgb)] for color in colors_rgb]
    
    return frame, colors_rgb #closest_colors



class CameraWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera Application")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QtWidgets.QVBoxLayout()

        self.image_label = QtWidgets.QLabel()
        self.layout.addWidget(self.image_label)

        self.text_label = QtWidgets.QLabel()
        self.text_label.setFont(QtGui.QFont('Times New Roman', 12))
        self.text_label.setText("Nema smiljneih stranica.")
        self.layout.addWidget(self.text_label)

        self.setLayout(self.layout)
        

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.cap = None
        
        self.center_colors = []
        self.button_colors = {}  # Spremanje boja svakog polja


    def start_camera(self):
        self.cap = cv2.VideoCapture(0)
        self.timer.start(20)

    def stop_camera(self):
        if self.cap:
            self.timer.stop()
            self.cap.release()
            self.cap = None
    

    # Obrada videozapisa
    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = frame[0:480, 100:580]
            frame = cv2.flip(frame, 1)
            
            processed_frame, closest_colors = process_frame(frame)
            processed_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = QtGui.QImage(processed_frame, processed_frame.shape[1], processed_frame.shape[0], 
                           processed_frame.strides[0], QtGui.QImage.Format_RGB888)
                           
            self.image_label.setPixmap(QtGui.QPixmap.fromImage(image))
            


            
            # Zapis boja za postavljanje 2D prikaza kocke
            if len(closest_colors) == 9:
                center_color = closest_colors[4]
                if all(np.linalg.norm(center_color - np.array(c)) > 10 for c in self.center_colors):
                    self.center_colors.append(center_color)

                    for x, tile in enumerate(cube_layout[(len(self.center_colors) - 1)]):
                        face = tile[0]
                        for side, color in preset_colors_rgb.items():
                            if color == closest_colors[x]:
                                self.button_colors[tile] = side
                    print(closest_colors)
                    #print(self.button_colors)
                    self.text_label.setText(f"Stranica {len(self.center_colors)} snimljena.")
                


    def closeEvent(self, event):
        self.cap.release()
        event.accept()

    def resize_camera(self, width, height):
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.resize(width, height)

    def snimljena_stranica(self):
        return center_colors

