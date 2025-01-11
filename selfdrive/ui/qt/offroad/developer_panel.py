from PyQt5.QtCore import pyqtSlot

from cereal import car
from openpilot.common.params import Params
from openpilot.selfdrive.ui.state import uiState
from openpilot.selfdrive.ui.qt.widgets.controls import ListWidget, ParamControl
from openpilot.selfdrive.ui.qt.widgets.ssh_keys import SshToggle, SshControl

class DeveloperPanel(ListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.params = Params()
        self.offroad = False

        # SSH keys
        self.addItem(SshToggle(self))
        self.addItem(SshControl(self))

        # Joystick Debug Mode toggle
        self.joystickToggle = ParamControl("JoystickDebugMode", self.tr("Joystick Debug Mode"), "", "")
        self.joystickToggle.toggleFlipped.connect(self.onJoystickToggleFlipped)
        self.addItem(self.joystickToggle)

        # Longitudinal Maneuver Mode toggle
        self.longManeuverToggle = ParamControl("LongitudinalManeuverMode", self.tr("Longitudinal Maneuver Mode"), "", "")
        self.longManeuverToggle.toggleFlipped.connect(self.onLongManeuverToggleFlipped)
        self.addItem(self.longManeuverToggle)

        # Check if release branch
        self.is_release = self.params.get_bool("IsReleaseBranch")

        # Connect offroad transition signal
        uiState().offroadTransition.connect(self.updateToggles)

    @pyqtSlot(bool)
    def onJoystickToggleFlipped(self, state):
        self.params.put_bool("LongitudinalManeuverMode", False)
        self.longManeuverToggle.refresh()

    @pyqtSlot(bool)
    def onLongManeuverToggleFlipped(self, state):
        self.params.put_bool("JoystickDebugMode", False)
        self.joystickToggle.refresh()

    @pyqtSlot(bool)
    def updateToggles(self, _offroad):
        for btn in self.findChildren(ParamControl):
            btn.setVisible(not self.is_release)
            btn.setEnabled(_offroad)

        cp_bytes = self.params.get("CarParamsPersistent")
        if cp_bytes:
            try:
                cp = car.CarParams.from_bytes(cp_bytes)
                has_longitudinal = cp.openpilotLongitudinalControl
                self.longManeuverToggle.setEnabled(has_longitudinal and _offroad)
            except Exception:
                self.longManeuverToggle.setEnabled(False)
        else:
            self.longManeuverToggle.setEnabled(False)

        self.offroad = _offroad

    def showEvent(self, event):
        super().showEvent(event)
        self.updateToggles(self.offroad)
