import os
import sys
import json
import signal
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import (
    QFile, QFileInfo, QDateTime, QIODevice, QObject, QDir, QSize,
    Qt, pyqtSignal, QFileSystemWatcher, QCoreApplication)
from PyQt5.QtGui import QPixmap, QSurfaceFormat, QFont
from PyQt5.QtXml import QDomDocument

from openpilot.common.params import Params
from openpilot.common.swaglog import cloudlog
from openpilot.system.hardware import HARDWARE

def getVersion():
    if not hasattr(getVersion, "_version"):
        getVersion._version = Params().get("Version", encoding='utf-8')
    return getVersion._version

def getBrand(w):
    return w.tr("openpilot")

def getUserAgent():
    return "openpilot-" + getVersion()

def getDongleId():
    id = Params().get("DongleId", encoding='utf-8')
    if id and id != "UnregisteredDevice":
        return id
    else:
        return None

def getSupportedLanguages():
    f = QFile(":/languages.json")
    if f.open(QIODevice.ReadOnly | QIODevice.Text):
        val = f.readAll()
        f.close()
        val_str = bytes(val).decode('utf-8')
        return json.loads(val_str)
    return {}

def timeAgo(w, date):
    diff = date.secsTo(QDateTime.currentDateTimeUtc())
    if diff < 60:
        s = w.tr("now")
    elif diff < 60 * 60:
        minutes = diff // 60
        s = w.tr("%n minute(s) ago", "", minutes)
    elif diff < 60 * 60 * 24:
        hours = diff // (60 * 60)
        s = w.tr("%n hour(s) ago", "", hours)
    elif diff < 3600 * 24 * 7:
        days = diff // (60 * 60 * 24)
        s = w.tr("%n day(s) ago", "", days)
    else:
        s = date.date().toString()
    return s

def setQtSurfaceFormat():
    fmt = QSurfaceFormat()
    if sys.platform == 'darwin':
        fmt.setVersion(3, 2)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        fmt.setRenderableType(QSurfaceFormat.OpenGL)
    else:
        fmt.setRenderableType(QSurfaceFormat.OpenGLES)
    fmt.setSamples(16)
    fmt.setStencilBufferSize(1)
    QSurfaceFormat.setDefaultFormat(fmt)

def sigTermHandler(signum, frame):
    signal.signal(signum, signal.SIG_DFL)
    QCoreApplication.quit()

def initApp(disable_hidpi=True):
    HARDWARE.set_display_power(True)
    HARDWARE.set_brightness(65)

    signal.signal(signal.SIGINT, sigTermHandler)
    signal.signal(signal.SIGTERM, sigTermHandler)

    if sys.platform == 'darwin':
        app = QApplication(sys.argv)
        app_dir = QCoreApplication.applicationDirPath()
        if disable_hidpi:
            os.environ['QT_SCALE_FACTOR'] = str(1.0 / app.devicePixelRatio())
    else:
        app_dir = QFileInfo(os.readlink("/proc/self/exe")).path()

    os.environ['QT_DBL_CLICK_DIST'] = '150'
    QDir.setCurrent(app_dir)

    setQtSurfaceFormat()

def swagLogMessageHandler(type, context, msg):
    levels = {
        Qt.DebugMsg: cloudlog.DEBUG,
        Qt.InfoMsg: cloudlog.INFO,
        Qt.WarningMsg: cloudlog.WARNING,
        Qt.CriticalMsg: cloudlog.ERROR,
        Qt.FatalMsg: cloudlog.CRITICAL,
    }
    file = context.file if context.file else ""
    function = context.function if context.function else ""
    line = context.line
    cloudlog.log(levels.get(type, cloudlog.INFO), file, line, function, msg)

def topWidget(widget):
    while widget.parentWidget() is not None:
        widget = widget.parentWidget()
    return widget

def loadPixmap(fileName, size=QSize(), aspectRatioMode=Qt.KeepAspectRatio):
    if size.isEmpty():
        return QPixmap(str(fileName))
    else:
        return QPixmap(str(fileName)).scaled(size, aspectRatioMode, Qt.SmoothTransformation)

def load_bootstrap_icons():
    icons = {}
    f = QFile(":/bootstrap-icons.svg")
    if f.open(QIODevice.ReadOnly | QIODevice.Text):
        xml = QDomDocument()
        xml.setContent(f)
        f.close()
        n = xml.documentElement().firstChild()
        while not n.isNull():
            e = n.toElement()
            if not e.isNull() and e.hasAttribute("id"):
                svg_str = n.toElement().toText().data()
                svg_str = svg_str.replace("<symbol", "<svg")
                svg_str = svg_str.replace("</symbol>", "</svg>")
                icons[e.attribute("id")] = svg_str.encode('utf-8')
            n = n.nextSibling()
    return icons

_icons = None
def bootstrapPixmap(id):
    global _icons
    if _icons is None:
        _icons = load_bootstrap_icons()
    pixmap = QPixmap()
    if id in _icons:
        pixmap.loadFromData(_icons[id], "svg")
    return pixmap

def hasLongitudinalControl(car_params):
    if car_params.getExperimentalLongitudinalAvailable():
        return Params().get_bool("ExperimentalLongitudinalEnabled")
    else:
        return car_params.getOpenpilotLongitudinalControl()


class InterFont(QFont):
    def __init__(self, pixel_size, weight=QFont.Normal):
        super().__init__("Inter")
        self.setPixelSize(pixel_size)
        self.setWeight(weight)

class ParamWatcher(QObject):
    paramChanged = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.watcher = QFileSystemWatcher(self)
        self.watcher.fileChanged.connect(self.fileChanged)
        self.params_hash = {}
        self.params = Params()

    def fileChanged(self, path):
        param_name = QFileInfo(path).fileName()
        param_value = self.params.get(param_name, encoding='utf-8')

        old_value = self.params_hash.get(param_name)
        content_changed = (old_value != param_value)
        self.params_hash[param_name] = param_value
        if content_changed:
            self.paramChanged.emit(param_name, param_value)

    def addParam(self, param_name):
        self.watcher.addPath(self.params.get_param_path(param_name))
