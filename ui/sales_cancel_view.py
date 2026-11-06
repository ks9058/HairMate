import re
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QFrame, QDialog, QAbstractItemView, QDateEdit, QToolTip
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor, QPainter, QPainterPath, QTextDocument, QCursor
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
"""


class RoundedHeader(QHeaderView):
    """상단 양쪽 모서리 라운드 커스텀 헤더 뷰"""

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


class ConfirmCancelSaleDialog(QDialog):
    """결제 정보 삭제 확인 커스텀 모달 팝업"""

    def __init__(self, sale_data: dict, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(400, 260)

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
        c_layout.setContentsMargins(25, 25, 25, 20)
        c_layout.setSpacing(16)

        info_html = f"""
            <div style='text-align: center; line-height: 140%; color: #000000; font-size: 13px;'>
                <b>결제번호: {sale_data['display_no']}</b><br>
                <b>고객이름: {sale_data['customer_name']}</b><br>
                <b>결제수단: {sale_data['payment_method']}</b><br>
                <b>결제금액: {sale_data['total_amount']:,}원</b>
            </div>
        """
        lbl_info = QLabel(info_html, container)
        lbl_info.setFont(QFont("Inter", 12))
        lbl_info.setAlignment(Qt.AlignCenter)
        lbl_info.setStyleSheet("border: none; background: transparent;")
        c_layout.addWidget(lbl_info)

        lbl_ask = QLabel("해당 정보를 정말로 <font color='#E53E3E'>삭제</font> 하시겠습니까?", container)
        lbl_ask.setFont(QFont("Inter", 13, QFont.Bold))
        lbl_ask.setAlignment(Qt.AlignCenter)
        lbl_ask.setStyleSheet("border: none; background: transparent; color: #000000;")
        c_layout.addWidget(lbl_ask)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        btn_confirm = QPushButton("확인", container)
        btn_confirm.setFixedHeight(40)
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
        btn_cancel.setFixedHeight(40)
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

        btn_layout.addWidget(btn_confirm, 1)
        btn_layout.addWidget(btn_cancel, 1)
        c_layout.addLayout(btn_layout)

        outer_layout.addWidget(container)


class SalesCancelView(QWidget):
    """결제취소 메인 뷰"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DBManager()
        self.sales_list = []
        self.selected_sale = None

        self.setup_ui()
        self.load_sales_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 15, 25, 20)
        main_layout.setSpacing(15)

        outer_container = QFrame(self)
        outer_container.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        outer_container.setAttribute(Qt.WA_StyledBackground, True)

        outer_layout = QVBoxLayout(outer_container)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.setSpacing(10)

        # 1. 상단 필터 영역
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(15)

        search_box = QFrame(outer_container)
        search_box.setFixedHeight(42)
        search_box.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        search_box.setAttribute(Qt.WA_StyledBackground, True)

        search_l = QHBoxLayout(search_box)
        search_l.setContentsMargins(12, 0, 12, 0)
        search_l.setSpacing(10)

        lbl_search_icon = QLabel(search_box)
        lbl_search_icon.setPixmap(get_icon("search.svg").pixmap(18, 18))
        lbl_search_icon.setStyleSheet("background: transparent;")

        self.txt_search = QLineEdit(search_box)
        self.txt_search.setPlaceholderText("이름 또는 전화번호")
        self.txt_search.setFont(QFont("Inter", 12))
        self.txt_search.setStyleSheet("border: none; background: transparent; color: #000000;")
        self.txt_search.textChanged.connect(self.filter_sales_data)

        search_l.addWidget(lbl_search_icon)
        search_l.addWidget(self.txt_search, 1)

        date_box = QFrame(outer_container)
        date_box.setFixedHeight(42)
        date_box.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        date_box.setAttribute(Qt.WA_StyledBackground, True)

        date_l = QHBoxLayout(date_box)
        date_l.setContentsMargins(12, 0, 12, 0)
        date_l.setSpacing(10)

        lbl_date_title = QLabel("결제일 :", date_box)
        lbl_date_title.setFont(QFont("Inter", 11, QFont.Bold))
        lbl_date_title.setStyleSheet("background: transparent; color: #333333;")

        self.date_filter = QDateEdit(date_box)
        self.date_filter.setDisplayFormat("yyyy-MM-dd")
        self.date_filter.setFont(QFont("Inter", 11))
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setDate(QDate.currentDate())
        
        cal = self.date_filter.calendarWidget()
        if cal:
            cal.setNavigationBarVisible(True)

        self.date_filter.setStyleSheet(f"""
            QDateEdit {{
                border: none;
                background: transparent;
                color: #000000;
            }}
            QCalendarWidget QWidget#qt_calendar_navigationbar {{
                background-color: {Colors.PRIMARY};
                min-height: 40px;
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
                selection-background-color: {Colors.PRIMARY};
                selection-color: #FFFFFF;
                font-size: 12px;
            }}
            QCalendarWidget QAbstractItemView::item:hover {{
                background-color: #666666;
                color: #FFFFFF;
            }}
            QCalendarWidget QWidget#qt_calendar_calendarview {{
                background-color: #FFFFFF;
            }}
        """)

        btn_clear_date = QPushButton("전체보기", date_box)
        btn_clear_date.setFixedSize(70, 28)
        btn_clear_date.setCursor(Qt.PointingHandCursor)
        btn_clear_date.setFont(QFont("Inter", 10, QFont.Bold))
        btn_clear_date.setStyleSheet("""
            QPushButton {
                background-color: #E0E0E0;
                color: #333333;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #C0C0C0;
            }
        """)
        btn_clear_date.clicked.connect(self.reset_date_filter)

        self.date_filter.dateChanged.connect(self.filter_sales_data)

        date_l.addWidget(lbl_date_title)
        date_l.addWidget(self.date_filter, 1)
        date_l.addWidget(btn_clear_date)

        filter_layout.addWidget(search_box, 1)
        filter_layout.addWidget(date_box, 1)
        outer_layout.addLayout(filter_layout)

        # 2. 결제 목록 테이블
        table_container = QFrame(outer_container)
        table_container.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        table_container.setAttribute(Qt.WA_StyledBackground, True)

        t_layout = QVBoxLayout(table_container)
        t_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(table_container)

        header = RoundedHeader(Qt.Horizontal, self.table)
        header.setFixedHeight(40)
        self.table.setHorizontalHeader(header)

        headers = ["번호", "고객이름", "전화번호", "시술메뉴", "결제수단", "결제금액", "결제일시", "적립포인트", "시술시간", "시술자"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.table.setStyleSheet("""
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
                padding: 8px 4px;
            }
            QTableWidget::item:selected {
                background-color: #E8F5E9;
                color: #000000;
                font-weight: bold;
            }
            QToolTip {
                background-color: #FFFFFF;
                color: #000000;
                border: 1px solid #C0C0C0;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
                font-family: Inter, sans-serif;
            }
        """)
        
        # 💡 [핵심] 컬럼 가로폭 개별 최적화
        h_header = self.table.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.Stretch)
        

        # 1: 고객이름 (120px 고정)
        h_header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 120)

        # 2: 전화번호 (140px 고정)
        h_header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(2, 140)

        # 3: 시술메뉴 (120px 고정)
        h_header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(3, 120)

        # 4: 결제수단 (100px 고정)
        h_header.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(4, 100)

        # 5: 결제금액 (130px 고정)
        h_header.setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(5, 130)

        # 6: 결제일시 (150px 고정 확보하여 날짜+시간 출력 보장)
        h_header.setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 150)



        self.table.setMouseTracking(True)
        self.table.cellEntered.connect(self.on_cell_entered)

        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        t_layout.addWidget(self.table)

        outer_layout.addWidget(table_container, 1)
        main_layout.addWidget(outer_container, 1)

        # 3. 하단 결제 정보 삭제 버튼
        self.btn_delete = QPushButton("결제 정보 삭제", self)
        self.btn_delete.setFixedSize(220, 48)
        self.btn_delete.setFont(QFont("Inter", 13, QFont.Bold))
        self.btn_delete.clicked.connect(self.confirm_and_delete_sale)
        
        main_layout.addWidget(self.btn_delete, 0, Qt.AlignCenter)

        self.update_delete_button_state(False)

    def on_cell_entered(self, row: int, col: int):
        item = self.table.item(row, col)
        if item and item.toolTip():
            QToolTip.showText(QCursor.pos(), item.toolTip(), self.table)
        else:
            QToolTip.hideText()

    def update_delete_button_state(self, enabled: bool):
        self.btn_delete.setEnabled(enabled)
        if enabled:
            self.btn_delete.setCursor(Qt.PointingHandCursor)
            self.btn_delete.setStyleSheet(f"""
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
        else:
            self.btn_delete.setCursor(Qt.ArrowCursor)
            self.btn_delete.setStyleSheet("""
                QPushButton {
                    background-color: #888888;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 8px;
                }
            """)

    def reset_date_filter(self):
        self.date_filter.blockSignals(True)
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.blockSignals(False)
        self.load_sales_data(use_date_filter=False)

    def load_sales_data(self, use_date_filter: bool = True):
        query = self.txt_search.text().strip()
        date_str = self.date_filter.date().toString("yyyy-MM-dd") if use_date_filter else ""

        self.sales_list = self.db_manager.get_sales_cancel_list(query=query, date_str=date_str)
        self.render_table()

    def filter_sales_data(self):
        self.load_sales_data(use_date_filter=True)

    def render_table(self):
        self.table.setRowCount(0)
        self.selected_sale = None
        self.update_delete_button_state(False)

        total_count = len(self.sales_list)
        for idx, sale in enumerate(self.sales_list):
            self.table.insertRow(idx)

            display_no = str(total_count - idx)
            sale["display_no"] = display_no

            item_no = QTableWidgetItem(display_no)
            item_no.setTextAlignment(Qt.AlignCenter)
            item_no.setData(Qt.UserRole, sale)
            self.table.setItem(idx, 0, item_no)

            item_name = QTableWidgetItem(sale["customer_name"])
            item_name.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(idx, 1, item_name)

            item_phone = QTableWidgetItem(sale["customer_phone"])
            item_phone.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(idx, 2, item_phone)

            services_text = sale["services"]
            svc_list = sale.get("services_list", [])

            if not svc_list and services_text and services_text != "-":
                svc_list = [s.strip() for s in re.split(r',\s*(?=[^\d])', services_text) if s.strip()]

            item_svc = QTableWidgetItem(services_text)
            item_svc.setTextAlignment(Qt.AlignCenter)

            if svc_list:
                formatted_items = "<br>".join([f"• {s}" for s in svc_list])
                tooltip_html = (
                    f"<div style='font-family: Inter, sans-serif; font-size: 12px; "
                    f"line-height: 160%; color: #000000; background-color: #FFFFFF; "
                    f"padding: 4px 6px; border-radius: 4px; white-space: nowrap; text-align: left;'>"
                    f"{formatted_items}</div>"
                )
                item_svc.setToolTip(tooltip_html)

            self.table.setItem(idx, 3, item_svc)

            item_method = QTableWidgetItem(sale["payment_method"])
            item_method.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(idx, 4, item_method)

            item_amt = QTableWidgetItem(f"{sale['total_amount']:,}")
            item_amt.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(idx, 5, item_amt)

            item_date = QTableWidgetItem(sale["visit_date"])
            item_date.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(idx, 6, item_date)

            item_earn = QTableWidgetItem(f"{sale['earned_point']:,} P")
            item_earn.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(idx, 7, item_earn)

            item_dur = QTableWidgetItem(sale["duration_str"])
            item_dur.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(idx, 8, item_dur)

            item_des = QTableWidgetItem(sale["designer_info"])
            item_des.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(idx, 9, item_des)

    def on_selection_changed(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            self.selected_sale = None
            self.update_delete_button_state(False)
            return

        row = self.table.currentRow()
        item_no = self.table.item(row, 0)
        if item_no:
            self.selected_sale = item_no.data(Qt.UserRole)
            self.update_delete_button_state(True)

    def confirm_and_delete_sale(self):
        if not self.selected_sale:
            return

        dialog = ConfirmCancelSaleDialog(self.selected_sale, self)
        if dialog.exec() == QDialog.Accepted:
            visit_id = self.selected_sale["visit_id"]
            success, msg = self.db_manager.cancel_sale_transaction(visit_id)
            if success:
                self.load_sales_data(use_date_filter=False)
            else:
                from ui.sales_registration_view import CustomAlertDialog
                CustomAlertDialog("오류", msg, self).exec()