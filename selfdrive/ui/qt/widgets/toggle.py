from PyQt5.QtWidgets import QAbstractButton
from PyQt5.QtCore import Qt, QPropertyAnimation, pyqtProperty, pyqtSignal, QRect, QRectF
from PyQt5.QtGui import QPainter, QColor

class Toggle(QAbstractButton):
    stateChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._height = 80
        self._height_rect = 60
        self.on = False
        self.animation_duration = 150
        self.immediateOffset = 0
        self.enabled = True

        self._radius = self._height // 2
        self._offset_circle = self._radius
        self._y_circle = self._radius
        self._y_rect = (self._height - self._height_rect) // 2

        self.circleColor = QColor(0xffffff)  # placeholder
        self.green = QColor(0xffffff)        # placeholder

        self._anim = QPropertyAnimation(self, b"offset_circle")

        self.setEnabled(True)
        self.setFixedHeight(self._height)

    def get_offset_circle(self):
        return self._offset_circle

    def set_offset_circle(self, o):
        self._offset_circle = o
        self.update()

    offset_circle = pyqtProperty(int, fget=get_offset_circle, fset=set_offset_circle)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Draw toggle background left
        painter.setBrush(self.green)
        left_rect = QRect(0, self._y_rect, self.offset_circle + self._radius, self._height_rect)
        painter.drawRoundedRect(left_rect, self._height_rect // 2, self._height_rect // 2)

        # Draw toggle background right
        painter.setBrush(QColor(0x393939))
        right_rect = QRect(self.offset_circle - self._radius, self._y_rect, self.width() - (self.offset_circle - self._radius), self._height_rect)
        painter.drawRoundedRect(right_rect, self._height_rect // 2, self._height_rect // 2)

        # Draw toggle circle
        painter.setBrush(self.circleColor)
        circle_rect = QRectF(self.offset_circle - self._radius, self._y_circle - self._radius, 2 * self._radius, 2 * self._radius)
        painter.drawEllipse(circle_rect)

    def mouseReleaseEvent(self, event):
        if not self.enabled:
            return
        left = self._radius
        right = self.width() - self._radius
        if ((self.offset_circle != left and self.offset_circle != right) or not self.rect().contains(event.pos())):
            return
        if event.button() & Qt.LeftButton:
            self.togglePosition()
            self.stateChanged.emit(self.on)

    def togglePosition(self):
        self.on = not self.on
        left = self._radius
        right = self.width() - self._radius
        start_value = left + self.immediateOffset if self.on else right - self.immediateOffset
        end_value = right if self.on else left
        self._anim.setStartValue(start_value)
        self._anim.setEndValue(end_value)
        self._anim.setDuration(self.animation_duration)
        self._anim.start()
        self.repaint()

    def getEnabled(self):
        return self.enabled

    def setEnabled(self, value):
        self.enabled = value
        if value:
            self.circleColor.setRgb(0xfafafa)
            self.green.setRgb(0x33ab4c)
        else:
            self.circleColor.setRgb(0x888888)
            self.green.setRgb(0x227722)