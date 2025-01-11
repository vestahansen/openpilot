from PyQt5.QtWidgets import QWidget, QHBoxLayout, QStackedLayout, QFrame, QVBoxLayout, QPushButton, QLabel, QStackedWidget
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot

from openpilot.common.params import Params
from openpilot.selfdrive.ui.state import uiState
from openpilot.selfdrive.ui.qt.util import getBrand
from openpilot.selfdrive.ui.qt.sidebar import Sidebar
from openpilot.selfdrive.ui.qt.body import BodyWindow
from openpilot.selfdrive.ui.qt.widgets.controls import ElidedLabel
from openpilot.selfdrive.ui.qt.widgets.prime import PrimeUserWidget, PrimeAdWidget, SetupWidget
from openpilot.selfdrive.ui.qt.widgets.offroad_alerts import UpdateAlert, OffroadAlert
from openpilot.selfdrive.ui.qt.offroad.experimental_mode import ExperimentalModeButton
from openpilot.selfdrive.ui.qt.onroad.onroad_home import OnroadWindow

# OffroadHome: the offroad home page

class OffroadHome(QFrame):
    openSettings = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.params = Params()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(16)

        self.update_notif = QPushButton("UPDATE")
        self.update_notif.setVisible(False)
        self.update_notif.setStyleSheet("background-color: #364DEF;")
        self.update_notif.clicked.connect(lambda: self.center_layout.setCurrentIndex(1))
        header_layout.addWidget(self.update_notif, 0, Qt.AlignLeft)

        self.alert_notif = QPushButton()
        self.alert_notif.setVisible(False)
        self.alert_notif.setStyleSheet("background-color: #E22C2C;")
        self.alert_notif.clicked.connect(lambda: self.center_layout.setCurrentIndex(2))
        header_layout.addWidget(self.alert_notif, 0, Qt.AlignLeft)

        self.version = ElidedLabel()
        header_layout.addWidget(self.version, 0, Qt.AlignRight)

        main_layout.addLayout(header_layout)
        main_layout.addSpacing(25)
        self.center_layout = QStackedLayout()

        home_widget = QWidget(self)
        home_layout = QHBoxLayout(home_widget)
        home_layout.setContentsMargins(0, 0, 0, 0)
        home_layout.setSpacing(30)

        self.left_widget = QStackedWidget(self)
        left_prime_layout = QVBoxLayout()
        left_prime_layout.setContentsMargins(0, 0, 0, 0)
        prime_user = PrimeUserWidget()
        prime_user.setStyleSheet("""
        border-radius: 10px;
        background-color: #333333;
        """)
        left_prime_layout.addWidget(prime_user)
        left_prime_layout.addStretch()
        left_layout_widget = QWidget()
        left_layout_widget.setLayout(left_prime_layout)
        self.left_widget.addWidget(left_layout_widget)
        self.left_widget.addWidget(PrimeAdWidget())
        self.left_widget.setStyleSheet("border-radius: 10px;")

        uiState().prime_state.changed.connect(self.updatePrimeWidget)

        home_layout.addWidget(self.left_widget, 1)

        right_widget = QWidget(self)
        right_column = QVBoxLayout(right_widget)
        right_column.setContentsMargins(0, 0, 0, 0)
        right_widget.setFixedWidth(750)
        right_column.setSpacing(30)

        experimental_mode = ExperimentalModeButton(self)
        experimental_mode.openSettings.connect(self.openSettings)
        right_column.addWidget(experimental_mode, 1)

        setup_widget = SetupWidget()
        setup_widget.openSettings.connect(self.openSettings)
        right_column.addWidget(setup_widget, 1)

        home_layout.addWidget(right_widget, 1)

        self.center_layout.addWidget(home_widget)

        self.update_widget = UpdateAlert()
        self.update_widget.dismiss.connect(lambda: self.center_layout.setCurrentIndex(0))
        self.center_layout.addWidget(self.update_widget)

        self.alerts_widget = OffroadAlert()
        self.alerts_widget.dismiss.connect(lambda: self.center_layout.setCurrentIndex(0))
        self.center_layout.addWidget(self.alerts_widget)

        main_layout.addLayout(self.center_layout, 1)

        self.setStyleSheet("""
        * {
          color: white;
        }
        OffroadHome {
          background-color: black;
        }
        OffroadHome > QPushButton {
          padding: 15px 30px;
          border-radius: 5px;
          font-size: 40px;
          font-weight: 500;
        }
        OffroadHome > QLabel {
          font-size: 55px;
        }
        """)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()
        self.timer.start(10 * 1000)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.timer.stop()

    def refresh(self):
        current_description = self.params.get("UpdaterCurrentDescription", encoding='utf-8') or ""
        self.version.setText(f"{getBrand(self)} {current_description}")

        update_available = False # self.update_widget.refresh()
        alerts = False # self.alerts_widget.refresh()

        idx = self.center_layout.currentIndex()
        if not update_available and not alerts:
            idx = 0
        elif update_available and (not self.update_notif.isVisible() or (not alerts and idx == 2)):
            idx = 1
        elif alerts and (not self.alert_notif.isVisible() or (not update_available and idx == 1)):
            idx = 2
        self.center_layout.setCurrentIndex(idx)

        self.update_notif.setVisible(update_available)
        self.alert_notif.setVisible(alerts)
        if alerts:
            self.alert_notif.setText(f"{alerts} {'ALERTS' if alerts > 1 else 'ALERT'}")

    @pyqtSlot()
    def updatePrimeWidget(self):
        if uiState().prime_state.isSubscribed():
            self.left_widget.setCurrentIndex(0)
        else:
            self.left_widget.setCurrentIndex(1)


