import cv2 as cv
import time
import threading, sys
from effects import HeartbeatOverlay
from animation import PopupImages
from PySide6 import QtWidgets, QtCore, QtMultimedia
from camera import Camera
from voiceeffect import relaymessage
from working_user import get_chrome_active_domain
from pathlib import Path
from elevenlabs.play import play
from datetime import datetime

def speed_from_seconds(t):
    start = 500   
    end   = 80    
    k = min(1.0, t / 15.0)
    return int(start + (end - start) * k)

def main():
    army = None
    overlay = None

    cam = Camera()
    app = QtWidgets.QApplication(sys.argv)

    alarm_path = Path(__file__).parent / "sounds" / "siren.mp3"  

    alarm_audio_out = QtMultimedia.QAudioOutput()
    alarm_audio_out.setVolume(0.5)

    alarm_player = QtMultimedia.QMediaPlayer()
    alarm_player.setAudioOutput(alarm_audio_out)
    alarm_player.setSource(QtCore.QUrl.fromLocalFile(str(alarm_path.resolve())))

    voice_lock = threading.Lock()
    voice_busy = False
    teacher_present = False
    teacher_handled = False
    teacher_enter_time = None  

    def process_frame():
        nonlocal army, overlay, voice_busy, teacher_present, teacher_handled, teacher_enter_time

        ok, frame = cam.cap.read()
        if not ok:
            return

        now = time.monotonic()

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

        is_teacher_now = (cam.me_box is not None and stable_other and closest_box is not None)

        if is_teacher_now and not teacher_present:
            teacher_present = True
            teacher_handled = False
            teacher_enter_time = now

        elif not is_teacher_now and teacher_present:
            teacher_present = False
            teacher_handled = False
            teacher_enter_time = None

        if teacher_present and not teacher_handled:
            url, is_illegal = get_chrome_active_domain()

            if is_illegal: # if chrome tab is in the illegal list

                if overlay is None: # no current visual overlays
                    overlay = HeartbeatOverlay()
                    overlay.show()

                    overlay.raise_()  # bring overlay to front
                    overlay.activateWindow() 
                    overlay.setAttribute(QtCore.Qt.WA_AlwaysStackOnTop) 

                    overlay.start_heartbeat()
                    overlay.start_shake_cursor()
                    alarm_player.play()

                if army is None: # check if quacker is in the scene
                    army = PopupImages("images/army2.png", "images/army1.png", 100)
                    army.raise_()

                if overlay and teacher_enter_time is not None: 
                    elapsed = now - teacher_enter_time
                    overlay.set_speed(speed_from_seconds(elapsed))

                def runner(u=url):
                    nonlocal voice_busy
                    try:
                        print("[audio] runner start")

                        result = relaymessage(u)
                        if not result:
                            print("[audio] relaymessage failed (quota?). Skipping.")
                            return

                        audio_bytes, duration_ms = result

                        # start anim with the tts
                        def start_anim():
                            if army:
                                print(f"animation started at {datetime.now()}")
                                print("start anim")
                                army.start_animation()

                        QtCore.QTimer.singleShot(0, app, start_anim)

                        play(audio_bytes)

                        #Stop animation on Qt thread (immediately after playback ends)
                        def stop_anim():
                            if army:
                                print(f"animation stopped at {datetime.now()}")
                                print("stop anim")
                                army.stop_animation()

                        QtCore.QTimer.singleShot(0, app, stop_anim)

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
                overlay.stop_heartbeat()
                overlay.close()
                alarm_player.stop()
                overlay.deleteLater()
                overlay = None
                

        cam._draw(frame, other_people, closest_box, closest_conf)
        # cv.imshow("TeachersPet's vision", frame)

        if cv.waitKey(1) & 0xFF == ord('q'):
            app.quit()

        cam.frame_count += 1

    timer = QtCore.QTimer()
    timer.timeout.connect(process_frame)
    timer.start(16)  

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
