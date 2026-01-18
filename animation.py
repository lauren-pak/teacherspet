from PySide6 import QtWidgets, QtCore, QtGui
import sys

class PopupImages(QtWidgets.QWidget):
    def __init__(self, img1_path, img2_path, speed=200):
        super().__init__()

        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

        # Store speed (ms)
        self.speed = max(10, int(speed))

        # Load images
        self.pix1 = QtGui.QPixmap(img1_path)
        self.pix2 = QtGui.QPixmap(img2_path)
        if self.pix1.isNull() or self.pix2.isNull():
            raise FileNotFoundError(f"Could not load images: {img1_path}, {img2_path}")

        # Scale images
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        max_width = int(screen.width() * 0.35)
        self.pix1 = self.pix1.scaledToWidth(max_width, QtCore.Qt.SmoothTransformation)
        self.pix2 = self.pix2.scaledToWidth(max_width, QtCore.Qt.SmoothTransformation)

        # One label is enough (swap pixmap)
        self.label = QtWidgets.QLabel(self)
        self.label.setPixmap(self.pix1)
        self.label.resize(self.pix1.size())

        self.resize(screen.width(), screen.height())

        # Center position
        x = (screen.width() - self.pix1.width()) // 2
        y = (screen.height() - self.pix1.height()) // 2
        self.label.move(x, y)

        self._show_first = True
        self.running = False

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._tick)

        self.show()

        self.setWindowOpacity(0.0)

        # Fade-in animation
        self.fade_anim = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(2000)          # ms
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)

    def set_speed(self, speed):
        self.speed = max(10, int(speed))
        if self.timer.isActive():
            self.timer.start(self.speed)

    def start_animation(self):
        if self.running:
            return
        self.running = True
        self._show_first = True
        self.label.setPixmap(self.pix1)

        self.fade_anim.stop()
        self.setWindowOpacity(0.0)
        self.fade_anim.start()
        
        self.timer.start(self.speed)

    def _tick(self):
        if not self.running:
            return
        self._show_first = not self._show_first
        self.label.setPixmap(self.pix1 if self._show_first else self.pix2)

    def stop_animation(self):
        self.running = False
        self.timer.stop()
        self.label.setPixmap(self.pix1)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    popup = PopupImages("images/army1.png", "images/army2.png", speed=100)
    popup.start_animation()
    QtCore.QTimer.singleShot(10000, popup.stop_animation)
    sys.exit(app.exec())
