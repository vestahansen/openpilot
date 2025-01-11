from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtNetwork import QNetworkReply

from openpilot.common.params import Params
from openpilot.selfdrive.ui.state import uiState, device
from openpilot.selfdrive.ui.qt.api import HttpRequest

class RequestRepeater(HttpRequest):
    def __init__(self, parent, requestURL, cacheKey="", period=0, while_onroad=False):
        super().__init__(parent)
        self.params = Params()
        self.prevResp = ""
        self.requestURL = requestURL
        self.cacheKey = cacheKey
        self.while_onroad = while_onroad

        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.VeryCoarseTimer)
        self.timer.timeout.connect(self._on_timeout)
        self.timer.start(period * 1000)

        if cacheKey:
            self.prevResp = self.params.get(cacheKey)
            if self.prevResp:
                QTimer.singleShot(500, lambda: self.requestDone.emit(self.prevResp, True, QNetworkReply.NoError))
            self.requestDone.connect(self._on_request_done)

    def _on_timeout(self):
        if (not uiState().scene.started or self.while_onroad) and device().isAwake() and not self.active():
            self.sendRequest(self.requestURL)

    def _on_request_done(self, resp, success, error):
        if success and resp != self.prevResp:
            self.params.put(self.cacheKey, resp)
            self.prevResp = resp
