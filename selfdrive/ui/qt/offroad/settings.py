from collections import OrderedDict
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QPushButton, QButtonGroup, QStackedWidget, QWidget, QSizePolicy

from cereal import car
from openpilot.common.params import Params
from openpilot.common.swaglog import cloudlog
from openpilot.system.hardware import TICI, PC
from openpilot.selfdrive.ui.state import uiState, ASSET_PATH
from openpilot.selfdrive.ui.qt.util import getSupportedLanguages
from openpilot.selfdrive.ui.qt.prime_state import PrimeState
from openpilot.selfdrive.ui.qt.widgets.controls import ListWidget, ButtonControl, LabelControl, ParamControl, ButtonParamControl
from openpilot.selfdrive.ui.qt.widgets.input import MultiOptionDialog, ConfirmationDialog
from openpilot.selfdrive.ui.qt.widgets.scrollview import ScrollView


class SettingsWindow(QFrame):
    closeSettings = pyqtSignal()
    reviewTrainingGuide = pyqtSignal()
    expandToggleDescription = pyqtSignal(str)

    def __init__(self, parent=None):
        super(SettingsWindow, self).__init__(parent)
        self.setObjectName("SettingsWindow")

        # setup two main layouts
        self.sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        self.panel_widget = QStackedWidget()

        # close button
        close_btn = QPushButton("×")
        close_btn.setStyleSheet("""
            QPushButton {
                font-size: 140px;
                padding-bottom: 20px;
                border-radius: 100px;
                background-color: #292929;
                font-weight: 400;
            }
            QPushButton:pressed {
                background-color: #3B3B3B;
            }
        """)
        close_btn.setFixedSize(200, 200)
        sidebar_layout.addSpacing(45)
        sidebar_layout.addWidget(close_btn, 0, Qt.AlignCenter)
        close_btn.clicked.connect(self.closeSettings.emit)

        # setup panels
        device_panel = DevicePanel(self)
        device_panel.reviewTrainingGuide.connect(self.reviewTrainingGuide.emit)

        toggles_panel = TogglesPanel(self)
        self.expandToggleDescription.connect(toggles_panel.expandToggleDescription)

        networking = Networking(self)
        uiState().prime_state.changed.connect(networking.setPrimeType)

        panels = [
            (self.tr("Device"), device_panel),
            (self.tr("Network"), networking),
            (self.tr("Toggles"), toggles_panel),
            (self.tr("Software"), SoftwarePanel(self)),
            (self.tr("Developer"), DeveloperPanel(self)),
        ]

        self.nav_btns = QButtonGroup(self)
        for i, (name, panel) in enumerate(panels):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setChecked(i == 0)
            btn.setStyleSheet("""
                QPushButton {
                    color: grey;
                    border: none;
                    background: none;
                    font-size: 65px;
                    font-weight: 500;
                }
                QPushButton:checked {
                    color: white;
                }
                QPushButton:pressed {
                    color: #ADADAD;
                }
            """)
            btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
            self.nav_btns.addButton(btn)
            sidebar_layout.addWidget(btn, 0, Qt.AlignRight)

            lr_margin = 50 if name != self.tr("Network") else 0  # Network panel handles its own margins
            panel.setContentsMargins(lr_margin, 25, lr_margin, 25)

            panel_frame = ScrollView(panel, self)
            self.panel_widget.addWidget(panel_frame)

            btn.clicked.connect(lambda _, index=i: self.setCurrentPanel(index))

        sidebar_layout.setContentsMargins(50, 50, 100, 50)

        # main settings layout, sidebar + main panel
        main_layout = QHBoxLayout(self)
        self.sidebar_widget.setFixedWidth(500)
        main_layout.addWidget(self.sidebar_widget)
        main_layout.addWidget(self.panel_widget)

        self.setStyleSheet("""
            * {
                color: white;
                font-size: 50px;
            }
            #SettingsWindow {
                background-color: black;
            }
            QStackedWidget, ScrollView {
                background-color: #292929;
                border-radius: 30px;
            }
        """)

    def showEvent(self, event):
        super(SettingsWindow, self).showEvent(event)
        self.setCurrentPanel(0)

    def setCurrentPanel(self, index, param=None):
        self.panel_widget.setCurrentIndex(index)
        self.nav_btns.buttons()[index].setChecked(True)
        if param:
            self.expandToggleDescription.emit(param)

    @pyqtSlot(str)
    def expandToggle(self, param):
        self.expandToggleDescription.emit(param)


