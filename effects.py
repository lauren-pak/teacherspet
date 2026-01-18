from PySide6 import QtWidgets, QtCore, QtGui
import sys, random, threading, pyautogui, time

import platform

if platform.system() == "Darwin":
    from AppKit import NSApp, NSFloatingWindowLevel


class HeartbeatOverlay(QtWidgets.QWidget):
    def __init__(self, color=139, opacity =40):
        super().__init__()
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            #QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        screen = QtWidgets.QApplication.primaryScreen().geometry()

        self.speed = 500
        self.color = int(color)

        expand = 50
        x = screen.x() - expand
        y = screen.y() - expand
        width = screen.width() + 2*expand
        height = screen.height() + 2*expand

        self.setGeometry(x, y, width, height)

        self.base_pos = self.pos()

        # heartbeat variables
        self.opacity = int(opacity)
        self.max_opacity = 170
        self.beat_phase = "fade"
        self._heartbeat_running = False

        self.fade_timer = QtCore.QTimer()
        self.fade_timer.timeout.connect(self.fade_step)
        self.fade_timer.start(16)

        # cursor shake
        self._shake_cursor_running = False

        if platform.system() == "Darwin":
            QtCore.QTimer.singleShot(
                0, self._enable_macos_fullscreen_overlay
            )
    def set_speed(self, speed):
        self.speed = min(50, int(speed))  # clamp so it never breaks


    def _enable_macos_fullscreen_overlay(self):
        from AppKit import NSWindow

        ns_window = NSApp().windows()[0]

        # Float above normal windows
        ns_window.setLevel_(NSFloatingWindowLevel)

        # Appear on all Spaces + fullscreen Spaces
        ns_window.setCollectionBehavior_(
            (1 << 0) |  # NSWindowCollectionBehaviorCanJoinAllSpaces
            (1 << 7)    # NSWindowCollectionBehaviorFullScreenAuxiliary
        )

    def start_heartbeat(self):
        self._heartbeat_running = True
        self.do_lub()

    def do_lub(self):
        if not self._heartbeat_running:
            return

        self.opacity = self.max_opacity
        self.update()

        QtCore.QTimer.singleShot(self.speed, self.do_dub)   # lub → dub

    def do_dub(self):
        if not self._heartbeat_running:
            return

        self.opacity = self.max_opacity - 30
        self.update()

        QtCore.QTimer.singleShot(self.speed, self.do_lub)   # dub → next lub

    def stop_heartbeat(self):
        """Stops the lub-dub loop."""
        self._heartbeat_running = False
        # Optional: stop fade immediately
        self.opacity = 30
        self.update()
        # Optional: stop cursor shake too
        self._shake_cursor_running = False

    def fade_step(self):
        if self.opacity > 30:
            self.opacity -= 3
            self.update()



    def start_shake_cursor(self, intensity=10, frequency=0.05):
        self._shake_cursor_running = True
        def stop(): self._shake_cursor_running = False
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
        gradient.setColorAt(0.6, QtGui.QColor(0, 0, 0, 0))
        gradient.setColorAt(1.0, QtGui.QColor(self.color, 0, 0, self.opacity))
        painter.fillRect(self.rect(), gradient)

# run overlay
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    overlay = HeartbeatOverlay()
    overlay.show()
    overlay.start_heartbeat()
    overlay.start_shake_cursor()

    sys.exit(app.exec())