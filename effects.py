from PySide6 import QtWidgets, QtCore, QtGui
import sys, random, platform, threading
import pyautogui
import time

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
        #self.edge_thickness = 80
        self.max_opacity = 170

        self.fade_timer = QtCore.QTimer()
        self.fade_timer.timeout.connect(self.fade_step)

        self._shake_cursor_running = False

        
    def showEvent(self, event):
        super().showEvent(event)
    def start_shake_cursor(self, intensity=10, frequency=0.5):
        self._shake_cursor_running = True
        def run():
            dx = 5
            dy = 5
            pyautogui.PAUSE = 0.05  # disables the automatic pause

            while self._shake_cursor_running:
                x, y = pyautogui.position()
                pyautogui.moveTo(x + dx, y + dy)
                dx *= -1
                dy *= -1

        threading.Thread(target=run, daemon=True).start()

    def stop_shake_cursor(self):
        self._shake_cursor_running = False

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

    def heartbeat(self):
        # First beat (lub)
        self.opacity = self.max_opacity
        self.update()
        self.shake()


        self.fade_timer.start(16) 

        QtCore.QTimer.singleShot(120, self.second_beat)

        next_interval = 420  # pause after dub
        QtCore.QTimer.singleShot(next_interval, self.heartbeat)

    def second_beat(self):
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

    

app = QtWidgets.QApplication(sys.argv)
overlay = HeartbeatOverlay()

overlay.show()  #shows just the red fade.
overlay.heartbeat()
overlay.start_shake_cursor()

sys.exit(app.exec())
