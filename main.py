import cv2 as cv
from ultralytics import YOLO
from collections import deque
import time
# import files
from camera import Camera

print("hello1")
def teachersPet():
    print("hello")
    new_camera = Camera()
    new_camera.run()

    #wait initialisation time
    time.sleep(10)


teachersPet()
