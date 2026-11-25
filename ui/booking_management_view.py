import os
import re
import json
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QScrollArea, QDialog,
    QDateEdit, QTextEdit, QSpinBox, QButtonGroup,
    QStackedWidget, QCompleter, QCalendarWidget
)
from PySide6.QtCore import Qt, QDate, Signal, QStringListModel, QPoint
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QPixmap, QPainterPath, QTextDocument
from ui.theme import Colors
from ui.customer_view import CustomAlertDialog
from core.db_manager import DBManager


def format_korean_phone(raw_text: str) -> str:
    """숫자만 추출하여 한국 전화번호 형식(010-1234-5678 등)으로 자동 하이픈 포맷팅"""
    digits = re.sub(r"\D", "", raw_text or "")[:11]
    if not digits:
        return ""
    if digits.startswith("02"):
        if len(digits) <= 2:
            return digits
        elif len(digits) <= 5:
            return f"{digits[:2]}-{digits[2:]}"
        elif len(digits) <= 9:
            return f"{digits[:2]}-{digits[2:5]}-{digits[5:]}"
        else:
            return f"{digits[:2]}-{digits[2:6]}-{digits[6:10]}"
    else:
        if len(digits) <= 3:
            return digits
        elif len(digits) <= 7:
            return f"{digits[:3]}-{digits[3:]}"
        elif len(digits) <= 10:
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        else:
            return f"{digits[:3]}-{digits[3:7]}-{digits[7:11]}"


def format_designer_label(name: str, position: str = "") -> str:
    """디자이너 표기 통일: '이름 (직급)'"""
    name_str = (name or "").strip()
    pos_str = (position or "").strip()
    return f"{name_str} ({pos_str})" if pos_str else name_str


def get_resource_arrow_path(direction: str = "down") -> str:
    """프로젝트 루트의 resources 폴더에 화살표 PNG를 생성하고 절대 경로 반환"""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    res_dir = os.path.join(project_root, "resources")
    os.makedirs(res_dir, exist_ok=True)

    file_path = os.path.join(res_dir, f"arrow_{direction}.png")
    if not os.path.exists(file_path):
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor("#444444"), 2)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)

        if direction == "down":
            painter.drawLine(5, 9, 12, 16)
            painter.drawLine(12, 16, 19, 9)
        elif direction == "up":
            painter.drawLine(5, 15, 12, 8)
            painter.drawLine(12, 8, 19, 15)

        painter.end()
        pixmap.save(file_path, "PNG")

    return file_path.replace("\\", "/")


STATUS_STYLES = {
    "예약완료": {
        "card_bg": "#EBF5FF",
        "card_border": "#93C5FD",
        "badge_bg": "#DBEAFE",
        "badge_fg": "#1D4ED8",
    },
    "방문완료": {
        "card_bg": "#ECFDF5",
        "card_border": "#6EE7B7",
        "badge_bg": "#D1FAE5",
        "badge_fg": "#047857",
    },
    "취소": {
        "card_bg": "#FEF2F2",
        "card_border": "#FCA5A5",
        "badge_bg": "#FEE2E2",
        "badge_fg": "#B91C1C",
    },
    "노쇼": {
        "card_bg": "#F1F5F9",
        "card_border": "#CBD5E1",
        "badge_bg": "#E2E8F0",
        "badge_fg": "#475569",
    },
}

SCROLLBAR_STYLE = """
    QScrollBar:vertical {
        border: none;
        background: #EAEAEA;
        width: 10px;
        margin: 0px;
        border-radius: 5px;
    }
    QScrollBar::handle:vertical {
        background: #B0B0B0;
        min-height: 25px;
        border-radius: 5px;
    }
    QScrollBar::handle:vertical:hover {
        background: #888888;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        background: none;
        height: 0px;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }
"""


class RoundedTableHeader(QHeaderView):
    """상단 양쪽 모서리만 라운드가 적용되고 하단은 일직선인 테이블 헤더 뷰"""

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setDefaultAlignment(Qt.AlignCenter)

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()

        r = 6.0
        x, y, w, h = float(rect.x()), float(rect.y()), float(rect.width()), float(rect.height())
        count = self.count()

        path = QPainterPath()
        if count == 1:
            path.moveTo(x + r, y)
            path.lineTo(x + w - r, y)
            path.quadTo(x + w, y, x + w, y + r)
            path.lineTo(x + w, y + h)
            path.lineTo(x, y + h)
            path.lineTo(x, y + r)
            path.quadTo(x, y, x + r, y)
        elif logicalIndex == 0:
            path.moveTo(x + r, y)
            path.lineTo(x + w, y)
            path.lineTo(x + w, y + h)
            path.lineTo(x, y + h)
            path.lineTo(x, y + r)
            path.quadTo(x, y, x + r, y)
        elif logicalIndex == count - 1:
            path.moveTo(x, y)
            path.lineTo(x + w - r, y)
            path.quadTo(x + w, y, x + w, y + r)
            path.lineTo(x + w, y + h)
            path.lineTo(x, y + h)
            path.closeSubpath()
        else:
            path.addRect(rect)

        painter.fillPath(path, QColor(Colors.PRIMARY))

        text = self.model().headerData(logicalIndex, self.orientation(), Qt.DisplayRole)
        if text:
            doc = QTextDocument()
            doc.setHtml(
                f"<div style='color: #FFFFFF; font-weight: bold; font-size: 13px; text-align: center;'>{text}</div>"
            )
            doc.setTextWidth(rect.width())
            y_offset = (rect.height() - doc.size().height()) / 2
            painter.translate(rect.x(), rect.y() + y_offset)
            doc.drawContents(painter)

        painter.restore()


def get_unified_combo_style() -> str:
    arrow_down = get_resource_arrow_path("down")
    return f"""
        QComboBox {{
            border: 1.5px solid #C0C0C0;
            border-radius: 6px;
            background-color: #FAFAFA;
            color: #000000;
            padding-left: 10px;
            padding-right: 26px;
            font-size: 12px;
        }}
        QComboBox:focus {{
            border: 1.5px solid {Colors.PRIMARY};
            background-color: #FFFFFF;
        }}
        QComboBox::drop-down {{
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 24px;
            border: none;
            background: transparent;
        }}
        QComboBox::down-arrow {{
            image: url("{arrow_down}");
            width: 11px;
            height: 11px;
        }}
        QComboBox QAbstractItemView {{
            background-color: #FFFFFF;
            color: #000000;
            border: 1px solid #B0B0B0;
            selection-background-color: #E8F5E9;
            selection-color: #000000;
        }}
    """


def get_calendar_widget_style() -> str:
    return f"""
        QCalendarWidget {{
            background-color: #FFFFFF;
            border: none;
            border-radius: 6px;
        }}
        QCalendarWidget QWidget#qt_calendar_navigationbar {{
            background-color: {Colors.PRIMARY};
            min-height: 40px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 0px;
        }}
        QCalendarWidget QToolButton {{
            color: #FFFFFF;
            font-size: 13px;
            font-weight: bold;
            background-color: transparent;
            border: none;
            margin: 2px;
            padding: 4px 6px;
        }}
        QCalendarWidget QToolButton#qt_calendar_monthbutton,
        QCalendarWidget QToolButton#qt_calendar_yearbutton {{
            padding-right: 18px;
        }}
        QCalendarWidget QToolButton#qt_calendar_monthbutton::menu-indicator,
        QCalendarWidget QToolButton#qt_calendar_yearbutton::menu-indicator {{
            subcontrol-origin: padding;
            subcontrol-position: center right;
            right: 4px;
            top: 0px;
        }}
        QCalendarWidget QToolButton:hover {{
            background-color: {Colors.PRIMARY_HOVER};
            border-radius: 4px;
        }}
        QCalendarWidget QMenu {{
            background-color: #FFFFFF;
            color: #000000;
            font-size: 12px;
            border: 1px solid #B0B0B0;
        }}
        QCalendarWidget QMenu::item {{
            padding: 6px 20px;
            color: #000000;
        }}
        QCalendarWidget QMenu::item:selected {{
            background-color: #555555;
            color: #FFFFFF;
            font-weight: bold;
        }}
        QCalendarWidget QSpinBox {{
            color: #FFFFFF;
            background-color: transparent;
            font-weight: bold;
            font-size: 13px;
            selection-background-color: {Colors.PRIMARY_HOVER};
            selection-color: #FFFFFF;
        }}
        QCalendarWidget QAbstractItemView:enabled {{
            color: #000000;
            background-color: #FFFFFF;
            selection-background-color: #4B5563;
            selection-color: #FFFFFF;
            font-size: 12px;
            font-weight: bold;
            outline: none;
        }}
        QCalendarWidget QAbstractItemView::item:selected {{
            background-color: #4B5563;
            color: #FFFFFF;
            border-radius: 4px;
        }}
        QCalendarWidget QAbstractItemView::item:hover {{
            background-color: #E5E7EB;
            color: #111827;
        }}
        QCalendarWidget QWidget#qt_calendar_calendarview {{
            background-color: #FFFFFF;
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: 6px;
            border-bottom-right-radius: 6px;
        }}
    """


