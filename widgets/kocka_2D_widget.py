import sys
from PyQt5 import QtWidgets, QtGui, QtCore



# Boje stranica
colors = {
    'U': 'rgb(255,255,255)',  # White
    'L': 'rgb(255,175,30)',  # Orange
    'F': 'rgb(90,210,100)',  # Green
    'R': 'rgb(240,50,50)',  # Red
    'B': 'rgb(30,95,255)',  # Blue
    'D': 'rgb(242,242,20)'  # Yellow
    }

# Layout kocke u 2D prikazu
cube_layout = [
    [' ', ' ', ' ', 'U1', 'U2', 'U3', ' ', ' ', ' '],
    [' ', ' ', ' ', 'U4', 'U5', 'U6', ' ', ' ', ' '],
    [' ', ' ', ' ', 'U7', 'U8', 'U9', ' ', ' ', ' '],
    ['L1', 'L2', 'L3', 'F1', 'F2', 'F3', 'R1', 'R2', 'R3', 'B1', 'B2', 'B3'],
    ['L4', 'L5', 'L6', 'F4', 'F5', 'F6', 'R4', 'R5', 'R6', 'B4', 'B5', 'B6'],
    ['L7', 'L8', 'L9', 'F7', 'F8', 'F9', 'R7', 'R8', 'R9', 'B7', 'B8', 'B9'],
    [' ', ' ', ' ', 'D1', 'D2', 'D3', ' ', ' ', ' '],
    [' ', ' ', ' ', 'D4', 'D5', 'D6', ' ', ' ', ' '],
    [' ', ' ', ' ', 'D7', 'D8', 'D9', ' ', ' ', ' '],
]


class Cube2DWidget(QtWidgets.QWidget):
    # Izrada signala za buttone
    buttonClickedSignal = QtCore.pyqtSignal(str)

    def __init__(self):
        super(Cube2DWidget, self).__init__()
        self.buttons = []
        self.button_colors = {}  # Spremanje boja svakog polja
        self.initUI()

    def initUI(self):
        grid = QtWidgets.QGridLayout()
        grid.setContentsMargins(0, 0, 5, 10)
        self.setLayout(grid)

        global colors, cube_layout

        # Izrada buttona
        for row, row_data in enumerate(cube_layout):
            for col, tile in enumerate(row_data):
                if tile != ' ':
                    face = tile[0]
                    button = QtWidgets.QPushButton(self)
                    button.setStyleSheet(f'background-color: {colors[face]}; border:2px solid black')
                    button.setFixedSize(QtCore.QSize(60, 60))
                    button.setObjectName(tile)
                    if tile not in ['U5', 'L5', 'F5', 'R5', 'B5', 'D5']:
                        button.clicked.connect(self.emitCustomSignal)
                    else: 
                        button.setText(tile[0])
                        button.setFont(QtGui.QFont('Times New Roman', 16))
                    grid.addWidget(button, row, col)
                    self.buttons.append(button)  # Dodavanje buttona u listu
                    self.button_colors[tile] = colors[face]  # Dodavanje buttona u rječnik s bojama

    # Emitiranje signala tijekom pritiska na jedan od izrađenih buttona
    def emitCustomSignal(self):
        button = self.sender()
        self.buttonClickedSignal.emit(button.objectName())

    def connectCustomSignal(self, slot):
        self.buttonClickedSignal.connect(slot)


    # Metoda za postavljanje boje pojedinačnih polja pritiskom gumba
    def setColor(self, button_name, color):
        for button in self.buttons:
            if button.objectName() == button_name:
                button.setStyleSheet(f'background-color: {color}; border:2px solid black')
                self.button_colors[button_name] = color  # Ažuriranje boje buttona

    # Metoda za postavljanje skeniranih boja
    def setScanedColors(self, color_dict):
        for button in self.buttons:
            if button.objectName() not in ['U5', 'L5', 'F5', 'R5', 'B5', 'D5']:
                if color_dict.get(button.objectName()):
                    button.setStyleSheet(f'background-color: {colors[color_dict.get(button.objectName())]}; border:2px solid black')
                    self.button_colors[button.objectName()] = colors[color_dict.get(button.objectName())]  # Ažuriranje boje buttona     

    # Metoda za resetiranje boja polja
    def resetColors(self):
        global colors
        for button in self.buttons:
            button.setStyleSheet(f'background-color: {colors[button.objectName()[0]]}; border:2px solid black')
            self.button_colors[button.objectName()] = colors[button.objectName()[0]]

    # Metoda za promjenu veličine buttona
    def buttonSize(self, widht, height):
        for button in self.buttons:
            button.setFixedSize(QtCore.QSize(int(widht), int(height)))

    # Metoda za dobivanje boja polja za kociemba algoritam
    def tileString(self):
        global colors
        side_color = ""
        # Poredak stranica
        face_order = ['U', 'R', 'F', 'D', 'L', 'B']

        for face in face_order:
            for x in range(1, 10):
                button_name = face + str(x)
                color = self.button_colors[button_name]
                for name, clr in colors.items():
                    if clr == color:
                        side_color += name 
        
        return side_color
