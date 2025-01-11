from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QScrollArea, QScroller, QScrollerProperties

class ScrollView(QScrollArea):
    def __init__(self, w=None, parent=None):
        super().__init__(parent)
        self.setWidget(w)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("background-color: transparent; border:none")

        style = """
        QScrollBar:vertical {
            border: none;
            background: transparent;
            width: 10px;
            margin: 0;
        }
        QScrollBar::handle:vertical {
            min-height: 0px;
            border-radius: 5px;
            background-color: white;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
        """
        self.verticalScrollBar().setStyleSheet(style)
        self.horizontalScrollBar().setStyleSheet(style)

        scroller = QScroller.scroller(self.viewport())
        sp = scroller.scrollerProperties()

        sp.setScrollMetric(QScrollerProperties.VerticalOvershootPolicy, QScrollerProperties.OvershootAlwaysOff)
        sp.setScrollMetric(QScrollerProperties.HorizontalOvershootPolicy, QScrollerProperties.OvershootAlwaysOff)
        sp.setScrollMetric(QScrollerProperties.MousePressEventDelay, 0.01)

        scroller.setScrollerProperties(sp)
        scroller.grabGesture(self.viewport(), QScroller.LeftMouseButtonGesture)

    def hideEvent(self, event):
        self.verticalScrollBar().setValue(0)
        super().hideEvent(event)