def get_unified_date_style() -> str:
    arrow_down = get_resource_arrow_path("down")
    return f"""
        QDateEdit {{
            border: 1.5px solid #C0C0C0;
            border-radius: 6px;
            background-color: #FAFAFA;
            color: #000000;
            padding-left: 8px;
            padding-right: 24px;
            font-size: 12px;
        }}
        QDateEdit:focus {{
            border: 1.5px solid {Colors.PRIMARY};
            background-color: #FFFFFF;
        }}
        QDateEdit::drop-down {{
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 24px;
            border: none;
            background: transparent;
        }}
        QDateEdit::down-arrow {{
            image: url("{arrow_down}");
            width: 10px;
            height: 10px;
        }}
        {get_calendar_widget_style()}
    """


def get_unified_spin_style() -> str:
    arrow_up = get_resource_arrow_path("up")
    arrow_down = get_resource_arrow_path("down")
    return f"""
        QSpinBox {{
            border: 1.5px solid #C0C0C0;
            border-radius: 6px;
            background-color: #FAFAFA;
            color: #000000;
            padding-left: 6px;
            padding-right: 20px;
            font-size: 12px;
        }}
        QSpinBox:focus {{
            border: 1.5px solid {Colors.PRIMARY};
            background-color: #FFFFFF;
        }}
        QSpinBox::up-button {{
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 20px;
            height: 17px;
            border: none;
            background: transparent;
        }}
        QSpinBox::up-arrow {{
            image: url("{arrow_up}");
            width: 10px;
            height: 10px;
        }}
        QSpinBox::down-button {{
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 20px;
            height: 17px;
            border: none;
            background: transparent;
        }}
        QSpinBox::down-arrow {{
            image: url("{arrow_down}");
            width: 10px;
            height: 10px;
        }}
    """


