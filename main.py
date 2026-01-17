import cv2 as cv
import time
import threading, sys
from effects import HeartbeatOverlay
from PySide6 import QtWidgets, QtCore
import subprocess
from camera import Camera
from voiceeffect import relaymessage
from working_user import get_chrome_active_domain
from heart import VideoOverlay
from pathlib import Path


def main():
    cam = Camera()
    overlay = None
    app = QtWidgets.QApplication(sys.argv)

    #heart animation overlay
    video_overlay = VideoOverlay(
    Path(__file__).parent / "graphics" / "heart_animation.mp4",
    size=(450, 450)
    )
    
    voice_lock = threading.Lock()
    voice_busy = False
    teacher_present = False
    teacher_handled = False

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

            min_closest_area = int(0.1 * W * H)

            other_people, closest_box, closest_conf, found_other = cam._find_others(
                person_boxes, min_closest_area=min_closest_area
            )

            # stability
            cam.other_hits.append(1 if found_other else 0)
            stable_other = (sum(cam.other_hits) >= cam.other_trigger)
            
    
            is_teacher_now = (cam.me_box is not None and stable_other and closest_box is not None)
    

            # teacher enters frame
            if is_teacher_now and not teacher_present:
                teacher_present = True
                teacher_handled = False   # reset latch on entry

            # teacher leaves frame
            elif not is_teacher_now and teacher_present:
                teacher_present = False
                teacher_handled = False  # optional, but clean


            if teacher_present and not teacher_handled:
                url, is_illegal = get_chrome_active_domain()
                cv.putText(
                    frame,
                    f"Teacher present: {teacher_present}",
                    (20, 90),
                    cv.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 0),
                    2
                )

                if is_illegal:
                    # subprocess.run(["osascript", "-e", "set volume output volume 100"])
                    print("here")
                    if overlay is None:
                        video_overlay.start()
                        overlay = HeartbeatOverlay()
                        overlay.show()
                        overlay.start_heartbeat()
                        overlay.start_shake_cursor()
                        

                    if(not teacher_handled):
                        with voice_lock:
                            if not voice_busy:
                                voice_busy = True

                                def runner(u=url):
                                    nonlocal voice_busy
                                    try:
                                        relaymessage(u) 

                                    except Exception as e:
                                        print(f"[voice] relaymessage failed: {e}")
                                    finally:
                                        with voice_lock:
                                            voice_busy = False

                                threading.Thread(target=runner, daemon=True).start()
                                teacher_handled = True
            elif not teacher_present:
                if overlay is not None:
                    video_overlay.stop()
                    overlay.stop_heartbeat()
                    overlay._shake_cursor_running = False
                    overlay.close()
                    overlay.deleteLater()
                    overlay = None
                    




            if stable_other:
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

    app.quit()

    


if __name__ == "__main__":
    main()
