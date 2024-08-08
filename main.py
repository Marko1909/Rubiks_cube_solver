import sys
import cv2
import numpy as np
import kociemba
import re
import time
import bluetooth

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtOpenGL import QGLWidget
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

from widgets import CameraWidget, Cube3DWidget, Cube2DWidget
from robot import robot_moves
from bt_connection import BluetoothWorker


# Izabrana boja za postavljanje boje polja
izabrana_boja = ()
prev_boja = ""
boje = [
    ['bijela', 'rgb(255,255,255)'],  #White
    ['narancasta', 'rgb(255,175,30)'],  #Orange
    ['zelena', 'rgb(90,210,100)'],  #Green
    ['crvena', 'rgb(240,50,50)'],  #Red
    ['plava', 'rgb(30,95,255)'],  #Blue
    ['zuta', 'rgb(242,242,20)']  #Yellow
]


class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Rubiks cube solver')
        self.setGeometry(200, 100, 1280, 720)
        self.setMinimumSize(1280, 720)
        self.initUI()
        self.showMaximized()
        self.bt_worker = None
        self.sock = None


    def initUI(self):
        self.fontSmall = QtGui.QFont('Arial', 8)
        self.fontButton = QtGui.QFont('Times New Roman', 16)
        self.font = QtGui.QFont('Times New Roman', 12)


    # Main frame
        self.frame_main = QtWidgets.QFrame(self)
        self.frame_main.setStyleSheet("*{background-color: rgb(200,200,200)}")
        self.frame_main.setGeometry(QtCore.QRect(9, 6, 1260, 700))
        self.frame_main.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_main.setFrameShadow(QtWidgets.QFrame.Raised)
    
        # Glavni grid-layout
        self.g_layout_main = QtWidgets.QGridLayout(self.frame_main)
        self.g_layout_main.setContentsMargins(5, 5, 5, 5)

        # Grid layout za boje i prikaz modela kocke       
        self.g_layout_kocka = QtWidgets.QGridLayout()
        self.g_layout_kocka.setContentsMargins(0, 0, 0, 0)
        self.g_layout_main.addLayout(self.g_layout_kocka, 0, 0, 1, 1)


        # Vertikalni razmak
        v_spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

        # Horizontalni razmak
        h_spacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)


    # Frame za buttone boja
        self.frame_boje = QtWidgets.QFrame(self)
        self.frame_boje.setFixedWidth(190)
        self.frame_boje.setStyleSheet("*{background-color: rgb(255,255,255)}")
        self.frame_boje.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_boje.setFrameShadow(QtWidgets.QFrame.Raised)
        self.g_layout_kocka.addWidget(self.frame_boje, 1, 0, 1, 1)

        # Layouti za buttone boja
        self.g_layout_boje = QtWidgets.QGridLayout()
        self.g_layout_boje.setContentsMargins(20, 20, 20, 20)
        self.v_layout_boje = QtWidgets.QVBoxLayout(self.frame_boje)
        self.v_layout_boje.addItem(v_spacer)
        self.v_layout_boje.addLayout(self.g_layout_boje)
        self.v_layout_boje.addItem(v_spacer)

        # Frame buttona za okretanje kocke
        self.frame_okreni_kocku = QtWidgets.QFrame(self)
        self.frame_okreni_kocku.setFixedWidth(190)
        self.frame_okreni_kocku.setStyleSheet("*{background-color: rgb(255,255,255)}")
        self.frame_okreni_kocku.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_okreni_kocku.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_okreni_kocku.hide()
        self.g_layout_kocka.addWidget(self.frame_okreni_kocku, 1, 0, 1, 1)

        # Layouti buttona za okretanje kocke
        self.g_layout_okreni = QtWidgets.QGridLayout(self.frame_okreni_kocku)
            

    # Prikaz modela kocke i ručno postavljanje boja 
        # Gumb za izbor i postavljanje bijele boje 
        self.button_bijela = QtWidgets.QPushButton(self)
        self.button_bijela.setFixedSize(56, 56)
        self.button_bijela.setObjectName("bijela")
        self.button_bijela.setText("U")
        self.button_bijela.setFont(self.fontButton)
        self.button_bijela.setStyleSheet("*{background-color: rgb(255,255,255)}")
        self.button_bijela.clicked.connect(self.izaberi_boju)
        self.g_layout_boje.addWidget(self.button_bijela, 0, 0, 1, 1)

        # Gumb za izbor i postavljanje narancaste boje 
        self.button_narancasta = QtWidgets.QPushButton(self)
        self.button_narancasta.setFixedSize(56, 56)
        self.button_narancasta.setObjectName("narancasta")
        self.button_narancasta.setText("L")
        self.button_narancasta.setFont(self.fontButton)
        self.button_narancasta.setStyleSheet("*{background-color: rgb(255, 175, 30)}")
        self.button_narancasta.clicked.connect(self.izaberi_boju)
        self.g_layout_boje.addWidget(self.button_narancasta, 0, 1, 1, 1)

        # Gumb za izbor i postavljanje zelene boje 
        self.button_zelena = QtWidgets.QPushButton(self)
        self.button_zelena.setFixedSize(56, 56)
        self.button_zelena.setObjectName("zelena")
        self.button_zelena.setText("F")
        self.button_zelena.setFont(self.fontButton)
        self.button_zelena.setStyleSheet("*{background-color: rgb(90, 210, 100)}")
        self.button_zelena.clicked.connect(self.izaberi_boju)
        self.g_layout_boje.addWidget(self.button_zelena, 1, 0, 1, 1)

        # Gumb za izbor i postavljanje crvene boje 
        self.button_crvena = QtWidgets.QPushButton(self)
        self.button_crvena.setFixedSize(56, 56)
        self.button_crvena.setObjectName("crvena")
        self.button_crvena.setText("R")
        self.button_crvena.setFont(self.fontButton)
        self.button_crvena.setStyleSheet("*{background-color: rgb(240, 50, 50)}")
        self.button_crvena.clicked.connect(self.izaberi_boju)
        self.g_layout_boje.addWidget(self.button_crvena, 1, 1, 1, 1)

        # Gumb za izbor i postavljanje plave boje 
        self.button_plava = QtWidgets.QPushButton(self)
        self.button_plava.setFixedSize(56, 56)
        self.button_plava.setObjectName("plava")
        self.button_plava.setText("B")
        self.button_plava.setFont(self.fontButton)
        self.button_plava.setStyleSheet("*{background-color: rgb(30, 95, 255)}")
        self.button_plava.clicked.connect(self.izaberi_boju)
        self.g_layout_boje.addWidget(self.button_plava, 2, 0, 1, 1)

        # Gumb za izbor i postavljanje zute boje 
        self.button_zuta = QtWidgets.QPushButton(self)
        self.button_zuta.setFixedSize(56, 56)
        self.button_zuta.setObjectName("zuta")
        self.button_zuta.setText("D")
        self.button_zuta.setFont(self.fontButton)
        self.button_zuta.setStyleSheet("*{background-color: rgb(242, 242, 20)}")
        self.button_zuta.clicked.connect(self.izaberi_boju)
        self.g_layout_boje.addWidget(self.button_zuta, 2, 1, 1, 1)

        # Gumb za reset boja stranica
        self.button_reset = QtWidgets.QPushButton(self)
        self.button_reset.setFont(self.font)
        self.button_reset.setText('Resetiraj boje')
        self.button_reset.setFixedSize(120, 35)
        self.button_reset.setStyleSheet("*{background-color: rgb(200,200,200)}")
        self.button_reset.clicked.connect(self.reset_2d_boje)
        self.g_layout_boje.addWidget(self.button_reset, 3, 0, 1, 2)



        # Label gumbi za okretanje kocke
        self.label_okretanje = QtWidgets.QLabel(self)
        self.label_okretanje.setFont(self.font)
        self.label_okretanje.setWordWrap(True)
        self.label_okretanje.setText("Okretanje kocke:")
        self.g_layout_okreni.addWidget(self.label_okretanje, 0, 0, 1, 2, QtCore.Qt.AlignCenter)

        # Gumb za okretanje kocke prema gore
        self.strelica_gore = QtWidgets.QPushButton(self)
        self.strelica_gore.setFixedSize(56, 56)
        self.strelica_gore.setIcon(QtGui.QIcon("ikone\Strelica_gore.png")) #icon
        self.strelica_gore.setIconSize(QtCore.QSize(50, 50))
        self.strelica_gore.clicked.connect(self.rotate_cube_up)
        self.g_layout_okreni.addWidget(self.strelica_gore, 1, 0, 1, 2, QtCore.Qt.AlignCenter)

        # Gumb za okretanje kocke u lijevu stranu
        self.strelica_lijevo = QtWidgets.QPushButton(self)
        self.strelica_lijevo.setFixedSize(56, 56)
        self.strelica_lijevo.setIcon(QtGui.QIcon("ikone\Strelica_lijevo.png")) #ikona
        self.strelica_lijevo.setIconSize(QtCore.QSize(50, 50))
        self.strelica_lijevo.clicked.connect(self.rotate_cube_left)
        self.g_layout_okreni.addWidget(self.strelica_lijevo, 2, 0, 1, 1)

        # Gumb za okretanje kocke u desnu stranu
        self.strelica_desno = QtWidgets.QPushButton(self)
        self.strelica_desno.setFixedSize(56, 56)
        self.strelica_desno.setIcon(QtGui.QIcon("ikone\Strelica_desno.png")) #icon
        self.strelica_desno.setIconSize(QtCore.QSize(50, 50))
        self.strelica_desno.clicked.connect(self.rotate_cube_right)
        self.g_layout_okreni.addWidget(self.strelica_desno, 2, 1, 1, 1)


        self.line = QtWidgets.QLabel(self)
        self.line.setFixedSize(160, 2)
        self.line.setStyleSheet("border: 1px solid black;")
        self.g_layout_okreni.addWidget(self.line, 3, 0, 1, 1, QtCore.Qt.AlignCenter)


        # Label gumbi za pokretanje animacije rjesavanja
        self.label_animacija = QtWidgets.QLabel(self)
        self.label_animacija.setFont(self.font)
        self.label_animacija.setWordWrap(True)
        self.label_animacija.setText("Upravljanje animacijom")
        self.g_layout_okreni.addWidget(self.label_animacija, 4, 0, 1, 2, QtCore.Qt.AlignCenter)

        # Gumb za pokretanje animacije rjesavanja
        self.button_pokreni_animaciju = QtWidgets.QPushButton(self)
        self.button_pokreni_animaciju.setFixedSize(56, 56)
        self.button_pokreni_animaciju.setIcon(QtGui.QIcon("ikone\Kreni.png")) #icon
        self.button_pokreni_animaciju.setIconSize(QtCore.QSize(50, 50))
        self.button_pokreni_animaciju.clicked.connect(self.pokreni_animaciju)
        self.g_layout_okreni.addWidget(self.button_pokreni_animaciju, 5, 0, 1, 1)
        
        # Gumb za zaustavljanje animacije rjesavanja
        self.button_zaustavi_animaciju = QtWidgets.QPushButton(self)
        self.button_zaustavi_animaciju.setFixedSize(56, 56)
        self.button_zaustavi_animaciju.setIcon(QtGui.QIcon("ikone\Stani.png")) #icon
        self.button_zaustavi_animaciju.setIconSize(QtCore.QSize(50, 50))
        self.button_zaustavi_animaciju.clicked.connect(self.zaustavi_animaciju)
        self.g_layout_okreni.addWidget(self.button_zaustavi_animaciju, 5, 1, 1, 1)

        # Gumb za postavljanje kocke korak unazad
        self.button_korak_unazad = QtWidgets.QPushButton(self)
        self.button_korak_unazad.setFixedSize(56, 56)
        self.button_korak_unazad.setIcon(QtGui.QIcon("ikone\Korak_unazad.png")) #icon
        self.button_korak_unazad.setIconSize(QtCore.QSize(50, 50))
        self.button_korak_unazad.clicked.connect(self.korak_unazad)
        self.g_layout_okreni.addWidget(self.button_korak_unazad, 6, 0, 1, 1)

        # Gumb za postavljanje kocke korak unaprijed  
        self.button_korak_unaprijed = QtWidgets.QPushButton(self)
        self.button_korak_unaprijed.setFixedSize(56, 56)
        self.button_korak_unaprijed.setIcon(QtGui.QIcon("ikone\Korak_unaprijed.png")) #icon
        self.button_korak_unaprijed.setIconSize(QtCore.QSize(50, 50))
        self.button_korak_unaprijed.clicked.connect(self.korak_unaprijed)
        self.g_layout_okreni.addWidget(self.button_korak_unaprijed, 6, 1, 1, 1)




    # Layout za gumbe za 2D ili 3D prikaz
        self.h_layout_prikaz = QtWidgets.QHBoxLayout()
        self.g_layout_kocka.addLayout(self.h_layout_prikaz, 0, 1, 1, 1)

        # Izbor 2D prikaza modela kocke
        self.button_2d = QtWidgets.QPushButton(self)
        self.button_2d.setFont(self.font)
        self.button_2d.setText('2D prikaz')
        self.button_2d.setFixedSize(120, 35)
        self.button_2d.setStyleSheet("*{background-color: rgb(200,200,200)}")
        self.button_2d.clicked.connect(self.prikaz_2d)
        self.h_layout_prikaz.addWidget(self.button_2d)

        # Izbor 3D prikaza modela kocke
        self.button_3d = QtWidgets.QPushButton(self)
        self.button_3d.setFont(self.font)
        self.button_3d.setText('3D prikaz')
        self.button_3d.setFixedSize(120, 35)
        self.button_3d.setStyleSheet("*{background-color: rgb(200,200,200)}")
        self.button_3d.clicked.connect(self.prikaz_3d)
        self.h_layout_prikaz.addWidget(self.button_3d)

        self.h_layout_prikaz.addItem(h_spacer)

    # Frame za 2D/3D prikaz kocke
        self.frame_kocka = QtWidgets.QFrame(self)
        self.frame_kocka.setStyleSheet("*{background-color: rgb(255,255,255)}")
        self.frame_kocka.setFixedSize(1200, 600)
        self.frame_kocka.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_kocka.setFrameShadow(QtWidgets.QFrame.Raised)
        self.g_layout_kocka.addWidget(self.frame_kocka, 1, 1, 1, 1)
        
        # Widget za 2D prikaz kocke
        self.cube_widget_2d = Cube2DWidget()
        self.cube_widget_2d.show()
        self.cube_widget_2d.connectCustomSignal(self.postavi_boju)
        
        # Widget za 3D prikaz kocke
        self.cube_widget_3d = Cube3DWidget()
        self.cube_widget_3d.hide()

        self.h_layout_kocka = QtWidgets.QHBoxLayout(self.frame_kocka)
        self.h_layout_kocka.addWidget(self.cube_widget_3d)
        self.h_layout_kocka.addWidget(self.cube_widget_2d)



    # Popup prozor za kameru
        self.camera_widget = CameraWidget()
        self.camera_widget.resize_camera(480, 480)

        self.popup = QtWidgets.QDialog()
        self.popup.setWindowTitle("Snimanje kocke")
        self.popup.finished.connect(self.ugasi_kameru)
        self.v_layout_popup = QtWidgets.QVBoxLayout(self.popup)
        self.v_layout_popup.addWidget(self.camera_widget)


    # Ispis koraka
        # Frame za labele
        self.frame_label = QtWidgets.QFrame(self)
        self.frame_label.setStyleSheet("*{background-color: rgb(255,255,255)}")
        self.frame_label.setFixedSize(1400, 300)
        self.frame_label.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_label.setFrameShadow(QtWidgets.QFrame.Raised)
        self.g_layout_main.addWidget(self.frame_label, 1, 0, 1, 1)

        # Layout za gumbe funkcija
        self.g_layout_label = QtWidgets.QGridLayout(self.frame_label)
        self.g_layout_label.setAlignment(QtCore.Qt.AlignLeft)

        # Label boja stranica
        self.label_boje = QtWidgets.QLabel(self)
        self.label_boje.setFont(self.font)
        self.label_boje.setText("Boje polja:")
        self.g_layout_label.addWidget(self.label_boje, 0, 0, 1, 1)

        # Label za ispis boja stranica
        self.label_ispis_boja = QtWidgets.QLabel(self)
        self.label_ispis_boja.setFixedSize(1100, 40)
        self.label_ispis_boja.setWordWrap(True)
        self.label_ispis_boja.setFont(self.font)
        self.g_layout_label.addWidget(self.label_ispis_boja, 0, 1, 1, 1)

        # Label koraci za rucno rjesanje
        self.label_koraci = QtWidgets.QLabel(self)
        self.label_koraci.setFont(self.font)
        self.label_koraci.setText("Koraci za ručno rješavanje:")
        self.g_layout_label.addWidget(self.label_koraci, 1, 0, 1, 1)

        # Label za ispis koraka za rucno rjesanje
        self.label_ispis_koraka = QtWidgets.QLabel(self)
        self.label_ispis_koraka.setFixedSize(1100, 40)
        self.label_ispis_koraka.setWordWrap(True)
        self.label_ispis_koraka.setFont(self.font)
        self.g_layout_label.addWidget(self.label_ispis_koraka, 1, 1, 1, 1)

    	# Label koraci za robotsko rjesavanje
        self.label_pokreti = QtWidgets.QLabel(self)
        self.label_pokreti.setFont(self.font)
        self.label_pokreti.setText("Koraci za robotsko rješavanje:")
        self.g_layout_label.addWidget(self.label_pokreti, 2, 0, 1, 1)

        # Label za ispis koraka za robotsko rjesavanje
        self.label_ispis_pokreta = QtWidgets.QLabel(self)
        self.label_ispis_pokreta.setFixedSize(1100, 40)
        self.label_ispis_pokreta.setWordWrap(True)
        self.label_ispis_pokreta.setFont(self.font)
        self.g_layout_label.addWidget(self.label_ispis_pokreta, 2, 1, 1, 1)



    # Funkcije i gumbi za poketanje, bluetooth....
        # Frame za gumbe funkcija
        self.frame_funk = QtWidgets.QFrame(self)
        self.frame_funk.setStyleSheet("*{background-color: rgb(255,255,255)}")
        self.frame_funk.setFixedSize(470, 914)
        self.frame_funk.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_funk.setFrameShadow(QtWidgets.QFrame.Raised)

        self.v_layout_funk = QtWidgets.QVBoxLayout()
        self.v_layout_funk.setContentsMargins(5, 53, 5, 0) # left, top, right, bottom
        self.g_layout_main.addLayout(self.v_layout_funk, 0, 1, 1, 2)
        self.v_layout_funk.addWidget(self.frame_funk)

        # Layout za gumbe funkcija
        self.g_layout_funk = QtWidgets.QGridLayout(self.frame_funk)
        self.g_layout_funk.setContentsMargins(10, 10, 10, 20)

        # Label za opis gumba kamera
        self.label_kamera = QtWidgets.QLabel(self)
        self.label_kamera.setFont(self.font)
        self.label_kamera.setText("Skočni prozor kamere za snimanje kocke")
        self.g_layout_funk.addWidget(self.label_kamera, 0, 0, 1, 2)

        # Gumb za snimanje kocke kamerom
        self.button_kamera = QtWidgets.QPushButton(self)
        self.button_kamera.setFont(self.font)
        self.button_kamera.setText('Kamera')
        self.button_kamera.setFixedSize(120, 40)
        self.button_kamera.setStyleSheet("*{background-color: rgb(200,200,200)}")
        self.button_kamera.clicked.connect(self.snimi_kocku)
        self.g_layout_funk.addWidget(self.button_kamera, 1, 0, 1, 1)
        
        # Label za prikaz stanja kamere (upaljena/ugašena)
        self.label_kamera_state = QtWidgets.QLabel(self)
        self.label_kamera_state.setFixedSize(40, 40)
        self.label_kamera_state.setStyleSheet("border: 2px solid black; border-radius: 20px; background-color: rgb(200,200,200) ")
        self.g_layout_funk.addWidget(self.label_kamera_state, 1, 1, 1, 1)

        # Label za opis gumba rijesi
        self.label_rijesi = QtWidgets.QLabel(self)
        self.label_rijesi.setFont(self.font)
        self.label_rijesi.setText("Pokretanje algoritma za rješavanje kocke")
        self.g_layout_funk.addWidget(self.label_rijesi, 2, 0, 1, 2)

        # Gumb za pokretanje rjesavanja kocke
        self.button_rijesi = QtWidgets.QPushButton(self)
        self.button_rijesi.setFont(self.font)
        self.button_rijesi.setText('Riješi')
        self.button_rijesi.setFixedSize(120, 40)
        self.button_rijesi.setStyleSheet("*{background-color: rgb(200,200,200)}")
        self.button_rijesi.clicked.connect(self.rijesi_kocku)
        self.g_layout_funk.addWidget(self.button_rijesi, 3, 0, 1, 1)

        # Label za opis gumba provjera konekcije
        self.label_provjera = QtWidgets.QLabel(self)
        self.label_provjera.setFont(self.font)
        self.label_provjera.setText("Spajanje bluetooth uređaja")
        self.g_layout_funk.addWidget(self.label_provjera, 4, 0, 1, 2)

        # Gumb za provjeravanje spojednog bluetooth uređaja
        self.button_bluetooth = QtWidgets.QPushButton(self)
        self.button_bluetooth.setFont(self.font)
        self.button_bluetooth.setText('Bluetooth')
        self.button_bluetooth.setFixedSize(120, 40)
        self.button_bluetooth.setStyleSheet("*{background-color: rgb(200,200,200)}")
        self.button_bluetooth.clicked.connect(self.spajanje_bluetooth)
        self.g_layout_funk.addWidget(self.button_bluetooth, 5, 0, 1, 1)

        # Label za prikaz stanja bluetooth veze 
        self.label_bluetooth_state = QtWidgets.QLabel(self)
        self.label_bluetooth_state.setFixedSize(40, 40)
        self.label_bluetooth_state.setStyleSheet("border: 2px solid black; border-radius: 20px; background-color: rgb(200,200,200) ")
        self.g_layout_funk.addWidget(self.label_bluetooth_state, 5, 1, 1, 1)

         # Label za opis gumba pokreni robot
        self.label_slanje = QtWidgets.QLabel(self)
        self.label_slanje.setFont(self.font)
        self.label_slanje.setText("Slanje koraka i pokretanje robota")
        self.g_layout_funk.addWidget(self.label_slanje, 6, 0, 1, 2)

        # Gumb za slanje korana na mikrokontroler i pokretanje slaganja
        self.button_slanje = QtWidgets.QPushButton(self)
        self.button_slanje.setFont(self.font)
        self.button_slanje.setText('Pošalji korake')
        self.button_slanje.setFixedSize(120, 40)
        self.button_slanje.setStyleSheet("*{background-color: rgb(200,200,200)}")
        self.button_slanje.clicked.connect(self.slanje_koraka)
        self.g_layout_funk.addWidget(self.button_slanje, 7, 0, 1, 1)

         # Label za prikaz stanja robota (trenutno rjesava ili miruje) 
        self.label_slanje_state = QtWidgets.QLabel(self)
        self.label_slanje_state.setFixedSize(40, 40)
        self.label_slanje_state.setStyleSheet("border: 2px solid black; border-radius: 20px; background-color: rgb(200,200,200) ")
        self.g_layout_funk.addWidget(self.label_slanje_state, 7, 1, 1, 1)

        self.label_spacer = QtWidgets.QLabel(self)
        self.label_spacer.setFixedSize(10,250)
        self.g_layout_funk.addWidget(self.label_spacer, 8, 0, 1, 2)


        # Label opis koraka
        self.label_opis_koraka = QtWidgets.QLabel(self)
        self.label_opis_koraka.setFont(self.font)
        self.label_opis_koraka.setFixedSize(400, 200)
        self.label_opis_koraka.setAlignment(QtCore.Qt.AlignCenter)
        self.label_opis_koraka.setWordWrap(True)
        self.label_opis_koraka.setText("U - Gornja bijela strana \nL - Lijeva narančasta strana \nF - Prednja zelena strana \
            \nR - Desna crvena strana  \nB - Zadnja plava strana \nD - Donja žuta strana \n' - Rotacija suprotna kazaljci na satu \
            \n2 - Dvostruki okretaj stranice (180°)")
        self.label_opis_koraka.setStyleSheet("*{background-color: rgb(200,200,200)}")
        self.g_layout_funk.addWidget(self.label_opis_koraka, 9, 0, 1, 2, QtCore.Qt.AlignCenter | QtCore.Qt.AlignBottom)
        

        # Timer za privjeru statusa konekcije
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.check_connection)
        self.timer.start(4000)  # Provjera svake 4 sekunde



