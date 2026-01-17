from PySide6 import QtWidgets, QtCore, QtGui
import sys, os

class PopupImages(QtWidgets.QWidget):
    def __init__(self, img1_path, img2_path):
        super().__init__()

        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # Load images
        self.pix1 = QtGui.QPixmap(img1_path)
        self.pix2 = QtGui.QPixmap(img2_path)

        # Scale images to 20% of screen width
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        max_width = screen.width() * 0.2
        self.pix1 = self.pix1.scaledToWidth(max_width, QtCore.Qt.SmoothTransformation)
        self.pix2 = self.pix2.scaledToWidth(max_width, QtCore.Qt.SmoothTransformation)

        # Labels
        self.label1 = QtWidgets.QLabel(self)
        self.label1.setPixmap(self.pix1)
        self.label1.resize(self.pix1.size())
        self.label1.setVisible(False)

        self.label2 = QtWidgets.QLabel(self)
        self.label2.setPixmap(self.pix2)
        self.label2.resize(self.pix2.size())
        self.label2.setVisible(False)

        self.resize(screen.width(), screen.height())

        # Position images at bottom-left
        margin = 20
        self.label1.move(margin, screen.height() - self.pix1.height() - margin)
        self.label2.move(margin + self.pix1.width() + 10, screen.height() - self.pix2.height() - margin)

        self.show()
        self.start_animation()

    def start_animation(self):
        self.label1.setVisible(True)
        anim1 = QtCore.QPropertyAnimation(self.label1, b"geometry")
        anim1.setDuration(500)
        anim1.setStartValue(QtCore.QRect(self.label1.x(), self.label1.y(), 0, 0))
        anim1.setEndValue(self.label1.geometry())
        anim1.setEasingCurve(QtCore.QEasingCurve.OutBounce)

        self.label2.setVisible(True)
        anim2 = QtCore.QPropertyAnimation(self.label2, b"geometry")
        anim2.setDuration(500)
        anim2.setStartValue(QtCore.QRect(self.label2.x(), self.label2.y(), 0, 0))
        anim2.setEndValue(self.label2.geometry())
        anim2.setEasingCurve(QtCore.QEasingCurve.OutBounce)

        # Keep reference to prevent garbage collection
        self.anim_group = QtCore.QSequentialAnimationGroup()
        self.anim_group.addAnimation(anim1)
        self.anim_group.addAnimation(anim2)
        self.anim_group.start()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    popup = PopupImages("images/army1.png", "images/army2.png")
    sys.exit(app.exec())
