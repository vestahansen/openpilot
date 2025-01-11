#!/usr/bin/env python3
import numpy as np
from pathlib import Path
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from PyQt5.QtGui import QColor


from cereal import log
from cereal.messaging import SubMaster
from openpilot.common.params import Params
from openpilot.common.filter_simple import FirstOrderFilter
from openpilot.common.transformations.orientation import euler2rot
from openpilot.system.hardware import HARDWARE
from openpilot.selfdrive.ui.qt.prime_state import PrimeState

UI_FREQ = 20  # Hz
UI_BORDER_SIZE = 30;
UI_HEADER_HEIGHT = 420;
BACKLIGHT_OFFROAD = 50
BACKLIGHT_DT = 0.05
BACKLIGHT_TS = 10.0
ASSET_PATH = Path(__file__).parent.parent / 'assets'

VIEW_FROM_DEVICE = np.array([
    [0.0, 1.0, 0.0],
    [0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0]
], dtype=np.float32)

def update_sockets(s):
    s.sm.update(0)

def update_state(s):
    sm = s.sm
    scene = s.scene

    if sm.updated['liveCalibration']:
        live_calib = sm['liveCalibration']
        cal_status = live_calib.calStatus
        if cal_status == log.LiveCalibrationData.Status.calibrated:
            device_from_calib = euler2rot(live_calib.rpyCalib)
            wide_from_device = euler2rot(live_calib.wideFromDeviceEuler)
            scene.view_from_calib = VIEW_FROM_DEVICE @ device_from_calib
            scene.view_from_wide_calib = VIEW_FROM_DEVICE @ wide_from_device @ device_from_calib
        else:
            scene.view_from_calib = VIEW_FROM_DEVICE.copy()
            scene.view_from_wide_calib = VIEW_FROM_DEVICE.copy()

    if sm.updated['pandaStates']:
        pandaStates = sm['pandaStates']
        if len(pandaStates) > 0:
            scene.pandaType = pandaStates[0].pandaType
            if scene.pandaType != log.PandaState.PandaType.unknown:
                scene.ignition = False
                for pandaState in pandaStates:
                    scene.ignition |= pandaState.ignitionLine or pandaState.ignitionCan
    elif (s.sm.frame - s.sm.recv_frame['pandaStates']) > 5 * UI_FREQ:
        scene.pandaType = log.PandaState.PandaType.unknown

    if sm.updated['wideRoadCameraState']:
        cam_state = sm['wideRoadCameraState']
        scale = 6.0 if cam_state.sensor == log.FrameData.ImageSensor.ar0231 else 1.0
        scene.light_sensor = max(100.0 - scale * cam_state.exposureValPercent, 0.0)
    elif not sm.all_alive(['wideRoadCameraState']) or not sm.all_valid(['wideRoadCameraState']):
        scene.light_sensor = -1

    scene.started = sm['deviceState'].started and scene.ignition

def ui_update_params(s):
    params = Params()
    s.scene.is_metric = params.get_bool("IsMetric")


class UIStatus:
    STATUS_DISENGAGED = 0
    STATUS_OVERRIDE = 1
    STATUS_ENGAGED = 2

class UIScene:
    def __init__(self):
        self.view_from_calib = VIEW_FROM_DEVICE.copy()
        self.view_from_wide_calib = VIEW_FROM_DEVICE.copy()
        self.pandaType = None
        self.personality = None
        self.light_sensor = -1
        self.started = False
        self.ignition = False
        self.is_metric = False
        self.started_frame = 0

BG_COLORS = {
    UIStatus.STATUS_DISENGAGED: QColor(0x17, 0x33, 0x49, 0xc8),
    UIStatus.STATUS_OVERRIDE: QColor(0x91, 0x9b, 0x95, 0xf1),
    UIStatus.STATUS_ENGAGED: QColor(0x17, 0x86, 0x44, 0xf1),
}


