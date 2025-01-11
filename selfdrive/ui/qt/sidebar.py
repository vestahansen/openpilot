from PyQt5.QtWidgets import QFrame, QSizePolicy
from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QFont

from cereal import log
from cereal.messaging import PubMaster, new_message
from openpilot.common.timing import nanos_since_boot
from openpilot.selfdrive.ui.state import UIState, ASSET_PATH
# from openpilot.selfdrive.ui.qt.network.networking import Networking
from openpilot.selfdrive.ui.qt.util import loadPixmap, InterFont

class Sidebar(QFrame):
    valueChanged = pyqtSignal()
    openSettings = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.onroad = False
        self.flag_pressed = False
        self.settings_pressed = False

        self.home_btn = QRect(60, 860, 180, 180)
        self.settings_btn = QRect(50, 35, 200, 117)
        self.good_color = QColor(255, 255, 255)
        self.warning_color = QColor(218, 202, 37)
        self.danger_color = QColor(201, 34, 49)

        self.home_img = loadPixmap(ASSET_PATH / "images/button_home.png", self.home_btn.size())
        self.flag_img = loadPixmap(ASSET_PATH / "images/button_flag.png", self.home_btn.size())
        self.settings_img = loadPixmap(ASSET_PATH / "images/button_settings.png", self.settings_btn.size(), Qt.IgnoreAspectRatio)

        self.valueChanged.connect(self.update)

        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setFixedWidth(300)

        self.ui_state = UIState()
        self.ui_state.uiUpdate.connect(self.updateState)

        self.pm = PubMaster(['userFlag'])
        self.networking = None

        self.connect_status = ((self.tr("CONNECT"), self.tr("OFFLINE")), self.warning_color)
        self.panda_status = ((self.tr("VEHICLE"), self.tr("ONLINE")), self.good_color)
        self.temp_status = ((self.tr("TEMP"), self.tr("HIGH")), self.danger_color)
        self.net_type = self.tr('--')
        self.net_strength = 0

        self.network_type = {
            log.DeviceState.NetworkType.none: self.tr("--"),
            log.DeviceState.NetworkType.wifi: self.tr("Wi-Fi"),
            log.DeviceState.NetworkType.ethernet: self.tr("ETH"),
            log.DeviceState.NetworkType.cell2G: self.tr("2G"),
            log.DeviceState.NetworkType.cell3G: self.tr("3G"),
            log.DeviceState.NetworkType.cell4G: self.tr("LTE"),
            log.DeviceState.NetworkType.cell5G: self.tr("5G"),
        }

    def mousePressEvent(self, event):
        if self.onroad and self.home_btn.contains(event.pos()):
            self.flag_pressed = True
            self.update()
        elif self.settings_btn.contains(event.pos()):
            self.settings_pressed = True
            self.update()

    def mouseReleaseEvent(self, event):
        if self.flag_pressed or self.settings_pressed:
            self.flag_pressed = False
            self.settings_pressed = False
            self.update()

        if self.onroad and self.home_btn.contains(event.pos()):
            msg = new_message('userFlag')
            self.pm.send('userFlag', msg)
        elif self.settings_btn.contains(event.pos()):
            self.openSettings.emit(0, '')

    def offroadTransition(self, offroad):
        self.onroad = not offroad
        self.update()

    def updateState(self, s):
        if not self.isVisible():
            return

        sm = s.sm
        # TODO: Uncomment the following line once Networking is implemented
        # self.networking = self.networking or self.window().findChild(Networking)
        tethering_on = self.networking and self.networking.wifi.tethering_on

        deviceState = sm['deviceState']
        self.net_type = "Hotspot" if tethering_on else self.network_type[deviceState.networkType.raw]
        strength = 4 if tethering_on else deviceState.networkStrength.raw
        self.net_strength = strength + 1 if strength > 0 else 0

        last_ping = deviceState.lastAthenaPingTime
        if last_ping == 0:
            self.connect_status = ((self.tr("CONNECT"), self.tr("OFFLINE")), self.warning_color)
        else:
            if nanos_since_boot() - last_ping < 80e9:
                self.connect_status = ((self.tr("CONNECT"), self.tr("ONLINE")), self.good_color)
            else:
                self.connect_status = ((self.tr("CONNECT"), self.tr("ERROR")), self.danger_color)

        ts = deviceState.thermalStatus
        if ts == log.DeviceState.ThermalStatus.green:
            self.temp_status = ((self.tr("TEMP"), self.tr("GOOD")), self.good_color)
        elif ts == log.DeviceState.ThermalStatus.yellow:
            self.temp_status = ((self.tr("TEMP"), self.tr("OK")), self.warning_color)
        else:
            self.temp_status = ((self.tr("TEMP"), self.tr("HIGH")), self.danger_color)

        pandaType = s.scene.pandaType
        if pandaType == log.PandaState.PandaType.unknown:
            self.panda_status = ((self.tr("NO"), self.tr("PANDA")), self.danger_color)
        else:
            self.panda_status = ((self.tr("VEHICLE"), self.tr("ONLINE")), self.good_color)

        self.valueChanged.emit()

    def drawMetric(self, painter, label, color, y):
        rect = QRect(30, y, 240, 126)

        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.setClipRect(rect.x() + 4, rect.y(), 18, rect.height(), Qt.ReplaceClip)
        painter.drawRoundedRect(QRect(rect.x() + 4, rect.y() + 4, 100, 118), 18, 18)
        painter.setClipping(False)

        pen = QPen(QColor(0xff, 0xff, 0xff, 0x55))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect, 20, 20)

        painter.setPen(QColor(0xff, 0xff, 0xff))
        painter.setFont(InterFont(35, QFont.DemiBold))
        painter.drawText(rect.adjusted(22, 0, 0, 0), Qt.AlignCenter, label[0] + "\n" + label[1])

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(self.rect(), QColor(57, 57, 57))

        painter.setOpacity(0.65 if self.settings_pressed else 1.0)
        painter.drawPixmap(self.settings_btn.x(), self.settings_btn.y(), self.settings_img)
        painter.setOpacity(0.65 if self.onroad and self.flag_pressed else 1.0)
        img = self.flag_img if self.onroad else self.home_img
        painter.drawPixmap(self.home_btn.x(), self.home_btn.y(), img)
        painter.setOpacity(1.0)

        x = 58
        gray = QColor(0x54, 0x54, 0x54)
        for i in range(5):
            painter.setBrush(Qt.white if i < self.net_strength else gray)
            painter.drawEllipse(x, 196, 27, 27)
            x += 37

        painter.setFont(InterFont(35))
        painter.setPen(QColor(0xff, 0xff, 0xff))
        rect = QRect(58, 247, self.width() - 100, 50)
        painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, self.net_type)

        self.drawMetric(painter, self.temp_status[0], self.temp_status[1], 338)
        self.drawMetric(painter, self.panda_status[0], self.panda_status[1], 496)
        self.drawMetric(painter, self.connect_status[0], self.connect_status[1], 654)
