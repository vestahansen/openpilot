import io
import qrcode
from PyQt5.QtWidgets import QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QImage, QIcon

from openpilot.system.hardware import HARDWARE
from openpilot.selfdrive.ui.state import uiState, BACKLIGHT_OFFROAD, ASSET_PATH
from openpilot.selfdrive.ui.qt.api import create_jwt
from openpilot.selfdrive.ui.qt.prime_state import PrimeState
from openpilot.selfdrive.ui.qt.widgets.input import DialogBase
from openpilot.selfdrive.ui.qt.widgets.wifi import WiFiPromptWidget


class PairingQRWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.img = QPixmap()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()
        self.timer.start(5 * 60 * 1000)
        HARDWARE.set_brightness(100)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.timer.stop()
        HARDWARE.set_brightness(BACKLIGHT_OFFROAD)

    def refresh(self):
        pair_token = create_jwt({"pair": True})
        qr_string = "https://connect.comma.ai/?pair=" + pair_token
        self.update_qr_code(qr_string)
        self.update()

    def update_qr_code(self, text):
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        image = QImage()
        image.loadFromData(buffer.read(), "PNG")
        sz = image.width()
        final_sz = ((self.width() // sz) - 1) * sz
        self.img = QPixmap.fromImage(
            image.scaled(final_sz, final_sz, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), Qt.white)
        s = (self.size() - self.img.size()) / 2
        p.drawPixmap(int(s.width()), int(s.height()), self.img)


class PairingPopup(DialogBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        hlayout = QHBoxLayout(self)
        hlayout.setContentsMargins(0, 0, 0, 0)
        hlayout.setSpacing(0)

        self.setStyleSheet("PairingPopup { background-color: #E0E0E0; }")

        vlayout = QVBoxLayout()
        vlayout.setContentsMargins(85, 70, 50, 70)
        vlayout.setSpacing(50)
        hlayout.addLayout(vlayout, 1)

        close = QPushButton(self)
        close.setIcon(QIcon(str(ASSET_PATH / "icons/close.svg")))
        close.setIconSize(QSize(80, 80))
        close.setStyleSheet("border: none;")
        vlayout.addWidget(close, 0, Qt.AlignLeft)
        close.clicked.connect(self.reject)

        vlayout.addSpacing(30)

        title = QLabel(self.tr("Pair your device to your comma account"), self)
        title.setStyleSheet("font-size: 75px; color: black;")
        title.setWordWrap(True)
        vlayout.addWidget(title)

        instructions_text = """
          <ol type='1' style='margin-left: 15px;'>
            <li style='margin-bottom: 50px;'>{}</li>
            <li style='margin-bottom: 50px;'>{}</li>
            <li style='margin-bottom: 50px;'>{}</li>
          </ol>
        """.format(
            self.tr("Go to https://connect.comma.ai on your phone"),
            self.tr("Click \"add new device\" and scan the QR code on the right"),
            self.tr("Bookmark connect.comma.ai to your home screen to use it like an app")
        )
        instructions = QLabel(instructions_text, self)
        instructions.setStyleSheet("font-size: 47px; font-weight: bold; color: black;")
        instructions.setWordWrap(True)
        vlayout.addWidget(instructions)

        vlayout.addStretch()

        qr = PairingQRWidget(self)
        hlayout.addWidget(qr, 1)


class PrimeUserWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("primeWidget")
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(56, 40, 56, 40)
        mainLayout.setSpacing(20)

        subscribed = QLabel(self.tr("✓ SUBSCRIBED"))
        subscribed.setStyleSheet("font-size: 41px; font-weight: bold; color: #86FF4E;")
        mainLayout.addWidget(subscribed)

        commaPrime = QLabel(self.tr("comma prime"))
        commaPrime.setStyleSheet("font-size: 75px; font-weight: bold;")
        mainLayout.addWidget(commaPrime)


class PrimeAdWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(80, 90, 80, 60)
        main_layout.setSpacing(0)

        upgrade = QLabel(self.tr("Upgrade Now"))
        upgrade.setStyleSheet("font-size: 75px; font-weight: bold;")
        main_layout.addWidget(upgrade, 0, Qt.AlignTop)
        main_layout.addSpacing(50)

        description = QLabel(self.tr("Become a comma prime member at connect.comma.ai"))
        description.setStyleSheet("font-size: 56px; font-weight: light; color: white;")
        description.setWordWrap(True)
        main_layout.addWidget(description, 0, Qt.AlignTop)

        main_layout.addStretch()

        features = QLabel(self.tr("PRIME FEATURES:"))
        features.setStyleSheet("font-size: 41px; font-weight: bold; color: #E5E5E5;")
        main_layout.addWidget(features, 0, Qt.AlignBottom)
        main_layout.addSpacing(30)

        bullets = [
            self.tr("Remote access"),
            self.tr("24/7 LTE connectivity"),
            self.tr("1 year of drive storage"),
            self.tr("Remote snapshots")
        ]
        for b in bullets:
            check = "<b><font color='#465BEA'>✓</font></b> "
            l = QLabel(check + b)
            l.setAlignment(Qt.AlignLeft)
            l.setStyleSheet("font-size: 50px; margin-bottom: 15px;")
            main_layout.addWidget(l, 0, Qt.AlignBottom)

        self.setStyleSheet("""
            PrimeAdWidget {
              border-radius: 10px;
              background-color: #333333;
            }
        """)


class SetupWidget(QFrame):
    openSettings = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mainLayout = QStackedWidget()

        finishRegistration = QFrame()
        finishRegistration.setObjectName("primeWidget")
        finishRegistrationLayout = QVBoxLayout(finishRegistration)
        finishRegistrationLayout.setSpacing(38)
        finishRegistrationLayout.setContentsMargins(64, 48, 64, 48)

        registrationTitle = QLabel(self.tr("Finish Setup"))
        registrationTitle.setStyleSheet("font-size: 75px; font-weight: bold;")
        finishRegistrationLayout.addWidget(registrationTitle)

        registrationDescription = QLabel(self.tr("Pair your device with comma connect (connect.comma.ai) and claim your comma prime offer."))
        registrationDescription.setWordWrap(True)
        registrationDescription.setStyleSheet("font-size: 50px; font-weight: light;")
        finishRegistrationLayout.addWidget(registrationDescription)

        finishRegistrationLayout.addStretch()

        pair = QPushButton(self.tr("Pair device"))
        pair.setStyleSheet("""
          QPushButton {
            font-size: 55px;
            font-weight: 500;
            border-radius: 10px;
            background-color: #465BEA;
            padding: 64px;
          }
          QPushButton:pressed {
            background-color: #3049F4;
          }
        """)
        finishRegistrationLayout.addWidget(pair)

        self.popup = PairingPopup(self)
        pair.clicked.connect(self.popup.exec_)

        self.mainLayout.addWidget(finishRegistration)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(30)

        wifi_prompt = WiFiPromptWidget()
        wifi_prompt.openSettings.connect(self.openSettings.emit)
        content_layout.addWidget(wifi_prompt)
        content_layout.addStretch()

        self.mainLayout.addWidget(content)
        self.mainLayout.setCurrentIndex(1)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(self.mainLayout)

        self.setStyleSheet("""
            #primeWidget {
              border-radius: 10px;
              background-color: #333333;
            }
        """)

        sp_retain = self.sizePolicy()
        sp_retain.setRetainSizeWhenHidden(True)
        self.setSizePolicy(sp_retain)

        uiState().prime_state.changed.connect(self.prime_state_changed)

    def prime_state_changed(self, type_):
        if type_ == PrimeState.Type.PRIME_TYPE_UNPAIRED:
            self.mainLayout.setCurrentIndex(0)
        else:
            self.popup.reject()
            self.mainLayout.setCurrentIndex(1)