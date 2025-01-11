from PyQt5.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QSizePolicy, QButtonGroup, QStyleOption
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtCore import Qt, pyqtSignal

from openpilot.common.params import Params
from openpilot.selfdrive.ui.qt.widgets.input import ConfirmationDialog
from openpilot.selfdrive.ui.qt.widgets.toggle import Toggle


class ElidedLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, text='', parent=None):
        super().__init__(text.strip(), parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMinimumWidth(1)
        self.lastText_ = ''
        self.elidedText_ = ''

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.lastText_ = ''
        self.elidedText_ = ''

    def paintEvent(self, event):
        curText = self.text()
        if curText != self.lastText_:
            self.elidedText_ = self.fontMetrics().elidedText(curText, Qt.ElideRight, self.contentsRect().width())
            self.lastText_ = curText

        painter = QPainter(self)
        self.drawFrame(painter)
        opt = QStyleOption()
        opt.initFrom(self)
        self.style().drawItemText(painter, self.contentsRect(), self.alignment(), opt.palette,
                                  self.isEnabled(), self.elidedText_, self.foregroundRole())

    def mouseReleaseEvent(self, event):
        if self.rect().contains(event.pos()):
            self.clicked.emit()


class AbstractControl(QFrame):
    showDescriptionEvent = pyqtSignal()

    def __init__(self, title, desc='', icon='', parent=None):
        super().__init__(parent)
        self.params = Params()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.hlayout = QHBoxLayout()
        self.hlayout.setContentsMargins(0, 0, 0, 0)
        self.hlayout.setSpacing(20)

        # left icon
        self.icon_label = QLabel(self)
        self.hlayout.addWidget(self.icon_label)
        if icon:
            self.icon_pixmap = QPixmap(icon).scaledToWidth(80, Qt.SmoothTransformation)
            self.icon_label.setPixmap(self.icon_pixmap)
            self.icon_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.icon_label.setVisible(bool(icon))

        # title
        self.title_label = QPushButton(title)
        self.title_label.setFixedHeight(120)
        self.title_label.setStyleSheet("font-size: 50px; font-weight: 400; text-align: left; border: none;")
        self.hlayout.addWidget(self.title_label, 1)

        # value next to control button
        self.value = ElidedLabel()
        self.value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.value.setStyleSheet("color: #aaaaaa")
        self.hlayout.addWidget(self.value)

        main_layout.addLayout(self.hlayout)

        # description
        self.description = QLabel(desc)
        self.description.setContentsMargins(40, 20, 40, 20)
        self.description.setStyleSheet("font-size: 40px; color: grey")
        self.description.setWordWrap(True)
        self.description.setVisible(False)
        main_layout.addWidget(self.description)

        self.title_label.clicked.connect(self.toggleDescription)
        main_layout.addStretch()

    def toggleDescription(self):
        if not self.description.isVisible():
            self.showDescriptionEvent.emit()
        if self.description.text():
            self.description.setVisible(not self.description.isVisible())

    def hideEvent(self, event):
        if self.description is not None:
            self.description.hide()

    def setDescription(self, desc):
        if self.description:
            self.description.setText(desc)

    def setTitle(self, title):
        self.title_label.setText(title)

    def setValue(self, val):
        self.value.setText(val)

    def getDescription(self):
        return self.description.text()


class ButtonControl(AbstractControl):
    clicked = pyqtSignal()

    def __init__(self, title, text, desc='', parent=None):
        super().__init__(title, desc, '', parent)
        self.btn = QPushButton(text)
        self.btn.setStyleSheet("""
        QPushButton {
            padding: 0;
            border-radius: 50px;
            font-size: 35px;
            font-weight: 500;
            color: #E4E4E4;
            background-color: #393939;
        }
        QPushButton:pressed {
            background-color: #4a4a4a;
        }
        QPushButton:disabled {
            color: #33E4E4E4;
        }
        """)
        self.btn.setFixedSize(250, 100)
        self.btn.clicked.connect(self.clicked.emit)
        self.hlayout.addWidget(self.btn)

    def setText(self, text):
        self.btn.setText(text)

    def text(self):
        return self.btn.text()

    def setEnabled(self, enabled):
        self.btn.setEnabled(enabled)


class ToggleControl(AbstractControl):
    toggleFlipped = pyqtSignal(bool)

    def __init__(self, title, desc='', icon='', state=False, parent=None):
        super().__init__(title, desc, icon, parent)
        self.toggle = Toggle(self)
        self.toggle.setFixedSize(150, 100)
        if state:
            self.toggle.togglePosition()
        self.hlayout.addWidget(self.toggle)
        self.toggle.stateChanged.connect(self.toggleFlipped.emit)

    def setEnabled(self, enabled):
        self.toggle.setEnabled(enabled)
        self.toggle.update()


class ParamControl(ToggleControl):
    def __init__(self, param, title, desc, icon, parent=None):
        super().__init__(title, desc, icon, False, parent)
        self.key = param
        self.confirm = False
        self.store_confirm = False
        self.active_icon_pixmap = None
        self.params = Params()
        self.toggleFlipped.connect(self.toggleClicked)

    def toggleClicked(self, state):
        def do_confirm():
            content = "<body><h2 style=\"text-align: center;\">" + self.title_label.text() + "</h2><br>" \
                      "<p style=\"text-align: center; margin: 0 128px; font-size: 50px;\">" + self.getDescription() + "</p></body>"
            return ConfirmationDialog(content, "Enable", "Cancel", True, self).exec()

        confirmed = self.store_confirm and self.params.get_bool(self.key + "Confirmed")
        if not self.confirm or confirmed or not state or do_confirm():
            if self.store_confirm and state:
                self.params.put_bool(self.key + "Confirmed", True)
            self.params.put_bool(self.key, state)
            self.setIcon(state)
        else:
            self.toggle.togglePosition()

    def setConfirmation(self, confirm, store_confirm):
        self.confirm = confirm
        self.store_confirm = store_confirm

    def setActiveIcon(self, icon):
        self.active_icon_pixmap = QPixmap(icon).scaledToWidth(80, Qt.SmoothTransformation)

    def refresh(self):
        state = self.params.get_bool(self.key)
        if state != self.toggle.on:
            self.toggle.togglePosition()
            self.setIcon(state)

    def showEvent(self, event):
        self.refresh()

    def setIcon(self, state):
        if state and self.active_icon_pixmap:
            self.icon_label.setPixmap(self.active_icon_pixmap)
        elif hasattr(self, 'icon_pixmap') and self.icon_pixmap:
            self.icon_label.setPixmap(self.icon_pixmap)


class ButtonParamControl(AbstractControl):
    def __init__(self, param, title, desc, icon, button_texts, minimum_button_width=225):
        super().__init__(title, desc, icon)
        self.params = Params()
        self.key = param
        style = """
        QPushButton {
            border-radius: 50px;
            font-size: 40px;
            font-weight: 500;
            height:100px;
            padding: 0 25 0 25;
            color: #E4E4E4;
            background-color: #393939;
        }
        QPushButton:pressed {
            background-color: #4a4a4a;
        }
        QPushButton:checked:enabled {
            background-color: #33Ab4C;
        }
        QPushButton:disabled {
            color: #33E4E4E4;
        }
        """
        value = int(self.params.get(self.key))
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        for i, text in enumerate(button_texts):
            button = QPushButton(text, self)
            button.setCheckable(True)
            button.setChecked(i == value)
            button.setStyleSheet(style)
            button.setMinimumWidth(minimum_button_width)
            self.hlayout.addWidget(button)
            self.button_group.addButton(button, i)

        self.button_group.buttonClicked[int].connect(self.buttonClicked)

    def buttonClicked(self, id):
        self.params.put(self.key, str(id))

    def setEnabled(self, enable):
        for btn in self.button_group.buttons():
            btn.setEnabled(enable)

    def setCheckedButton(self, id):
        self.button_group.button(id).setChecked(True)

    def refresh(self):
        value = int(self.params.get(self.key))
        self.button_group.button(value).setChecked(True)

    def showEvent(self, event):
        self.refresh()