class DatePickerPopup(QDialog):
    """상단 날짜 버튼 클릭 시 원하는 날짜로 즉시 이동할 수 있는 미니 달력 팝업"""
    date_selected = Signal(QDate)

    def __init__(self, current_date: QDate, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(316, 282)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        frame = QFrame(self)
        frame.setObjectName("CalPopupFrame")
        frame.setStyleSheet("""
            QFrame#CalPopupFrame {
                background-color: #FFFFFF;
                border: 1.5px solid #94A3B8;
                border-radius: 8px;
            }
        """)
        f_layout = QVBoxLayout(frame)
        f_layout.setContentsMargins(0, 0, 0, 0)
        f_layout.setSpacing(0)

        self.calendar = QCalendarWidget(frame)
        self.calendar.setSelectedDate(current_date)
        self.calendar.setNavigationBarVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.setStyleSheet(get_calendar_widget_style())
        self.calendar.clicked.connect(self._on_clicked)

        f_layout.addWidget(self.calendar)
        layout.addWidget(frame)

    def _on_clicked(self, qdate: QDate):
        self.date_selected.emit(qdate)
        self.accept()


class ConfirmActionDialog(QDialog):
    """예약 중복/삭제 확인용 커스텀 모달"""

    def __init__(self, title: str, message: str, confirm_text: str = "확인",
                 danger: bool = False, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(410, 230)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)

        box = QFrame(self)
        box.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1.5px solid #C0C0C0;
            }
        """)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(14)

        lbl_title = QLabel(title, box)
        lbl_title.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("border: none; color: #0F172A;")
        layout.addWidget(lbl_title)

        lbl_msg = QLabel(message, box)
        lbl_msg.setFont(QFont("Inter", 11))
        lbl_msg.setWordWrap(True)
        lbl_msg.setAlignment(Qt.AlignCenter)
        lbl_msg.setStyleSheet("border: none; color: #334155;")
        layout.addWidget(lbl_msg, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_cancel = QPushButton("취소", box)
        btn_cancel.setFixedHeight(38)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                color: #334155;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
            }
        """)
        btn_cancel.clicked.connect(self.reject)

        confirm_bg = "#DC2626" if danger else Colors.PRIMARY
        confirm_hover = "#B91C1C" if danger else Colors.PRIMARY_HOVER
        btn_ok = QPushButton(confirm_text, box)
        btn_ok.setFixedHeight(38)
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background-color: {confirm_bg};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {confirm_hover};
            }}
        """)
        btn_ok.clicked.connect(self.accept)

        btn_row.addWidget(btn_cancel, 1)
        btn_row.addWidget(btn_ok, 1)
        layout.addLayout(btn_row)

        outer.addWidget(box)


class ReservationFormDialog(QDialog):
    """예약 등록 및 수정 모달 다이얼로그 (상단 바 드래그 이동 지원)"""

    def __init__(self, db_manager: DBManager, designers: list, services: list,
                 customers: list, reservation: dict = None,
                 default_date: QDate = None, default_time: str = "10:00",
                 default_user_id: int = None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.designers = designers
        self.services = services
        self.customers = customers
        self.reservation = reservation
        self.is_edit = reservation is not None

        self.selected_customer_id = None
        self.is_guest_mode = False
        self.selected_service_items = []
        self._drag_offset = None

        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setModal(True)
        self.setFixedSize(500, 715)

        self._setup_ui(default_date, default_time, default_user_id)
        if self.is_edit:
            self._populate_edit_data()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.position().y() <= 54:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and (event.buttons() & Qt.LeftButton):
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def _setup_ui(self, default_date: QDate, default_time: str, default_user_id: int):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)

        container = QFrame(self)
        container.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 14px;
                border: 1.5px solid #CBD5E1;
            }
        """)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 18, 24, 20)
        layout.setSpacing(10)

        # 드래그 가능한 상단 헤더 바
        header_bar = QFrame(container)
        header_bar.setFixedHeight(36)
        header_bar.setCursor(Qt.OpenHandCursor)
        header_bar.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }
        """)
        header_row = QHBoxLayout(header_bar)
        header_row.setContentsMargins(12, 0, 8, 0)

        title_text = "예약 상세 / 수정" if self.is_edit else "예약 등록"
        lbl_title = QLabel(title_text, header_bar)
        lbl_title.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #0F172A; border: none; background: transparent;")

        lbl_drag_hint = QLabel("⠿ 드래그 이동", header_bar)
        lbl_drag_hint.setFont(QFont("Inter", 9))
        lbl_drag_hint.setStyleSheet("color: #94A3B8; border: none; background: transparent;")

        btn_close = QPushButton("✕", header_bar)
        btn_close.setFixedSize(26, 26)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #64748B;
                border: none;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #0F172A;
            }
        """)
        btn_close.clicked.connect(self.reject)

        header_row.addWidget(lbl_title)
        header_row.addSpacing(8)
        header_row.addWidget(lbl_drag_hint)
        header_row.addStretch()
        header_row.addWidget(btn_close)
        layout.addWidget(header_bar)

        # 1. 고객 정보
        cust_label_row = QHBoxLayout()
        lbl_cust = self._section_label("고객 정보", container)
        self.btn_toggle_guest = QPushButton("+ 미등록 고객 입력", container)
        self.btn_toggle_guest.setCheckable(True)
        self.btn_toggle_guest.setFixedHeight(28)
        self.btn_toggle_guest.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_guest.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: {Colors.PRIMARY};
                border: 1.5px solid {Colors.PRIMARY};
                border-radius: 6px;
                padding: 0 10px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:checked {{
                background-color: {Colors.PRIMARY};
                color: #FFFFFF;
            }}
        """)
        self.btn_toggle_guest.toggled.connect(self._on_toggle_guest_mode)

        cust_label_row.addWidget(lbl_cust)
        cust_label_row.addStretch()
        cust_label_row.addWidget(self.btn_toggle_guest)
        layout.addLayout(cust_label_row)

        # 기존 고객 검색 영역
        self.existing_cust_box = QWidget(container)
        self.existing_cust_box.setStyleSheet("border: none; background: transparent;")
        ec_layout = QVBoxLayout(self.existing_cust_box)
        ec_layout.setContentsMargins(0, 2, 0, 2)
        ec_layout.setSpacing(6)

        self.input_customer_search = QLineEdit(self.existing_cust_box)
        self.input_customer_search.setPlaceholderText("등록 고객 이름 또는 전화번호 검색 후 Enter...")
        self.input_customer_search.setFixedHeight(38)
        self.input_customer_search.setStyleSheet(self._input_style())

        self._customer_map = {}
        display_items = []
        for c in self.customers:
            label = f"{c['name']} ({c['phone']})"
            self._customer_map[label] = c
            display_items.append(label)

        self.customer_completer = QCompleter(self)
        self.customer_completer.setModel(QStringListModel(display_items, self.customer_completer))
        self.customer_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.customer_completer.setFilterMode(Qt.MatchContains)
        self.customer_completer.activated.connect(self._on_customer_selected)
        self.input_customer_search.setCompleter(self.customer_completer)
        self.input_customer_search.textChanged.connect(self._on_customer_text_changed)
        self.input_customer_search.returnPressed.connect(self._on_customer_search_enter)

        self.lbl_selected_cust_info = QLabel("등록 고객을 선택하거나 우측 버튼으로 미등록 고객을 입력하세요.", self.existing_cust_box)
        self.lbl_selected_cust_info.setFont(QFont("Inter", 9))
        self.lbl_selected_cust_info.setStyleSheet("color: #64748B; border: none;")

        ec_layout.addWidget(self.input_customer_search)
        ec_layout.addWidget(self.lbl_selected_cust_info)
        layout.addWidget(self.existing_cust_box)

        # 미등록 고객 직접 입력 영역
        self.guest_cust_box = QWidget(container)
        self.guest_cust_box.setVisible(False)
        self.guest_cust_box.setStyleSheet("border: none; background: transparent;")
        gc_layout = QHBoxLayout(self.guest_cust_box)
        gc_layout.setContentsMargins(0, 2, 0, 2)
        gc_layout.setSpacing(8)

        self.input_guest_name = QLineEdit(self.guest_cust_box)
        self.input_guest_name.setPlaceholderText("고객명 (예: 김민지)")
        self.input_guest_name.setFixedHeight(38)
        self.input_guest_name.setStyleSheet(self._input_style())
        self.input_guest_name.returnPressed.connect(lambda: self.input_guest_phone.setFocus())

        self.input_guest_phone = QLineEdit(self.guest_cust_box)
        self.input_guest_phone.setPlaceholderText("연락처 (010-0000-0000)")
        self.input_guest_phone.setFixedHeight(38)
        self.input_guest_phone.setStyleSheet(self._input_style())
        self.input_guest_phone.textChanged.connect(self._on_guest_phone_changed)
        self.input_guest_phone.returnPressed.connect(lambda: self.combo_designer.setFocus())

        gc_layout.addWidget(self.input_guest_name, 1)
        gc_layout.addWidget(self.input_guest_phone, 1)
        layout.addWidget(self.guest_cust_box)

        # 2. 담당 디자이너 ('이름 (직급)' 형식)
        layout.addWidget(self._section_label("담당 디자이너", container))
        self.combo_designer = QComboBox(container)
        self.combo_designer.setFixedHeight(38)
        self.combo_designer.setStyleSheet(get_unified_combo_style())
        for d in self.designers:
            label = format_designer_label(d.get("name", ""), d.get("position", ""))
            self.combo_designer.addItem(label, d["id"])
        if default_user_id:
            idx = self.combo_designer.findData(default_user_id)
            if idx >= 0:
                self.combo_designer.setCurrentIndex(idx)
        layout.addWidget(self.combo_designer)

        # 3. 예정 시술 선택
        layout.addWidget(self._section_label("예정 시술", container))
        svc_row = QHBoxLayout()
        svc_row.setSpacing(8)
        self.combo_service = QComboBox(container)
        self.combo_service.setFixedHeight(38)
        self.combo_service.setStyleSheet(get_unified_combo_style())
        for s in self.services:
            self.combo_service.addItem(
                f"[{s['category_name']}] {s['name']} ({s['duration_minutes']}분)",
                s,
            )

        btn_add_svc = QPushButton("+ 추가", container)
        btn_add_svc.setFixedSize(72, 38)
        btn_add_svc.setCursor(Qt.PointingHandCursor)
        btn_add_svc.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
            }}
        """)
        btn_add_svc.clicked.connect(self._add_selected_service)

        btn_clear_svc = QPushButton("초기화", container)
        btn_clear_svc.setFixedSize(58, 38)
        btn_clear_svc.setCursor(Qt.PointingHandCursor)
        btn_clear_svc.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                color: #475569;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
            }
        """)
        btn_clear_svc.clicked.connect(self._clear_selected_services)

        svc_row.addWidget(self.combo_service, 1)
        svc_row.addWidget(btn_add_svc)
        svc_row.addWidget(btn_clear_svc)
        layout.addLayout(svc_row)

        self.input_service_summary = QLineEdit(container)
        self.input_service_summary.setPlaceholderText("시술 선택 후 [+ 추가]를 누르면 자동 입력됩니다 (직접 입력 가능)")
        self.input_service_summary.setFixedHeight(36)
        self.input_service_summary.setStyleSheet(self._input_style())
        layout.addWidget(self.input_service_summary)

        # 4. 예약 일시 및 예상 소요시간 (30분 단위, 기본 30분)
        layout.addWidget(self._section_label("예약 일시 및 예상 소요시간", container))
        dt_row = QHBoxLayout()
        dt_row.setSpacing(8)

        self.date_edit = QDateEdit(container)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(default_date or QDate.currentDate())
        self.date_edit.setFixedHeight(38)
        self.date_edit.setStyleSheet(get_unified_date_style())
        cal = self.date_edit.calendarWidget()
        if cal:
            cal.setNavigationBarVisible(True)

        self.combo_time = QComboBox(container)
        self.combo_time.setFixedSize(108, 38)
        self.combo_time.setStyleSheet(get_unified_combo_style())
        for h in range(9, 22):
            for m in (0, 30):
                self.combo_time.addItem(f"{h:02d}:{m:02d}")
        t_idx = self.combo_time.findText(default_time or "10:00")
        if t_idx >= 0:
            self.combo_time.setCurrentIndex(t_idx)

        lbl_dur = QLabel("소요:", container)
        lbl_dur.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        lbl_dur.setStyleSheet("color: #334155; border: none;")

        self.spin_duration = QSpinBox(container)
        self.spin_duration.setRange(30, 600)
        self.spin_duration.setSingleStep(30)
        self.spin_duration.setValue(30)
        self.spin_duration.setSuffix("분")
        self.spin_duration.setAlignment(Qt.AlignCenter)
        self.spin_duration.setFixedSize(92, 38)
        self.spin_duration.setStyleSheet(get_unified_spin_style())

        dt_row.addWidget(self.date_edit, 1)
        dt_row.addWidget(self.combo_time)
        dt_row.addWidget(lbl_dur)
        dt_row.addWidget(self.spin_duration)
        layout.addLayout(dt_row)

        # 5. 예약 상태 선택
        layout.addWidget(self._section_label("예약 상태", container))
        status_row = QHBoxLayout()
        status_row.setSpacing(6)
        self.status_group = QButtonGroup(self)
        self.status_group.setExclusive(True)
        self.status_buttons = {}

        for idx, st_name in enumerate(["예약완료", "방문완료", "취소", "노쇼"]):
            btn = QPushButton(st_name, container)
            btn.setCheckable(True)
            btn.setFixedHeight(34)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #F8FAFC;
                    color: #475569;
                    border: 1px solid #CBD5E1;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                QPushButton:checked {{
                    background-color: {Colors.PRIMARY};
                    color: #FFFFFF;
                    border: 1.5px solid {Colors.PRIMARY};
                }}
            """)
            self.status_group.addButton(btn, idx)
            self.status_buttons[st_name] = btn
            status_row.addWidget(btn, 1)
        self.status_buttons["예약완료"].setChecked(True)
        layout.addLayout(status_row)

        # 6. 메모 (세로 스크롤바 UI 적용)
        layout.addWidget(self._section_label("메모", container))
        self.txt_memo = QTextEdit(container)
        self.txt_memo.setPlaceholderText("요청 사항, 시술 참고 메모 등을 입력하세요...")
        self.txt_memo.setFixedHeight(72)
        self.txt_memo.setStyleSheet(f"""
            QTextEdit {{
                background-color: #FAFAFA;
                border: 1.5px solid #C0C0C0;
                border-radius: 8px;
                padding: 8px;
                font-size: 12px;
                color: #0F172A;
            }}
            QTextEdit:focus {{
                border: 1.5px solid {Colors.PRIMARY};
                background-color: #FFFFFF;
            }}
            {SCROLLBAR_STYLE}
        """)
        self.txt_memo.verticalScrollBar().setStyleSheet(SCROLLBAR_STYLE)
        layout.addWidget(self.txt_memo)

        # 하단 액션 버튼 바
        footer_row = QHBoxLayout()
        footer_row.setSpacing(10)

        if self.is_edit:
            btn_delete = QPushButton("삭제", container)
            btn_delete.setFixedSize(76, 40)
            btn_delete.setCursor(Qt.PointingHandCursor)
            btn_delete.setStyleSheet("""
                QPushButton {
                    background-color: #FEF2F2;
                    color: #DC2626;
                    border: 1.5px solid #FCA5A5;
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #FEE2E2;
                }
            """)
            btn_delete.clicked.connect(self._on_delete_clicked)
            footer_row.addWidget(btn_delete)

        footer_row.addStretch()

        btn_cancel = QPushButton("취소", container)
        btn_cancel.setFixedSize(90, 40)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                color: #334155;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
            }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("예약 저장", container)
        btn_save.setFixedSize(115, 40)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
            }}
        """)
        btn_save.clicked.connect(self._on_save_clicked)

        footer_row.addWidget(btn_cancel)
        footer_row.addWidget(btn_save)
        layout.addLayout(footer_row)

        outer.addWidget(container)

    def _section_label(self, text: str, parent) -> QLabel:
        lbl = QLabel(text, parent)
        lbl.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #1E293B; border: none;")
        return lbl

    def _input_style(self) -> str:
        return f"""
            QLineEdit {{
                background-color: #FAFAFA;
                border: 1.5px solid #C0C0C0;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 12.5px;
                color: #0F172A;
            }}
            QLineEdit:focus {{
                border: 1.5px solid {Colors.PRIMARY};
                background-color: #FFFFFF;
            }}
        """

    def _on_guest_phone_changed(self, text: str):
        formatted = format_korean_phone(text)
        if formatted != text:
            self.input_guest_phone.blockSignals(True)
            self.input_guest_phone.setText(formatted)
            self.input_guest_phone.setCursorPosition(len(formatted))
            self.input_guest_phone.blockSignals(False)

    def _on_toggle_guest_mode(self, checked: bool):
        self.is_guest_mode = checked
        self.existing_cust_box.setVisible(not checked)
        self.guest_cust_box.setVisible(checked)
        if checked:
            self.selected_customer_id = None
            self.btn_toggle_guest.setText("기존 고객 검색")
            self.input_guest_name.setFocus()
        else:
            self.btn_toggle_guest.setText("+ 미등록 고객 입력")
            self.input_customer_search.setFocus()

    def _on_customer_selected(self, label: str):
        cust = self._customer_map.get(label)
        if cust:
            self.selected_customer_id = cust["id"]
            self.input_customer_search.blockSignals(True)
            self.input_customer_search.setText(label)
            self.input_customer_search.blockSignals(False)
            self.lbl_selected_cust_info.setText(
                f"선택된 고객: {cust['name']} ({cust['phone']}) · 선결제 잔액 {cust['prepaid_balance']:,}원"
            )
            self.lbl_selected_cust_info.setStyleSheet(f"color: {Colors.PRIMARY}; font-weight: bold; border: none;")

    def _on_customer_text_changed(self, text: str):
        cust = self._customer_map.get(text.strip())
        if cust:
            self._on_customer_selected(text.strip())
        else:
            self.selected_customer_id = None
            self.lbl_selected_cust_info.setText("목록에서 등록 고객을 선택하거나 입력 후 Enter를 누르세요.")
            self.lbl_selected_cust_info.setStyleSheet("color: #64748B; border: none;")

    def _on_customer_search_enter(self):
        """고객 검색창에서 Enter 키 입력 시 일치하는 첫 번째 고객 즉시 적용"""
        keyword = self.input_customer_search.text().strip()
        if not keyword:
            return

        popup = self.customer_completer.popup()
        if popup and popup.isVisible():
            idx = popup.currentIndex()
            if idx.isValid():
                label = idx.data()
                if label in self._customer_map:
                    self._on_customer_selected(label)
                    popup.hide()
                    return

        if keyword in self._customer_map:
            self._on_customer_selected(keyword)
            return

        digits_kw = re.sub(r"\D", "", keyword)
        matched_label = None
        for label, cust in self._customer_map.items():
            c_name = (cust.get("name") or "").lower()
            c_phone = cust.get("phone") or ""
            c_digits = re.sub(r"\D", "", c_phone)
            if keyword.lower() in c_name or keyword in c_phone or (digits_kw and digits_kw in c_digits):
                matched_label = label
                break

        if matched_label:
            self._on_customer_selected(matched_label)
            if popup:
                popup.hide()
        else:
            self.lbl_selected_cust_info.setText("일치하는 등록 고객이 없습니다. [+ 미등록 고객 입력]을 눌러 주세요.")
            self.lbl_selected_cust_info.setStyleSheet("color: #DC2626; font-weight: bold; border: none;")

    def _add_selected_service(self):
        svc = self.combo_service.currentData()
        if not svc:
            return
        self.selected_service_items.append({
            "id": svc["id"],
            "name": svc["name"],
            "duration": int(svc.get("duration_minutes", 30)),
        })
        names = [item["name"] for item in self.selected_service_items]
        total_dur = sum(item["duration"] for item in self.selected_service_items)
        rounded_dur = max(30, ((total_dur + 29) // 30) * 30)
        self.input_service_summary.setText(" + ".join(names))
        self.spin_duration.setValue(rounded_dur)

    def _clear_selected_services(self):
        self.selected_service_items.clear()
        self.input_service_summary.clear()
        self.spin_duration.setValue(30)

    def _populate_edit_data(self):
        r = self.reservation
        if r.get("is_guest") or not r.get("customer_id"):
            self.btn_toggle_guest.setChecked(True)
            self.input_guest_name.setText(r.get("customer_name", ""))
            self.input_guest_phone.setText(format_korean_phone(r.get("customer_phone", "")))
        else:
            self.btn_toggle_guest.setChecked(False)
            self.selected_customer_id = r.get("customer_id")
            display_label = f"{r.get('customer_name', '')} ({r.get('customer_phone', '')})"
            self.input_customer_search.setText(display_label)
            self.selected_customer_id = r.get("customer_id")
            self.lbl_selected_cust_info.setText(f"선택된 고객: {display_label}")
            self.lbl_selected_cust_info.setStyleSheet(f"color: {Colors.PRIMARY}; font-weight: bold; border: none;")

        if r.get("user_id"):
            idx = self.combo_designer.findData(r["user_id"])
            if idx >= 0:
                self.combo_designer.setCurrentIndex(idx)

        self.input_service_summary.setText(r.get("service_summary", ""))
        try:
            raw_ids = json.loads(r.get("service_ids_json", "[]"))
            svc_lookup = {s["id"]: s for s in self.services}
            self.selected_service_items = [
                {"id": sid, "name": svc_lookup[sid]["name"], "duration": svc_lookup[sid]["duration_minutes"]}
                for sid in raw_ids if sid in svc_lookup
            ]
        except Exception:
            self.selected_service_items = []

        res_dt = r.get("reserved_at", "")
        if len(res_dt) >= 16:
            d_part, t_part = res_dt[:10], res_dt[11:16]
            qd = QDate.fromString(d_part, "yyyy-MM-dd")
            if qd.isValid():
                self.date_edit.setDate(qd)
            t_idx = self.combo_time.findText(t_part)
            if t_idx >= 0:
                self.combo_time.setCurrentIndex(t_idx)

        self.spin_duration.setValue(int(r.get("duration_minutes", 30)))

        st = r.get("status", "예약완료")
        if st in self.status_buttons:
            self.status_buttons[st].setChecked(True)

        self.txt_memo.setPlainText(r.get("memo", ""))

    def _on_save_clicked(self):
        if self.is_guest_mode:
            guest_name = self.input_guest_name.text().strip()
            guest_phone = format_korean_phone(self.input_guest_phone.text().strip())
            if not guest_name:
                CustomAlertDialog("입력 확인", "미등록 고객의 이름을 입력해 주세요.", self).exec()
                self.input_guest_name.setFocus()
                return
            customer_id = None
        else:
            if not self.selected_customer_id:
                CustomAlertDialog(
                    "고객 선택 확인",
                    "등록된 고객을 검색 목록에서 선택(또는 입력 후 Enter)하거나,\n우측 [+ 미등록 고객 입력] 버튼을 눌러 주세요.",
                    self,
                ).exec()
                self.input_customer_search.setFocus()
                return
            customer_id = self.selected_customer_id
            guest_name = ""
            guest_phone = ""

        user_id = self.combo_designer.currentData()
        service_summary = self.input_service_summary.text().strip() or "시술 상담"
        service_ids_json = json.dumps([item["id"] for item in self.selected_service_items])
        reserved_at_str = f"{self.date_edit.date().toString('yyyy-MM-dd')} {self.combo_time.currentText()}:00"
        duration_minutes = int(self.spin_duration.value())
        memo = self.txt_memo.toPlainText().strip()

        checked_btn = self.status_group.checkedButton()
        status = checked_btn.text() if checked_btn else "예약완료"

        if status not in ("취소", "노쇼"):
            exclude_id = self.reservation["id"] if self.is_edit else None
            has_conflict, conflict_msg = self.db_manager.check_reservation_conflict(
                user_id=user_id,
                reserved_at_str=reserved_at_str,
                duration_minutes=duration_minutes,
                exclude_id=exclude_id,
            )
            if has_conflict:
                warn_dlg = ConfirmActionDialog(
                    "일정 중복 경고",
                    f"{conflict_msg}\n그래도 이 시간대에 예약을 저장하시겠습니까?",
                    confirm_text="중복 무시하고 저장",
                    danger=True,
                    parent=self,
                )
                if warn_dlg.exec() != QDialog.Accepted:
                    return

        if self.is_edit:
            ok, msg = self.db_manager.update_reservation(
                reservation_id=self.reservation["id"],
                customer_id=customer_id,
                guest_name=guest_name,
                guest_phone=guest_phone,
                user_id=user_id,
                service_summary=service_summary,
                service_ids_json=service_ids_json,
                reserved_at_str=reserved_at_str,
                duration_minutes=duration_minutes,
                status=status,
                memo=memo,
            )
        else:
            ok, msg = self.db_manager.add_reservation(
                customer_id=customer_id,
                guest_name=guest_name,
                guest_phone=guest_phone,
                user_id=user_id,
                service_summary=service_summary,
                service_ids_json=service_ids_json,
                reserved_at_str=reserved_at_str,
                duration_minutes=duration_minutes,
                status=status,
                memo=memo,
            )

        if ok:
            self.accept()
        else:
            CustomAlertDialog("저장 오류", msg, self).exec()

    def _on_delete_clicked(self):
        confirm = ConfirmActionDialog(
            "예약 삭제 확인",
            "선택한 예약 일정을 정말로 삭제하시겠습니까?",
            confirm_text="삭제",
            danger=True,
            parent=self,
        )
        if confirm.exec() == QDialog.Accepted:
            if self.db_manager.delete_reservation(self.reservation["id"]):
                self.accept()


class ReservationCardWidget(QFrame):
    """일간 타임테이블 내 개별 예약 블록 카드 (30분 슬롯에서도 잘리지 않고 겹치지 않게 표시)"""

    def __init__(self, reservation: dict, on_edit_cb, on_checkout_cb, parent=None):
        super().__init__(parent)
        self.reservation = reservation
        self.on_edit_cb = on_edit_cb
        self.on_checkout_cb = on_checkout_cb

        status = reservation.get("status", "예약완료")
        st = STATUS_STYLES.get(status, STATUS_STYLES["예약완료"])
        dur = int(reservation.get("duration_minutes", 30))
        is_compact = dur <= 30

        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("ResCard")
        self.setStyleSheet(f"""
            QFrame#ResCard {{
                background-color: {st['card_bg']};
                border: 1.5px solid {st['card_border']};
                border-radius: 7px;
            }}
            QFrame#ResCard:hover {{
                border: 1.5px solid {Colors.PRIMARY};
            }}
        """)

        main_row = QHBoxLayout(self)
        main_row.setContentsMargins(10, 4 if is_compact else 7, 10, 4 if is_compact else 7)
        main_row.setSpacing(8)

        # 좌측 정보 영역
        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(1 if is_compact else 2)

        start_str = reservation["reserved_at"][11:16]
        try:
            dt_s = datetime.strptime(reservation["reserved_at"], "%Y-%m-%d %H:%M")
            dt_e = dt_s + timedelta(minutes=dur)
            time_range = f"{start_str} - {dt_e.strftime('%H:%M')}"
        except Exception:
            time_range = start_str

        guest_tag = "미등록, " if reservation.get("is_guest") else ""
        phone_txt = format_korean_phone(reservation.get("customer_phone") or "") or "연락처 없음"
        cust_line = f"{reservation['customer_name']} ({guest_tag}{phone_txt})"
        svc_txt = reservation.get("service_summary") or "-"
        des_txt = f"담당: {reservation.get('designer_name', '-')}"

        if is_compact:
            line1 = QLabel(f"{time_range}  |  {cust_line}", self)
            line1.setFont(QFont("Inter", 10, QFont.Weight.Bold))
            line1.setStyleSheet("color: #0F172A; background: transparent; border: none;")

            line2 = QLabel(f"{svc_txt} · {des_txt}", self)
            line2.setFont(QFont("Inter", 9))
            line2.setStyleSheet("color: #475569; background: transparent; border: none;")

            left_col.addWidget(line1)
            left_col.addWidget(line2)
        else:
            lbl_time = QLabel(time_range, self)
            lbl_time.setFont(QFont("Inter", 10, QFont.Weight.Bold))
            lbl_time.setStyleSheet("color: #0F172A; background: transparent; border: none;")

            lbl_cust = QLabel(cust_line, self)
            lbl_cust.setFont(QFont("Inter", 10, QFont.Weight.Bold))
            lbl_cust.setStyleSheet("color: #1E293B; background: transparent; border: none;")

            lbl_svc = QLabel(svc_txt, self)
            lbl_svc.setFont(QFont("Inter", 9))
            lbl_svc.setStyleSheet("color: #475569; background: transparent; border: none;")

            lbl_des = QLabel(des_txt, self)
            lbl_des.setFont(QFont("Inter", 9))
            lbl_des.setStyleSheet("color: #64748B; background: transparent; border: none;")

            left_col.addWidget(lbl_time)
            left_col.addWidget(lbl_cust)
            left_col.addWidget(lbl_svc)
            left_col.addWidget(lbl_des)
            left_col.addStretch()

        # 우측 액션 영역
        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(3 if is_compact else 6)
        right_col.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        lbl_badge = QLabel(status, self)
        lbl_badge.setFixedSize(70, 20)
        lbl_badge.setAlignment(Qt.AlignCenter)
        lbl_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {st['badge_bg']};
                color: {st['badge_fg']};
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
                border: none;
            }}
        """)
        right_col.addWidget(lbl_badge)

        if status == "예약완료":
            btn_checkout = QPushButton("결제 등록", self)
            btn_checkout.setFixedSize(70, 22 if is_compact else 25)
            btn_checkout.setCursor(Qt.PointingHandCursor)
            btn_checkout.setStyleSheet(f"""
                QPushButton {{
                    background-color: #FFFFFF;
                    color: {Colors.PRIMARY};
                    border: 1.5px solid {Colors.PRIMARY};
                    border-radius: 4px;
                    font-size: 10px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {Colors.PRIMARY};
                    color: #FFFFFF;
                }}
            """)
            btn_checkout.clicked.connect(lambda: self.on_checkout_cb(self.reservation))
            right_col.addWidget(btn_checkout)
        else:
            right_col.addStretch()

        main_row.addLayout(left_col, 1)
        main_row.addLayout(right_col)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            event.accept()
            self.on_edit_cb(self.reservation)
            return
        super().mousePressEvent(event)