class DevicePanel(ListWidget):
    reviewTrainingGuide = pyqtSignal()

    def __init__(self, parent=None):
        super(DevicePanel, self).__init__(parent)
        self.params = Params()
        self.setSpacing(50)
        self.addItem(LabelControl(self.tr("Dongle ID"), self.params.get("DongleId", encoding='utf8') or self.tr("N/A")))
        self.addItem(LabelControl(self.tr("Serial"), self.params.get("HardwareSerial", encoding='utf8')))

        self.pair_device = ButtonControl(self.tr("Pair Device"), self.tr("PAIR"),
                                         self.tr("Pair your device with comma connect (connect.comma.ai) and claim your comma prime offer."))
        self.pair_device.clicked.connect(self.pair)
        self.addItem(self.pair_device)

        dcam_btn = ButtonControl(self.tr("Driver Camera"), self.tr("PREVIEW"),
                                 self.tr("Preview the driver facing camera to ensure that driver monitoring has good visibility. (vehicle must be off)"))
        dcam_btn.clicked.connect(self.showDriverView)
        self.addItem(dcam_btn)

        reset_calib_btn = ButtonControl(self.tr("Reset Calibration"), self.tr("RESET"), "")
        reset_calib_btn.clicked.connect(self.resetCalibration)
        self.addItem(reset_calib_btn)

        retrain_btn = ButtonControl(self.tr("Review Training Guide"), self.tr("REVIEW"), self.tr("Review the rules, features, and limitations of openpilot"))
        retrain_btn.clicked.connect(self.reviewTraining)
        self.addItem(retrain_btn)

        if TICI:
            regulatory_btn = ButtonControl(self.tr("Regulatory"), self.tr("VIEW"), "")
            regulatory_btn.clicked.connect(self.showRegulatory)
            self.addItem(regulatory_btn)

        translate_btn = ButtonControl(self.tr("Change Language"), self.tr("CHANGE"), "")
        translate_btn.clicked.connect(self.changeLanguage)
        self.addItem(translate_btn)

        uiState().prime_state.changed.connect(self.updatePrimeStatus)
        uiState().offroadTransition.connect(self.updateOffroad)

        power_layout = QHBoxLayout()
        power_layout.setSpacing(30)

        reboot_btn = QPushButton(self.tr("Reboot"))
        reboot_btn.setObjectName("reboot_btn")
        power_layout.addWidget(reboot_btn)
        reboot_btn.clicked.connect(self.reboot)

        poweroff_btn = QPushButton(self.tr("Power Off"))
        poweroff_btn.setObjectName("poweroff_btn")
        power_layout.addWidget(poweroff_btn)
        poweroff_btn.clicked.connect(self.poweroff)

        if not PC:
            uiState().offroadTransition.connect(poweroff_btn.setVisible)

        self.setStyleSheet("""
            #reboot_btn { height: 120px; border-radius: 15px; background-color: #393939; }
            #reboot_btn:pressed { background-color: #4a4a4a; }
            #poweroff_btn { height: 120px; border-radius: 15px; background-color: #E22C2C; }
            #poweroff_btn:pressed { background-color: #FF2424; }
        """)
        self.addItem(power_layout)

    def updatePrimeStatus(self, prime_type):
        self.pair_device.setVisible(prime_type == PrimeState.Type.PRIME_TYPE_UNPAIRED)

    def updateOffroad(self, offroad):
        for btn in self.findChildren(ButtonControl):
            if btn != self.pair_device:
                btn.setEnabled(offroad)

    def pair(self):
        # Implementation for pairing
        pass

    def showDriverView(self):
        # Implementation for showing driver view
        pass

    def resetCalibration(self):
        if ConfirmationDialog.confirm(self.tr("Are you sure you want to reset calibration?"), self.tr("Reset"), self):
            self.params.delete("CalibrationParams")
            self.params.delete("LiveTorqueParameters")

    def reviewTraining(self):
        if ConfirmationDialog.confirm(self.tr("Are you sure you want to review the training guide?"), self.tr("Review"), self):
            self.reviewTrainingGuide.emit()

    def showRegulatory(self):
        with open(ASSET_PATH / "offroad/fcc.html") as f:
            text = f.read()
        ConfirmationDialog.rich(text, self)

    def changeLanguage(self):
        langs = getSupportedLanguages()
        selection = MultiOptionDialog(self.tr("Select a language"), list(langs.keys()), self).exec()
        if selection:
            # put language setting, exit Qt UI, and trigger fast restart
            self.params.put("LanguageSetting", langs[selection].encode())
            qApp.exit(18)
            watchdog_kick(0);

    def reboot(self):
        if not uiState().engaged:
            if ConfirmationDialog.confirm(self.tr("Are you sure you want to reboot?"), self.tr("Reboot"), self):
                if not uiState().engaged:
                    self.params.put_bool("DoReboot", True)
        else:
            ConfirmationDialog.alert(self.tr("Disengage to Reboot"), self)

    def poweroff(self):
        if not uiState().engaged:
            if ConfirmationDialog.confirm(self.tr("Are you sure you want to power off?"), self.tr("Power Off"), self):
                if not uiState().engaged:
                    self.params.put_bool("DoShutdown", True)
        else:
            ConfirmationDialog.alert(self.tr("Disengage to Power Off"), self)