# HomeWindow: the container for the offroad and onroad UIs

class HomeWindow(QWidget):
    openSettings = pyqtSignal(int, str)
    closeSettings = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = Sidebar(self)
        main_layout.addWidget(self.sidebar)
        self.sidebar.openSettings.connect(self.openSettings)

        self.slayout = QStackedLayout()
        main_layout.addLayout(self.slayout)

        self.home = OffroadHome(self)
        self.home.openSettings.connect(self.openSettings)
        self.slayout.addWidget(self.home)

        self.onroad = OnroadWindow(self)
        self.slayout.addWidget(self.onroad)

        self.body = BodyWindow(self)
        self.slayout.addWidget(self.body)

        # self.setAttribute(Qt.WA_NoSystemBackground)
        # uiState().uiUpdate.connect(self.updateState)
        # uiState().offroadTransition.connect(self.offroadTransition)
        # uiState().offroadTransition.connect(self.sidebar.offroadTransition)

    @pyqtSlot(bool)
    def showSidebar(self, show):
        self.sidebar.setVisible(show)

    @pyqtSlot()
    def updateState(self):
        sm = uiState().sm
        if self.onroad.isVisible() and not self.body.isEnabled() and sm["carParams"].getCarParams().getNotCar():
            self.body.setEnabled(True)
            self.slayout.setCurrentWidget(self.body)

    @pyqtSlot(bool)
    def offroadTransition(self, offroad):
        self.body.setEnabled(False)
        self.sidebar.setVisible(offroad)
        if offroad:
            self.slayout.setCurrentWidget(self.home)
        else:
            self.slayout.setCurrentWidget(self.onroad)

    def mousePressEvent(self, event):
        if (self.onroad.isVisible() or self.body.isVisible()) and (not self.sidebar.isVisible() or event.x() > self.sidebar.width()):
            self.sidebar.setVisible(not self.sidebar.isVisible())

    def mouseDoubleClickEvent(self, event):
        self.mousePressEvent(event)
        sm = uiState().sm
        if sm["carParams"].getCarParams().getNotCar():
            if self.onroad.isVisible():
                self.slayout.setCurrentWidget(self.body)
            elif self.body.isVisible():
                self.slayout.setCurrentWidget(self.onroad)
            self.showSidebar(False)