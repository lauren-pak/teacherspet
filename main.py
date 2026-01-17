import cv2 as cv
from ultralytics import YOLO
from collections import deque
import time
import sys
from PySide6 import QtWidgets, QtCore

# import files
from camera import Camera
from effects import HeartbeatOverlay

effects = HeartbeatOverlay()

def main():
    cam = Camera()

    INIT_SECONDS = 5
    init_deadline = time.monotonic() + INIT_SECONDS

    EFFECT_DURATION = 5
    COOLDOWN_SECONDS = 3
    next_allowed_effect_time = 0.0

    try:
        while True:
            ok, frame = cam.cap.read()
            if not ok:
                break

            H, W = frame.shape[:2]
            cx, cy = W / 2.0, H / 2.0

            # person detection
            person_boxes = cam._get_person_boxes(frame)
            cam._init_me(person_boxes, cx, cy)
            cam._update_me(person_boxes)

            # min closest area = 3% of frame
            min_closest_area = int(0.03 * W * H)

            other_people, closest_box, closest_conf, found_other = cam._find_others(
                person_boxes, min_closest_area=min_closest_area
            )

            # stability
            cam.other_hits.append(found_other)
            stable_other = (sum(cam.other_hits) >= cam.other_trigger)

            # teacher condition
            is_teacher = (cam.me_box is not None and stable_other)

            if stable_other:
                cv.putText(frame, "BACKGROUND PERSON DETECTED!", (20, 50),
                           cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)

            cam._draw(frame, other_people, closest_box, closest_conf)
            cv.imshow("TeachersPet's vision", frame)

            now = time.monotonic()
            if now >= init_deadline and is_teacher and now >= next_allowed_effect_time:
                next_allowed_effect_time = now + COOLDOWN_SECONDS
                effects.run_overlay_process(duration=EFFECT_DURATION)

            if cv.waitKey(1) & 0xFF == ord('q'):
                break

            cam.frame_count += 1

    finally:
        cam.cap.release()
        cv.destroyAllWindows()


if __name__ == "__main__":
    # overlay-mode (subprocess)
    if len(sys.argv) >= 3 and sys.argv[1] == "--overlay":
        effects.overlay_main(duration=int(sys.argv[2]))
    else:
        main()