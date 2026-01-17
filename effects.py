from PySide6 import QtWidgets, QtCore, QtGui
import sys, random, platform, threading
import pyautogui
import time
import subprocess

if platform.system() == "Windows":
    import win32gui
    import win32con


class HeartbeatOverlay(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )

        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        screen = QtWidgets.QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.base_pos = self.pos()

        self.opacity = 50
        self.max_opacity = 170

        self.fade_timer = QtCore.QTimer(self)
        self.fade_timer.timeout.connect(self.fade_step)

        self._shake_cursor_running = False
        self._heartbeat_running = False 

    def closeEvent(self, event):
        self.stop_all()
        event.accept()

    def start_shake_cursor(self, duration=5, intensity=10, frequency=0.05):
        self._shake_cursor_running = True

        def stop():
            self._shake_cursor_running = False

        def run():
            dx = intensity
            dy = intensity
            pyautogui.PAUSE = 0  # disable built-in pause

            while self._shake_cursor_running:
                x, y = pyautogui.position()
                pyautogui.moveTo(x + dx, y + dy)
                dx *= -1
                dy *= -1
                time.sleep(frequency)

        threading.Thread(target=run, daemon=True).start()
        threading.Timer(duration, stop).start()

    def stop_shake_cursor(self):
        self._shake_cursor_running = False

    # ---------------- Click-through ----------------
    def make_clickthrough(self):
        if platform.system() == "Windows":
            hwnd = self.winId().__int__()
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            ex_style |= win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
        elif platform.system() == "Darwin":
            try:
                ns_window = self.window().windowHandle().nativeInterface().objcInstance()
                ns_window.setIgnoresMouseEvents_(True)
            except Exception as e:
                print("macOS click-through failed:", e)

    def start_heartbeat(self):
        """Call this once to begin looping heartbeat."""
        self._heartbeat_running = True
        self.heartbeat()

    def stop_heartbeat(self):
        self._heartbeat_running = False
        self.fade_timer.stop()

    def stop_all(self):
        """Stop everything and close overlay."""
        self.stop_heartbeat()
        self.stop_shake_cursor()
        self.close()

    def heartbeat(self, interval_ms=16):
        if not self._heartbeat_running:  # ✅ NEW
            return

        # First beat (lub)
        self.opacity = self.max_opacity
        self.update()
        self.shake()

        self.fade_timer.start(interval_ms)

        QtCore.QTimer.singleShot(120, self.second_beat)

        next_interval = 420
        QtCore.QTimer.singleShot(next_interval, self.heartbeat)

    def second_beat(self):
        if not self._heartbeat_running:  # ✅ NEW
            return

        self.opacity = self.max_opacity - 30
        self.update()
        self.shake(intensity=4)
        self.fade_timer.start(16)

    def fade_step(self):
        self.opacity -= 5
        if self.opacity <= 60:
            self.opacity = 60
            self.fade_timer.stop()
        self.update()

    def shake(self, intensity=6):
        dx = random.randint(-intensity, intensity)
        dy = random.randint(-intensity, intensity)
        self.move(self.base_pos.x() + dx, self.base_pos.y() + dy)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        gradient = QtGui.QRadialGradient(
            self.width() // 2,
            self.height() // 2,
            max(self.width(), self.height()) // 2
        )
        gradient.setColorAt(0.7, QtGui.QColor(0, 0, 0, 0))
        gradient.setColorAt(1.0, QtGui.QColor(139, 0, 0, self.opacity))

        painter.fillRect(self.rect(), gradient)

    def run_overlay_process(duration=5):
        """
        Runs the overlay in THIS SAME FILE, but as a new process:
        python3 teacherspet_onefile.py --overlay 5
        """
        subprocess.Popen([sys.executable, __file__, "--overlay", str(duration)])


    def overlay_main(duration=5):
        """
        Overlay-only mode. Safe because it owns the Qt event loop and doesn't touch cv.imshow.
        """
        app = QtWidgets.QApplication(sys.argv)
        overlay = HeartbeatOverlay()
        overlay.show()
        overlay.start_heartbeat()
        overlay.start_shake_cursor(duration=duration)

        QtCore.QTimer.singleShot(int(duration * 1000), overlay.stop_all)
        QtCore.QTimer.singleShot(int(duration * 1000) + 50, app.quit)
        sys.exit(app.exec())