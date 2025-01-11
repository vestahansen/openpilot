from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QEvent, pyqtSignal, QSize
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame,
                             QWidget, QButtonGroup, QScrollArea, QGridLayout)

from openpilot.selfdrive.ui.state import ASSET_PATH


class DialogBase(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        assert parent is not None
        parent.installEventFilter(self)

        self.setStyleSheet("""
            * {
              outline: none;
              color: white;
              font-family: Inter;
            }
            DialogBase {
              background-color: black;
            }
            QPushButton {
              height: 160px;
              font-size: 55px;
              font-weight: 400;
              border-radius: 10px;
              color: white;
              background-color: #333333;
            }
            QPushButton:pressed {
              background-color: #444444;
            }
        """)

    def eventFilter(self, obj, event):
        if obj == self.parent() and event.type() == QEvent.Hide:
            self.reject()
        return super().eventFilter(obj, event)

    def exec_(self):
        return super().exec_()


class Keyboard(QWidget):
    emitEnter = pyqtSignal()
    emitBackspace = pyqtSignal()
    emitKey = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout()
        keys = [
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M'],
            ['Space', 'Backspace', 'Enter']
        ]
        for row, key_row in enumerate(keys):
            for col, key in enumerate(key_row):
                btn = QPushButton(key)
                btn.setFixedSize(75, 75)
                if key == 'Backspace':
                    btn.clicked.connect(self.emitBackspace)
                elif key == 'Enter':
                    btn.clicked.connect(self.emitEnter)
                elif key == 'Space':
                    btn.clicked.connect(lambda ch, key=key: self.emitKey.emit(' '))
                else:
                    btn.clicked.connect(lambda ch, key=key: self.emitKey.emit(key))
                layout.addWidget(btn, row, col)
        self.setLayout(layout)


class InputDialog(DialogBase):
    cancel = pyqtSignal()
    emitText = pyqtSignal(str)

    def __init__(self, title, parent, subtitle="", secret=False):
        super().__init__(parent)
        self.minLength = -1

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(50, 55, 50, 50)
        self.main_layout.setSpacing(0)

        header_layout = QHBoxLayout()

        vlayout = QVBoxLayout()
        header_layout.addLayout(vlayout)
        self.label = QLabel(title, self)
        self.label.setStyleSheet("font-size: 90px; font-weight: bold;")
        vlayout.addWidget(self.label, alignment=Qt.AlignTop | Qt.AlignLeft)

        if subtitle:
            self.sublabel = QLabel(subtitle, self)
            self.sublabel.setStyleSheet("font-size: 55px; font-weight: light; color: #BDBDBD;")
            vlayout.addWidget(self.sublabel, alignment=Qt.AlignTop | Qt.AlignLeft)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(386, 125)
        cancel_btn.setStyleSheet("""
            QPushButton {
              font-size: 48px;
              border-radius: 10px;
              color: #E4E4E4;
              background-color: #333333;
            }
            QPushButton:pressed {
              background-color: #444444;
            }
        """)
        header_layout.addWidget(cancel_btn, alignment=Qt.AlignRight)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.clicked.connect(self.cancel)

        self.main_layout.addLayout(header_layout)

        self.main_layout.addStretch(2)

        textbox_widget = QWidget()
        textbox_widget.setObjectName("textbox")
        textbox_layout = QHBoxLayout(textbox_widget)
        textbox_layout.setContentsMargins(50, 0, 50, 0)

        textbox_widget.setStyleSheet("""
            #textbox {
              margin-left: 50px;
              margin-right: 50px;
              border-radius: 0;
              border-bottom: 3px solid #BDBDBD;
            }
            * {
              border: none;
              font-size: 80px;
              font-weight: light;
              background-color: transparent;
            }
        """)

        self.line = QLineEdit()
        if secret:
            self.line.setEchoMode(QLineEdit.Password)
        textbox_layout.addWidget(self.line, 1)

        if secret:
            self.eye_btn = QPushButton()
            self.eye_btn.setCheckable(True)
            self.eye_btn.setFixedSize(150, 120)
            self.eye_btn.toggled.connect(self.toggleEchoMode)
            self.eye_btn.setIcon(QIcon(ASSET_PATH / "img_eye_open.svg"))
            self.eye_btn.setIconSize(QSize(81, 44))
            textbox_layout.addWidget(self.eye_btn)

        self.main_layout.addWidget(textbox_widget, alignment=Qt.AlignBottom)
        self.main_layout.addSpacing(25)

        self.k = Keyboard(self)
        self.k.emitEnter.connect(self.handleEnter)
        self.k.emitBackspace.connect(self.line.backspace)
        self.k.emitKey.connect(lambda key: self.line.insert(key[0]))
        self.main_layout.addWidget(self.k, alignment=Qt.AlignBottom)

    def toggleEchoMode(self, checked):
        if checked:
            self.eye_btn.setIcon(QIcon(ASSET_PATH / "img_eye_closed.svg"))
            self.eye_btn.setIconSize(QSize(81, 54))
            self.line.setEchoMode(QLineEdit.Password)
        else:
            self.eye_btn.setIcon(QIcon(ASSET_PATH / "img_eye_open.svg"))
            self.eye_btn.setIconSize(QSize(81, 44))
            self.line.setEchoMode(QLineEdit.Normal)

    @staticmethod
    def getText(title, parent, subtitle="", secret=False, minLength=-1, defaultText=""):
        dialog = InputDialog(title, parent, subtitle, secret)
        dialog.line.setText(defaultText)
        dialog.setMinLength(minLength)
        result = dialog.exec_()
        return dialog.text() if result else ""

    def text(self):
        return self.line.text()

    def show(self):
        super().show()

    def handleEnter(self):
        if len(self.line.text()) >= self.minLength:
            self.accept()
            self.emitText.emit(self.line.text())
        else:
            self.setMessage(f"Need at least {self.minLength} character(s)!", False)

    def setMessage(self, message, clearInputField=True):
        self.label.setText(message)
        if clearInputField:
            self.line.setText("")

    def setMinLength(self, length):
        self.minLength = length


class ConfirmationDialog(DialogBase):
    def __init__(self, prompt_text, confirm_text, cancel_text, rich, parent):
        super().__init__(parent)
        container = QFrame(self)
        container.setStyleSheet("""
            QFrame { background-color: #1B1B1B; color: #C9C9C9; }
            #confirm_btn { background-color: #465BEA; }
            #confirm_btn:pressed { background-color: #3049F4; }
        """)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(32, 32 if rich else 120, 32, 32)

        prompt = QLabel(prompt_text, self)
        prompt.setWordWrap(True)
        prompt.setAlignment(Qt.AlignLeft if rich else Qt.AlignHCenter)
        font_style = "font-size: 42px; font-weight: light;" if rich else "font-size: 70px; font-weight: bold;"
        prompt.setStyleSheet(font_style + " margin: 45px;")
        if rich:
            scroll_view = QScrollArea(self)
            scroll_view.setWidgetResizable(True)
            scroll_view.setWidget(prompt)
            main_layout.addWidget(scroll_view, alignment=Qt.AlignTop)
        else:
            main_layout.addWidget(prompt, alignment=Qt.AlignTop)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(30)
        main_layout.addLayout(btn_layout)

        if cancel_text:
            cancel_btn = QPushButton(cancel_text)
            btn_layout.addWidget(cancel_btn)
            cancel_btn.clicked.connect(self.reject)

        if confirm_text:
            confirm_btn = QPushButton(confirm_text)
            confirm_btn.setObjectName("confirm_btn")
            btn_layout.addWidget(confirm_btn)
            confirm_btn.clicked.connect(self.accept)

        outer_layout = QVBoxLayout(self)
        margin = 100 if rich else 200
        outer_layout.setContentsMargins(margin, margin, margin, margin)
        outer_layout.addWidget(container)

    @staticmethod
    def alert(prompt_text, parent):
        dialog = ConfirmationDialog(prompt_text, "Ok", "", False, parent)
        return dialog.exec_()

    @staticmethod
    def confirm(prompt_text, confirm_text, parent):
        dialog = ConfirmationDialog(prompt_text, confirm_text, "Cancel", False, parent)
        return dialog.exec_()

    @staticmethod
    def rich(prompt_text, parent):
        dialog = ConfirmationDialog(prompt_text, "Ok", "", True, parent)
        return dialog.exec_()


class MultiOptionDialog(DialogBase):
    def __init__(self, prompt_text, option_list, current, parent):
        super().__init__(parent)
        self.selection = current

        container = QFrame(self)
        container.setStyleSheet("""
            QFrame { background-color: #1B1B1B; }
            #confirm_btn[enabled="false"] { background-color: #2B2B2B; }
            #confirm_btn:enabled { background-color: #465BEA; }
            #confirm_btn:enabled:pressed { background-color: #3049F4; }
        """)

        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(55, 50, 55, 50)

        title = QLabel(prompt_text, self)
        title.setStyleSheet("font-size: 70px; font-weight: 500;")
        main_layout.addWidget(title, alignment=Qt.AlignLeft | Qt.AlignTop)
        main_layout.addSpacing(25)

        listWidget = QWidget(self)
        listLayout = QVBoxLayout(listWidget)
        listLayout.setSpacing(20)
        listWidget.setStyleSheet("""
            QPushButton {
                height: 135px;
                padding: 0px 50px;
                text-align: left;
                font-size: 55px;
                font-weight: 300;
                border-radius: 10px;
                background-color: #4F4F4F;
            }
            QPushButton:checked { background-color: #465BEA; }
        """)

        group = QButtonGroup(listWidget)
        group.setExclusive(True)

        self.confirm_btn = QPushButton("Select")
        self.confirm_btn.setObjectName("confirm_btn")
        self.confirm_btn.setEnabled(False)

        for s in option_list:
            selectionLabel = QPushButton(s)
            selectionLabel.setCheckable(True)
            selectionLabel.setChecked(s == current)
            selectionLabel.toggled.connect(lambda checked, s=s: self.optionToggled(checked, s))
            group.addButton(selectionLabel)
            listLayout.addWidget(selectionLabel)
            if s == current:
                self.selection = s
                self.confirm_btn.setEnabled(False)

        listLayout.addStretch(1)

        scroll_view = QScrollArea(self)
        scroll_view.setWidgetResizable(True)
        scroll_view.setWidget(listWidget)
        scroll_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        main_layout.addWidget(scroll_view)
        main_layout.addSpacing(35)

        blayout = QHBoxLayout()
        main_layout.addLayout(blayout)
        blayout.setSpacing(50)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        self.confirm_btn.clicked.connect(self.accept)
        blayout.addWidget(cancel_btn)
        blayout.addWidget(self.confirm_btn)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(50, 50, 50, 50)
        outer_layout.addWidget(container)

    def optionToggled(self, checked, s):
        if checked:
            self.selection = s
            self.confirm_btn.setEnabled(self.selection != self.selection)

    @staticmethod
    def getSelection(prompt_text, option_list, current, parent):
        dialog = MultiOptionDialog(prompt_text, option_list, current, parent)
        if dialog.exec_():
            return dialog.selection
        return ""