class BookingManagementView(QWidget):
    """예약 관리 메인 뷰 (일간 타임테이블 / 리스트 보기 + 결제 연동)"""
    proceed_to_payment = Signal(dict)

    SLOT_START_HOUR = 9
    SLOT_END_HOUR = 20
    HALF_HOUR_HEIGHT = 58

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DBManager()
        self.current_date = QDate.currentDate()
        self.view_mode = "daily"
        self._pre_search_mode = None
        self.designers = []
        self.reservations = []

        self._setup_ui()
        self.reload_all()

    def _setup_ui(self):
        self.setStyleSheet(f"background-color: {Colors.BACKGROUND};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 14, 24, 20)
        main_layout.setSpacing(10)

        # =====================================================================
        # 1. 상단 1행: 타이틀 ('예약 현황') + [+ 신규 예약 등록] 버튼
        # =====================================================================
        title_bar = QHBoxLayout()
        title_bar.setSpacing(10)

        lbl_title = QLabel("예약 현황", self)
        lbl_title.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #0F172A; border: none;")
        title_bar.addWidget(lbl_title)
        title_bar.addStretch()

        btn_new_booking = QPushButton("+ 신규 예약 등록", self)
        btn_new_booking.setFixedSize(140, 36)
        btn_new_booking.setCursor(Qt.PointingHandCursor)
        btn_new_booking.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        btn_new_booking.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
            }}
        """)
        btn_new_booking.clicked.connect(lambda: self.open_reservation_dialog())
        title_bar.addWidget(btn_new_booking)
        main_layout.addLayout(title_bar)

        # =====================================================================
        # 2. 상단 2행: 날짜 네비게이션 + 뷰 모드 탭 (일간 타임테이블 / 리스트 보기) + 필터/검색
        # =====================================================================
        sub_bar = QHBoxLayout()
        sub_bar.setSpacing(8)

        btn_prev = QPushButton("‹", self)
        btn_prev.setFixedSize(30, 34)
        btn_prev.setCursor(Qt.PointingHandCursor)
        btn_prev.setStyleSheet(self._nav_btn_style())
        btn_prev.clicked.connect(lambda: self._shift_date(-1))

        self.btn_date_display = QPushButton(self)
        self.btn_date_display.setFixedSize(210, 34)
        self.btn_date_display.setCursor(Qt.PointingHandCursor)
        self.btn_date_display.setToolTip("클릭하여 달력에서 원하는 날짜로 바로 이동")
        self.btn_date_display.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        self.btn_date_display.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #0F172A;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 0 12px;
            }
            QPushButton:hover {
                border: 1.5px solid #0D5C46;
                color: #0D5C46;
            }
        """)
        self.btn_date_display.clicked.connect(self._open_date_picker_popup)

        btn_next = QPushButton("›", self)
        btn_next.setFixedSize(30, 34)
        btn_next.setCursor(Qt.PointingHandCursor)
        btn_next.setStyleSheet(self._nav_btn_style())
        btn_next.clicked.connect(lambda: self._shift_date(1))

        btn_today = QPushButton("오늘", self)
        btn_today.setFixedSize(50, 34)
        btn_today.setCursor(Qt.PointingHandCursor)
        btn_today.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #334155;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F1F5F9;
            }
        """)
        btn_today.clicked.connect(self._go_today)

        sub_bar.addWidget(btn_prev)
        sub_bar.addWidget(self.btn_date_display)
        sub_bar.addWidget(btn_next)
        sub_bar.addWidget(btn_today)
        sub_bar.addSpacing(6)

        seg_box = QFrame(self)
        seg_box.setFixedHeight(36)
        seg_box.setStyleSheet("""
            QFrame {
                background-color: #E2E8F0;
                border-radius: 8px;
            }
        """)
        seg_layout = QHBoxLayout(seg_box)
        seg_layout.setContentsMargins(3, 3, 3, 3)
        seg_layout.setSpacing(4)

        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)

        self.btn_mode_daily = self._create_mode_btn("일간 타임테이블", "daily", 118, seg_box)
        self.btn_mode_list = self._create_mode_btn("리스트 보기", "list", 96, seg_box)

        for idx, b in enumerate([self.btn_mode_daily, self.btn_mode_list]):
            self.mode_group.addButton(b, idx)
            seg_layout.addWidget(b)
        self.btn_mode_daily.setChecked(True)

        sub_bar.addWidget(seg_box)
        sub_bar.addStretch()

        self.combo_filter_designer = QComboBox(self)
        self.combo_filter_designer.setFixedSize(215, 34)
        self.combo_filter_designer.setStyleSheet(get_unified_combo_style())
        self.combo_filter_designer.currentIndexChanged.connect(self.refresh_reservations)

        self.combo_filter_status = QComboBox(self)
        self.combo_filter_status.setFixedSize(118, 34)
        self.combo_filter_status.setStyleSheet(get_unified_combo_style())
        self.combo_filter_status.addItem("상태: 전체", "all")
        for st in ["예약완료", "방문완료", "취소", "노쇼"]:
            self.combo_filter_status.addItem(st, st)
        self.combo_filter_status.currentIndexChanged.connect(self.refresh_reservations)

        self.txt_search = QLineEdit(self)
        self.txt_search.setPlaceholderText("검색: 고객명/연락처")
        self.txt_search.setClearButtonEnabled(True)
        self.txt_search.setFixedSize(175, 34)
        self.txt_search.setStyleSheet(f"""
            QLineEdit {{
                background-color: #FFFFFF;
                border: 1.5px solid #C0C0C0;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 12px;
                color: #0F172A;
            }}
            QLineEdit:focus {{
                border: 1.5px solid {Colors.PRIMARY};
            }}
        """)
        self.txt_search.textChanged.connect(self._on_search_text_changed)

        sub_bar.addWidget(self.combo_filter_designer)
        sub_bar.addWidget(self.combo_filter_status)
        sub_bar.addWidget(self.txt_search)
        main_layout.addLayout(sub_bar)

        # =====================================================================
        # 3. 메인 콘텐츠 스택 (0: 일간 타임테이블, 1: 리스트 보기)
        # =====================================================================
        self.view_stack = QStackedWidget(self)

        # [0] 일간 타임테이블 컨테이너
        daily_outer_frame = QFrame(self)
        daily_outer_frame.setObjectName("DailyOuterFrame")
        daily_outer_frame.setStyleSheet("QFrame#DailyOuterFrame { background-color: #DCDCDC; border-radius: 10px; }")
        daily_outer_frame.setAttribute(Qt.WA_StyledBackground, True)
        daily_frame_layout = QVBoxLayout(daily_outer_frame)
        daily_frame_layout.setContentsMargins(8, 8, 8, 8)

        self.daily_container = QFrame(daily_outer_frame)
        self.daily_container.setObjectName("DailyContainer")
        self.daily_container.setStyleSheet("""
            QFrame#DailyContainer {
                background-color: #FFFFFF;
                border: none;
                border-radius: 6px;
            }
        """)
        daily_outer = QVBoxLayout(self.daily_container)
        daily_outer.setContentsMargins(0, 0, 0, 0)
        daily_outer.setSpacing(0)

        self.daily_header_widget = QWidget(self.daily_container)
        self.daily_header_widget.setObjectName("DailyHeaderWidget")
        self.daily_header_widget.setFixedHeight(42)
        self.daily_header_widget.setAttribute(Qt.WA_StyledBackground, True)
        self.daily_header_widget.setStyleSheet(f"""
            QWidget#DailyHeaderWidget {{
                background-color: {Colors.PRIMARY};
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}
        """)
        self.daily_header_layout = QHBoxLayout(self.daily_header_widget)
        self.daily_header_layout.setContentsMargins(0, 0, 10, 0)
        self.daily_header_layout.setSpacing(0)
        daily_outer.addWidget(self.daily_header_widget)

        self.daily_scroll = QScrollArea(self.daily_container)
        self.daily_scroll.setWidgetResizable(True)
        self.daily_scroll.setFrameShape(QFrame.NoFrame)
        self.daily_scroll.setStyleSheet("""
            QScrollArea {
                background-color: #FFFFFF;
                border: none;
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
                border-bottom-left-radius: 6px;
                border-bottom-right-radius: 6px;
            }
        """)
        self.daily_scroll.verticalScrollBar().setStyleSheet(SCROLLBAR_STYLE)
        daily_outer.addWidget(self.daily_scroll, 1)

        daily_frame_layout.addWidget(self.daily_container)
        self.view_stack.addWidget(daily_outer_frame)

        # [1] 리스트 보기 테이블
        list_outer = QFrame(self)
        list_outer.setObjectName("ListOuter")
        list_outer.setStyleSheet("QFrame#ListOuter { background-color: #DCDCDC; border-radius: 10px; }")
        list_outer.setAttribute(Qt.WA_StyledBackground, True)
        list_o_layout = QVBoxLayout(list_outer)
        list_o_layout.setContentsMargins(8, 8, 8, 8)

        list_inner = QFrame(list_outer)
        list_inner.setObjectName("ListInner")
        list_inner.setStyleSheet("QFrame#ListInner { background-color: #FFFFFF; border-radius: 6px; }")
        list_inner.setAttribute(Qt.WA_StyledBackground, True)
        list_i_layout = QVBoxLayout(list_inner)
        list_i_layout.setContentsMargins(0, 0, 0, 0)

        self.list_table = QTableWidget(list_inner)
        self._style_table(self.list_table)
        self.list_table.cellDoubleClicked.connect(self._on_list_cell_double_clicked)
        list_i_layout.addWidget(self.list_table)
        list_o_layout.addWidget(list_inner)
        self.view_stack.addWidget(list_outer)

        main_layout.addWidget(self.view_stack, 1)
        self._update_date_label()

    # -------------------------------------------------------------------------
    # 스타일 & 위젯 생성 헬퍼
    # -------------------------------------------------------------------------
    def _nav_btn_style(self) -> str:
        return """
            QPushButton {
                background-color: #FFFFFF;
                color: #334155;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F1F5F9;
            }
        """

    def _create_mode_btn(self, text: str, mode_key: str, min_w: int, parent) -> QPushButton:
        btn = QPushButton(text, parent)
        btn.setCheckable(True)
        btn.setFixedHeight(30)
        btn.setMinimumWidth(min_w)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: #475569;
                border: none;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:checked {{
                background-color: {Colors.PRIMARY};
                color: #FFFFFF;
            }}
            QPushButton:hover:!checked {{
                color: #0F172A;
            }}
        """)
        btn.clicked.connect(lambda: self._switch_view_mode(mode_key))
        return btn

    def _style_table(self, table: QTableWidget):
        custom_header = RoundedTableHeader(Qt.Horizontal, table)
        custom_header.setFixedHeight(40)
        table.setHorizontalHeader(custom_header)

        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setFocusPolicy(Qt.NoFocus)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                color: #000000;
                outline: none;
            }
            QTableWidget::item {
                border-bottom: 1px solid #E0E0E0;
                padding: 6px 8px;
            }
            QTableWidget::item:selected {
                background-color: #E8F5E9;
                color: #000000;
            }
        """)
        table.verticalScrollBar().setStyleSheet(SCROLLBAR_STYLE)

    # -------------------------------------------------------------------------
    # 데이터 로드 및 날짜/뷰 전환
    # -------------------------------------------------------------------------
    def reload_all(self):
        self.designers = self.db_manager.get_all_designers()
        self.combo_filter_designer.blockSignals(True)
        prev_val = self.combo_filter_designer.currentData()
        self.combo_filter_designer.clear()
        self.combo_filter_designer.addItem("디자이너: 전체", "all")
        for d in self.designers:
            label = format_designer_label(d.get("name", ""), d.get("position", ""))
            self.combo_filter_designer.addItem(label, d["id"])
        if prev_val is not None:
            idx = self.combo_filter_designer.findData(prev_val)
            if idx >= 0:
                self.combo_filter_designer.setCurrentIndex(idx)
        self.combo_filter_designer.blockSignals(False)

        self.refresh_reservations()

    def _update_date_label(self, is_search_mode: bool = False, result_count: int = 0):
        if is_search_mode:
            self.btn_date_display.setText(f"오늘 이후 검색 ({result_count}건) ▾")
            self.btn_date_display.setStyleSheet(f"""
                QPushButton {{
                    background-color: #ECFDF5;
                    color: {Colors.PRIMARY};
                    border: 1.5px solid {Colors.PRIMARY};
                    border-radius: 6px;
                    padding: 0 12px;
                }}
                QPushButton:hover {{
                    background-color: #D1FAE5;
                }}
            """)
        else:
            weekdays = ["월", "화", "수", "목", "금", "토", "일"]
            wd = weekdays[self.current_date.dayOfWeek() - 1]
            self.btn_date_display.setText(
                f"{self.current_date.toString('yyyy년 M월 d일')} ({wd}) ▾"
            )
            self.btn_date_display.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    color: #0F172A;
                    border: 1px solid #CBD5E1;
                    border-radius: 6px;
                    padding: 0 12px;
                }
                QPushButton:hover {
                    border: 1.5px solid #0D5C46;
                    color: #0D5C46;
                }
            """)

    def _open_date_picker_popup(self):
        popup = DatePickerPopup(self.current_date, self)
        popup.date_selected.connect(self._on_date_picked)
        global_pos = self.btn_date_display.mapToGlobal(QPoint(0, self.btn_date_display.height() + 4))
        popup.move(global_pos)
        popup.exec()

    def _on_date_picked(self, qdate: QDate):
        self.current_date = qdate
        if self.txt_search.text().strip():
            self.txt_search.blockSignals(True)
            self.txt_search.clear()
            self.txt_search.blockSignals(False)
            if self._pre_search_mode:
                self._restore_pre_search_mode()
        self._update_date_label()
        self.refresh_reservations()

    def _shift_date(self, step: int):
        self.current_date = self.current_date.addDays(step)
        if self.txt_search.text().strip():
            self.txt_search.blockSignals(True)
            self.txt_search.clear()
            self.txt_search.blockSignals(False)
            if self._pre_search_mode:
                self._restore_pre_search_mode()
        self._update_date_label()
        self.refresh_reservations()

    def _go_today(self):
        self.current_date = QDate.currentDate()
        if self.txt_search.text().strip():
            self.txt_search.blockSignals(True)
            self.txt_search.clear()
            self.txt_search.blockSignals(False)
            if self._pre_search_mode:
                self._restore_pre_search_mode()
        self._update_date_label()
        self.refresh_reservations()

    def _switch_view_mode(self, mode_key: str):
        self.view_mode = mode_key
        if not self.txt_search.text().strip():
            self._pre_search_mode = None
        self.view_stack.setCurrentIndex(0 if mode_key == "daily" else 1)
        self.refresh_reservations()

    def _restore_pre_search_mode(self):
        """검색 종료 시 검색 직전 뷰 모드('daily' 또는 'list')로 복귀"""
        target_mode = self._pre_search_mode or "daily"
        self._pre_search_mode = None
        self.view_mode = target_mode
        if target_mode == "daily":
            self.btn_mode_daily.setChecked(True)
            self.view_stack.setCurrentIndex(0)
        else:
            self.btn_mode_list.setChecked(True)
            self.view_stack.setCurrentIndex(1)

    def _on_search_text_changed(self, text: str):
        query = text.strip()
        if query:
            if self._pre_search_mode is None:
                self._pre_search_mode = self.view_mode
            if self.view_mode != "list":
                self.view_mode = "list"
                self.btn_mode_list.setChecked(True)
                self.view_stack.setCurrentIndex(1)
        else:
            if self._pre_search_mode is not None:
                self._restore_pre_search_mode()

        self.refresh_reservations()

    def refresh_reservations(self):
        designer_id = self.combo_filter_designer.currentData() or "all"
        status = self.combo_filter_status.currentData() or "all"
        query = self.txt_search.text().strip()

        if query:
            # 검색어가 있으면 오늘 이후 전체 예정 예약을 조회
            start_date = QDate.currentDate().toString("yyyy-MM-dd")
            end_date = "2099-12-31"
        else:
            start_date = self.current_date.toString("yyyy-MM-dd")
            end_date = start_date

        self.reservations = self.db_manager.get_reservations(
            start_date=start_date,
            end_date=end_date,
            designer_id=str(designer_id),
            status=str(status),
            query=query,
        )

        self._update_date_label(is_search_mode=bool(query), result_count=len(self.reservations))

        if self.view_mode == "daily":
            self._render_daily_timetable()
        else:
            self._render_list_view()

    # -------------------------------------------------------------------------
    # [0] 일간 타임테이블 렌더링
    # -------------------------------------------------------------------------
    def _render_daily_timetable(self):
        while self.daily_header_layout.count():
            item = self.daily_header_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        selected_des = self.combo_filter_designer.currentData()
        if selected_des and selected_des != "all":
            visible_designers = [d for d in self.designers if d["id"] == selected_des]
        else:
            visible_designers = list(self.designers)

        if not visible_designers:
            visible_designers = [{"id": None, "name": "전체 디자이너", "position": ""}]

        corner_lbl = QLabel("시간", self.daily_header_widget)
        corner_lbl.setFixedWidth(68)
        corner_lbl.setAlignment(Qt.AlignCenter)
        corner_lbl.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        corner_lbl.setStyleSheet("color: #FFFFFF; border: none; background: transparent;")
        self.daily_header_layout.addWidget(corner_lbl)

        for d in visible_designers:
            title = format_designer_label(d.get("name", ""), d.get("position", ""))
            col_lbl = QLabel(title, self.daily_header_widget)
            col_lbl.setAlignment(Qt.AlignCenter)
            col_lbl.setFont(QFont("Inter", 12, QFont.Weight.Bold))
            col_lbl.setStyleSheet("""
                QLabel {
                    color: #FFFFFF;
                    border: none;
                    border-left: 1px solid rgba(255, 255, 255, 0.25);
                    background: transparent;
                }
            """)
            self.daily_header_layout.addWidget(col_lbl, 1)

        body_widget = QWidget()
        body_widget.setObjectName("DailyBodyWidget")
        body_widget.setStyleSheet("QWidget#DailyBodyWidget { background-color: #FFFFFF; border-radius: 0px; }")
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        total_slots = (self.SLOT_END_HOUR - self.SLOT_START_HOUR + 1) * 2
        total_height = total_slots * self.HALF_HOUR_HEIGHT

        time_col = QFrame(body_widget)
        time_col.setFixedSize(68, total_height)
        time_col.setStyleSheet("background-color: #FAFAFA; border: none; border-radius: 0px;")
        for slot_idx in range(total_slots):
            hour = self.SLOT_START_HOUR + (slot_idx // 2)
            minute = 30 if slot_idx % 2 == 1 else 0
            y_pos = slot_idx * self.HALF_HOUR_HEIGHT

            lbl_t = QLabel(f"{hour:02d}:{minute:02d}", time_col)
            lbl_t.setGeometry(0, y_pos, 60, 22)
            lbl_t.setAlignment(Qt.AlignRight | Qt.AlignTop)
            lbl_t.setFont(QFont("Inter", 10, QFont.Weight.Bold if minute == 0 else QFont.Weight.Normal))
            lbl_t.setStyleSheet("color: #64748B; border: none; padding-top: 4px;")

        body_layout.addWidget(time_col)

        status_filter = self.combo_filter_status.currentData() or "all"

        for d in visible_designers:
            col_frame = QFrame(body_widget)
            col_frame.setObjectName("DesignerColFrame")
            col_frame.setMinimumHeight(total_height)
            col_frame.setStyleSheet("""
                QFrame#DesignerColFrame {
                    background-color: #FFFFFF;
                    border: none;
                    border-left: 1px solid #E2E8F0;
                    border-radius: 0px;
                }
            """)

            for slot_idx in range(total_slots):
                hour = self.SLOT_START_HOUR + (slot_idx // 2)
                minute = 30 if slot_idx % 2 == 1 else 0
                y_pos = slot_idx * self.HALF_HOUR_HEIGHT
                time_str = f"{hour:02d}:{minute:02d}"

                slot_btn = QPushButton("", col_frame)
                slot_btn.setGeometry(0, y_pos, 2000, self.HALF_HOUR_HEIGHT)
                slot_btn.setCursor(Qt.PointingHandCursor)
                border_color = "#E2E8F0" if minute == 0 else "#F1F5F9"
                slot_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        border: none;
                        border-radius: 0px;
                        border-bottom: 1px solid {border_color};
                    }}
                    QPushButton:hover {{
                        background-color: #F8FAFC;
                    }}
                """)
                des_id = d.get("id")
                slot_btn.clicked.connect(
                    lambda checked=False, t=time_str, uid=des_id: self.open_reservation_dialog(
                        default_time=t, default_user_id=uid
                    )
                )

            des_reservations = [
                r for r in self.reservations
                if (d.get("id") is None or r.get("user_id") == d.get("id"))
                and not (status_filter == "all" and r.get("status") == "취소")
            ]

            col_overlay_layout = QVBoxLayout(col_frame)
            col_overlay_layout.setContentsMargins(6, 0, 6, 0)
            col_overlay_layout.setSpacing(0)

            canvas = QWidget(col_frame)
            canvas.setStyleSheet("background: transparent; border: none;")
            canvas.setMinimumHeight(total_height)
            col_overlay_layout.addWidget(canvas)

            for r in des_reservations:
                try:
                    dt_s = datetime.strptime(r["reserved_at"], "%Y-%m-%d %H:%M")
                    start_mins = (dt_s.hour - self.SLOT_START_HOUR) * 60 + dt_s.minute
                    start_mins = max(0, start_mins)
                    y_px = int((start_mins / 30.0) * self.HALF_HOUR_HEIGHT) + 2
                    dur = max(30, int(r.get("duration_minutes", 30)))
                    h_px = int((dur / 30.0) * self.HALF_HOUR_HEIGHT) - 4
                except Exception:
                    y_px = 2
                    h_px = self.HALF_HOUR_HEIGHT - 4

                card = ReservationCardWidget(
                    reservation=r,
                    on_edit_cb=self.open_reservation_dialog,
                    on_checkout_cb=self._handle_checkout_click,
                    parent=canvas,
                )
                card.setGeometry(2, y_px, 240, h_px)

            canvas.resizeEvent = lambda event, c_list=canvas: [
                child.setGeometry(2, child.y(), max(160, c_list.width() - 4), child.height())
                for child in c_list.findChildren(ReservationCardWidget)
            ]

            body_layout.addWidget(col_frame, 1)

        self.daily_scroll.setWidget(body_widget)

    # -------------------------------------------------------------------------
    # [1] 리스트 보기 렌더링 ('이름 (직급)' 표기 통일)
    # -------------------------------------------------------------------------
    def _render_list_view(self):
        headers = ["예약일시", "고객명", "연락처", "구분", "담당 디자이너", "예정 시술", "소요시간", "상태", "메모", "결제 연동"]
        self.list_table.clear()
        self.list_table.setColumnCount(len(headers))
        self.list_table.setHorizontalHeaderLabels(headers)

        h_header = self.list_table.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.Stretch)
        for col, width in [(0, 140), (1, 100), (2, 130), (3, 80), (6, 80), (7, 85), (9, 105)]:
            h_header.setSectionResizeMode(col, QHeaderView.Fixed)
            self.list_table.setColumnWidth(col, width)

        designer_lookup = {
            d["id"]: format_designer_label(d.get("name", ""), d.get("position", ""))
            for d in self.designers
        }

        self.list_table.setRowCount(len(self.reservations))
        for row_idx, r in enumerate(self.reservations):
            self.list_table.setRowHeight(row_idx, 44)
            formatted_phone = format_korean_phone(r["customer_phone"]) if r["customer_phone"] else "-"
            designer_text = designer_lookup.get(
                r.get("user_id"),
                r.get("designer_name") or r.get("designer_display") or "-"
            )
            vals = [
                r["reserved_at"],
                r["customer_name"],
                formatted_phone,
                "미등록" if r["is_guest"] else "등록고객",
                designer_text,
                r["service_summary"] or "-",
                f"{r['duration_minutes']}분",
                r["status"],
                r["memo"] or "-",
            ]
            for c_idx, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                item.setData(Qt.UserRole, r)
                self.list_table.setItem(row_idx, c_idx, item)

            if r["status"] == "예약완료":
                btn_wrap = QWidget()
                btn_wrap.setStyleSheet("background: transparent; border: none;")
                bw_layout = QHBoxLayout(btn_wrap)
                bw_layout.setContentsMargins(0, 0, 0, 0)
                bw_layout.setAlignment(Qt.AlignCenter)

                btn_go = QPushButton("결제 등록", btn_wrap)
                btn_go.setFixedSize(78, 28)
                btn_go.setCursor(Qt.PointingHandCursor)
                btn_go.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {Colors.PRIMARY};
                        color: #FFFFFF;
                        border: none;
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: {Colors.PRIMARY_HOVER};
                    }}
                """)
                btn_go.clicked.connect(lambda checked=False, res=r: self._handle_checkout_click(res))
                bw_layout.addWidget(btn_go)
                self.list_table.setCellWidget(row_idx, 9, btn_wrap)
            else:
                done_item = QTableWidgetItem("-")
                done_item.setTextAlignment(Qt.AlignCenter)
                self.list_table.setItem(row_idx, 9, done_item)

    def _on_list_cell_double_clicked(self, row: int, col: int):
        item = self.list_table.item(row, 0)
        if item and item.data(Qt.UserRole):
            self.open_reservation_dialog(reservation=item.data(Qt.UserRole))

    # -------------------------------------------------------------------------
    # 모달 실행 및 결제 등록 화면 연동
    # -------------------------------------------------------------------------
    def open_reservation_dialog(self, reservation: dict = None,
                                default_time: str = "10:00", default_user_id: int = None):
        designers = self.db_manager.get_all_designers()
        services = self.db_manager.get_active_services_with_duration()
        customers = self.db_manager.get_all_customers()

        dlg = ReservationFormDialog(
            db_manager=self.db_manager,
            designers=designers,
            services=services,
            customers=customers,
            reservation=reservation,
            default_date=self.current_date,
            default_time=default_time,
            default_user_id=default_user_id,
            parent=self,
        )
        if dlg.exec() == QDialog.Accepted:
            self.refresh_reservations()

    def _handle_checkout_click(self, reservation: dict):
        """[결제 등록] 클릭 시 결제등록 화면으로 예약 데이터 전달"""
        try:
            service_ids = json.loads(reservation.get("service_ids_json", "[]"))
        except Exception:
            service_ids = []

        payload = {
            "reservation_id": reservation["id"],
            "customer_id": reservation.get("customer_id"),
            "customer_name": reservation.get("customer_name", ""),
            "customer_phone": format_korean_phone(reservation.get("customer_phone", "")),
            "is_guest": bool(reservation.get("is_guest")),
            "user_id": reservation.get("user_id"),
            "service_ids": service_ids,
            "service_summary": reservation.get("service_summary", ""),
            "duration_minutes": reservation.get("duration_minutes", 30),
            "memo": reservation.get("memo", ""),
        }
        self.proceed_to_payment.emit(payload)