class UIState(QObject):
    uiUpdate = pyqtSignal(object)
    offroadTransition = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sm = SubMaster([
            'modelV2', 'controlsState', 'liveCalibration', 'radarState', 'deviceState',
            'pandaStates', 'carParams', 'driverMonitoringState', 'carState', 'driverStateV2',
            'wideRoadCameraState', 'managerState', 'selfdriveState', 'longitudinalPlan'
        ])
        self.status = UIStatus.STATUS_DISENGAGED
        self.scene = UIScene()
        self.language = Params().get("LanguageSetting", encoding='utf-8') or ''
        self.prime_state = PrimeState(self)
        self.started_prev = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(int(1000 / UI_FREQ))

    def update(self):
        update_sockets(self)
        update_state(self)
        self.updateStatus()
        if self.sm.frame % UI_FREQ == 0:
            pass
        self.uiUpdate.emit(self)

    def updateStatus(self):
        if self.scene.started and self.sm.updated['selfdriveState']:
            ss = self.sm['selfdriveState']
            state = ss.state
            if (state == log.SelfdriveState.OpenpilotState.preEnabled or
                state == log.SelfdriveState.OpenpilotState.overriding):
                self.status = UIStatus.STATUS_OVERRIDE
            else:
                self.status = UIStatus.STATUS_ENGAGED if ss.enabled else UIStatus.STATUS_DISENGAGED

        if self.scene.started != self.started_prev or self.sm.frame == 1:
            if self.scene.started:
                self.status = UIStatus.STATUS_DISENGAGED
                self.scene.started_frame = self.sm.frame
            self.started_prev = self.scene.started
            self.offroadTransition.emit(not self.scene.started)


class Device(QObject):
    displayPowerChanged = pyqtSignal(bool)
    interactiveTimeout = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.awake = False
        self.interactive_timeout = 0
        self.ignition_on = False
        self.offroad_brightness = BACKLIGHT_OFFROAD
        self.last_brightness = 0
        self.brightness_filter = FirstOrderFilter(BACKLIGHT_OFFROAD, BACKLIGHT_TS, BACKLIGHT_DT)
        self.setAwake(True)
        self.resetInteractiveTimeout()
        uiState().uiUpdate.connect(self.update)

    def update(self, s):
        self.updateBrightness(s)
        self.updateWakefulness(s)

    def setAwake(self, on):
        if on != self.awake:
            self.awake = on
            HARDWARE.set_display_power(self.awake)
            self.displayPowerChanged.emit(self.awake)

    def resetInteractiveTimeout(self, timeout=-1):
        if timeout == -1:
            timeout = 10 if self.ignition_on else 30
        self.interactive_timeout = timeout * UI_FREQ

    def updateBrightness(self, s):
        clipped_brightness = self.offroad_brightness
        if s.scene.started and s.scene.light_sensor >= 0:
            clipped_brightness = s.scene.light_sensor
            if clipped_brightness <= 8:
                clipped_brightness = (clipped_brightness / 903.3)
            else:
                clipped_brightness = ((clipped_brightness + 16.0) / 116.0) ** 3.0
            clipped_brightness = np.clip(100.0 * clipped_brightness, 10.0, 100.0)
        brightness = self.brightness_filter.update(clipped_brightness)
        if not self.awake:
            brightness = 0
        if brightness != self.last_brightness:
            HARDWARE.set_screen_brightness(brightness)
            self.last_brightness = brightness

    def updateWakefulness(self, s):
        ignition_just_turned_off = not s.scene.ignition and self.ignition_on
        self.ignition_on = s.scene.ignition
        if ignition_just_turned_off:
            self.resetInteractiveTimeout()
        elif self.interactive_timeout > 0:
            self.interactive_timeout -= 1
            if self.interactive_timeout == 0:
                self.interactiveTimeout.emit()
        self.setAwake(s.scene.ignition or self.interactive_timeout > 0)

    def isAwake(self):
        return self.awake

    def setOffroadBrightness(self, brightness):
        self.offroad_brightness = max(0, min(brightness, 100))

_ui_state_instance = None
def uiState():
    global _ui_state_instance
    if _ui_state_instance is None:
        _ui_state_instance = UIState()
    return _ui_state_instance

_device_instance = None
def device():
    global _device_instance
    if _device_instance is None:
        _device_instance = Device()
    return _device_instance
