import sys
import cv2
import numpy as np

from PyQt5 import QtWidgets, QtGui, QtCore


# Funkcije za obradu slike
def detect_color(tile):
    avg_color = tile.mean(axis=0).mean(axis=0)
    return avg_color

def is_overlapping(box1, box2):
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    return not (x1 > x2 + w2 or x2 > x1 + w1 or y1 > y2 + h2 or y2 > y1 + h1)

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

preset_colors_rgb = {
    'white': [255, 255, 255],
    'yellow': [175, 200, 10],
    'red': [255, 0, 0],
    'orange': [200, 100, 10],
    'green': [0, 255, 0],
    'blue': [0, 0, 255]
}

def closest_color(color, preset_colors):
    min_distance = float('inf')
    closest_color_name = None
    for name, preset_color in preset_colors.items():
        distance = np.linalg.norm(color - preset_color)
        if color[0] > 160 and color[1] < 60:
            closest_color_name = 'red'
        elif distance < min_distance:
            min_distance = distance
            closest_color_name = name
    return closest_color_name

def process_frame(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 20, 25)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    cube_contours = []
    for contour in contours:
        epsilon = 0.15 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        if len(approx) == 4:
            cube_contours.append(approx)
    
    cube_contours = filter_overlapping_contours(cube_contours)
    
    tiles = []
    colors = []
    positions = []
    for contour in cube_contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w > 50 and h > 50:
            tile = frame[y:y+h, x:x+w]
            tiles.append(tile)
            color = detect_color(tile)
            colors.append(color)
            positions.append((x, y, w, h))
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
    
    positions_colors = sorted(zip(positions, colors), key=lambda b: b[0][1])
    rows = [positions_colors[i:i+3] for i in range(0, len(positions_colors), 3)]
    sorted_positions_colors = [sorted(row, key=lambda b: b[0][0]) for row in rows]
    sorted_positions_colors = [color for row in sorted_positions_colors for _, color in row]
    
    colors_rgb = [cv2.cvtColor(np.uint8([[color]]), cv2.COLOR_BGR2RGB)[0][0] for color in sorted_positions_colors]
    closest_colors = [preset_colors_rgb[closest_color(color, preset_colors_rgb)] for color in colors_rgb]
    
    return frame, closest_colors

# Main application class

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
        self.cap = cv2.VideoCapture(0)

        self.timer.start(20)
        self.sides_colors = []
        self.center_colors = []

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = frame[0:480, 100:580]
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            processed_frame, closest_colors = process_frame(frame_rgb)
            
            image = QtGui.QImage(processed_frame, processed_frame.shape[1], processed_frame.shape[0], 
                           processed_frame.strides[0], QtGui.QImage.Format_RGB888)
                           
            self.image_label.setPixmap(QtGui.QPixmap.fromImage(image))
            
            stranica = 0 

            if len(closest_colors) == 9:
                center_color = closest_colors[4]
                if all(np.linalg.norm(center_color - np.array(c)) > 10 for c in self.center_colors):
                    self.sides_colors.append(closest_colors)
                    self.center_colors.append(center_color)
                    stranica += 1





    def closeEvent(self, event):
        self.cap.release()
        event.accept()

    def resize_camera(self, width, height):
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.resize(width, height)

    def snimljena_stranica(self):
        return center_colors