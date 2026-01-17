import cv2 as cv
from ultralytics import YOLO
from collections import deque
import time
import sys
from PySide6 import QtWidgets, QtCore

# import files
from camera import Camera
from effects import HeartbeatOverlay

cam = Camera()
overlay = HeartbeatOverlay()

IsTeacher = False

def run_camera(frame):

    H, W = frame.shape[:2]
    cx, cy = W / 2.0, H / 2.0

    person_boxes = cam._get_person_boxes(frame)

    cam._init_me(person_boxes, cx, cy)
    cam._update_me(person_boxes)

    other_people, closest_box, closest_conf, found_other = cam._find_others(person_boxes)
    
    if cam.me_box is not None and other_people:
        IsTeacher = True
    else:
        IsTeacher = False

    # Alert smoothing
    cam.other_hits.append(found_other)
    if sum(cam.other_hits) >= cam.other_trigger:
        cv.putText(frame, "BACKGROUND PERSON DETECTED!", (20, 50),
                    cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)

    cam._draw(frame, other_people, closest_box, closest_conf)

    cv.imshow("TeachersPet's vision", frame)
    
    cam.frame_count += 1

def run_effects(duration=5):
    app = QtWidgets.QApplication.instance()
    created = False
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
        created = True

    overlay.show()
    overlay.start_heartbeat()
    overlay.start_shake_cursor(duration=duration)

    # stop overlay after duration seconds
    QtCore.QTimer.singleShot(duration * 1000, overlay.stop_all)

    if created:
        app.exec()




def teachersPet():
    try:
        while True:
            ok, frame = cam.cap.read()
            if not ok:
                break

            run_camera(frame)

            while IsTeacher:
                run_effects()
                
            overlay.closeEvent()
            if cv.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cam.cap.release()
        cv.destroyAllWindows()




teachersPet()