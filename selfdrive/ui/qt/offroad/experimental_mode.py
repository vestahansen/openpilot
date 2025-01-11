from PyQt5.QtWidgets import QPushButton, QLabel, QHBoxLayout, QSizePolicy
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath, QLinearGradient, QColor, QPen
from PyQt5.QtCore import Qt, QRectF, pyqtSignal

from openpilot.common.params import Params
from openpilot.selfdrive.ui.state import ASSET_PATH


class ExperimentalModeButton(QPushButton):
    openSettings = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.params = Params()
        self.experimental_mode = False
        self.img_width = 100
        self.horizontal_padding = 30
        self.chill_pixmap = QPixmap(str(ASSET_PATH / "img_couch.svg")).scaledToWidth(self.img_width, Qt.SmoothTransformation)
        self.experimental_pixmap = QPixmap(str(ASSET_PATH / "img_experimental_grey.svg")).scaledToWidth(self.img_width, Qt.SmoothTransformation)

        self.clicked.connect(lambda: self.openSettings.emit(2, "ExperimentalMode"))

        self.setFixedHeight(125)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(self.horizontal_padding, 0, self.horizontal_padding, 0)

        self.mode_label = QLabel()
        self.mode_icon = QLabel()
        self.mode_icon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        main_layout.addWidget(self.mode_label, 1, Qt.AlignLeft)
        main_layout.addWidget(self.mode_icon, 0, Qt.AlignRight)

        self.setLayout(main_layout)

        self.setStyleSheet("""
        QPushButton {
            border: none;
        }

        QLabel {
            font-size: 45px;
            font-weight: 300;
            text-align: left;
            font-family: JetBrainsMono;
            color: #000000;
        }
        """)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setPen(Qt.NoPen)
        p.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 10, 10)

        pressed = self.isDown()
        gradient = QLinearGradient(self.rect().left(), 0, self.rect().right(), 0)
        if self.experimental_mode:
            gradient.setColorAt(0, QColor(255, 155, 63, 0xcc if pressed else 0xff))
            gradient.setColorAt(1, QColor(219, 56, 34, 0xcc if pressed else 0xff))
        else:
            gradient.setColorAt(0, QColor(20, 255, 171, 0xcc if pressed else 0xff))
            gradient.setColorAt(1, QColor(35, 149, 255, 0xcc if pressed else 0xff))
        p.fillPath(path, gradient)

        p.setPen(QPen(QColor(0, 0, 0, 0x4d), 3, Qt.SolidLine))
        line_x = self.rect().right() - self.img_width - (2 * self.horizontal_padding)
        p.drawLine(line_x, self.rect().bottom(), line_x, self.rect().top())

        super().paintEvent(event)

    def showEvent(self, event):
        self.experimental_mode = self.params.get_bool("ExperimentalMode")
        if self.experimental_mode:
            self.mode_icon.setPixmap(self.experimental_pixmap)
            self.mode_label.setText("EXPERIMENTAL MODE ON")
        else:
            self.mode_icon.setPixmap(self.chill_pixmap)
            self.mode_label.setText("CHILL MODE ON")
        super().showEvent(event)
