from pathlib import Path
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QVideoSink


class VideoOverlay(QtWidgets.QWidget):
    def __init__(self, video_path: Path, size=(420, 420)):
        super().__init__()

        self.video_path = video_path
        self.target_size = QtCore.QSize(*size)

        # --- Window flags ---
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )

        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        try:
            self.setWindowFlag(QtCore.Qt.WindowTransparentForInput, True)
        except Exception:
            pass

        self.setAutoFillBackground(False)

        # --- Video plumbing ---
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.audio.setVolume(0.0)
        self.player.setAudioOutput(self.audio)

        self.sink = QVideoSink(self)
        self.player.setVideoOutput(self.sink)
        self.sink.videoFrameChanged.connect(self._on_frame)

        self.player.setSource(QtCore.QUrl.fromLocalFile(str(self.video_path)))
        self.player.mediaStatusChanged.connect(self._loop)

        self._pixmap: QtGui.QPixmap | None = None

        self.resize(self.target_size)
        self._center_on_current_screen()

        # Start hidden
        self.hide()

    def start(self):
        """Show overlay and start (or resume) video."""
        self.show()
        self.raise_()
        self.player.play()

    def stop(self):
        """Hide overlay and pause video."""
        self.player.pause()
        self.hide()

    def is_running(self) -> bool:
        return self.isVisible()


    def _center_on_current_screen(self):
        screen = QtGui.QGuiApplication.screenAt(QtGui.QCursor.pos())
        if screen is None:
            screen = QtGui.QGuiApplication.primaryScreen()

        geo = screen.availableGeometry()
        x = geo.x() + (geo.width() - self.width()) // 2
        y = geo.y() + (geo.height() - self.height()) // 2
        self.move(x, y)

    def _loop(self, status: QMediaPlayer.MediaStatus):
        if status == QMediaPlayer.EndOfMedia:
            self.player.setPosition(0)
            self.player.play()

    @QtCore.Slot("QVideoFrame")
    def _on_frame(self, frame):
        if not frame.isValid():
            return

        img = frame.toImage()
        if img.isNull():
            return

        if img.format() != QtGui.QImage.Format_ARGB32_Premultiplied:
            img = img.convertToFormat(QtGui.QImage.Format_ARGB32_Premultiplied)

        pm = QtGui.QPixmap.fromImage(img)
        pm = pm.scaled(
            self.size(),
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        self._pixmap = pm
        self.update()

    def paintEvent(self, event):
        if not self._pixmap:
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)

        x = (self.width() - self._pixmap.width()) // 2
        y = (self.height() - self._pixmap.height()) // 2
        painter.drawPixmap(x, y, self._pixmap)

    def closeEvent(self, event):
        try:
            self.player.stop()
        except Exception:
            pass
        super().closeEvent(event)

