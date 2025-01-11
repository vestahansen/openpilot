#!/usr/bin/env python3
import sys
from PyQt5.QtCore import QTranslator
from PyQt5.QtWidgets import QApplication

from openpilot.common.params import Params
from openpilot.common.realtime import config_realtime_process
from openpilot.selfdrive.ui.qt.qt_window import setMainWindow
from openpilot.selfdrive.ui.qt.window import MainWindow
# from openpilot.selfdrive.ui.qt.util import swagLogMessageHandler

if __name__ == "__main__":
    # TODO: Is this a good priority?
    config_realtime_process(7, 50)
    # swagLogMessageHandler()

    translator = QTranslator()
    translation_file = Params().get("LanguageSetting", encoding='utf8')
    if translation_file:
        if not translator.load(f":{translation_file}"):
            print(f"Failed to load translation file: {translation_file}", file=sys.stderr)

    app = QApplication(sys.argv)
    app.installTranslator(translator)

    main_window = MainWindow()
    setMainWindow(main_window)
    app.installEventFilter(main_window)
    sys.exit(app.exec_())