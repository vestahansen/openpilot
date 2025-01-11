import os
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QStackedLayout, QHBoxLayout

from selfdrive.ui.state import uiState, BG_COLORS, UI_BORDER_SIZE
from selfdrive.ui.qt.onroad.alerts import OnroadAlerts
# from selfdrive.ui.qt.onroad.annotated_camera import AnnotatedCameraWidget
# from selfdrive.ui.qt.widgets.camera_widget import CameraWidget

STATUS_DISENGAGED = 0  # Define the disengaged status constant
VISION_STREAM_ROAD = "roadCameraState"  # Replace with the actual vision stream if different

class OnroadWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.bg = BG_COLORS[STATUS_DISENGAGED]

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(UI_BORDER_SIZE, UI_BORDER_SIZE, UI_BORDER_SIZE, UI_BORDER_SIZE)

        stacked_layout = QStackedLayout()
        stacked_layout.setStackingMode(QStackedLayout.StackAll)
        main_layout.addLayout(stacked_layout)

        # self.nvg = AnnotatedCameraWidget(VISION_STREAM_ROAD, self)

        split_wrapper = QWidget()
        self.split = QHBoxLayout(split_wrapper)
        self.split.setContentsMargins(0, 0, 0, 0)
        self.split.setSpacing(0)
        # self.split.addWidget(self.nvg)

        if os.getenv("DUAL_CAMERA_VIEW"):
            arCam = CameraWidget("camerad", VISION_STREAM_ROAD, self)
            self.split.insertWidget(0, arCam)

        stacked_layout.addWidget(split_wrapper)

        self.alerts = OnroadAlerts(self)
        self.alerts.setAttribute(Qt.WA_TransparentForMouseEvents)
        stacked_layout.addWidget(self.alerts)

        self.alerts.raise_()
        self.setAttribute(Qt.WA_OpaquePaintEvent)

        ui_state = uiState()
        ui_state.uiUpdate.connect(self.updateState)
        ui_state.offroadTransition.connect(self.offroadTransition)

    @pyqtSlot(object)
    def updateState(self, s):
        if not s.scene.started:
            return

        self.alerts.updateState(s)
        # self.nvg.updateState(s)

        bgColor = BG_COLORS[s.status]
        if self.bg != bgColor:
            self.bg = bgColor
            self.update()

    @pyqtSlot(bool)
    def offroadTransition(self, offroad):
        self.alerts.clear()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(self.bg.red(), self.bg.green(), self.bg.blue(), 255))
