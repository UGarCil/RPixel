# import pygame 
import os 
import cv2 
import argparse
from os.path import join as jn
from collections import namedtuple

import random
import json 

import sys
import cv2
import numpy as np
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QImage, QPixmap, QKeySequence
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton,QColorDialog,QMessageBox,QShortcut
import uuid

from datetime import datetime


# Determine the width and height ratio of the camera
from picamera2 import Picamera2
import time
########################### ARGPARSE arguments ###################################
# parser = argparse.ArgumentParser(description='Multistack with the picamera and raspberry pi')
# args = parser.parse_args()

##################################################################################
# pygame.init()
# display_info = pygame.display.Info()
# define the dimensions of the screen
# W = int(display_info.current_w*args.res)
# H = int(W*cameraRatio)
# W = 1920
# H = 1080




cap = Picamera2() 
cap.preview_configuration.main.size = (640,480)
cap.preview_configuration.main.format = "RGB888"
cap.preview_configuration.align() 
cap.configure("preview")
cap.start() 


# DD LATERAL_PADDING_MENU
# LATERAL_PADDING = (int,int)
# interp. how many pixels to leave as padding to accomodate the lateral panel of the application
# Define the named tuple with fields 'x' and 'y'
Coordinate = namedtuple('Coordinate', ['x', 'y'])
LATERAL_PADDING = Coordinate(400,0)
TOP_PADDING = Coordinate(0,80)

# DD. SAVEPATH 
# savePath = str
# interp. the location of the file that will store the program's output
savePath = jn(os.path.dirname(__file__),"output.txt")

# DD. BRUSH_SETTINGS
# brush_settings = {"color":(int, int, int)}
# interp. a set of parameters represented as a mutable object to be used globally within different submodules of the program
brush_settings = {"color":(0, 255, 0), "size":20,"resize_sensitivity":5, "is_brush_mode":"brush"}

# DD. DISPLAY_SETTINGS
# display_settings = {"image":np.array, "mask":np.array}
# interp. a set of numpy arrays representing images and masks for the program
display_settings = {"image":None, "mask":None}

cursor_settings = {"in_display":False}

os_settings = {"project_folder":"", "current_folder":"", "current_prefix":""}