class TogglesPanel(ListWidget):
    def __init__(self, parent=None):
        super(TogglesPanel, self).__init__(parent)
        self.params = Params()
        self.toggles = OrderedDict()

        toggle_defs = [
            ("OpenpilotEnabledToggle",
             self.tr("Enable openpilot"),
             self.tr("Use the openpilot system for adaptive cruise control and lane keep driver assistance. Your attention is required at all times to use this feature. Changing this setting takes effect when the car is powered off."),
             ASSET_PATH / "img_chffr_wheel.png"),
            ("ExperimentalLongitudinalEnabled",
             self.tr("openpilot Longitudinal Control (Alpha)"),
             self.tr("<b>WARNING: openpilot longitudinal control is in alpha for this car and will disable Automatic Emergency Braking (AEB).</b><br><br>On this car, openpilot defaults to the car's built-in ACC instead of openpilot's longitudinal control. Enable this to switch to openpilot longitudinal control. Enabling Experimental mode is recommended when enabling openpilot longitudinal control alpha."),
             ASSET_PATH / "offroad/icon_speed_limit.png"),
            ("ExperimentalMode",
             self.tr("Experimental Mode"),
             "",
             ASSET_PATH / "img_experimental_white.svg"),
            ("DisengageOnAccelerator",
             self.tr("Disengage on Accelerator Pedal"),
             self.tr("When enabled, pressing the accelerator pedal will disengage openpilot."),
             ASSET_PATH / "offroad/icon_disengage_on_accelerator.svg"),
            ("IsLdwEnabled",
             self.tr("Enable Lane Departure Warnings"),
             self.tr("Receive alerts to steer back into the lane when your vehicle drifts over a detected lane line without a turn signal activated while driving over 31 mph (50 km/h)."),
             ASSET_PATH / "offroad/icon_warning.png"),
            ("AlwaysOnDM",
             self.tr("Always-On Driver Monitoring"),
             self.tr("Enable driver monitoring even when openpilot is not engaged."),
             ASSET_PATH / "offroad/icon_monitoring.png"),
            ("RecordFront",
             self.tr("Record and Upload Driver Camera"),
             self.tr("Upload data from the driver facing camera and help improve the driver monitoring algorithm."),
             ASSET_PATH / "offroad/icon_monitoring.png"),
            ("IsMetric",
             self.tr("Use Metric System"),
             self.tr("Display speed in km/h instead of mph."),
             ASSET_PATH / "offroad/icon_metric.png"),
        ]

        longi_button_texts = [self.tr("Aggressive"), self.tr("Standard"), self.tr("Relaxed")]
        self.long_personality_setting = ButtonParamControl("LongitudinalPersonality", self.tr("Driving Personality"),
                                                           self.tr("Standard is recommended. In aggressive mode, openpilot will follow lead cars closer and be more aggressive with the gas and brake. In relaxed mode openpilot will stay further away from lead cars. On supported cars, you can cycle through these personalities with your steering wheel distance button."),
                                                           str(ASSET_PATH / "offroad/icon_speed_limit.png"),
                                                           longi_button_texts)

        uiState().uiUpdate.connect(self.updateState)

        for param, title, desc, icon in toggle_defs:
            toggle = ParamControl(param, title, desc, str(icon))
            locked = self.params.get_bool(f"{param}Lock") if f"{param}Lock" in self.params.all_keys() else False
            toggle.setEnabled(not locked)
            self.addItem(toggle)
            self.toggles[param] = toggle

            if param == "DisengageOnAccelerator":
                self.addItem(self.long_personality_setting)

        self.toggles["ExperimentalMode"].setActiveIcon(str(ASSET_PATH / "img_experimental.svg"))
        self.toggles["ExperimentalMode"].setConfirmation(True, True)
        self.toggles["ExperimentalLongitudinalEnabled"].setConfirmation(True, False)

        self.toggles["ExperimentalLongitudinalEnabled"].toggleFlipped.connect(self.updateToggles)

    @pyqtSlot(object)
    def updateState(self, state):
        sm = state.sm
        if sm.updated['selfdriveState']:
            personality = sm['selfdriveState'].personality
            if personality != state.scene.personality and state.scene.started and self.isVisible():
                self.long_personality_setting.setCheckedButton(int(personality))
            uiState().scene.personality = personality

    @pyqtSlot(str)
    def expandToggleDescription(self, param):
        if param in self.toggles:
            self.toggles[param].showDescription()

    def showEvent(self, event):
        super(TogglesPanel, self).showEvent(event)
        self.updateToggles()

    def updateToggles(self):
        experimental_mode_toggle = self.toggles.get("ExperimentalMode")
        op_long_toggle = self.toggles.get("ExperimentalLongitudinalEnabled")
        e2e_description = self.tr("openpilot defaults to driving in <b>chill mode</b>. Experimental mode enables <b>alpha-level features</b> that aren't ready for chill mode. Experimental features are listed below:<br><h4>End-to-End Longitudinal Control</h4><br>Let the driving model control the gas and brakes. openpilot will drive as it thinks a human would, including stopping for red lights and stop signs. Since the driving model decides the speed to drive, the set speed will only act as an upper bound. This is an alpha quality feature; mistakes should be expected.<br><h4>New Driving Visualization</h4><br>The driving visualization will transition to the road-facing wide-angle camera at low speeds to better show some turns. The Experimental mode logo will also be shown in the top right corner.")

        is_release = self.params.get_bool("IsReleaseBranch")
        cp_bytes = self.params.get("CarParamsPersistent")
        if cp_bytes:
            try:
                cp = car.CarParams.from_bytes(cp_bytes)
                experimental_long_available = cp.experimentalLongitudinalAvailable
                if not experimental_long_available or is_release:
                    self.params.delete("ExperimentalLongitudinalEnabled")
                if op_long_toggle:
                    op_long_toggle.setVisible(experimental_long_available and not is_release)
                has_longitudinal = cp.openpilotLongitudinalControl
                if has_longitudinal:
                    if experimental_mode_toggle:
                        experimental_mode_toggle.setEnabled(True)
                        experimental_mode_toggle.setDescription(e2e_description)
                    self.long_personality_setting.setEnabled(True)
                else:
                    if experimental_mode_toggle:
                        experimental_mode_toggle.setEnabled(False)
                    self.long_personality_setting.setEnabled(False)
                    self.params.delete("ExperimentalMode")

                    unavailable = self.tr("Experimental mode is currently unavailable on this car since the car's stock ACC is used for longitudinal control.")
                    if experimental_long_available:
                        if is_release:
                            long_desc = unavailable + " " + self.tr("An alpha version of openpilot longitudinal control can be tested, along with Experimental mode, on non-release branches.")
                        else:
                            long_desc = self.tr("Enable the openpilot longitudinal control (alpha) toggle to allow Experimental mode.")
                    else:
                        long_desc = unavailable + " " + self.tr("openpilot longitudinal control may come in a future update.")
                    if experimental_mode_toggle:
                        experimental_mode_toggle.setDescription("<b>" + long_desc + "</b><br><br>" + e2e_description)
                if experimental_mode_toggle:
                    experimental_mode_toggle.refresh()
            except Exception as e:
                cloudlog.exception("Error parsing CarParamsPersistent")
                if experimental_mode_toggle:
                    experimental_mode_toggle.setDescription(e2e_description)
                if op_long_toggle:
                    op_long_toggle.setVisible(False)
        else:
            if experimental_mode_toggle:
                experimental_mode_toggle.setDescription(e2e_description)
            if op_long_toggle:
                op_long_toggle.setVisible(False)


class SoftwarePanel(ListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

class DeveloperPanel(ListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

class Networking(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def setPrimeType(self, prime_type):
        pass