# Funkcije
    
    # Skaliranje dijelova aplikacije s prozorom
    def resizeEvent(self, event):
        super(Window, self).resizeEvent(event)

        new_width = event.size().width()        # Razlika po horizontali je 640px (1920 - 1280)
        new_height = event.size().height()      # Razlika po vertikali je 280px (1000 - 720)

        self.frame_main.setGeometry(9, 6, (new_width-20), (new_height-20))
        
        self.frame_kocka.setFixedSize((1200 - int((1920 - new_width) / 1.2)), (600 - int((1920 - new_width) / 4)))
        self.cube_widget_3d.setFixedSize((1200 - int((1920 - new_width) / 1.2)), (600 - int((1920 - new_width) / 4)))
        self.cube_widget_2d.setFixedSize((750 - int((1920 - new_width) / 2.8)), (560 - int((1920 - new_width) / 4)))
        self.cube_widget_2d.buttonSize((60 - int(1920 - new_width) / 36), (60- int((1920 - new_width) / 36)))

        self.frame_label.setFixedSize((1400 - int((1920 - new_width) / 1.19)), (300 - int((1920 - new_width) / 5)))
        self.frame_funk.setFixedSize((470 - int((1920 - new_width) / 6)), (914 - int((1920 - new_width) / 2.28)))
        self.label_opis_koraka.setFixedSize(400 - int((1920 - new_width) / 7), 200)
        self.label_spacer.setFixedSize(10, 250 - int((1920 - new_width) / 3))

        self.label_ispis_boja.setFixedSize((1100 - int((1920 - new_width) / 1.2)), 40)
        self.label_ispis_koraka.setFixedSize((1100 - int((1920 - new_width) / 1.2)), 40)
        self.label_ispis_pokreta.setFixedSize((1100 - int((1920 - new_width) / 1.2)), 40)



    # Funkcije za okretanje 3D modela kocke
    def rotate_cube_right(self):
        self.cube_widget_3d.rotateCube(0, 90, 0)

    def rotate_cube_left(self):
        self.cube_widget_3d.rotateCube(0, -90, 0)

    def rotate_cube_up(self):
        self.cube_widget_3d.rotateCube(0, 0, 180)


    # Funkcije za postavljanje 2D ili 3D prikaza
    def prikaz_3d(self):
        self.cube_widget_3d.setColors(self.cube_widget_2d.button_colors)
        self.cube_widget_3d.current_index = 0
        self.frame_boje.hide()
        self.cube_widget_2d.hide()
        self.frame_okreni_kocku.show()
        self.cube_widget_3d.show()

    def prikaz_2d(self):
        self.frame_okreni_kocku.hide()
        self.cube_widget_3d.hide()
        self.frame_boje.show()
        self.cube_widget_2d.show()
    

    # Funkcije za postavljanje boja buttonima
    def izaberi_boju(self):
        global prev_boja, izabrana_boja
        button = self.sender()
        for boja in boje:
            if button.objectName() == boja[0]:
                if self.button_bijela.objectName() == prev_boja:
                    self.button_bijela.setStyleSheet(f'background-color: {izabrana_boja}; border: 0px solid black')
                elif self.button_crvena.objectName() == prev_boja:
                    self.button_crvena.setStyleSheet(f'background-color: {izabrana_boja}; border: 0px solid black')
                elif self.button_narancasta.objectName() == prev_boja:
                    self.button_narancasta.setStyleSheet(f'background-color: {izabrana_boja}; border: 0px solid black')
                elif self.button_plava.objectName() == prev_boja:
                    self.button_plava.setStyleSheet(f'background-color: {izabrana_boja}; border: 0px solid black')
                elif self.button_zelena.objectName() == prev_boja:
                    self.button_zelena.setStyleSheet(f'background-color: {izabrana_boja}; border: 0px solid black')
                elif self.button_zuta.objectName() == prev_boja:
                    self.button_zuta.setStyleSheet(f'background-color: {izabrana_boja}; border: 0px solid black')

                button.setStyleSheet(f'background-color: {boja[1]}; border: 3px solid black')
                izabrana_boja = boja[1]
                prev_boja = boja[0]


    def postavi_boju(self, button_name):
        global izabrana_boja
        self.cube_widget_2d.setColor(button_name, izabrana_boja)


    def reset_2d_boje(self):
        self.cube_widget_2d.resetColors()
    

    # Funkcija za otvaranje popup prozora i snimanje kocke
    def snimi_kocku(self):
        self.label_kamera_state.setStyleSheet("border: 2px solid black; border-radius: 20px; background-color: rgb(90,255,90) ")
        self.camera_widget.start_camera()
        self.popup.exec_()
        self.camera_widget.center_colors = []
        self.camera_widget.button_colors = {}

    def ugasi_kameru(self):
        self.label_kamera_state.setStyleSheet("border: 2px solid black; border-radius: 20px; background-color: rgb(200,200,200) ")
        button_colors = self.camera_widget.button_colors
        if len(self.camera_widget.center_colors) == 6:
            self.cube_widget_2d.setScanedColors(button_colors)

        self.camera_widget.stop_camera()


    # Funkcija za dobivanje rjesenja i ispis istog
    def rijesi_kocku(self):
        koraci = kociemba.solve(self.cube_widget_2d.tileString())
        self.label_ispis_boja.setText(self.cube_widget_2d.tileString())
        self.label_ispis_koraka.setText(koraci)
        pokreti = robot_moves(koraci)

        if len(pokreti) > 100:
            pokreti = [pokreti[i:i+99] for i in range(0, len(pokreti), 99)]

        pokreti = ' '.join(pokreti)
        self.label_ispis_pokreta.setText(pokreti)


    # Funkcija za pokretanje animacije rješavanja 3D kocke
    def pokreni_animaciju(self):
        koraci = self.label_ispis_koraka.text()
        move_list = re.findall(r'[RLUDFB]\'?[0-2]?', koraci)  # Izrada liste iz stringa 
        self.cube_widget_3d.control_flag = True
        self.cube_widget_3d.animated_solve(move_list)


    # Funkcija za zaustavljanje animacije rješavanja 3D kocke
    def zaustavi_animaciju(self):
        self.cube_widget_3d.control_flag = False


    # Funkcija za postavljanje 3D kocke korak unaprijed
    def korak_unaprijed(self):
        koraci = self.label_ispis_koraka.text()
        move_list = re.findall(r'[RLUDFB]\'?[0-2]?', koraci)  # Izrada liste iz stringa 
        if not self.cube_widget_3d.cube.animate and not self.cube_widget_3d.cube.rotate_animation and self.cube_widget_3d.executed == 0:
            for x in range(len(move_list)):
                if x == self.cube_widget_3d.current_index:
                    if len(move_list[x]) == 2:
                        if  move_list[x][1] == "2":
                            self.cube_widget_3d.rotateSide(move_list[x][0], 2)
                        else:
                            self.cube_widget_3d.rotateSide(move_list[x], 1)
                    else:
                        self.cube_widget_3d.rotateSide(move_list[x], 1)

            if self.cube_widget_3d.current_index < len(move_list):
                self.cube_widget_3d.current_index += 1


    # Funkcija za postavljanje 3D kocke korak unazad
    def korak_unazad(self):
        koraci = self.label_ispis_koraka.text()
        move_list = re.findall(r'[RLUDFB]\'?[0-2]?', koraci)  # Izrada liste iz stringa 
        new_move = ""

        if not self.cube_widget_3d.cube.animate and not self.cube_widget_3d.cube.rotate_animation and self.cube_widget_3d.executed == 0:
            for x, move in enumerate(move_list, start=1):
                if x == self.cube_widget_3d.current_index:
                    if len(move) == 2:
                        if move[1] == "2":
                            new_move = move[0] + "'"
                            self.cube_widget_3d.rotateSide(new_move, 2)
                        else:
                            new_move = move[0]
                            self.cube_widget_3d.rotateSide(new_move, 1)
                    else:
                        new_move = move + "'"
                        self.cube_widget_3d.rotateSide(new_move, 1)

            self.cube_widget_3d.rotateSide(new_move, 1)
            self.cube_widget_3d.current_index -= 1

    # Funkcija za spajanje bluetooth uređaja
    def spajanje_bluetooth(self):
        self.label_bluetooth_state.setStyleSheet("border: 2px solid black; border-radius: 20px; background-color: rgb(90,255,90) ")
        
        self.bt_worker = BluetoothWorker()
        self.bt_worker.connection_status.connect(self.on_connection_status)
        self.bt_worker.start()

    def on_connection_status(self, success, message):
        if success:
            self.sock = self.bt_worker.sock
            self.label_provjera.setText(message)
            self.label_bluetooth_state.setStyleSheet("border: 2px solid black; border-radius: 20px; background-color: rgb(45,90,255) ")  
        else:
            self.label_provjera.setText(message)
            self.label_bluetooth_state.setStyleSheet("border: 2px solid black; border-radius: 20px; background-color: rgb(220,0,0) ")
            return


    # Funkcija za slanje koraka na mikrokontroler putem bluetooth veze
    def slanje_koraka(self):
        if self.sock is None:
            self.label_slanje_state.setStyleSheet("border: 2px solid black; border-radius: 20px; background-color: rgb(220,0,0) ")
            return

        message = self.label_ispis_pokreta.text()
        message = message.replace(" ", "") 

        if message:
            self.sock.send(message)
            self.label_slanje_state.setStyleSheet("border: 2px solid black; border-radius: 20px; background-color: rgb(90,255,90) ")
        else:
            self.label_slanje_state.setStyleSheet("border: 2px solid black; border-radius: 20px; background-color: rgb(200,200,200) ")

    # Funkcija za provjeru konekcije   
    def check_connection(self):
        if self.sock:
            try:
                self.sock.send("ping".encode('utf-8'))
                self.label_bluetooth_state.setStyleSheet("border: 2px solid black; border-radius: 20px; background-color: rgb(20,40,255) ")
            except:
                self.label_bluetooth_state.setStyleSheet("border: 2px solid black; border-radius: 20px; background-color: rgb(200,200,200) ")
                self.sock.close()
                self.sock = None


app = QtWidgets.QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec_())
