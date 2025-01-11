import subprocess
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QTimer, Qt, QDateTime

from openpilot.common.params import Params
from openpilot.selfdrive.ui.qt.widgets.controls import ListWidget, LabelControl, ButtonControl
from openpilot.selfdrive.ui.qt.widgets.input import ConfirmationDialog, MultiOptionDialog
from openpilot.selfdrive.ui.qt.util import getBrand, timeAgo
from openpilot.selfdrive.ui.state import uiState


class SoftwarePanel(ListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.params = Params()
        self.is_onroad = False

        self.onroadLbl = QLabel(self.tr("Updates are only downloaded while the car is off."))
        self.onroadLbl.setStyleSheet("font-size: 50px; font-weight: 400; text-align: left; padding-top: 30px; padding-bottom: 30px;")
        self.addItem(self.onroadLbl)

        self.versionLbl = LabelControl(self.tr("Current Version"), "")
        self.addItem(self.versionLbl)

        self.downloadBtn = ButtonControl(self.tr("Download"), self.tr("CHECK"))
        self.downloadBtn.clicked.connect(self.downloadBtnClicked)
        self.addItem(self.downloadBtn)

        self.installBtn = ButtonControl(self.tr("Install Update"), self.tr("INSTALL"))
        self.installBtn.clicked.connect(self.installBtnClicked)
        self.addItem(self.installBtn)

        self.targetBranchBtn = ButtonControl(self.tr("Target Branch"), self.tr("SELECT"))
        self.targetBranchBtn.clicked.connect(self.targetBranchBtnClicked)
        if not self.params.get_bool("IsTestedBranch"):
            self.addItem(self.targetBranchBtn)

        self.uninstallBtn = ButtonControl(self.tr("Uninstall {0}").format(getBrand(self)), self.tr("UNINSTALL"))
        self.uninstallBtn.clicked.connect(self.uninstallBtnClicked)
        self.addItem(self.uninstallBtn)

        uiState().offroadTransition.connect(self.offroadTransition)
        self.updateLabels()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateLabels)
        self.timer.start(1000)

    def checkForUpdates(self):
        subprocess.Popen(['pkill', '-SIGUSR1', '-f', 'system.updated.updated'])

    def downloadBtnClicked(self):
        self.downloadBtn.setEnabled(False)
        if self.downloadBtn.text() == self.tr("CHECK"):
            self.checkForUpdates()
        else:
            subprocess.Popen(['pkill', '-SIGHUP', '-f', 'system.updated.updated'])

    def installBtnClicked(self):
        self.installBtn.setEnabled(False)
        self.params.put_bool("DoReboot", True)

    def targetBranchBtnClicked(self):
        current = self.params.get("GitBranch", encoding='utf-8')
        branches = self.params.get("UpdaterAvailableBranches", encoding='utf-8').split(",")
        for b in [current, "devel-staging", "devel", "nightly", "nightly-dev", "master-ci", "master"]:
            if b in branches:
                branches.remove(b)
                branches.insert(0, b)
        cur = self.params.get("UpdaterTargetBranch", encoding='utf-8')
        selection = MultiOptionDialog.getSelection(self.tr("Select a branch"), branches, cur, self)
        if selection:
            self.params.put("UpdaterTargetBranch", selection.encode('utf8'))
            self.targetBranchBtn.setValue(self.params.get("UpdaterTargetBranch", encoding='utf-8'))
            self.checkForUpdates()

    def uninstallBtnClicked(self):
        if ConfirmationDialog.confirm(self.tr("Are you sure you want to uninstall?"), self.tr("Uninstall"), self):
            self.params.put_bool("DoUninstall", True)

    def offroadTransition(self, offroad):
        self.is_onroad = not offroad
        self.updateLabels()

    def updateLabels(self):
        if not self.isVisible():
            return

        self.onroadLbl.setVisible(self.is_onroad)
        self.downloadBtn.setVisible(not self.is_onroad)

        updater_state = self.params.get("UpdaterState", encoding='utf-8')
        failed = int(self.params.get("UpdateFailedCount") or 0) > 0
        if updater_state != "idle":
            self.downloadBtn.setEnabled(False)
            self.downloadBtn.setValue(updater_state)
        else:
            if failed:
                self.downloadBtn.setText(self.tr("CHECK"))
                self.downloadBtn.setValue(self.tr("failed to check for update"))
            elif self.params.get_bool("UpdaterFetchAvailable"):
                self.downloadBtn.setText(self.tr("DOWNLOAD"))
                self.downloadBtn.setValue(self.tr("update available"))
            else:
                lastUpdate = self.tr("never")
                tm = self.params.get("LastUpdateTime", encoding='utf-8')
                if tm:
                    lastUpdate = timeAgo(QDateTime.fromString(tm + "Z", Qt.ISODate))
                self.downloadBtn.setText(self.tr("CHECK"))
                self.downloadBtn.setValue(self.tr("up to date, last checked {0}").format(lastUpdate))
            self.downloadBtn.setEnabled(True)
        self.targetBranchBtn.setValue(self.params.get("UpdaterTargetBranch", encoding='utf-8'))

        self.versionLbl.setText(self.params.get("UpdaterCurrentDescription", encoding='utf-8'))
        self.versionLbl.setDescription(self.params.get("UpdaterCurrentReleaseNotes", encoding='utf-8'))

        self.installBtn.setVisible(not self.is_onroad and self.params.get_bool("UpdateAvailable"))
        self.installBtn.setValue(self.params.get("UpdaterNewDescription", encoding='utf-8'))
        self.installBtn.setDescription(self.params.get("UpdaterNewReleaseNotes", encoding='utf-8'))

        self.update()

    def showEvent(self, event):
        self.installBtn.setEnabled(True)
        self.updateLabels()
