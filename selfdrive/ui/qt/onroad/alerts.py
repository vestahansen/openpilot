import time
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QColor, QPainter, QBrush, QLinearGradient, QFont

from cereal import log
from openpilot.system.hardware import PC
from openpilot.selfdrive.ui.state import UIState

class Alert:
    def __init__(self, text1='', text2='', type='', size=log.SelfdriveState.AlertSize.none, status=log.SelfdriveState.AlertStatus.normal):
        self.text1 = text1
        self.text2 = text2
        self.type = type
        self.size = size
        self.status = status

    def equal(self, other):
        return self.text1 == other.text1 and self.text2 == other.text2 and self.type == other.type

class OnroadAlerts(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.alert = Alert()
        self.bg = QColor(0, 0, 0, 0)
        self.alert_colors = {
            log.SelfdriveState.AlertStatus.normal: QColor(0x15, 0x15, 0x15, 0xf1),
            log.SelfdriveState.AlertStatus.userPrompt: QColor(0xDA, 0x6F, 0x25, 0xf1),
            log.SelfdriveState.AlertStatus.critical: QColor(0xC9, 0x22, 0x31, 0xf1),
        }

    def updateState(self, s: UIState):
        a = self.getAlert(s.sm, s.scene.started_frame)
        if not self.alert.equal(a):
            self.alert = a
            self.update()

    def clear(self):
        self.alert = Alert()
        self.update()

    def getAlert(self, sm, started_frame):
        ss = sm['selfdriveState']
        selfdrive_frame = sm.rcv_frame['selfdriveState']

        a = Alert()
        if selfdrive_frame >= started_frame:  # Don't get old alert.
            a = Alert(ss.alertText1, ss.alertText2, ss.alertType, ss.alertSize, ss.alertStatus)

        if not sm.updated['selfdriveState'] and (sm.frame - started_frame) > 5 * sm.freq:
            SELFDRIVE_STATE_TIMEOUT = 5
            ss_missing = (time.time()*1e9 - sm.rcv_times['selfdriveState']) / 1e9

            # Handle selfdrive timeout
            if selfdrive_frame < started_frame:
                # car is started, but selfdriveState hasn't been seen at all
                a = Alert("openpilot Unavailable", "Waiting to start", "selfdriveWaiting",
                               log.SelfdriveState.AlertSize.mid, log.SelfdriveState.AlertStatus.normal)
            elif ss_missing > SELFDRIVE_STATE_TIMEOUT and not PC:
                # car is started, but selfdrive is lagging or died
                if ss.enabled and (ss_missing - SELFDRIVE_STATE_TIMEOUT) < 10:
                    a = Alert("TAKE CONTROL IMMEDIATELY", "System Unresponsive", "selfdriveUnresponsive",
                                   log.SelfdriveState.AlertSize.full, log.SelfdriveState.AlertStatus.critical)
                else:
                    a = Alert("System Unresponsive", "Reboot Device", "selfdriveUnresponsivePermanent",
                                   log.SelfdriveState.AlertSize.mid, log.SelfdriveState.AlertStatus.normal)
        return a

    def paintEvent(self, event):
        if self.alert.size == log.SelfdriveState.AlertSize.none:
            return

        alert_heights = {
            log.SelfdriveState.AlertSize.small: 271,
            log.SelfdriveState.AlertSize.mid: 420,
            log.SelfdriveState.AlertSize.full: self.height(),
        }
        h = alert_heights[self.alert.size]

        margin = 40
        radius = 30
        if self.alert.size == log.SelfdriveState.AlertSize.full:
            margin = 0
            radius = 0
        r = QRect(0 + margin, self.height() - h + margin, self.width() - margin*2, h - margin*2)

        p = QPainter(self)

        # draw background + gradient
        p.setPen(Qt.NoPen)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        p.setBrush(QBrush(self.alert_colors[self.alert.status]))
        p.drawRoundedRect(r, radius, radius)

        g = QLinearGradient(0, r.y(), 0, r.bottom())
        g.setColorAt(0, QColor.fromRgbF(0, 0, 0, 0.05))
        g.setColorAt(1, QColor.fromRgbF(0, 0, 0, 0.35))

        p.setCompositionMode(QPainter.CompositionMode_DestinationOver)
        p.setBrush(QBrush(g))
        p.drawRoundedRect(r, radius, radius)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # text
        c = r.center()
        p.setPen(QColor(0xff, 0xff, 0xff))
        p.setRenderHint(QPainter.TextAntialiasing)
        if self.alert.size == log.SelfdriveState.AlertSize.small:
            p.setFont(QFont("Inter", 74, QFont.DemiBold))
            p.drawText(r, Qt.AlignCenter, self.alert.text1)
        elif self.alert.size == log.SelfdriveState.AlertSize.mid:
            p.setFont(QFont("Inter", 88, QFont.Bold))
            p.drawText(QRect(0, c.y() - 125, self.width(), 150), Qt.AlignHCenter | Qt.AlignTop, self.alert.text1)
            p.setFont(QFont("Inter", 66))
            p.drawText(QRect(0, c.y() + 21, self.width(), 90), Qt.AlignHCenter, self.alert.text2)
        elif self.alert.size == log.SelfdriveState.AlertSize.full:
            l = len(self.alert.text1) > 15
            p.setFont(QFont("Inter", 132 if l else 177, QFont.Bold))
            p.drawText(QRect(0, r.y() + (240 if l else 270), self.width(), 600), Qt.AlignHCenter | Qt.TextWordWrap, self.alert.text1)
            p.setFont(QFont("Inter", 88))
            p.drawText(QRect(0, r.height() - (361 if l else 420), self.width(), 300), Qt.AlignHCenter | Qt.TextWordWrap, self.alert.text2)