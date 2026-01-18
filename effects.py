from PySide6 import QtWidgets, QtCore, QtGui, QtMultimedia
import sys, random, threading, pyautogui, time, platform
from pathlib import Path

if platform.system() == "Darwin":
    from AppKit import NSApp, NSFloatingWindowLevel


class HeartbeatOverlay(QtWidgets.QWidget):
    def __init__(self, speed=70, color=139, opacity=60):
        super().__init__()

        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        screen = QtWidgets.QApplication.primaryScreen().geometry()

        self.speed = int(speed)   # ms between lub and dub
        self.color = int(color)

        expand = 50
        x = screen.x() - expand
        y = screen.y() - expand
        width = screen.width() + 2 * expand
        height = screen.height() + 2 * expand
        self.setGeometry(x, y, width, height)

        self.base_pos = self.pos()

        # heartbeat variables
        self.opacity = int(opacity)
        self.max_opacity = 170
        self._heartbeat_running = False

        self.fade_timer = QtCore.QTimer(self)
        self.fade_timer.timeout.connect(self.fade_step)
        self.fade_timer.start(16)

        # cursor shake
        self._shake_cursor_running = False

        if platform.system() == "Darwin":
            QtCore.QTimer.singleShot(0, self._enable_macos_fullscreen_overlay)

    def _init_mp3(self, mp3_path, volume):
        p = Path(mp3_path)

        # Make relative paths work regardless of working directory
        if not p.is_absolute():
            p = Path(__file__).parent / p

        if not p.exists():
            print(f"[HeartbeatOverlay] MP3 not found: {p}")
            return


    def set_speed(self, speed):
        self.speed = max(50, int(speed))  # clamp so it never breaks

    def _enable_macos_fullscreen_overlay(self):
        try:
            ns_window = NSApp().windows()[0]
        except Exception:
            return

        ns_window.setLevel_(NSFloatingWindowLevel)
        ns_window.setCollectionBehavior_(
            (1 << 0) |  # CanJoinAllSpaces
            (1 << 7)    # FullScreenAuxiliary
        )

    def start_heartbeat(self):
        self._heartbeat_running = True
        self.do_lub()

    def do_lub(self):
        if not self._heartbeat_running:
            return

        self.opacity = self.max_opacity
        self.update()

        QtCore.QTimer.singleShot(self.speed, self.do_dub)

    def do_dub(self):
        if not self._heartbeat_running:
            return

        self.opacity = self.max_opacity - 30
        self.update()

        QtCore.QTimer.singleShot(self.speed, self.do_lub)

    def stop_heartbeat(self):
        self._heartbeat_running = False
        self.opacity = 30
        self.update()
        self._shake_cursor_running = False

        if self.player is not None:
            self.player.stop()

    def fade_step(self):
        if self.opacity > 30:
            self.opacity -= 3
            self.update()

    def start_shake_cursor(self, intensity=10, frequency=0.05):
        self._shake_cursor_running = True

        def run():
            dx, dy = intensity, intensity
            pyautogui.PAUSE = 0
            while self._shake_cursor_running:
                x, y = pyautogui.position()
                pyautogui.moveTo(x + dx, y + dy)
                dx *= -1
                dy *= -1
                time.sleep(frequency)

        threading.Thread(target=run, daemon=True).start()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        gradient = QtGui.QRadialGradient(
            self.width() // 2,
            self.height() // 2,
            max(self.width(), self.height()) // 2
        )
        gradient.setColorAt(0.8, QtGui.QColor(0, 0, 0, 0))
        gradient.setColorAt(1.0, QtGui.QColor(self.color, 0, 0, self.opacity))
        painter.fillRect(self.rect(), gradient)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    overlay = HeartbeatOverlay(
        speed=120, 
    )
    overlay.show()
    overlay.start_heartbeat()
    overlay.start_shake_cursor()

    sys.exit(app.exec())
