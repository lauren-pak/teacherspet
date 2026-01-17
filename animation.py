from PySide6 import QtWidgets, QtCore, QtGui
import sys, os, time

class PopupImages(QtWidgets.QWidget):
    def __init__(self, img1_path, img2_path, latency=500):
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
        self.label1.setVisible(True)

        self.label2 = QtWidgets.QLabel(self)
        self.label2.setPixmap(self.pix2)
        self.label2.resize(self.pix2.size())
        self.label2.setVisible(False)

        self.resize(screen.width(), screen.height())

        # Position images at bottom-left
        margin = 10
        self.label1.move(margin, screen.height() - self.pix1.height() - margin)
        self.label2.move(margin, screen.height() - self.pix1.height() - margin)

        self.running = False

        self.show()
        
        

    def start_animation(self, latency, running):
        if running:
            # Step 1: Show label1
            self.label1.setVisible(True)
            self.label2.setVisible(False)

            # Step 2: After 500ms, hide label1, show label2
            QtCore.QTimer.singleShot(latency, lambda: self.switch_images(latency, running=True))

    def switch_images(self, latency, running):
        if running:
            self.label1.setVisible(False)
            self.label2.setVisible(True)

            # Step 3: After another 500ms, hide label2 and repeat
            QtCore.QTimer.singleShot(latency, lambda: self.start_animation(latency, running=True))

    def stop_animation(self, running=False):
        if not running:
            self.label1.setVisible(True)
            self.label2.setVisible(False)
            #self.close()

        

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    popup = PopupImages("images/army1.png", "images/army2.png", 500)
    popup.start_animation(500, running=True)
    QtCore.QTimer.singleShot(10000, lambda: popup.stop_animation(running=False))
    sys.exit(app.exec())
