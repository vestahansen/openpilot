import os
import json
import time
import base64
import hashlib
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QUrl
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from openpilot.selfdrive.ui.qt.util import getDongleId, getUserAgent

BASE_URL = os.environ.get("API_HOST", "https://api.commadotai.com")

def get_rsa_private_key():
    key_path = os.path.expanduser("~/.comma/persist/comma/id_rsa")
    try:
        with open(key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
            )
        return private_key
    except Exception:
        print("No RSA private key found, please run manager.py or registration.py")
        return None

def rsa_sign(data):
    private_key = get_rsa_private_key()
    if not private_key:
        return None
    signature = private_key.sign(
        data,
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return signature


def b64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=')

def create_jwt(payloads=None, expiry=3600):
    if payloads is None:
        payloads = {}
    header = {"alg": "RS256"}

    t = int(time.time())
    payload = {"identity": getDongleId() or "", "nbf": t, "iat": t, "exp": t + expiry}
    payload.update(payloads)

    header_json = json.dumps(header, separators=(',', ':'), sort_keys=True).encode('utf-8')
    payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True).encode('utf-8')

    encoded_header = b64url_encode(header_json)
    encoded_payload = b64url_encode(payload_json)

    jwt_unsigned = encoded_header + b'.' + encoded_payload

    jwt_hash = hashlib.sha256(jwt_unsigned).digest()

    signature = rsa_sign(jwt_hash)
    if not signature:
        return ""

    encoded_signature = b64url_encode(signature)

    jwt = jwt_unsigned + b'.' + encoded_signature

    return jwt.decode('utf-8')


class HttpRequest(QObject):
    requestDone = pyqtSignal(str, bool, QNetworkReply.NetworkError)

    class Method:
        GET = "GET"
        DELETE = "DELETE"

    def __init__(self, parent=None, create_jwt=True, timeout=20000):
        super().__init__(parent)
        self.create_jwt = create_jwt
        self.timeout_interval = timeout
        self.reply = None
        self.networkTimer = QTimer(self)
        self.networkTimer.setSingleShot(True)
        self.networkTimer.timeout.connect(self.requestTimeout)

    def active(self):
        return self.reply is not None

    def timeout(self):
        return self.reply is not None and self.reply.error() == QNetworkReply.OperationCanceledError

    def sendRequest(self, requestURL, method="GET"):
        if self.active():
            print("HttpRequest is active")
            return

        if self.create_jwt:
            token = create_jwt()
        else:
            token_json_path = os.path.expanduser("~/.comma/auth.json")
            try:
                with open(token_json_path, "r") as f:
                    token_json = f.read()
                token_data = json.loads(token_json)
                token = token_data.get("access_token", "")
            except Exception:
                token = ""

        request = QNetworkRequest(QUrl(requestURL))
        request.setRawHeader(b"User-Agent", getUserAgent().encode('utf-8'))
        if token:
            request.setRawHeader(b"Authorization", ("JWT " + token).encode('utf-8'))

        if method == self.Method.GET:
            self.reply = self.nam().get(request)
        elif method == self.Method.DELETE:
            self.reply = self.nam().deleteResource(request)
        else:
            print(f"Unsupported HTTP method: {method}")
            return

        self.networkTimer.start(self.timeout_interval)
        self.reply.finished.connect(self.requestFinished)

    def requestTimeout(self):
        if self.reply:
            self.reply.abort()

    def requestFinished(self):
        self.networkTimer.stop()
        if self.reply.error() == QNetworkReply.NoError:
            response = bytes(self.reply.readAll()).decode('utf-8')
            self.requestDone.emit(response, True, self.reply.error())
        else:
            if self.reply.error() == QNetworkReply.OperationCanceledError:
                self.nam().clearAccessCache()
                self.nam().clearConnectionCache()
                error = "Request timed out"
            else:
                error = self.reply.errorString()
            self.requestDone.emit(error, False, self.reply.error())

        self.reply.deleteLater()
        self.reply = None

    @staticmethod
    def nam():
        if not hasattr(HttpRequest, '_nam'):
            HttpRequest._nam = QNetworkAccessManager()
        return HttpRequest._nam
