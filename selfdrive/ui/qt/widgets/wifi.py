from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame, QStackedLayout, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy

from cereal import log
from openpilot.selfdrive.ui.state import UIState, uiState, ASSET_PATH

class WiFiPromptWidget(QFrame):
    openSettings = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.stack = QStackedLayout(self)

        # Setup Wi-Fi
        setup = QFrame()
        setup_layout = QVBoxLayout(setup)
        setup_layout.setContentsMargins(56, 40, 56, 40)
        setup_layout.setSpacing(20)

        # Title layout
        title_layout = QHBoxLayout()
        title_layout.setSpacing(32)

        icon = QLabel()
        pixmap = QPixmap(str(ASSET_PATH / "offroad/icon_wifi_strength_full.svg"))
        icon.setPixmap(pixmap.scaledToWidth(80, Qt.SmoothTransformation))
        title_layout.addWidget(icon)

        title = QLabel("Setup Wi-Fi")
        title.setStyleSheet("font-size: 64px; font-weight: 600;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        setup_layout.addLayout(title_layout)

        desc = QLabel("Connect to Wi-Fi to upload driving data and help improve openpilot")
        desc.setStyleSheet("font-size: 40px; font-weight: 400;")
        desc.setWordWrap(True)
        setup_layout.addWidget(desc)

        settings_btn = QPushButton("Open Settings")
        settings_btn.clicked.connect(lambda: self.openSettings.emit(1, ""))
        settings_btn.setStyleSheet("""
        QPushButton {
            font-size: 48px;
            font-weight: 500;
            border-radius: 10px;
            background-color: #465BEA;
            padding: 32px;
        }
        QPushButton:pressed {
            background-color: #3049F4;
        }
        """)
        setup_layout.addWidget(settings_btn)
        self.stack.addWidget(setup)

        # Uploading data
        uploading = QWidget()
        uploading_layout = QVBoxLayout(uploading)
        uploading_layout.setContentsMargins(64, 56, 64, 56)
        uploading_layout.setSpacing(36)

        # Title layout
        title_layout = QHBoxLayout()

        title = QLabel("Ready to upload")
        title.setStyleSheet("font-size: 64px; font-weight: 600;")
        title.setWordWrap(True)
        title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        title_layout.addWidget(title)
        title_layout.addStretch()

        icon = QLabel()
        pixmap = QPixmap(str(ASSET_PATH / "offroad/icon_wifi_uploading.svg"))
        icon.setPixmap(pixmap.scaledToWidth(120, Qt.SmoothTransformation))
        title_layout.addWidget(icon)
        uploading_layout.addLayout(title_layout)

        desc = QLabel("Training data will be pulled periodically while your device is on Wi-Fi")
        desc.setStyleSheet("font-size: 48px; font-weight: 400;")
        desc.setWordWrap(True)
        uploading_layout.addWidget(desc)
        self.stack.addWidget(uploading)

        self.setStyleSheet("""
        WiFiPromptWidget {
            background-color: #333333;
            border-radius: 10px;
        }
        """)

        uiState().uiUpdate.connect(self.updateState)

    def updateState(self, s: UIState):
        if not self.isVisible():
            return

        sm = s.sm

        if sm.updated['deviceState']:
            device_state = sm['deviceState']
            network_type = device_state.networkType
            uploading = (network_type == log.DeviceState.NetworkType.wifi or
                         network_type == log.DeviceState.NetworkType.ethernet)
            self.stack.setCurrentIndex(1 if uploading else 0)
