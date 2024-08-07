import sys
import numpy as np
import time

from PyQt5 import QtWidgets, QtGui, QtCore
from OpenGL.GL import *
from OpenGL.GLU import *


vertices = (
    (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, -1),
    (1, -1, 1), (1, 1, 1), (-1, -1, 1), (-1, 1, 1)
)

edges = ((0, 1), (0, 3), (0, 4), (2, 1), (2, 3), (2, 7), (6, 3), (6, 4), (6, 7), (5, 1), (5, 4), (5, 7))
surfaces = ((0, 1, 2, 3), (3, 2, 7, 6), (6, 7, 5, 4), (4, 5, 1, 0), (1, 5, 7, 2), (4, 0, 3, 6))



# Define a function to convert the RGB string to a tuple
def rgb_string_to_tuple(color):
    rgb = color.lstrip('rgb(').rstrip(')').split(',')
    tuple_color = tuple(int(x) / 255.0 for x in rgb)
    
    return tuple_color


def cube_position_dict(color_dict):
    cube_faces = {}

    face_map = {
        'U': (2, 'y', 2, 4),  # Up
        'D': (0, 'y', 0, 5),  # Down
        'L': (0, 'x', 0, 1),  # Left
        'R': (2, 'x', 2, 3),  # Right
        'F': (2, 'z', 2, 2),  # Front
        'B': (0, 'z', 0, 0)   # Back
    }

    for tile, color in color_dict.items():
        face_key, index = tile[0], int(tile[1]) - 1
        face_axis, const_axis, const_val, face = face_map[face_key]

        if const_axis == 'x':
            pos = (const_val, 2 - (index // 3), index % 3)
        elif const_axis == 'y':
            pos = (index % 3, const_val, 2 - (index // 3))
        elif const_axis == 'z':
            pos = (index % 3, 2 - (index // 3), const_val)

        # Adjust the positions for flipped faces
        if face_key == 'U':
            pos = (pos[0], pos[1], 2 - pos[2])
        elif face_key == 'R':
            pos = (pos[0], pos[1], 2 - pos[2])
        elif face_key == 'B':
            pos = (2 - pos[0], pos[1], pos[2])

        if pos not in cube_faces:
            cube_faces[pos] = []
        cube_faces[pos].append((face, color))

    return cube_faces


class Cube():
    def __init__(self, id, N, scale, cube_faces_dict):
        self.N = N
        self.scale = scale
        self.cube_faces_dict = cube_faces_dict
        self.init_i = [*id]
        self.current_i = [*id]
        self.rot = [[1 if i == j else 0 for i in range(3)] for j in range(3)]

    def isAffected(self, axis, slice, dir):
        return self.current_i[axis] == slice

    def update(self, axis, slice, dir):
        if not self.isAffected(axis, slice, dir):
            return
        i, j = (axis + 1) % 3, (axis + 2) % 3
        for k in range(3):
            self.rot[k][i], self.rot[k][j] = -self.rot[k][j] * dir, self.rot[k][i] * dir
        self.current_i[i], self.current_i[j] = (
            self.current_i[j] if dir < 0 else self.N - 1 - self.current_i[j],
            self.current_i[i] if dir > 0 else self.N - 1 - self.current_i[i])

    def transformMat(self):
        scaleA = [[s * self.scale for s in a] for a in self.rot]
        scaleT = [(p - (self.N - 1) / 2) * 2.1 * self.scale * 0.96 for p in self.current_i]
        return [*scaleA[0], 0, *scaleA[1], 0, *scaleA[2], 0, *scaleT, 1]


    def draw(self, surf, vert, animate, angle, axis, slice, dir):
        glPushMatrix()
        if animate and self.isAffected(axis, slice, dir):
            glRotatef(angle * dir, *[1 if i == axis else 0 for i in range(3)])
        glMultMatrixf(self.transformMat())

        position = tuple(self.init_i)
        face_colors = {i: (0.5, 0.5, 0.5) for i in range(6)}  # Default to gray

        if position in self.cube_faces_dict:
            for face, color in self.cube_faces_dict[position]:
                face_colors[face] = rgb_string_to_tuple(color)

        glBegin(GL_QUADS)
        for i, surface in enumerate(surfaces):
            glColor3fv(face_colors[i])  # Apply color for each face
            for vertex in surface:
                glVertex3fv(vertices[vertex])
        glEnd()

        # Draw the edges of the cube
        glLineWidth(2)  # Set the line width
        glColor3f(0, 0, 0)  # Set color to black for the edges
        glBegin(GL_LINES)  # Start drawing lines
        for edge in edges:
            for vertex in edge:
                glVertex3fv(vertices[vertex])  # Specify the vertices for each edge
        glEnd()  # End drawing lines

        glPopMatrix()

class EntireCube():
    def __init__(self, N, scale):
        self.N = N
        self.scale = scale
        self.cube_faces_dict ={}
        self.color_positions({})
        self.ang_x, self.ang_y, self.ang_z = 0, 0, 0
        self.animate, self.animate_ang, self.animate_speed = False, 0, 5
        self.action = (0, 0, 0)
        self.rotate_animation = False
        self.rotate_angle = 0
        self.rotate_axis = (0, 0, 0)


    def color_positions(self, tile_colors):
        self.tile_colors = tile_colors
        self.cube_faces_dict = cube_position_dict(self.tile_colors)
        self.cubes = [Cube((x, y, z), self.N, self.scale, self.cube_faces_dict) for x in range(self.N) for y in range(self.N) for z in range(self.N)]


    def keyPressEvent(self, event):
        if not self.animate and not self.rotate_animation:
            if event == "L":
                self.animate, self.action = True, (0, 0, 1)
            elif event == "R'":
                self.animate, self.action = True, (0, 2, 1)
            elif event == "U'":
                self.animate, self.action = True, (1, 2, 1)
            elif event == "D":
                self.animate, self.action = True, (1, 0, 1)
            elif event == "F'":
                self.animate, self.action = True, (2, 2, 1)
            elif event == "B":
                self.animate, self.action = True, (2, 0, 1)
            elif event == "L'":
                self.animate, self.action = True, (0, 0, -1)
            elif event == "R":
                self.animate, self.action = True, (0, 2, -1)
            elif event == "U":
                self.animate, self.action = True, (1, 2, -1)
            elif event == "D'":
                self.animate, self.action = True, (1, 0, -1)
            elif event == "F":
                self.animate, self.action = True, (2, 2, -1)
            elif event == "B'":
                self.animate, self.action = True, (2, 0, -1)


    def update_animation(self):
        if self.animate:
            if self.animate_ang >= 90:
                for cube in self.cubes:
                    cube.update(*self.action)
                self.animate, self.animate_ang = False, 0
            else:
                self.animate_ang += self.animate_speed
    
        elif self.rotate_animation:
            if not self.rotate_axis[2]:
                if self.rotate_angle >= 90:
                    self.rotate_animation = False
                    self.rotate_angle = 0
                    self.ang_y += self.rotate_axis[1]
                    if self.ang_y == 360:
                        self.ang_y = 0
                    if self.ang_y == -360:
                        self.ang_y = 0

                else:
                    self.rotate_angle += self.animate_speed

            else:
                if self.rotate_angle >= 180:
                    self.rotate_animation = False
                    self.rotate_angle = 0
                    if self.ang_y == 0 or self.ang_y == 180 or self.ang_y == -180:
                        self.ang_z += self.rotate_axis[2]
                        if self.ang_z == 360:
                            self.ang_z = 0

                    elif self.ang_y == 90 or self.ang_y == -90 or self.ang_y == 270 or self.ang_y == -270:
                        self.ang_z += self.rotate_axis[2]
                        self.ang_y += 180
                        if self.ang_z == 360:
                            self.ang_z = 0
                        if self.ang_y == 450:
                            self.ang_y = 90
                else:
                    self.rotate_angle += self.animate_speed
            


    def rotateCube(self, x, y, z):
        if not self.animate and not self.rotate_animation:
            self.rotate_animation = True
            self.rotate_axis = (x, y, z)



class Cube3DWidget(QtWidgets.QOpenGLWidget):
    def __init__(self, parent=None):
        super(Cube3DWidget, self).__init__(parent)
        self.cube = EntireCube(N=3, scale=1)  # Create the entire cube
        self.timer = QtCore.QTimer()  # Create a timer to regularly update the widget
        self.timer.timeout.connect(self.update)  # Connect the timer to the update method
        self.timer.start(16)  # Start the timer (approximately 60 FPS)
        self.setMinimumSize(600, 600)
        self.executed = 0
        self.control_flag = False
        self.current_index = 0


    def initializeGL(self):
        glClearColor(1, 1, 1, 1)  # Set the background color to white
        glEnable(GL_DEPTH_TEST)  # Enable depth testing for correct rendering of 3D objects

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)  # Set the viewport to the new window dimensions
        glMatrixMode(GL_PROJECTION)  # Switch to the projection matrix
        glLoadIdentity()  # Reset the projection matrix
        gluPerspective(45, w / h, 1, 100)  # Set the perspective projection
        glMatrixMode(GL_MODELVIEW)  # Switch back to the modelview matrix

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # Clear the color and depth buffers
        glLoadIdentity()  # Reset the modelview matrix
        glTranslatef(0, 0, -10)  # Move the matrix
        gluLookAt(5, 5, 5, 0, 0, 0, 0, 1, 0)  # Set the camera position and orientation

        if self.cube.rotate_animation:
            glRotatef(self.cube.rotate_angle, *self.cube.rotate_axis)
            
        glRotatef(self.cube.ang_x, 1, 0, 0)
        glRotatef(self.cube.ang_y, 0, 1, 0)
        glRotatef(self.cube.ang_z, 0, 0, 1)

        self.cube.update_animation()
    
        for cube in self.cube.cubes:
            cube.draw(surfaces, vertices, self.cube.animate, self.cube.animate_ang, *self.cube.action)


    def rotateSide(self, event, execute):
        self.executed = execute

        if execute > 0:
            self.cube.keyPressEvent(event)
            execute -= 1
            self.executed -= 1
            if execute > 0:
                QtCore.QTimer.singleShot(500, lambda: self.rotateSide(event, execute))  # Pricekaj pola sekunde da prvi korak zavrsi
 


    def rotateCube(self, x, y, z):
        self.cube.rotateCube(x, y, z)


    def setColors(self, colors):
        self.cube.color_positions(colors)
        self.update()


    def animated_solve(self, library):
        solve_timer = QtCore.QTimer(self)
        if self.control_flag and self.current_index < len(library) :
            if not self.cube.animate and not self.cube.rotate_animation and self.executed == 0:
                if len(library[self.current_index]) == 2:
                    if  library[self.current_index][1] == "2":
                        self.rotateSide(library[self.current_index][0], 2)
                    else:
                        self.rotateSide(library[self.current_index], 1)
                else:
                    self.rotateSide(library[self.current_index], 1)
                
                self.current_index += 1

                solve_timer.start(2500)  # Timer 2 sec
                solve_timer.timeout.connect(lambda: self.animated_solve(library))

            if self.current_index == len(library):
                self.control_flag = False
                
        

