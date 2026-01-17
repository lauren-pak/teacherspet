# heart_overlay.py
import sys
import time
import cv2 as cv
from PySide6 import QtCore, QtGui, QtWidgets


class HeartOverlayWindow(QtWidgets.QWidget):
    def __init__(self, mp4_path: str = "/graphics/heart_animation", duration: float = 5.0, fps_cap: float | None = None):
        super().__init__()
        self.mp4_path = mp4_path
        self.duration = duration
        self.fps_cap = fps_cap

        # --- window flags: frameless + always on top + transparent ---
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.Tool  # keeps it out of taskbar / alt-tab on many platforms
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground, True)

        # Fullscreen overlay on the primary screen
        screen = QtGui.QGuiApplication.primaryScreen()
        geom = screen.geometry()
        self.setGeometry(geom)

        # Click-through (best-effort cross-platform)
        # On Windows this often works; on macOS you may need a platform-specific tweak (see notes below).
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)

        # video
        self.cap = cv.VideoCapture(self.mp4_path)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open MP4: {self.mp4_path}")

        self.native_fps = self.cap.get(cv.CAP_PROP_FPS) or 30.0
        self.frame_interval_ms = int(1000 / (fps_cap or self.native_fps))

        self.start_t = time.monotonic()
        self.frame = None  # BGRA numpy

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(self.frame_interval_ms)

    def _tick(self):
        # stop after duration
        if (time.monotonic() - self.start_t) >= self.duration:
            self.close()
            return

        ok, bgr = self.cap.read()
        if not ok:
            # loop video
            self.cap.set(cv.CAP_PROP_POS_FRAMES, 0)
            ok, bgr = self.cap.read()
            if not ok:
                self.close()
                return

        # Convert to BGRA. If your MP4 has no alpha channel, it will be fully opaque.
        # (If you need transparency, see notes below.)
        bgra = cv.cvtColor(bgr, cv.COLOR_BGR2BGRA)
        self.frame = bgra
        self.update()  # triggers paintEvent

    def paintEvent(self, event):
        if self.frame is None:
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)

        h, w = self.frame.shape[:2]
        qimg = QtGui.QImage(
            self.frame.data,
            w,
            h,
            self.frame.strides[0],
            QtGui.QImage.Format.Format_BGRA8888,
        )

        pix = QtGui.QPixmap.fromImage(qimg)

        # Example: draw heart near top-right corner, scaled smaller
        target_w = int(self.width() * 0.25)
        target_h = int(target_w * (pix.height() / pix.width()))
        x = self.width() - target_w - 40
        y = 40

        painter.drawPixmap(QtCore.QRect(x, y, target_w, target_h), pix)
        painter.end()

    def closeEvent(self, event):
        try:
            if self.cap:
                self.cap.release()
        finally:
            super().closeEvent(event)


def run_heart_overlay(mp4_path: str, duration: float = 5.0):
    """
    Entry point to be run as a separate process:
    python heart_overlay.py --overlay path/to/heart.mp4 5
    """
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    w = HeartOverlayWindow(mp4_path, duration=duration)
    w.show()
    app.exec()


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--overlay":
        
        mp4 = sys.argv[2]
        print(mp4)
        dur = float(sys.argv[3]) if len(sys.argv) >= 4 else 5.0
        run_heart_overlay(mp4, duration=dur)
    else:
        print("Usage: python heart_overlay.py --overlay heart.mp4 5")
