import cv2 as cv
from ultralytics import YOLO
from collections import deque
import time
import sys
from PySide6 import QtWidgets

# import files
from camera import Camera
from effects import HeartbeatOverlay

cam = Camera()

def run_camera():
    try:
        while True:
            ok, frame = cam.cap.read()
            if not ok:
                break

            H, W = frame.shape[:2]
            cx, cy = W / 2.0, H / 2.0

            person_boxes = cam._get_person_boxes(frame)

            cam._init_me(person_boxes, cx, cy)
            cam._update_me(person_boxes)

            other_people, closest_box, closest_conf, found_other = cam._find_others(person_boxes)

            # Alert smoothing
            cam.other_hits.append(found_other)
            if sum(cam.other_hits) >= cam.other_trigger:
                cv.putText(frame, "BACKGROUND PERSON DETECTED!", (20, 50),
                            cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)

            cam._draw(frame, other_people, closest_box, closest_conf)

            cv.imshow("TeachersPet's vision", frame)
            if cv.waitKey(1) & 0xFF == ord('q'):
                break

            cam.frame_count += 1

    finally:
        cam.cap.release()
        cv.destroyAllWindows()

def run_effects():
    print("here")
    app = QtWidgets.QApplication(sys.argv)
    overlay = HeartbeatOverlay()

    overlay.show()  #shows just the red fade.
    overlay.heartbeat()
    overlay.start_shake_cursor()
    print("here")
    sys.exit(app.exec())
    time.sleep(5)


def teachersPet():
    run_camera()

    #wait initialisation time
    time.sleep(10)



run_effects()