import cv2 as cv
import time
import threading, sys
from effects import HeartbeatOverlay
from animation import PopupImages
from PySide6 import QtWidgets, QtCore
import subprocess
from camera import Camera
from voiceeffect import relaymessage
from working_user import get_chrome_active_domain
from heart import VideoOverlay
from pathlib import Path


def main():
    army = None
    overlay = None

    cam = Camera()
    app = QtWidgets.QApplication(sys.argv)

    video_overlay = VideoOverlay(
    Path(__file__).parent / "images" / "heart_animation.mp4",
    size=(450, 450)
    )

    voice_lock = threading.Lock()
    voice_busy = False
    teacher_present = False
    teacher_handled = False

    def process_frame():
        nonlocal army, overlay, voice_busy, teacher_present, teacher_handled

        ok, frame = cam.cap.read()
        if not ok:
            return

        H, W = frame.shape[:2]
        cx, cy = W / 2.0, H / 2.0

        person_boxes = cam._get_person_boxes(frame)
        cam._init_me(person_boxes, cx, cy)
        cam._update_me(person_boxes)

        min_closest_area = int(0.1 * W * H)

        other_people, closest_box, closest_conf, found_other = cam._find_others(
            person_boxes, min_closest_area=min_closest_area
        )

        cam.other_hits.append(1 if found_other else 0)
        stable_other = (sum(cam.other_hits) >= cam.other_trigger)

        is_teacher_now = (
            cam.me_box is not None and stable_other and closest_box is not None
        )

        if is_teacher_now and not teacher_present:
            teacher_present = True
            teacher_handled = False

        elif not is_teacher_now and teacher_present:
            teacher_present = False
            teacher_handled = False

        if teacher_present and not teacher_handled:
            url, is_illegal = get_chrome_active_domain()

            if is_illegal:
                if army is None:
                    army = PopupImages("images/army1.png", "images/army2.png", 200)

                if overlay is None:
                    video_overlay.start()
                    overlay = HeartbeatOverlay()
                    overlay.show()
                    overlay.start_heartbeat()
                    overlay.start_shake_cursor()

                def runner(u=url):
                    nonlocal voice_busy
                    try:
                        audiosamplelen = relaymessage(u)
                        QtCore.QTimer.singleShot(0, army.start_animation)
                        QtCore.QTimer.singleShot(
                            audiosamplelen, army.stop_animation
                        )
                    finally:
                        with voice_lock:
                            voice_busy = False

                with voice_lock:
                    if not voice_busy:
                        voice_busy = True
                        threading.Thread(target=runner, daemon=True).start()
                        teacher_handled = True

        elif not teacher_present:
            if army:
                army.close()
                army.deleteLater()
                army = None

            if overlay:
                video_overlay.stop()
                overlay.stop_heartbeat()
                overlay.close()
                overlay.deleteLater()
                overlay = None

        cam._draw(frame, other_people, closest_box, closest_conf)
        cv.imshow("TeachersPet's vision", frame)

        if cv.waitKey(1) & 0xFF == ord('q'):
            app.quit()

        cam.frame_count += 1
    
    timer = QtCore.QTimer()
    timer.timeout.connect(process_frame)
    timer.start(1)  # ~1000 FPS max, camera will cap it anyway

    sys.exit(app.exec())


    


if __name__ == "__main__":
    main()
