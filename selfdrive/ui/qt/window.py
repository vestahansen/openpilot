from PyQt5.QtWidgets import QWidget, QStackedLayout
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtCore import QEvent, Qt

from openpilot.selfdrive.ui.state import ASSET_PATH, device, uiState
from openpilot.selfdrive.ui.qt.home import HomeWindow
from openpilot.selfdrive.ui.qt.offroad.settings import SettingsWindow
# from openpilot.selfdrive.ui.qt.offroad.onboarding import OnboardingWindow

class MainWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.main_layout = QStackedLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.homeWindow = HomeWindow(self)
        self.main_layout.addWidget(self.homeWindow)
        self.homeWindow.openSettings.connect(self.openSettings)
        self.homeWindow.closeSettings.connect(self.closeSettings)

        self.settingsWindow = SettingsWindow(self)
        self.main_layout.addWidget(self.settingsWindow)
        self.settingsWindow.closeSettings.connect(self.closeSettings)
        self.settingsWindow.reviewTrainingGuide.connect(self.showTrainingGuide)

        # self.onboardingWindow = OnboardingWindow(self)
        # self.main_layout.addWidget(self.onboardingWindow)
        # self.onboardingWindow.onboardingDone.connect(self.showHomeWindow)
        # if not self.onboardingWindow.completed():
        #     self.main_layout.setCurrentWidget(self.onboardingWindow)

        uiState().offroadTransition.connect(self.handleOffroadTransition)
        device().interactiveTimeout.connect(self.handleInteractiveTimeout)

        QFontDatabase.addApplicationFont(str(ASSET_PATH / "fonts/Inter-Black.ttf"))
        QFontDatabase.addApplicationFont(str(ASSET_PATH / "fonts/Inter-Bold.ttf"))
        QFontDatabase.addApplicationFont(str(ASSET_PATH / "fonts/Inter-ExtraBold.ttf"))
        QFontDatabase.addApplicationFont(str(ASSET_PATH / "fonts/Inter-ExtraLight.ttf"))
        QFontDatabase.addApplicationFont(str(ASSET_PATH / "fonts/Inter-Medium.ttf"))
        QFontDatabase.addApplicationFont(str(ASSET_PATH / "fonts/Inter-Regular.ttf"))
        QFontDatabase.addApplicationFont(str(ASSET_PATH / "fonts/Inter-SemiBold.ttf"))
        QFontDatabase.addApplicationFont(str(ASSET_PATH / "fonts/Inter-Thin.ttf"))
        QFontDatabase.addApplicationFont(str(ASSET_PATH / "fonts/JetBrainsMono-Medium.ttf"))

        self.setStyleSheet("""
            * {
                font-family: Inter;
                outline: none;
            }
        """)
        self.setAttribute(Qt.WA_NoSystemBackground)

        self.installEventFilter(self)

    def openSettings(self, index=0, param=""):
        self.main_layout.setCurrentWidget(self.settingsWindow)
        self.settingsWindow.setCurrentPanel(index, param)

    def closeSettings(self):
        self.main_layout.setCurrentWidget(self.homeWindow)
        if uiState().scene.started:
            self.homeWindow.showSidebar(False)

    def showTrainingGuide(self):
        self.onboardingWindow.showTrainingGuide()
        self.main_layout.setCurrentWidget(self.onboardingWindow)

    def showHomeWindow(self):
        self.main_layout.setCurrentWidget(self.homeWindow)

    def handleOffroadTransition(self, offroad):
        if not offroad:
            self.closeSettings()

    def handleInteractiveTimeout(self):
        if self.main_layout.currentWidget() == self.settingsWindow:
            self.closeSettings()

    def eventFilter(self, obj, event):
        ignore = False
        if event.type() in (QEvent.TouchBegin, QEvent.TouchUpdate, QEvent.TouchEnd,
                            QEvent.MouseButtonPress, QEvent.MouseMove):
            ignore = not device().isAwake()
            device().resetInteractiveTimeout()
        return ignore