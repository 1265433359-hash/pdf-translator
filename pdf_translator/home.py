"""Landing/home page: an 打开 card + a 最近 list (like a document launcher)."""
import os
import time
from datetime import datetime

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QFrame, QPushButton, QScrollArea, QSizePolicy,
                               QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor


def format_ts(ts):
    """'今天 16:20' for today, else 'M月D日' (falls back to '' when unknown)."""
    if not ts:
        return ""
    try:
        dt = datetime.fromtimestamp(float(ts))
    except (ValueError, OSError, OverflowError):
        return ""
    today = datetime.fromtimestamp(time.time()).date()
    if dt.date() == today:
        return f"今天 {dt.strftime('%H:%M')}"
    return f"{dt.month}月{dt.day}日"


class _ClickFrame(QFrame):
    clicked = Signal()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(e)


class HomeWidget(QWidget):
    open_requested = Signal()
    open_path_requested = Signal(str)
    clear_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("homePage")
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        center = QWidget()
        center.setMaximumWidth(820)
        col = QVBoxLayout(center)
        col.setContentsMargins(40, 32, 40, 32)
        col.setSpacing(20)

        # 打开 card
        open_card = _ClickFrame()
        open_card.setObjectName("openCard")
        open_card.setCursor(Qt.CursorShape.PointingHandCursor)
        oc = QHBoxLayout(open_card)
        oc.setContentsMargins(24, 20, 24, 20)
        title = QLabel("📂  打开")
        title.setObjectName("openTitle")
        oc.addWidget(title)
        oc.addStretch()
        open_card.clicked.connect(self.open_requested.emit)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28); shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 38))
        open_card.setGraphicsEffect(shadow)
        col.addWidget(open_card)

        # 最近 header
        head = QHBoxLayout()
        recent_label = QLabel("最近")
        recent_label.setObjectName("recentTitle")
        head.addWidget(recent_label)
        head.addStretch()
        clear_btn = QPushButton("🧹")
        clear_btn.setToolTip("清空最近记录")
        clear_btn.setFixedWidth(40)
        clear_btn.clicked.connect(self.clear_requested.emit)
        head.addWidget(clear_btn)
        col.addLayout(head)

        # recent list (scrollable)
        self._list_host = QWidget()
        self._list_lay = QVBoxLayout(self._list_host)
        self._list_lay.setContentsMargins(0, 0, 0, 0)
        self._list_lay.setSpacing(6)
        self._list_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(self._list_host)
        col.addWidget(scroll, 1)

        outer.addStretch()
        outer.addWidget(center, 3)
        outer.addStretch()
        # visual styling comes from the active theme QSS (#openCard, #recentRow, ...)

    def set_recents(self, items):
        # clear
        while self._list_lay.count():
            w = self._list_lay.takeAt(0).widget()
            if w:
                w.deleteLater()
        if not items:
            empty = QLabel("（暂无最近文件，点上方「打开」选择 PDF）")
            empty.setStyleSheet("color: gray; padding: 12px;")
            self._list_lay.addWidget(empty)
            return
        for it in items:
            path = it["path"]
            row = _ClickFrame()
            row.setObjectName("recentRow")
            row.setCursor(Qt.CursorShape.PointingHandCursor)
            rl = QHBoxLayout(row)
            rl.setContentsMargins(12, 10, 12, 10)
            icon = QLabel("📄")
            name = QLabel(os.path.splitext(os.path.basename(path))[0])
            name.setObjectName("recentName")
            name.setToolTip(path)
            name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            date = QLabel(format_ts(it.get("ts")))
            date.setObjectName("recentDate")
            rl.addWidget(icon)
            rl.addWidget(name, 1)
            rl.addWidget(date)
            row.clicked.connect(lambda p=path: self.open_path_requested.emit(p))
            self._list_lay.addWidget(row)
