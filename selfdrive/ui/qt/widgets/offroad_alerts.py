import json
from PyQt5.QtWidgets import QFrame, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtCore import Qt, pyqtSignal

from openpilot.common.params import Params
from openpilot.system.hardware import HARDWARE
from openpilot.selfdrive.ui.qt.widgets.scrollview import ScrollView


class AbstractAlert(QFrame):
    dismiss = pyqtSignal()

    def __init__(self, hasRebootBtn, parent=None):
        super().__init__(parent)

        self.params = Params()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(30)

        widget = QWidget()
        self.scrollable_layout = QVBoxLayout(widget)
        widget.setStyleSheet("background-color: transparent;")
        main_layout.addWidget(ScrollView(widget))

        # Bottom footer, dismiss + reboot buttons
        footer_layout = QHBoxLayout()
        main_layout.addLayout(footer_layout)

        dismiss_btn = QPushButton("Close")
        dismiss_btn.setFixedSize(400, 125)
        footer_layout.addWidget(dismiss_btn, 0, Qt.AlignBottom | Qt.AlignLeft)
        dismiss_btn.clicked.connect(self.dismiss)

        self.snooze_btn = QPushButton("Snooze Update")
        self.snooze_btn.setVisible(False)
        self.snooze_btn.setFixedSize(550, 125)
        footer_layout.addWidget(self.snooze_btn, 0, Qt.AlignBottom | Qt.AlignRight)
        self.snooze_btn.clicked.connect(self.snoozeUpdate)
        self.snooze_btn.clicked.connect(self.dismiss)
        self.snooze_btn.setStyleSheet("color: white; background-color: #4F4F4F;")

        if hasRebootBtn:
            rebootBtn = QPushButton("Reboot and Update")
            rebootBtn.setFixedSize(600, 125)
            footer_layout.addWidget(rebootBtn, 0, Qt.AlignBottom | Qt.AlignRight)
            rebootBtn.clicked.connect(lambda: HARDWARE.reboot())

        self.setStyleSheet("""
        * {
            font-size: 48px;
            color: white;
        }
        QFrame {
            border-radius: 30px;
            background-color: #393939;
        }
        QPushButton {
            color: black;
            font-weight: 500;
            border-radius: 30px;
            background-color: white;
        }
        """)

    def snoozeUpdate(self):
        self.params.put_bool("SnoozeUpdate", True)


class OffroadAlert(AbstractAlert):
    def __init__(self, parent=None):
        super().__init__(False, parent)
        self.alerts = {}

    def refresh(self):
        # Build widgets for each offroad alert on first refresh
        if not self.alerts:
            with open(Path(__file__).parents[3] / 'selfdrived/alerts_offroad.json') as f:
                obj = json.load(f)

            # Descending sort labels by severity
            sorted_alerts = sorted(
                [(k, v['severity']) for k, v in obj.items()],
                key=lambda x: x[1], reverse=True
            )

            for key, severity in sorted_alerts:
                label = QLabel(self)
                self.alerts[key] = label
                label.setMargin(60)
                label.setWordWrap(True)
                label.setStyleSheet("background-color: {}".format("#E22C2C" if severity else "#292929"))
                self.scrollable_layout.addWidget(label)
            self.scrollable_layout.addStretch(1)

        alertCount = 0
        for key, label in self.alerts.items():
            text = ''
            bytes = self.params.get(key)
            if bytes:
                doc_par = json.loads(bytes)
                text = self.tr(doc_par.get("text", ""))
                extra = doc_par.get("extra", "")
                if extra:
                    text = text.format(extra)
            label.setText(text)
            visible = bool(text)
            label.setVisible(visible)
            alertCount += visible
        self.snooze_btn.setVisible(bool(self.alerts.get("Offroad_ConnectivityNeeded", QLabel()).text()))
        return alertCount


class UpdateAlert(AbstractAlert):
    def __init__(self, parent=None):
        super().__init__(True, parent)
        self.releaseNotes = QLabel(self)
        self.releaseNotes.setWordWrap(True)
        self.releaseNotes.setAlignment(Qt.AlignTop)
        self.scrollable_layout.addWidget(self.releaseNotes)

    def refresh(self):
        updateAvailable = self.params.get_bool("UpdateAvailable")
        if updateAvailable:
            self.releaseNotes.setText(self.params.get("UpdaterNewReleaseNotes").decode('utf-8'))
        return updateAvailable
