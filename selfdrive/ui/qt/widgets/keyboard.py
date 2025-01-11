from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QTouchEvent, QMouseEvent
from PyQt5.QtWidgets import QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QStackedLayout, QButtonGroup

BACKSPACE_KEY = "⌫"
ENTER_KEY = "→"

KEY_STRETCH = {"  ": 3, ENTER_KEY: 2}
CONTROL_BUTTONS = ["↑", "↓", "ABC", "#+=", "123", BACKSPACE_KEY, ENTER_KEY]

key_spacing_vertical = 20
key_spacing_horizontal = 15

class KeyButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setAttribute(Qt.WA_AcceptTouchEvents)
        self.setFocusPolicy(Qt.NoFocus)

    def event(self, event):
        if event.type() in (QEvent.TouchBegin, QEvent.TouchEnd):
            touch_event = event  # type: QTouchEvent
            if touch_event.touchPoints():
                mouse_type = QEvent.MouseButtonPress if event.type() == QEvent.TouchBegin else QEvent.MouseButtonRelease
                touch_point = touch_event.touchPoints()[0]
                mouse_event = QMouseEvent(mouse_type, touch_point.pos(), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
                QPushButton.event(self, mouse_event)
                event.accept()
                self.parentWidget().update()
                return True
        return super().event(event)

class KeyboardLayout(QWidget):
    def __init__(self, parent, layout):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        btn_group = QButtonGroup(self)
        btn_group.buttonClicked.connect(parent.handleButton)

        for idx, row in enumerate(layout):
            hlayout = QHBoxLayout()
            hlayout.setSpacing(0)

            if main_layout.count() == 1:
                hlayout.addSpacing(90)

            for key in row:
                btn = KeyButton(key)
                if key == BACKSPACE_KEY:
                    btn.setAutoRepeat(True)
                elif key == ENTER_KEY:
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #465BEA;
                        }
                        QPushButton:pressed {
                            background-color: #444444;
                        }
                    """)
                btn.setFixedHeight(135 + key_spacing_vertical)
                btn_group.addButton(btn)
                hlayout.addWidget(btn, KEY_STRETCH.get(key, 1))

            if main_layout.count() == 1:
                hlayout.addSpacing(90)

            main_layout.addLayout(hlayout)

        self.setStyleSheet(f"""
            QPushButton {{
                font-size: 75px;
                margin-left: {key_spacing_vertical / 2}px;
                margin-right: {key_spacing_vertical / 2}px;
                margin-top: {key_spacing_horizontal / 2}px;
                margin-bottom: {key_spacing_horizontal / 2}px;
                padding: 0px;
                border-radius: 10px;
                color: #dddddd;
                background-color: #444444;
            }}
            QPushButton:pressed {{
                background-color: #333333;
            }}
        """)

class Keyboard(QFrame):
    emitKey = pyqtSignal(str)
    emitBackspace = pyqtSignal()
    emitEnter = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QStackedLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # lowercase
        lowercase = [
            ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
            ["a", "s", "d", "f", "g", "h", "j", "k", "l"],
            ["↑", "z", "x", "c", "v", "b", "n", "m", BACKSPACE_KEY],
            ["123", "/", "-", "  ", ".", ENTER_KEY],
        ]
        self.main_layout.addWidget(KeyboardLayout(self, lowercase))

        # uppercase
        uppercase = [
            ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
            ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
            ["↓", "Z", "X", "C", "V", "B", "N", "M", BACKSPACE_KEY],
            ["123", "  ", ".", ENTER_KEY],
        ]
        self.main_layout.addWidget(KeyboardLayout(self, uppercase))

        # numbers + specials
        numbers = [
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
            ["-", "/", ":", ";", "(", ")", "$", "&&", "@", "\""],
            ["#+=", ".", ",", "?", "!", "`", BACKSPACE_KEY],
            ["ABC", "  ", ".", ENTER_KEY],
        ]
        self.main_layout.addWidget(KeyboardLayout(self, numbers))

        # extra specials
        specials = [
            ["[", "]", "{", "}", "#", "%", "^", "*", "+", "="],
            ["_", "\\", "|", "~", "<", ">", "€", "£", "¥", "•"],
            ["123", ".", ",", "?", "!", "'", BACKSPACE_KEY],
            ["ABC", "  ", ".", ENTER_KEY],
        ]
        self.main_layout.addWidget(KeyboardLayout(self, specials))

        self.main_layout.setCurrentIndex(0)

    def handleButton(self, btn):
        key = btn.text()
        if key in CONTROL_BUTTONS:
            if key == "↓" or key == "ABC":
                self.main_layout.setCurrentIndex(0)
            elif key == "↑":
                self.main_layout.setCurrentIndex(1)
            elif key == "123":
                self.main_layout.setCurrentIndex(2)
            elif key == "#+=":
                self.main_layout.setCurrentIndex(3)
            elif key == ENTER_KEY:
                self.main_layout.setCurrentIndex(0)
                self.emitEnter.emit()
            elif key == BACKSPACE_KEY:
                self.emitBackspace.emit()
        else:
            if "A" <= key <= "Z":
                self.main_layout.setCurrentIndex(0)
            self.emitKey.emit(key)