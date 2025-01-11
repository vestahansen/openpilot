import os
import json
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from openpilot.selfdrive.ui.qt.util import getDongleId, Params
from openpilot.selfdrive.ui.qt.api import BASE_URL, HttpRequest

class PrimeState(QObject):
    changed = pyqtSignal(int)

    class Type:
        PRIME_TYPE_UNKNOWN = -2
        PRIME_TYPE_UNPAIRED = -1
        PRIME_TYPE_NONE = 0
        PRIME_TYPE_MAGENTA = 1
        PRIME_TYPE_LITE = 2
        PRIME_TYPE_BLUE = 3
        PRIME_TYPE_MAGENTA_NEW = 4
        PRIME_TYPE_PURPLE = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self.prime_type = PrimeState.Type.PRIME_TYPE_UNKNOWN

        env_prime_type = os.getenv('PRIME_TYPE')
        params = Params()
        type_str = env_prime_type or params.get("PrimeType", encoding='utf-8')

        if type_str:
            try:
                self.prime_type = int(type_str)
            except ValueError:
                pass

        dongle_id = getDongleId()
        if dongle_id:
            url = f"{BASE_URL}/v1.1/devices/{dongle_id}/"
            self.request = HttpRequest(self)
            self.request.requestDone.connect(self.handleReply)
            self.request.sendRequest(url)

            self.timer = QTimer(self)
            self.timer.timeout.connect(lambda: self.request.sendRequest(url))
            self.timer.start(5000)

        QTimer.singleShot(1, lambda: self.changed.emit(self.prime_type))

    def handleReply(self, response, success, error_code):
        if not success:
            return

        try:
            doc = json.loads(response)
        except json.JSONDecodeError:
            print("JSON Parse failed on getting pairing and PrimeState status")
            return

        is_paired = doc.get("is_paired", False)
        prime_type = int(doc.get("prime_type", PrimeState.Type.PRIME_TYPE_UNKNOWN))
        self.setType(prime_type if is_paired else PrimeState.Type.PRIME_TYPE_UNPAIRED)

    def setType(self, type):
        if type != self.prime_type:
            self.prime_type = type
            Params().put("PrimeType", str(self.prime_type))
            self.changed.emit(self.prime_type)

    def currentType(self):
        return self.prime_type

    def isSubscribed(self):
        return self.prime_type > PrimeState.Type.PRIME_TYPE_NONE
