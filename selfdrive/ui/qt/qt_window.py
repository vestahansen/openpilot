import os
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QGuiApplication
from openpilot.system.hardware import PC, TICI

DEVICE_SCREEN_SIZE = QSize(2160, 1080)

def setMainWindow(w: QWidget) -> None:
    scale = float(os.getenv("SCALE", "1.0"))
    sz = QGuiApplication.primaryScreen().size()

    if PC and scale == 1.0 and not (sz - DEVICE_SCREEN_SIZE).isValid():
        w.setMinimumSize(QSize(640, 480))
        w.setMaximumSize(DEVICE_SCREEN_SIZE)
        w.resize(sz)
    else:
        w.setFixedSize(DEVICE_SCREEN_SIZE * scale)

    w.show()

    if TICI:
        # TODO: Add the QPA/wayland code
        w.setWindowState(Qt.WindowFullScreen)
        w.setVisible(True)