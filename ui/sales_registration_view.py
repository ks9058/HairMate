from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QFrame, QMessageBox, QAbstractItemView, QStackedWidget,
    QComboBox, QDateEdit, QGridLayout, QScrollArea, QDialog, QSizePolicy,
    QSpinBox
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QFont, QColor, QPainter, QPainterPath, QTextDocument
from ui.theme import Colors, get_icon
from core.db_manager import DBManager


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
    QScrollBar:horizontal {
        border: none;
        background: #EAEAEA;
        height: 10px;
        margin: 0px;
        border-radius: 5px;
    }
    QScrollBar::handle:horizontal {
        background: #B0B0B0;
        min-width: 25px;
        border-radius: 5px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #888888;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        background: none;
        width: 0px;
    }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none;
    }
"""


class HorizontalScrollArea(QScrollArea):
    """마우스 휠(위/아래) 조작 시 가로(좌/우) 스크롤로 동작하는 커스텀 QScrollArea"""

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta != 0:
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta
            )
            event.accept()
        else:
            super().wheelEvent(event)


class CustomAlertDialog(QDialog):
    """커스텀 알림/안내 팝업 (단일 '확인' 버튼 적용)"""

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMinimumWidth(480)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(5, 5, 5, 5)

        container = QFrame(self)
        container.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #C0C0C0;
            }
        """)
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(35, 30, 35, 25)
        c_layout.setSpacing(22)

        formatted_msg = message.replace("\n", "<br>")
        lbl_msg = QLabel(f"<div style='line-height: 150%; text-align: center;'>{formatted_msg}</div>", container)
        lbl_msg.setFont(QFont("Inter", 13, QFont.Bold))
        lbl_msg.setAlignment(Qt.AlignCenter)
        lbl_msg.setStyleSheet("border: none; background: transparent; color: #000000;")

        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignCenter)

        btn_confirm = QPushButton("확인", container)
        btn_confirm.setFixedSize(130, 42)
        btn_confirm.setCursor(Qt.PointingHandCursor)
        btn_confirm.setFont(QFont("Inter", 12, QFont.Bold))
        btn_confirm.setStyleSheet(f"""
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
        btn_confirm.clicked.connect(self.accept)

        btn_layout.addWidget(btn_confirm)

        c_layout.addWidget(lbl_msg)
        c_layout.addLayout(btn_layout)

        outer_layout.addWidget(container)


class ConfirmCancelDialog(QDialog):
    """뒤로가기 클릭 시 노출되는 결제 취소 확인 팝업"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(540, 220)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(5, 5, 5, 5)

        container = QFrame(self)
        container.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #C0C0C0;
            }
        """)
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(30, 35, 30, 25)
        c_layout.setSpacing(25)

        lbl_msg = QLabel("현재 등록중인 결제건을 <font color='#E53E3E'>취소</font> 하시겠습니까?", container)
        lbl_msg.setFont(QFont("Inter", 16, QFont.Bold))
        lbl_msg.setAlignment(Qt.AlignCenter)
        lbl_msg.setStyleSheet("border: none; background: transparent; color: #000000;")

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)
        btn_layout.setAlignment(Qt.AlignCenter)

        btn_confirm = QPushButton("확인", container)
        btn_confirm.setFixedSize(130, 42)
        btn_confirm.setCursor(Qt.PointingHandCursor)
        btn_confirm.setFont(QFont("Inter", 12, QFont.Bold))
        btn_confirm.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: {Colors.PRIMARY};
                border: 2px solid {Colors.PRIMARY};
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: #E8F5E9;
            }}
        """)
        btn_confirm.clicked.connect(self.accept)

        btn_cancel = QPushButton("취소", container)
        btn_cancel.setFixedSize(130, 42)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setFont(QFont("Inter", 12, QFont.Bold))
        btn_cancel.setStyleSheet(f"""
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
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_confirm)
        btn_layout.addWidget(btn_cancel)

        c_layout.addWidget(lbl_msg)
        c_layout.addLayout(btn_layout)

        outer_layout.addWidget(container)


class RoundedHeader(QHeaderView):
    """상단 양쪽 모서리만 라운드 적용 커스텀 헤더 뷰"""

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setDefaultAlignment(Qt.AlignCenter)

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()

        r = 8.0
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
            doc.setHtml(f"<div style='color: #FFFFFF; font-weight: bold; font-size: 13px; text-align: center;'>{text}</div>")
            doc.setTextWidth(rect.width())

            y_offset = (rect.height() - doc.size().height()) / 2
            painter.translate(rect.x(), rect.y() + y_offset)
            doc.drawContents(painter)

        painter.restore()


class YellowStarHeader(QHeaderView):
    """상단 양쪽 모서리만 라운드 적용 및 별표(*) 노란색 커스텀 헤더 뷰"""

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setDefaultAlignment(Qt.AlignCenter)

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()

        r = 8.0
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
            formatted_text = text.replace("*", " <font color='#FFD700'>*</font>")
            doc = QTextDocument()
            doc.setHtml(f"<div style='color: #FFFFFF; font-weight: bold; font-size: 13px; text-align: center;'>{formatted_text}</div>")
            doc.setTextWidth(rect.width())

            y_offset = (rect.height() - doc.size().height()) / 2
            painter.translate(rect.x(), rect.y() + y_offset)
            doc.drawContents(painter)

        painter.restore()


class QuantityControlWidget(QWidget):
    """장바구니 표의 증감 컬럼 내 + / - 버튼"""

    def __init__(self, service_id: int, on_increase, on_decrease, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        layout.setAlignment(Qt.AlignCenter)

        btn_plus = QPushButton("+", self)
        btn_plus.setFixedSize(22, 22)
        btn_plus.setCursor(Qt.PointingHandCursor)
        btn_plus.setFont(QFont("Inter", 10, QFont.Bold))
        btn_plus.setStyleSheet(f"""
            QPushButton {{
                background-color: #E0E0E0;
                color: #000000;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY};
                color: #FFFFFF;
            }}
        """)
        btn_plus.clicked.connect(lambda: on_increase(service_id))

        btn_minus = QPushButton("-", self)
        btn_minus.setFixedSize(22, 22)
        btn_minus.setCursor(Qt.PointingHandCursor)
        btn_minus.setFont(QFont("Inter", 10, QFont.Bold))
        btn_minus.setStyleSheet(f"""
            QPushButton {{
                background-color: #E0E0E0;
                color: #000000;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {Colors.DANGER};
                color: #FFFFFF;
            }}
        """)
        btn_minus.clicked.connect(lambda: on_decrease(service_id))

        layout.addWidget(btn_plus)
        layout.addWidget(btn_minus)


class SalesRegistrationView(QWidget):
    """매출 등록 메인 뷰"""

    page_changed = Signal(bool)

    KEY_GENERAL_RATE = "point_rate_general"
    KEY_PREPAID_RATE = "point_rate_prepaid"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DBManager()
        self.selected_customer = None
        self.cart_items = []
        self.categories_data = []
        self.services_map = {}
        self.active_category_name = None

        self.total_amount = 0       
        self.remaining_amount = 0   
        self.payments_history = []  

        self.setup_ui()
        self.load_customer_list()
        self.load_menu_data()
        self.load_designers()

    def get_point_rates(self) -> tuple[float, float]:
        """DB 설정 테이블에서 일반 및 선결제 적립률 비율 조회 (기본값: 일반 10%, 선결제 20%)"""
        gen_str = self.db_manager.get_setting(self.KEY_GENERAL_RATE, default="10")
        prep_str = self.db_manager.get_setting(self.KEY_PREPAID_RATE, default="20")

        try:
            gen_rate = float(gen_str) / 100.0
        except ValueError:
            gen_rate = 0.10

        try:
            prep_rate = float(prep_str) / 100.0
        except ValueError:
            prep_rate = 0.20

        return gen_rate, prep_rate

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(25, 15, 25, 25)
        main_layout.setSpacing(0)

        self.main_stack = QStackedWidget(self)

        # =============================================================
        # Page 0: 고객 선택 화면
        # =============================================================
        page_select_cust = QWidget()
        select_layout = QHBoxLayout(page_select_cust)
        select_layout.setContentsMargins(0, 0, 0, 0)
        select_layout.setSpacing(20)

        left_outer = QFrame(page_select_cust)
        left_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        left_outer.setAttribute(Qt.WA_StyledBackground, True)

        left_layout = QVBoxLayout(left_outer)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(8)

        search_box = QFrame(left_outer)
        search_box.setFixedHeight(42)
        search_box.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        search_box.setAttribute(Qt.WA_StyledBackground, True)

        search_layout = QHBoxLayout(search_box)
        search_layout.setContentsMargins(12, 0, 12, 0)
        search_layout.setSpacing(10)

        lbl_search_icon = QLabel(search_box)
        lbl_search_icon.setPixmap(get_icon("search.svg").pixmap(18, 18))
        lbl_search_icon.setStyleSheet("background: transparent;")

        self.txt_search = QLineEdit(search_box)
        self.txt_search.setPlaceholderText("이름 또는 전화번호")
        self.txt_search.setFont(QFont("Inter", 12))
        self.txt_search.setStyleSheet("border: none; background: transparent; color: #000000;")
        self.txt_search.textChanged.connect(self.filter_customer_list)

        search_layout.addWidget(lbl_search_icon)
        search_layout.addWidget(self.txt_search, 1)
        left_layout.addWidget(search_box)

        table_container = QFrame(left_outer)
        table_container.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        table_container.setAttribute(Qt.WA_StyledBackground, True)

        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.cust_table = QTableWidget(table_container)

        custom_cust_header = RoundedHeader(Qt.Horizontal, self.cust_table)
        custom_cust_header.setFixedHeight(40)
        self.cust_table.setHorizontalHeader(custom_cust_header)

        self.cust_table.setColumnCount(4)
        self.cust_table.setHorizontalHeaderLabels(["번호", "이름", "전화번호", "최근 방문일자"])
        self.cust_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cust_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.cust_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cust_table.verticalHeader().setVisible(False)
        self.cust_table.setShowGrid(False)
        self.cust_table.setFocusPolicy(Qt.NoFocus)
        self.cust_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cust_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.cust_table.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: #FFFFFF;
                border-radius: 6px;
                font-size: 13px;
                color: #000000;
                outline: none;
            }
            QTableWidget::item {
                border-bottom: 1px solid #E0E0E0;
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #E8F5E9;
                color: #000000;
                font-weight: bold;
            }
        """)
        self.cust_table.verticalScrollBar().setStyleSheet(SCROLLBAR_STYLE)
        self.cust_table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.cust_table.itemSelectionChanged.connect(self.on_customer_selected)

        table_layout.addWidget(self.cust_table)
        left_layout.addWidget(table_container, 1)
        select_layout.addWidget(left_outer, 2)

        page_empty = QWidget()
        page_empty_layout = QVBoxLayout(page_empty)
        lbl_empty = QLabel("매출 등록할 고객을 선택해 주세요", page_empty)
        lbl_empty.setFont(QFont("Inter", 20, QFont.Bold))
        lbl_empty.setStyleSheet("color: #000000; background: transparent;")
        lbl_empty.setAlignment(Qt.AlignCenter)
        page_empty_layout.addWidget(lbl_empty)

        select_layout.addWidget(page_empty, 3)
        self.main_stack.addWidget(page_select_cust)

        # =============================================================
        # Page 1: 매출 등록 대시보드
        # =============================================================
        page_sales = QWidget()
        sales_layout = QHBoxLayout(page_sales)
        sales_layout.setContentsMargins(0, 0, 0, 0)
        sales_layout.setSpacing(20)

        left_sales_panel = QWidget(page_sales)
        left_s_layout = QVBoxLayout(left_sales_panel)
        left_s_layout.setContentsMargins(0, 0, 0, 0)
        left_s_layout.setSpacing(10)

        # 1. 상단 옵션 바
        ctrl_frame = QFrame(left_sales_panel)
        ctrl_frame.setFixedHeight(58)
        ctrl_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #DCDCDC; border-radius: 6px;")
        ctrl_layout = QHBoxLayout(ctrl_frame)
        ctrl_layout.setContentsMargins(10, 6, 10, 6)
        ctrl_layout.setSpacing(8)

        unified_input_style = """
            border: 1.5px solid #C0C0C0;
            border-radius: 4px;
            background-color: #FAFAFA;
            color: #000000;
            padding: 2px 4px;
        """

        v_designer = QVBoxLayout()
        v_designer.setSpacing(2)
        lbl_d = QLabel("담당 디자이너", ctrl_frame)
        lbl_d.setFont(QFont("Inter", 9, QFont.Bold))
        lbl_d.setStyleSheet("color: #666666; border: none; background: transparent;")
        self.cb_designer = QComboBox(ctrl_frame)
        self.cb_designer.setFixedHeight(26)
        self.cb_designer.setFont(QFont("Inter", 10))
        self.cb_designer.setStyleSheet(f"""
            QComboBox {{
                {unified_input_style}
            }}
            QComboBox:focus {{
                border: 1.5px solid #0D705C;
                background-color: #FFFFFF;
            }}
        """)
        v_designer.addWidget(lbl_d)
        v_designer.addWidget(self.cb_designer)

        v_date = QVBoxLayout()
        v_date.setSpacing(2)
        lbl_dt = QLabel("결제일", ctrl_frame)
        lbl_dt.setFont(QFont("Inter", 9, QFont.Bold))
        lbl_dt.setStyleSheet("color: #666666; border: none; background: transparent;")
        self.date_visit = QDateEdit(ctrl_frame)
        self.date_visit.setDate(QDate.currentDate())
        self.date_visit.setFixedHeight(26)
        self.date_visit.setFont(QFont("Inter", 10))
        self.date_visit.setStyleSheet(f"""
            QDateEdit {{
                {unified_input_style}
            }}
            QDateEdit:focus {{
                border: 1.5px solid #0D705C;
                background-color: #FFFFFF;
            }}
        """)
        v_date.addWidget(lbl_dt)
        v_date.addWidget(self.date_visit)

        v_dur = QVBoxLayout()
        v_dur.setSpacing(2)
        lbl_dur = QLabel("시술 시간", ctrl_frame)
        lbl_dur.setFont(QFont("Inter", 9, QFont.Bold))
        lbl_dur.setStyleSheet("color: #666666; border: none; background: transparent;")

        h_dur_box = QHBoxLayout()
        h_dur_box.setSpacing(4)
        
        self.spn_duration = QSpinBox(ctrl_frame)
        self.spn_duration.setRange(0, 1440)
        self.spn_duration.setSingleStep(30)
        self.spn_duration.setValue(30)
        self.spn_duration.setFixedHeight(26)
        self.spn_duration.setAlignment(Qt.AlignCenter)
        self.spn_duration.setFont(QFont("Inter", 10, QFont.Bold))
        self.spn_duration.setStyleSheet(f"""
            QSpinBox {{
                {unified_input_style}
            }}
            QSpinBox:focus {{
                border: 1.5px solid #0D705C;
                background-color: #FFFFFF;
            }}
        """)
        
        lbl_min_unit = QLabel("분", ctrl_frame)
        lbl_min_unit.setFont(QFont("Inter", 10, QFont.Bold))
        lbl_min_unit.setStyleSheet("color: #333333; border: none; background: transparent;")

        h_dur_box.addWidget(self.spn_duration, 1)
        h_dur_box.addWidget(lbl_min_unit)

        v_dur.addWidget(lbl_dur)
        v_dur.addLayout(h_dur_box)

        ctrl_layout.addLayout(v_designer, 4)
        ctrl_layout.addLayout(v_date, 4)
        ctrl_layout.addLayout(v_dur, 3)
        left_s_layout.addWidget(ctrl_frame)

        # 2. 통합 결제 정보 카드
        pay_card = QFrame(left_sales_panel)
        pay_card.setStyleSheet(f"background-color: #FFFFFF; border: 2px solid {Colors.PRIMARY}; border-radius: 8px;")
        pay_card_layout = QVBoxLayout(pay_card)
        pay_card_layout.setContentsMargins(16, 12, 16, 12)
        pay_card_layout.setSpacing(6)

        r_total = QHBoxLayout()
        lbl_t_title = QLabel("총 결제 금액 :", pay_card)
        lbl_t_title.setFont(QFont("Inter", 12, QFont.Bold))
        lbl_t_title.setStyleSheet("border: none; background: transparent; color: #000000;")
        self.lbl_total_amount = QLabel("0 원", pay_card)
        self.lbl_total_amount.setFont(QFont("Inter", 14, QFont.Bold))
        self.lbl_total_amount.setAlignment(Qt.AlignRight)
        self.lbl_total_amount.setStyleSheet("border: none; background: transparent; color: #000000;")
        r_total.addWidget(lbl_t_title)
        r_total.addWidget(self.lbl_total_amount, 1)
        pay_card_layout.addLayout(r_total)

        r_recv = QHBoxLayout()
        lbl_rc_title = QLabel("받은 금액 :", pay_card)
        lbl_rc_title.setFont(QFont("Inter", 12, QFont.Bold))
        lbl_rc_title.setStyleSheet("border: none; background: transparent; color: #000000;")
        
        self.txt_received_amount = QLineEdit("0", pay_card)
        self.txt_received_amount.setFont(QFont("Inter", 13, QFont.Bold))
        self.txt_received_amount.setAlignment(Qt.AlignRight)
        self.txt_received_amount.setStyleSheet("""
            QLineEdit {
                border: 1.5px solid #C0C0C0;
                border-radius: 6px;
                padding: 3px 8px;
                background-color: #FAFAFA;
                color: #000000;
            }
            QLineEdit:focus {
                border: 2px solid #0D705C;
                background-color: #FFFFFF;
            }
        """)
        self.txt_received_amount.textChanged.connect(self.on_received_amount_changed)

        r_recv.addWidget(lbl_rc_title)
        r_recv.addWidget(self.txt_received_amount, 1)
        pay_card_layout.addLayout(r_recv)

        r_status = QHBoxLayout()
        self.lbl_status_title = QLabel("남은 금액 :", pay_card)
        self.lbl_status_title.setFont(QFont("Inter", 12, QFont.Bold))
        self.lbl_status_title.setStyleSheet("border: none; background: transparent; color: #E53E3E;")

        self.lbl_status_val = QLabel("0 원", pay_card)
        self.lbl_status_val.setFont(QFont("Inter", 13, QFont.Bold))
        self.lbl_status_val.setAlignment(Qt.AlignRight)
        self.lbl_status_val.setStyleSheet("border: none; background: transparent; color: #E53E3E;")

        r_status.addWidget(self.lbl_status_title)
        r_status.addWidget(self.lbl_status_val, 1)
        pay_card_layout.addLayout(r_status)

        r_earn_point = QHBoxLayout()
        lbl_earn_title = QLabel("적립 예정 포인트 :", pay_card)
        lbl_earn_title.setFont(QFont("Inter", 10, QFont.Bold))
        lbl_earn_title.setStyleSheet("border: none; background: transparent; color: #2B6CB0;")

        self.lbl_earn_point_val = QLabel("0 P", pay_card)
        self.lbl_earn_point_val.setFont(QFont("Inter", 10, QFont.Bold))
        self.lbl_earn_point_val.setAlignment(Qt.AlignRight)
        self.lbl_earn_point_val.setStyleSheet("border: none; background: transparent; color: #2B6CB0;")

        r_earn_point.addWidget(lbl_earn_title)
        r_earn_point.addWidget(self.lbl_earn_point_val, 1)
        pay_card_layout.addLayout(r_earn_point)

        self.lbl_history_summary = QLabel("", pay_card)
        self.lbl_history_summary.setFont(QFont("Inter", 9, QFont.Bold))
        self.lbl_history_summary.setStyleSheet("color: #0D705C; border: none; background: transparent;")
        self.lbl_history_summary.setAlignment(Qt.AlignRight)
        pay_card_layout.addWidget(self.lbl_history_summary)

        left_s_layout.addWidget(pay_card)

        # 3. 결제 수단 버튼 3종
        pay_btn_layout = QHBoxLayout()
        pay_btn_layout.setSpacing(8)

        self.btn_pay_cash = QPushButton("현금 결제", left_sales_panel)
        self.btn_pay_card = QPushButton("카드 결제", left_sales_panel)
        self.btn_pay_point = QPushButton("포인트 결제", left_sales_panel)

        self.btn_pay_cash.clicked.connect(lambda: self.process_payment("현금"))
        self.btn_pay_card.clicked.connect(lambda: self.process_payment("카드"))
        self.btn_pay_point.clicked.connect(lambda: self.process_payment("포인트"))

        for btn in [self.btn_pay_cash, self.btn_pay_card, self.btn_pay_point]:
            btn.setFixedHeight(40)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFont(QFont("Inter", 11, QFont.Bold))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.PRIMARY};
                    color: #FFFFFF;
                    border: none;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background-color: {Colors.PRIMARY_HOVER};
                }}
            """)
            pay_btn_layout.addWidget(btn)

        left_s_layout.addLayout(pay_btn_layout)

        # 4. 고객 정보 박스 (고객번호 항목 제거)
        cust_info_outer = QFrame(left_sales_panel)
        cust_info_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        cust_info_outer.setAttribute(Qt.WA_StyledBackground, True)
        c_layout = QVBoxLayout(cust_info_outer)
        c_layout.setContentsMargins(8, 8, 8, 8)

        c_inner = QFrame(cust_info_outer)
        c_inner.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        c_inner.setAttribute(Qt.WA_StyledBackground, True)
        ci_layout = QVBoxLayout(c_inner)
        ci_layout.setContentsMargins(15, 12, 15, 12)
        ci_layout.setSpacing(10)

        upper_info_widget = QWidget(c_inner)
        upper_info_layout = QVBoxLayout(upper_info_widget)
        upper_info_layout.setContentsMargins(0, 0, 0, 0)
        upper_info_layout.setSpacing(6)

        row_qss = """
            QFrame {
                border: none;
                border-bottom: 1.5px solid #7A7A7A;
                border-radius: 0px;
                background-color: transparent;
            }
            QLabel {
                border: none;
                background: transparent;
                font-weight: bold;
            }
        """

        # 이름
        f_name = QFrame(upper_info_widget)
        f_name.setFixedHeight(30)
        f_name.setStyleSheet(row_qss)
        r_name = QHBoxLayout(f_name)
        r_name.setContentsMargins(0, 0, 0, 0)
        lbl_name = QLabel("이 름 :", f_name)
        lbl_name.setFont(QFont("Inter", 10, QFont.Bold))
        lbl_name.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbl_info_name = QLabel("-", f_name)
        self.lbl_info_name.setFont(QFont("Inter", 10, QFont.Bold))
        self.lbl_info_name.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        r_name.addWidget(lbl_name)
        r_name.addWidget(self.lbl_info_name, 1)
        upper_info_layout.addWidget(f_name)

        # 전화번호
        f_phone = QFrame(upper_info_widget)
        f_phone.setFixedHeight(30)
        f_phone.setStyleSheet(row_qss)
        r_phone = QHBoxLayout(f_phone)
        r_phone.setContentsMargins(0, 0, 0, 0)
        lbl_phone = QLabel("전화번호 :", f_phone)
        lbl_phone.setFont(QFont("Inter", 10, QFont.Bold))
        lbl_phone.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbl_info_phone = QLabel("-", f_phone)
        self.lbl_info_phone.setFont(QFont("Inter", 10, QFont.Bold))
        self.lbl_info_phone.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        r_phone.addWidget(lbl_phone)
        r_phone.addWidget(self.lbl_info_phone, 1)
        upper_info_layout.addWidget(f_phone)

        # 포인트
        f_point = QFrame(upper_info_widget)
        f_point.setFixedHeight(30)
        f_point.setStyleSheet(row_qss)
        r_point = QHBoxLayout(f_point)
        r_point.setContentsMargins(0, 0, 0, 0)
        lbl_pt = QLabel("포 인 트 :", f_point)
        lbl_pt.setFont(QFont("Inter", 10, QFont.Bold))
        lbl_pt.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbl_info_point = QLabel("0P", f_point)
        self.lbl_info_point.setFont(QFont("Inter", 10, QFont.Bold))
        self.lbl_info_point.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        r_point.addWidget(lbl_pt)
        r_point.addWidget(self.lbl_info_point, 1)
        upper_info_layout.addWidget(f_point)

        # 메모 영역
        memo_widget = QWidget(c_inner)
        memo_layout = QVBoxLayout(memo_widget)
        memo_layout.setContentsMargins(0, 0, 0, 0)
        memo_layout.setSpacing(4)

        lbl_m_title = QLabel("메모 :", memo_widget)
        lbl_m_title.setFont(QFont("Inter", 10, QFont.Bold))
        lbl_m_title.setStyleSheet("border: none; background: transparent; color: #000000; font-weight: bold;")
        
        self.txt_info_memo = QTextEdit(memo_widget)
        self.txt_info_memo.setPlaceholderText("특이사항 및 메모 입력")
        self.txt_info_memo.setFont(QFont("Inter", 10, QFont.Bold))
        self.txt_info_memo.setStyleSheet("""
            QTextEdit {
                background-color: #FAFAFA;
                border: 1.5px solid #7A7A7A;
                border-radius: 6px;
                padding: 6px;
                color: #333333;
                font-weight: bold;
            }
            QTextEdit:focus {
                border: 1.5px solid #0D705C;
                background-color: #FFFFFF;
            }
        """)
        self.txt_info_memo.verticalScrollBar().setStyleSheet(SCROLLBAR_STYLE)

        memo_layout.addWidget(lbl_m_title)
        memo_layout.addWidget(self.txt_info_memo, 1)

        ci_layout.addWidget(upper_info_widget, 1)
        ci_layout.addWidget(memo_widget, 1)

        c_layout.addWidget(c_inner)
        left_s_layout.addWidget(cust_info_outer, 1)

        # 우측 패널
        right_sales_panel = QWidget(page_sales)
        right_s_layout = QVBoxLayout(right_sales_panel)
        right_s_layout.setContentsMargins(0, 0, 0, 0)
        right_s_layout.setSpacing(10)

        # 1. 장바구니 영역 패널
        cart_outer = QFrame(right_sales_panel)
        cart_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        cart_outer.setAttribute(Qt.WA_StyledBackground, True)
        cart_o_layout = QVBoxLayout(cart_outer)
        cart_o_layout.setContentsMargins(8, 8, 8, 8)

        cart_inner = QFrame(cart_outer)
        cart_inner.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        cart_inner.setAttribute(Qt.WA_StyledBackground, True)
        cart_i_layout = QVBoxLayout(cart_inner)
        cart_i_layout.setContentsMargins(0, 0, 0, 8)
        cart_i_layout.setSpacing(6)

        self.cart_table = QTableWidget(cart_inner)
        
        custom_header = YellowStarHeader(Qt.Horizontal, self.cart_table)
        custom_header.setFixedHeight(38)
        self.cart_table.setHorizontalHeader(custom_header)

        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(["메뉴명", "단가*", "수량*", "금액", "증감"])
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.verticalHeader().setDefaultSectionSize(40)
        self.cart_table.setShowGrid(False)
        self.cart_table.setFocusPolicy(Qt.NoFocus)
        self.cart_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.cart_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.cart_table.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: #FFFFFF;
                border-radius: 6px;
                font-size: 13px;
                color: #000000;
            }
            QTableWidget::item {
                border-bottom: 1px solid #E0E0E0;
                padding: 4px;
            }
        """)
        self.cart_table.verticalScrollBar().setStyleSheet(SCROLLBAR_STYLE)
        self.cart_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cart_table.itemChanged.connect(self.on_cart_cell_changed)
        cart_i_layout.addWidget(self.cart_table, 1)

        lbl_cart_tip = QLabel("* 단가와 수량은 더블클릭 후 키보드로 수정할 수 있습니다 *", cart_inner)
        lbl_cart_tip.setFont(QFont("Inter", 11, QFont.Bold))
        lbl_cart_tip.setStyleSheet("color: #E53E3E; background: transparent;")
        lbl_cart_tip.setAlignment(Qt.AlignCenter)
        cart_i_layout.addWidget(lbl_cart_tip)

        cart_o_layout.addWidget(cart_inner)
        right_s_layout.addWidget(cart_outer, 1)

        # 2. 카테고리 탭 및 시술 메뉴 그리드
        menu_outer = QFrame(right_sales_panel)
        menu_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        menu_outer.setAttribute(Qt.WA_StyledBackground, True)
        menu_o_layout = QVBoxLayout(menu_outer)
        menu_o_layout.setContentsMargins(8, 8, 8, 8)
        menu_o_layout.setSpacing(8)

        category_scroll = HorizontalScrollArea(menu_outer)
        category_scroll.setFixedHeight(66)
        category_scroll.setWidgetResizable(True)
        category_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        category_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        category_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        category_scroll.horizontalScrollBar().setStyleSheet("""
            QScrollBar:horizontal {
                border: none;
                background: #EAEAEA;
                height: 10px;
                margin: 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background: #B0B0B0;
                min-width: 25px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #888888;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                background: none;
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)

        category_widget = QWidget()
        category_widget.setStyleSheet("background: transparent;")
        self.category_bar_layout = QHBoxLayout(category_widget)
        self.category_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.category_bar_layout.setSpacing(8)
        self.category_bar_layout.setAlignment(Qt.AlignLeft)
        category_scroll.setWidget(category_widget)

        menu_o_layout.addWidget(category_scroll)

        menu_inner = QFrame(menu_outer)
        menu_inner.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        menu_inner.setAttribute(Qt.WA_StyledBackground, True)
        menu_i_layout = QVBoxLayout(menu_inner)
        menu_i_layout.setContentsMargins(6, 6, 6, 6)

        scroll_area = QScrollArea(menu_inner)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        scroll_area.verticalScrollBar().setStyleSheet("""
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
        """)

        self.service_grid_widget = QWidget()
        self.service_grid_widget.setStyleSheet("background: transparent;")
        
        self.service_grid_layout = QGridLayout(self.service_grid_widget)
        self.service_grid_layout.setContentsMargins(2, 2, 2, 2)
        self.service_grid_layout.setSpacing(6)
        self.service_grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        for c in range(4):
            self.service_grid_layout.setColumnStretch(c, 1)

        scroll_area.setWidget(self.service_grid_widget)
        menu_i_layout.addWidget(scroll_area)

        menu_o_layout.addWidget(menu_inner, 1)
        right_s_layout.addWidget(menu_outer, 1)

        sales_layout.addWidget(left_sales_panel, 35)
        sales_layout.addWidget(right_sales_panel, 65)

        self.main_stack.addWidget(page_sales)

        main_layout.addWidget(self.main_stack)
        self.main_stack.setCurrentIndex(0)

    # -------------------------------------------------------------
    # 뒤로가기 취소 확인 팝업 호출
    # -------------------------------------------------------------
    def confirm_and_clear_selection(self):
        """뒤로가기 클릭 시 취소 확인 팝업 노출"""
        dialog = ConfirmCancelDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.clear_customer_selection()

    # -------------------------------------------------------------
    # 데이터 로딩 및 동적 카테고리/시술 버튼 생성
    # -------------------------------------------------------------
    def load_customer_list(self):
        self.all_customers = self.db_manager.get_all_customers()
        self.filter_customer_list()

    def filter_customer_list(self):
        query = self.txt_search.text().strip().lower()
        self.cust_table.setRowCount(0)

        row_count = 0
        for cust in self.all_customers:
            name = cust["name"]
            phone = cust["phone"]
            if query and (query not in name.lower() and query not in phone.lower()):
                continue

            self.cust_table.insertRow(row_count)

            item_no = QTableWidgetItem(str(row_count + 1))
            item_no.setTextAlignment(Qt.AlignCenter)
            item_no.setData(Qt.UserRole, cust["id"])
            self.cust_table.setItem(row_count, 0, item_no)

            item_name = QTableWidgetItem(name)
            item_name.setTextAlignment(Qt.AlignCenter)
            self.cust_table.setItem(row_count, 1, item_name)

            item_phone = QTableWidgetItem(phone)
            item_phone.setTextAlignment(Qt.AlignCenter)
            self.cust_table.setItem(row_count, 2, item_phone)

            item_visit = QTableWidgetItem(cust["recent_visit"] or "-")
            item_visit.setTextAlignment(Qt.AlignCenter)
            self.cust_table.setItem(row_count, 3, item_visit)

            row_count += 1

    def update_table_column_widths(self):
        total_width = self.cust_table.viewport().width()
        if total_width > 0:
            w0 = int(total_width * 0.15)
            w1 = int(total_width * 0.25)
            w2 = int(total_width * 0.30)
            w3 = total_width - (w0 + w1 + w2)
            self.cust_table.setColumnWidth(0, w0)
            self.cust_table.setColumnWidth(1, w1)
            self.cust_table.setColumnWidth(2, w2)
            self.cust_table.setColumnWidth(3, w3)

    def showEvent(self, event):
        super().showEvent(event)
        self.update_table_column_widths()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_table_column_widths()

    def load_designers(self):
        self.cb_designer.clear()
        designers = self.db_manager.get_all_designers()
        for d in designers:
            self.cb_designer.addItem(f"{d['name']} ({d['position']})", d['id'])

    def load_menu_data(self):
        self.categories_data, self.services_map = self.db_manager.fetch_active_categories_and_services()
        self.render_category_buttons()

    def render_category_buttons(self):
        while self.category_bar_layout.count():
            item = self.category_bar_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.categories_data:
            return

        for cat in self.categories_data:
            cat_name = cat["name"]
            btn = QPushButton(cat_name, self)
            btn.setFixedSize(95, 50)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFont(QFont("Inter", 11, QFont.Bold))
            btn.clicked.connect(lambda _, name=cat_name: self.select_category(name))
            self.category_bar_layout.addWidget(btn)

        if self.categories_data:
            self.select_category(self.categories_data[0]["name"])

    def select_category(self, category_name: str):
        self.active_category_name = category_name
        for i in range(self.category_bar_layout.count()):
            btn = self.category_bar_layout.itemAt(i).widget()
            if isinstance(btn, QPushButton):
                if btn.text() == category_name:
                    btn.setStyleSheet(f"background-color: {Colors.PRIMARY}; color: #FFFFFF; border: none; border-radius: 10px;")
                else:
                    btn.setStyleSheet("background-color: #888888; color: #FFFFFF; border: none; border-radius: 10px;")
        self.render_service_grid(category_name)

    def render_service_grid(self, category_name: str):
        """시술 메뉴 그리드 생성"""
        while self.service_grid_layout.count():
            item = self.service_grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        services = self.services_map.get(category_name, [])
        col_count = 4

        for idx, svc in enumerate(services):
            row = idx // col_count
            col = idx % col_count

            btn_text = f"{svc['name']}\n{svc['price']:,}"
            btn = QPushButton(btn_text, self.service_grid_widget)
            
            btn.setFixedHeight(60)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFont(QFont("Inter", 11, QFont.Bold))
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.PRIMARY};
                    color: #FFFFFF;
                    border: none;
                    border-radius: 10px;
                    text-align: center;
                    padding: 4px 4px;
                }}
                QPushButton:hover {{
                    background-color: {Colors.PRIMARY_HOVER};
                }}
            """)
            btn.clicked.connect(lambda _, item=svc, cat=category_name: self.add_to_cart(item, cat))
            self.service_grid_layout.addWidget(btn, row, col)

    # -------------------------------------------------------------
    # 고객 선택 및 상태 관리
    # -------------------------------------------------------------
    def on_customer_selected(self):
        selected_items = self.cust_table.selectedItems()
        if not selected_items:
            return

        row = self.cust_table.currentRow()
        cust_id = self.cust_table.item(row, 0).data(Qt.UserRole)
        target_cust = next((c for c in self.all_customers if int(c["id"]) == int(cust_id)), None)

        if target_cust:
            self.selected_customer = dict(target_cust)
            self.lbl_info_name.setText(self.selected_customer["name"])
            self.lbl_info_phone.setText(self.selected_customer["phone"])
            self.lbl_info_point.setText(f"{self.selected_customer.get('point', 0):,}P")
            
            self.txt_info_memo.setPlainText(self.selected_customer.get("memo", "") or "")

            self.payments_history.clear()
            self.lbl_history_summary.setText("")
            self.main_stack.setCurrentIndex(1)
            
            self.page_changed.emit(True)

    def clear_customer_selection(self):
        self.selected_customer = None
        self.cust_table.clearSelection()
        self.cart_items.clear()
        self.payments_history.clear()
        self.update_cart_table()
        self.main_stack.setCurrentIndex(0)
        
        self.page_changed.emit(False)

    def on_received_amount_changed(self, text: str):
        digits = "".join(filter(str.isdigit, text))
        val = int(digits) if digits else 0

        self.txt_received_amount.blockSignals(True)
        self.txt_received_amount.setText(f"{val:,}")
        self.txt_received_amount.blockSignals(False)

        self.recalculate_payment_status()

    # -------------------------------------------------------------
    # 항목별 (일반 vs 선결제) 차등 적립 포인트 연산 (원금 + 보너스)
    # -------------------------------------------------------------
    def calculate_expected_earned_points(self, current_cash_card_pay: int = 0) -> int:
        gen_rate, prep_rate = self.get_point_rates()

        already_cash_card = sum(p["amount"] for p in self.payments_history if p["method"] in ["현금", "카드"])
        total_cash_card_paid = already_cash_card + current_cash_card_pay

        if self.total_amount <= 0 or total_cash_card_paid <= 0:
            return 0

        cash_card_ratio = min(1.0, total_cash_card_paid / float(self.total_amount))

        total_earned = 0
        for item in self.cart_items:
            item_total = item["price"] * item["qty"]
            is_prepaid = (item.get("category_name") == "선결제")
            
            if is_prepaid:
                earned_for_item = item_total * (1.0 + prep_rate)
            else:
                earned_for_item = item_total * gen_rate

            total_earned += int(earned_for_item * cash_card_ratio)

        return total_earned

    def recalculate_payment_status(self):
        digits = "".join(filter(str.isdigit, self.txt_received_amount.text()))
        received_val = int(digits) if digits else 0

        diff = received_val - self.remaining_amount

        if diff >= 0:
            self.lbl_status_title.setText("거스름돈 :")
            self.lbl_status_title.setStyleSheet("border: none; background: transparent; color: #0D705C;")
            self.lbl_status_val.setText(f"{diff:,} 원")
            self.lbl_status_val.setStyleSheet("border: none; background: transparent; color: #0D705C;")
        else:
            rem = abs(diff)
            self.lbl_status_title.setText("남은 금액 :")
            self.lbl_status_title.setStyleSheet("border: none; background: transparent; color: #E53E3E;")
            self.lbl_status_val.setText(f"{rem:,} 원")
            self.lbl_status_val.setStyleSheet("border: none; background: transparent; color: #E53E3E;")

        current_pay_val = min(received_val, self.remaining_amount)
        expected_earn_point = self.calculate_expected_earned_points(current_pay_val)
        
        gen_rate, prep_rate = self.get_point_rates()
        self.lbl_earn_point_val.setText(f"{expected_earn_point:,} P (일반 {int(gen_rate*100)}% / 선결제 {int(prep_rate*100)}%)")

    def add_to_cart(self, service: dict, category_name: str = ""):
        service_id = service["id"]
        cat_name = category_name or self.active_category_name or ""

        existing = next((item for item in self.cart_items if item["id"] == service_id), None)

        if existing:
            existing["qty"] += 1
        else:
            self.cart_items.append({
                "id": service_id,
                "name": service["name"],
                "price": service["price"],
                "category_name": cat_name,
                "qty": 1
            })
        self.update_cart_table()

    def increase_qty(self, service_id: int):
        for item in self.cart_items:
            if item["id"] == service_id:
                item["qty"] += 1
                break
        self.update_cart_table()

    def decrease_qty(self, service_id: int):
        for idx, item in enumerate(self.cart_items):
            if item["id"] == service_id:
                item["qty"] -= 1
                if item["qty"] <= 0:
                    self.cart_items.pop(idx)
                break
        self.update_cart_table()

    def on_cart_cell_changed(self, item: QTableWidgetItem):
        row = item.row()
        col = item.column()

        if row < 0 or row >= len(self.cart_items):
            return

        val_str = item.text().replace(",", "").strip()
        if not val_str.isdigit():
            self.update_cart_table()
            return

        val = int(val_str)
        if col == 1:
            self.cart_items[row]["price"] = val
        elif col == 2:
            if val <= 0:
                self.cart_items.pop(row)
            else:
                self.cart_items[row]["qty"] = val

        self.update_cart_table()

    def update_cart_table(self):
        self.cart_table.blockSignals(True)
        self.cart_table.setRowCount(0)
        
        self.total_amount = sum(item["price"] * item["qty"] for item in self.cart_items)
        
        paid_so_far = sum(p["amount"] for p in self.payments_history)
        self.remaining_amount = max(0, self.total_amount - paid_so_far)

        for row, item in enumerate(self.cart_items):
            line_total = item["price"] * item["qty"]
            self.cart_table.insertRow(row)

            it_name = QTableWidgetItem(item["name"])
            it_name.setFlags(it_name.flags() & ~Qt.ItemIsEditable)
            it_name.setTextAlignment(Qt.AlignCenter)
            self.cart_table.setItem(row, 0, it_name)

            it_price = QTableWidgetItem(f"{item['price']:,}")
            it_price.setTextAlignment(Qt.AlignCenter)
            self.cart_table.setItem(row, 1, it_price)

            it_qty = QTableWidgetItem(str(item["qty"]))
            it_qty.setTextAlignment(Qt.AlignCenter)
            self.cart_table.setItem(row, 2, it_qty)

            it_total = QTableWidgetItem(f"{line_total:,}")
            it_total.setFlags(it_total.flags() & ~Qt.ItemIsEditable)
            it_total.setTextAlignment(Qt.AlignCenter)
            self.cart_table.setItem(row, 3, it_total)

            ctrl_widget = QuantityControlWidget(item["id"], self.increase_qty, self.decrease_qty)
            self.cart_table.setCellWidget(row, 4, ctrl_widget)

        self.cart_table.blockSignals(False)

        self.lbl_total_amount.setText(f"{self.remaining_amount:,} 원" if paid_so_far > 0 else f"{self.total_amount:,} 원")
        
        self.txt_received_amount.blockSignals(True)
        self.txt_received_amount.setText(f"{self.remaining_amount:,}")
        self.txt_received_amount.blockSignals(False)

        self.recalculate_payment_status()

    # -------------------------------------------------------------
    # 커스텀 알림 창(CustomAlertDialog) 적용 결제 처리 및 DB 매출 등록
    # -------------------------------------------------------------
    def process_payment(self, method: str):
        if not self.cart_items:
            CustomAlertDialog("결제 오류", "장바구니에 담긴 시술이 없습니다.", self).exec()
            return

        if self.remaining_amount <= 0:
            CustomAlertDialog("결제 완료", "이미 결제가 완료되었습니다.", self).exec()
            return

        digits = "".join(filter(str.isdigit, self.txt_received_amount.text()))
        input_amt = int(digits) if digits else 0

        if input_amt <= 0:
            CustomAlertDialog("결제 오류", "결제할 금액을 입력해 주세요.", self).exec()
            return

        total_point_used = sum(p["amount"] for p in self.payments_history if p["method"] == "포인트")

        if method == "포인트":
            available_point = self.selected_customer.get("point", 0) if self.selected_customer else 0
            current_usable_point = available_point - total_point_used

            if current_usable_point <= 0:
                CustomAlertDialog("포인트 부족", "사용 가능한 보유 포인트가 없습니다.", self).exec()
                return

            if input_amt > current_usable_point:
                CustomAlertDialog(
                    "포인트 부족", 
                    f"입력한 금액({input_amt:,}원)이 사용 가능 포인트({current_usable_point:,}P)를 초과할 수 없습니다.", 
                    self
                ).exec()
                return

        pay_amt = min(input_amt, self.remaining_amount)
        change_amt = max(0, input_amt - self.remaining_amount)

        self.payments_history.append({"method": method, "amount": pay_amt})
        self.remaining_amount -= pay_amt

        total_point_used = sum(p["amount"] for p in self.payments_history if p["method"] == "포인트")
        current_display_point = max(0, self.selected_customer.get("point", 0) - total_point_used)
        self.lbl_info_point.setText(f"{current_display_point:,}P")

        history_str = " | ".join([f"{p['method']} {p['amount']:,}원" for p in self.payments_history])
        self.lbl_history_summary.setText(f"결제 내역: {history_str}")

        if self.remaining_amount <= 0:
            earned_point = self.calculate_expected_earned_points(0)
            
            cust_id = self.selected_customer["id"]
            new_memo = self.txt_info_memo.toPlainText().strip()
            designer_id = self.cb_designer.currentData()
            duration_minutes = self.spn_duration.value()
            selected_date = self.date_visit.date().toString("yyyy-MM-dd")
            current_time_str = datetime.now().strftime("%H:%M:%S")
            visited_at_str = f"{selected_date} {current_time_str}"

            # DB에 방문, 시술내역, 결제이력, 포인트내역 통합 저장
            save_success = self.db_manager.record_sale(
                customer_id=cust_id,
                user_id=designer_id,
                duration_minutes=duration_minutes,
                total_amount=self.total_amount,
                used_point=total_point_used,
                earned_point=earned_point,
                visited_at_str=visited_at_str,
                memo=new_memo,
                cart_items=self.cart_items,
                payments_history=self.payments_history
            )

            if not save_success:
                CustomAlertDialog("저장 오류", "DB 매출 저장 중 오류가 발생했습니다.", self).exec()
                return

            msg = f"결제가 성공적으로 완료되었습니다!\n\n• 총 결제 금액: {self.total_amount:,}원"
            if total_point_used > 0:
                msg += f"\n• 사용 포인트: -{total_point_used:,} P"
            if earned_point > 0:
                msg += f"\n• 충전/적립 포인트: +{earned_point:,} P"

            final_point = self.selected_customer.get("point", 0) - total_point_used + earned_point
            msg += f"\n• 최종 보유 포인트: {final_point:,} P"

            if change_amt > 0:
                msg += f"\n\n※ 거스름돈: {change_amt:,}원"

            CustomAlertDialog("결제 완료", msg, self).exec()
            
            # 결제 완료 후 목록 새로고침 (최근 방문일자 갱신 반영)
            self.load_customer_list()
            self.clear_customer_selection()
        else:
            CustomAlertDialog(
                "부분 결제 완료", 
                f"[{method}] {pay_amt:,}원 결제 승인되었습니다.\n남은 결제 금액: {self.remaining_amount:,}원", 
                self
            ).exec()
            self.txt_received_amount.blockSignals(True)
            self.txt_received_amount.setText(f"{self.remaining_amount:,}")
            self.txt_received_amount.blockSignals(False)
            self.recalculate_payment_status()