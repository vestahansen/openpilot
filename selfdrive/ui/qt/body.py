from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout, QStackedLayout
from PyQt5.QtGui import QPainter, QColor, QPen, QMovie, QPolygonF
from PyQt5.QtCore import Qt, QPoint, QPointF, QTimer

from openpilot.common.params import Params
from openpilot.common.timing import nanos_since_boot
from openpilot.common.filter_simple import FirstOrderFilter
from openpilot.selfdrive.ui.state import ASSET_PATH, uiState

UI_FREQ = 20.0

class RecordButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(False)
        self.setFixedSize(148, 148)
        self.toggled.connect(self.disableButton)

    def disableButton(self):
        self.setEnabled(False)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        center = QPoint(self.width() // 2, self.height() // 2)

        bg = QColor("#FFFFFF") if self.isChecked() else QColor("#737373")
        accent = QColor("#FF0000") if self.isChecked() else QColor("#FFFFFF")
        if not self.isEnabled():
            bg = QColor("#404040")
            accent = QColor("#FFFFFF")

        if self.isDown():
            accent.setAlphaF(0.7)

        p.setPen(Qt.NoPen)
        p.setBrush(bg)
        p.drawEllipse(center, 74, 74)

        p.setPen(QPen(accent, 6))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, 42, 42)

        p.setPen(Qt.NoPen)
        p.setBrush(accent)
        p.drawEllipse(center, 22, 22)


class BodyWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.charging = False
        self.last_button = 0
        self.fuel_filter = FirstOrderFilter(1.0, 5.0, 1.0 / UI_FREQ)

        layout = QStackedLayout(self)
        layout.setStackingMode(QStackedLayout.StackAll)

        w = QWidget()
        vlayout = QVBoxLayout(w)
        vlayout.setContentsMargins(45, 45, 45, 45)
        layout.addWidget(w)

        self.face = QLabel()
        self.face.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.face)
        self.awake = QMovie(str(ASSET_PATH / "body/awake.gif"))
        self.awake.setCacheMode(QMovie.CacheAll)
        self.sleep = QMovie(str(ASSET_PATH / "body/sleep.gif"))
        self.sleep.setCacheMode(QMovie.CacheAll)

        self.btn = RecordButton(self)
        vlayout.addWidget(self.btn, 0, Qt.AlignBottom | Qt.AlignRight)
        self.btn.clicked.connect(self.onButtonClicked)
        w.raise_()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateState)
        self.timer.start(int(1000 / UI_FREQ))

    def offroadTransition(self, offroad):
        self.btn.setChecked(True)
        self.btn.setEnabled(True)
        self.fuel_filter.reset(1.0)

    def onButtonClicked(self):
        checked = self.btn.isChecked()
        self.btn.setEnabled(False)
        Params().putBool("DisableLogging", not checked)
        self.last_button = nanos_since_boot()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        p.fillRect(self.rect(), QColor(0, 0, 0))

        p.save()
        p.translate(self.width() - 136, 16)
        gray = QColor("#737373")
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(gray, 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawRoundedRect(2, 2, 78, 36, 8, 8)

        p.setPen(Qt.NoPen)
        p.setBrush(gray)
        p.drawRoundedRect(84, 12, 6, 16, 4, 4)
        p.drawRect(84, 12, 3, 16)

        fuel = max(min(self.fuel_filter.x, 1.0), 0.2)
        m = 5
        p.setPen(Qt.NoPen)
        color = QColor("#32D74B") if fuel > 0.25 else QColor("#FF453A")
        p.setBrush(color)
        p.drawRoundedRect(2 + m, 2 + m, (78 - 2 * m) * fuel, 36 - 2 * m, 4, 4)

        if self.charging:
            p.setPen(Qt.NoPen)
            p.setBrush(Qt.white)
            charger = QPolygonF([
                QPointF(12.31, 0),
                QPointF(12.31, 16.92),
                QPointF(18.46, 16.92),
                QPointF(6.15, 40),
                QPointF(6.15, 23.08),
                QPointF(0, 23.08),
            ])
            p.drawPolygon(charger.translated(98, 0))
        p.restore()

    def updateState(self):
        if not self.isVisible():
            return

        s = uiState()
        sm = s.sm
        cs = sm['carState']

        self.charging = cs.charging
        self.fuel_filter.update(cs.fuelGauge)

        standstill = abs(cs.vEgo) < 0.01
        m = self.sleep if standstill else self.awake

        if m != self.face.movie():
            self.face.setMovie(m)
            self.face.movie().start()

        if sm.updated['managerState'] and (sm.rcv_time['managerState'] - self.last_button) * 1e-9 > 0.5:
            for proc in sm['managerState'].managerState.processes:
                if proc.name == "loggerd":
                    self.btn.setEnabled(True)
                    self.btn.setChecked(proc.running)

        self.update()