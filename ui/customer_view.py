from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QFrame, QMessageBox, QAbstractItemView, QDialog, QStackedWidget,
    QTextEdit, QProgressBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ui.theme import Colors, Styles, get_icon
from core.db_manager import DBManager


class ConfirmCustomerDeleteDialog(QDialog):
    """와이어프레임 1:1 매칭 고객 삭제 확인 팝업 모달"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("고객 삭제 확인")
        self.setFixedSize(380, 180)
        self.setStyleSheet("background-color: #FFFFFF;")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 25)
        layout.setSpacing(25)

        lbl_msg = QLabel("해당 고객을 정말로 <span style='color:#E53E3E; font-weight:bold;'>삭제</span> 하시겠습니까?", self)
        lbl_msg.setFont(QFont("Inter", 14, QFont.Bold))
        lbl_msg.setAlignment(Qt.AlignCenter)
        lbl_msg.setStyleSheet("color: #000000; background: transparent;")
        layout.addWidget(lbl_msg)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        btn_confirm = QPushButton("확인", self)
        btn_confirm.setFixedHeight(42)
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
                background-color: #F0FDF4;
            }}
        """)
        btn_confirm.clicked.connect(self.accept)

        btn_cancel = QPushButton("취소", self)
        btn_cancel.setFixedHeight(42)
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

        layout.addLayout(btn_layout)


class CustomerView(QWidget):
    """고객 관리 메인 뷰"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DBManager()
        self.selected_customer_id = None
        self.all_customers = []

        self.setup_ui()
        self.load_customer_list()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(25, 15, 25, 25)
        main_layout.setSpacing(20)

        # -------------------------------------------------------------
        # 1. 좌측 고객 목록 패널 (가로 비율 2)
        # -------------------------------------------------------------
        left_outer = QFrame(self)
        left_outer.setStyleSheet("""
            QFrame {
                background-color: #DCDCDC;
                border-radius: 10px;
            }
        """)
        left_outer.setAttribute(Qt.WA_StyledBackground, True)

        left_layout = QVBoxLayout(left_outer)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(8)

        # 1.1 상단 검색바
        search_box = QFrame(left_outer)
        search_box.setFixedHeight(42)
        search_box.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 6px;
            }
        """)
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
        self.txt_search.setStyleSheet("""
            QLineEdit {
                border: none;
                background-color: transparent;
                color: #000000;
            }
        """)
        self.txt_search.textChanged.connect(self.filter_customer_list)

        search_layout.addWidget(lbl_search_icon)
        search_layout.addWidget(self.txt_search, 1)

        left_layout.addWidget(search_box)

        # 1.2 테이블 위젯
        table_container = QFrame(left_outer)
        table_container.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 6px;
            }
        """)
        table_container.setAttribute(Qt.WA_StyledBackground, True)

        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(table_container)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["번호", "이름", "전화번호", "최근 방문일자"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: none;
                background-color: #FFFFFF;
                border-radius: 6px;
                font-size: 13px;
                color: #000000;
                outline: none;
            }}
            QHeaderView {{
                background-color: transparent;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            QHeaderView::section {{
                background-color: {Colors.PRIMARY};
                color: #FFFFFF;
                font-weight: bold;
                font-size: 13px;
                border: none;
                height: 40px;
                text-align: center;
            }}
            QHeaderView::section:first {{
                border-top-left-radius: 6px;
            }}
            QHeaderView::section:last {{
                border-top-right-radius: 6px;
            }}
            QTableWidget::item {{
                border-bottom: 1px solid #E0E0E0;
                padding: 8px;
                outline: none;
            }}
            QTableWidget::item:focus {{
                border-bottom: 1px solid #E0E0E0;
                outline: none;
            }}
            QTableWidget::item:selected {{
                background-color: #E8F5E9;
                color: #000000;
                font-weight: bold;
                outline: none;
            }}
            QScrollBar:vertical {{
                border: none;
                background: #F2F2F2;
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: #C0C0C0;
                min-height: 25px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Colors.PRIMARY};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)

        self.table.itemSelectionChanged.connect(self.on_table_selection_changed)
        table_layout.addWidget(self.table)

        left_layout.addWidget(table_container, 1)
        main_layout.addWidget(left_outer, 2)

        # -------------------------------------------------------------
        # 2. 우측 스택 영역 (가로 비율 3)
        # -------------------------------------------------------------
        self.right_container = QWidget(self)
        right_main_layout = QVBoxLayout(self.right_container)
        right_main_layout.setContentsMargins(0, 0, 0, 0)
        right_main_layout.setSpacing(10)

        # 2.1 Stacked Widget
        self.right_stack = QStackedWidget(self.right_container)
        
        # -------------------------------------------------------------
        # Page 0: 신규 고객 등록 화면 (폭 400px 고정 & 타이틀 상단 밀착)
        # -------------------------------------------------------------
        page_reg = QWidget()
        page_reg_layout = QVBoxLayout(page_reg)
        page_reg_layout.setContentsMargins(0, 0, 0, 0)

        page_reg_layout.addStretch(1)

        # 폭 400px 고정 컨테이너 (과도한 좌우 확장 방지)
        reg_container = QWidget(page_reg)
        reg_container.setFixedWidth(400)
        reg_layout = QVBoxLayout(reg_container)
        reg_layout.setContentsMargins(0, 0, 0, 0)
        reg_layout.setSpacing(16)

        # 신규 고객 등록 타이틀 (입력란 바로 위 배치)
        lbl_reg_title = QLabel("신규 고객 등록", reg_container)
        lbl_reg_title.setFont(QFont("Inter", 20, QFont.Bold))
        lbl_reg_title.setStyleSheet("color: #000000; background: transparent;")
        lbl_reg_title.setAlignment(Qt.AlignCenter)
        reg_layout.addWidget(lbl_reg_title)

        reg_outer = QFrame(reg_container)
        reg_outer.setStyleSheet("""
            QFrame {
                background-color: #DCDCDC;
                border-radius: 10px;
            }
        """)
        reg_outer.setAttribute(Qt.WA_StyledBackground, True)

        reg_outer_layout = QVBoxLayout(reg_outer)
        reg_outer_layout.setContentsMargins(8, 8, 8, 8)

        reg_inner = QFrame(reg_outer)
        reg_inner.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 6px;
            }
        """)
        reg_inner.setAttribute(Qt.WA_StyledBackground, True)

        inner_layout = QVBoxLayout(reg_inner)
        inner_layout.setContentsMargins(25, 30, 25, 30)
        inner_layout.setSpacing(22)

        # 공통 언더라인 행 스타일
        row_qss = """
            QFrame {
                border: none;
                border-bottom: 1.5px solid #7A7A7A;
                border-radius: 0px;
                background-color: transparent;
            }
            QLabel, QLineEdit {
                border: none;
                background: transparent;
            }
        """

        # 이름 입력
        frame_name = QFrame(reg_inner)
        frame_name.setStyleSheet(row_qss)
        row_name = QHBoxLayout(frame_name)
        row_name.setContentsMargins(0, 0, 0, 4)
        lbl_name = QLabel("이름<sup style='color:red;'>*</sup> :", frame_name)
        lbl_name.setFont(QFont("Inter", 12, QFont.Bold))
        lbl_name.setStyleSheet("color: #000000; background: transparent;")
        
        self.txt_reg_name = QLineEdit(frame_name)
        self.txt_reg_name.setPlaceholderText("예) 홍길동")
        self.txt_reg_name.setFont(QFont("Inter", 12))
        self.txt_reg_name.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.txt_reg_name.setStyleSheet("color: #000000; padding: 0px;")

        row_name.addWidget(lbl_name)
        row_name.addWidget(self.txt_reg_name, 1)
        inner_layout.addWidget(frame_name)

        # 전화번호 입력
        frame_phone = QFrame(reg_inner)
        frame_phone.setStyleSheet(row_qss)
        row_phone = QHBoxLayout(frame_phone)
        row_phone.setContentsMargins(0, 0, 0, 4)
        lbl_phone = QLabel("전화번호<sup style='color:red;'>*</sup> :", frame_phone)
        lbl_phone.setFont(QFont("Inter", 12, QFont.Bold))
        lbl_phone.setStyleSheet("color: #000000; background: transparent;")

        self.txt_reg_phone = QLineEdit(frame_phone)
        self.txt_reg_phone.setPlaceholderText("예) 010-1234-5678")
        self.txt_reg_phone.setFont(QFont("Inter", 12))
        self.txt_reg_phone.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.txt_reg_phone.setStyleSheet("color: #000000; padding: 0px;")
        self.txt_reg_phone.textChanged.connect(lambda t: self.format_phone_number(self.txt_reg_phone, t))

        row_phone.addWidget(lbl_phone)
        row_phone.addWidget(self.txt_reg_phone, 1)
        inner_layout.addWidget(frame_phone)

        # 메모 입력
        frame_memo = QFrame(reg_inner)
        frame_memo.setStyleSheet(row_qss)
        row_memo = QHBoxLayout(frame_memo)
        row_memo.setContentsMargins(0, 0, 0, 4)
        lbl_memo = QLabel("메모 :", frame_memo)
        lbl_memo.setFont(QFont("Inter", 12, QFont.Bold))
        lbl_memo.setStyleSheet("color: #000000; background: transparent;")

        self.txt_reg_memo = QLineEdit(frame_memo)
        self.txt_reg_memo.setPlaceholderText("자유롭게 작성하세요")
        self.txt_reg_memo.setFont(QFont("Inter", 12))
        self.txt_reg_memo.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.txt_reg_memo.setStyleSheet("color: #000000; padding: 0px;")

        row_memo.addWidget(lbl_memo)
        row_memo.addWidget(self.txt_reg_memo, 1)
        inner_layout.addWidget(frame_memo)

        reg_outer_layout.addWidget(reg_inner)
        reg_layout.addWidget(reg_outer)

        self.btn_register = QPushButton("등록하기", reg_container)
        self.btn_register.setFixedHeight(48)
        self.btn_register.setCursor(Qt.PointingHandCursor)
        self.btn_register.setFont(QFont("Inter", 13, QFont.Bold))
        self.btn_register.setStyleSheet(f"""
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
        self.btn_register.clicked.connect(self.save_new_customer)
        reg_layout.addWidget(self.btn_register)

        page_reg_layout.addWidget(reg_container, 0, Qt.AlignCenter)
        page_reg_layout.addStretch(1)
        self.right_stack.addWidget(page_reg)

        # -------------------------------------------------------------
        # Page 1: 고객 정보 상세 / 방문 및 통계 화면
        # -------------------------------------------------------------
        page_detail = QWidget()
        page_detail_layout = QVBoxLayout(page_detail)
        page_detail_layout.setContentsMargins(0, 0, 0, 0)
        page_detail_layout.setSpacing(10)

        # 헤더 (+ 버튼 / 고객 정보 조회 타이틀)
        detail_header = QHBoxLayout()
        lbl_detail_title = QLabel("고객 정보 조회", page_detail)
        lbl_detail_title.setFont(QFont("Inter", 20, QFont.Bold))
        lbl_detail_title.setStyleSheet("color: #000000; background: transparent;")

        btn_plus = QPushButton("+", page_detail)
        btn_plus.setFixedSize(36, 30)
        btn_plus.setCursor(Qt.PointingHandCursor)
        btn_plus.setFont(QFont("Inter", 16, QFont.Bold))
        btn_plus.setStyleSheet(f"""
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
        btn_plus.clicked.connect(self.reset_form)

        detail_header.addWidget(lbl_detail_title, 1, Qt.AlignCenter)
        detail_header.addWidget(btn_plus, 0, Qt.AlignRight)
        page_detail_layout.addLayout(detail_header)

        # 탭 버튼 그룹
        tab_button_layout = QHBoxLayout()
        tab_button_layout.setSpacing(8)

        self.btn_tab_info = QPushButton("상세정보", page_detail)
        self.btn_tab_info.setFixedHeight(36)
        self.btn_tab_info.setCursor(Qt.PointingHandCursor)
        self.btn_tab_info.setFont(QFont("Inter", 12, QFont.Bold))

        self.btn_tab_stats = QPushButton("방문 및 통계", page_detail)
        self.btn_tab_stats.setFixedHeight(36)
        self.btn_tab_stats.setCursor(Qt.PointingHandCursor)
        self.btn_tab_stats.setFont(QFont("Inter", 12, QFont.Bold))

        self.btn_tab_info.clicked.connect(lambda: self.switch_detail_tab(0))
        self.btn_tab_stats.clicked.connect(lambda: self.switch_detail_tab(1))

        tab_button_layout.addWidget(self.btn_tab_info, 1)
        tab_button_layout.addWidget(self.btn_tab_stats, 1)
        page_detail_layout.addLayout(tab_button_layout)

        # 탭 스택 (0: 상세정보, 1: 방문 및 통계)
        self.detail_tab_stack = QStackedWidget(page_detail)

        # Tab 0: 상세 정보
        tab0_widget = QWidget()
        tab0_layout = QVBoxLayout(tab0_widget)
        tab0_layout.setContentsMargins(0, 0, 0, 0)
        tab0_layout.setSpacing(12)

        tab0_outer = QFrame(tab0_widget)
        tab0_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        tab0_outer.setAttribute(Qt.WA_StyledBackground, True)
        tab0_outer_layout = QHBoxLayout(tab0_outer)
        tab0_outer_layout.setContentsMargins(8, 8, 8, 8)
        tab0_outer_layout.setSpacing(8)

        # 좌측 고객 기본 정보
        tab0_left_inner = QFrame(tab0_outer)
        tab0_left_inner.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        tab0_left_inner.setAttribute(Qt.WA_StyledBackground, True)
        left_info_layout = QVBoxLayout(tab0_left_inner)
        left_info_layout.setContentsMargins(15, 20, 15, 20)
        left_info_layout.setSpacing(18)

        # 고객번호
        f_id = QFrame(tab0_left_inner)
        f_id.setStyleSheet(row_qss)
        r_id = QHBoxLayout(f_id)
        r_id.setContentsMargins(0, 0, 0, 4)
        lbl_id = QLabel("고객번호 :", f_id)
        lbl_id.setFont(QFont("Inter", 11, QFont.Bold))
        self.lbl_info_id = QLabel("-", f_id)
        self.lbl_info_id.setFont(QFont("Inter", 11))
        self.lbl_info_id.setAlignment(Qt.AlignRight)
        r_id.addWidget(lbl_id)
        r_id.addWidget(self.lbl_info_id, 1)
        left_info_layout.addWidget(f_id)

        # 이름
        f_name = QFrame(tab0_left_inner)
        f_name.setStyleSheet(row_qss)
        r_name = QHBoxLayout(f_name)
        r_name.setContentsMargins(0, 0, 0, 4)
        lbl_name = QLabel("이 름 :", f_name)
        lbl_name.setFont(QFont("Inter", 11, QFont.Bold))
        self.txt_info_name = QLineEdit(f_name)
        self.txt_info_name.setFont(QFont("Inter", 11))
        self.txt_info_name.setAlignment(Qt.AlignRight)
        r_name.addWidget(lbl_name)
        r_name.addWidget(self.txt_info_name, 1)
        left_info_layout.addWidget(f_name)

        # 전화번호
        f_phone = QFrame(tab0_left_inner)
        f_phone.setStyleSheet(row_qss)
        r_phone = QHBoxLayout(f_phone)
        r_phone.setContentsMargins(0, 0, 0, 4)
        lbl_phone = QLabel("전화번호 :", f_phone)
        lbl_phone.setFont(QFont("Inter", 11, QFont.Bold))
        self.txt_info_phone = QLineEdit(f_phone)
        self.txt_info_phone.setFont(QFont("Inter", 11))
        self.txt_info_phone.setAlignment(Qt.AlignRight)
        self.txt_info_phone.textChanged.connect(lambda t: self.format_phone_number(self.txt_info_phone, t))
        r_phone.addWidget(lbl_phone)
        r_phone.addWidget(self.txt_info_phone, 1)
        left_info_layout.addWidget(f_phone)

        # 포인트
        f_point = QFrame(tab0_left_inner)
        f_point.setStyleSheet(row_qss)
        r_point = QHBoxLayout(f_point)
        r_point.setContentsMargins(0, 0, 0, 4)
        lbl_point = QLabel("포인트 :", f_point)
        lbl_point.setFont(QFont("Inter", 11, QFont.Bold))
        self.lbl_info_point = QLabel("0P", f_point)
        self.lbl_info_point.setFont(QFont("Inter", 11, QFont.Bold))
        self.lbl_info_point.setAlignment(Qt.AlignRight)
        r_point.addWidget(lbl_point)
        r_point.addWidget(self.lbl_info_point, 1)
        left_info_layout.addWidget(f_point)

        left_info_layout.addStretch(1)
        tab0_outer_layout.addWidget(tab0_left_inner, 1)

        # 우측 메모 박스
        tab0_right_inner = QFrame(tab0_outer)
        tab0_right_inner.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        tab0_right_inner.setAttribute(Qt.WA_StyledBackground, True)
        right_memo_layout = QVBoxLayout(tab0_right_inner)
        right_memo_layout.setContentsMargins(12, 12, 12, 12)
        right_memo_layout.setSpacing(8)

        lbl_memo_title = QLabel("메모 :", tab0_right_inner)
        lbl_memo_title.setFont(QFont("Inter", 11, QFont.Bold))
        lbl_memo_title.setStyleSheet("color: #000000; border: none; background: transparent;")
        right_memo_layout.addWidget(lbl_memo_title)

        self.txt_info_memo = QTextEdit(tab0_right_inner)
        self.txt_info_memo.setPlaceholderText("고객 관련 특이사항 및 메모 입력")
        self.txt_info_memo.setFont(QFont("Inter", 11))
        self.txt_info_memo.setStyleSheet("border: none; background: transparent;")
        right_memo_layout.addWidget(self.txt_info_memo, 1)

        tab0_outer_layout.addWidget(tab0_right_inner, 1)
        tab0_layout.addWidget(tab0_outer, 1)

        # 하단 수정 / 삭제 버튼 그룹 (삭제 버튼 빨간색 반영)
        btn_action_layout = QHBoxLayout()
        btn_action_layout.setSpacing(10)

        self.btn_update = QPushButton("고객 정보 수정", tab0_widget)
        self.btn_update.setFixedHeight(44)
        self.btn_update.setCursor(Qt.PointingHandCursor)
        self.btn_update.setFont(QFont("Inter", 12, QFont.Bold))
        self.btn_update.setStyleSheet(f"""
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
        self.btn_update.clicked.connect(self.update_customer_info)

        self.btn_delete = QPushButton("고객 정보 삭제", tab0_widget)
        self.btn_delete.setFixedHeight(44)
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        self.btn_delete.setFont(QFont("Inter", 12, QFont.Bold))
        self.btn_delete.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.DANGER};
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: #B30000;
            }}
        """)
        self.btn_delete.clicked.connect(self.delete_customer_info)

        btn_action_layout.addWidget(self.btn_update, 1)
        btn_action_layout.addWidget(self.btn_delete, 1)
        tab0_layout.addLayout(btn_action_layout)

        self.detail_tab_stack.addWidget(tab0_widget)

        # Tab 1: 방문 및 통계
        tab1_widget = QWidget()
        tab1_layout = QVBoxLayout(tab1_widget)
        tab1_layout.setContentsMargins(0, 0, 0, 0)
        tab1_layout.setSpacing(10)

        self.visit_table = QTableWidget(tab1_widget)
        self.visit_table.setColumnCount(5)
        self.visit_table.setHorizontalHeaderLabels(["고객이름", "결제일", "결제금액", "시술", "시술자"])
        self.visit_table.setFixedHeight(140)
        self.visit_table.verticalHeader().setVisible(False)
        self.visit_table.setShowGrid(False)
        self.visit_table.setFocusPolicy(Qt.NoFocus)
        self.visit_table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid #E0E0E0;
                background-color: #FFFFFF;
                border-radius: 6px;
                font-size: 11px;
                color: #000000;
            }}
            QHeaderView::section {{
                background-color: {Colors.PRIMARY};
                color: #FFFFFF;
                font-weight: bold;
                font-size: 11px;
                border: none;
                height: 28px;
                text-align: center;
            }}
            QTableWidget::item {{
                border-bottom: 1px solid #E0E0E0;
                padding: 4px;
            }}
        """)
        v_header = self.visit_table.horizontalHeader()
        v_header.setSectionResizeMode(QHeaderView.Stretch)
        tab1_layout.addWidget(self.visit_table)

        stats_bottom_layout = QHBoxLayout()
        stats_bottom_layout.setSpacing(10)

        pref_card = QFrame(tab1_widget)
        pref_card.setStyleSheet("background-color: #FFFFFF; border-radius: 6px; border: 1px solid #E0E0E0;")
        pref_layout = QVBoxLayout(pref_card)
        pref_layout.setContentsMargins(10, 10, 10, 10)
        
        lbl_pref_title = QLabel("시술 선호도 분석", pref_card)
        lbl_pref_title.setFont(QFont("Inter", 11, QFont.Bold))
        pref_layout.addWidget(lbl_pref_title)

        self.pref_container = QVBoxLayout()
        self.pref_container.setSpacing(6)
        pref_layout.addLayout(self.pref_container)
        pref_layout.addStretch(1)

        stats_bottom_layout.addWidget(pref_card, 1)

        summary_layout = QVBoxLayout()
        summary_layout.setSpacing(6)

        self.card_visits = self._create_stat_card("총 방문 횟수", "0회")
        self.card_total = self._create_stat_card("총 결제 금액", "0원")
        self.card_avg = self._create_stat_card("평균 결제 금액", "0원")

        summary_layout.addWidget(self.card_visits)
        summary_layout.addWidget(self.card_total)
        summary_layout.addWidget(self.card_avg)

        stats_bottom_layout.addLayout(summary_layout, 1)
        tab1_layout.addLayout(stats_bottom_layout)

        self.detail_tab_stack.addWidget(tab1_widget)

        page_detail_layout.addWidget(self.detail_tab_stack)
        self.right_stack.addWidget(page_detail)

        right_main_layout.addWidget(self.right_stack)
        main_layout.addWidget(self.right_container, 3)

        self.switch_detail_tab(0)

    def _create_stat_card(self, title: str, default_val: str) -> QFrame:
        card = QFrame(self)
        card.setStyleSheet("background-color: #FFFFFF; border-radius: 6px; border: 1px solid #E0E0E0;")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        lbl_t = QLabel(title, card)
        lbl_t.setFont(QFont("Inter", 10, QFont.Bold))
        lbl_t.setStyleSheet("color: #555555; border: none;")

        lbl_v = QLabel(default_val, card)
        lbl_v.setObjectName("val_label")
        lbl_v.setFont(QFont("Inter", 12, QFont.Bold))
        lbl_v.setAlignment(Qt.AlignCenter)
        lbl_v.setStyleSheet("color: #000000; border: none;")

        layout.addWidget(lbl_t)
        layout.addWidget(lbl_v)
        return card

    def update_stat_card_val(self, card: QFrame, val: str):
        lbl = card.findChild(QLabel, "val_label")
        if lbl:
            lbl.setText(val)

    def switch_detail_tab(self, index: int):
        """상세정보 / 방문 및 통계 탭 전환"""
        self.detail_tab_stack.setCurrentIndex(index)
        if index == 0:
            self.btn_tab_info.setStyleSheet(f"""
                background-color: {Colors.PRIMARY};
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            """)
            self.btn_tab_stats.setStyleSheet("""
                background-color: #E0E0E0;
                color: #333333;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            """)
        else:
            self.btn_tab_stats.setStyleSheet(f"""
                background-color: {Colors.PRIMARY};
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            """)
            self.btn_tab_info.setStyleSheet("""
                background-color: #E0E0E0;
                color: #333333;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            """)

    def showEvent(self, event):
        super().showEvent(event)
        self.update_table_column_widths()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_table_column_widths()

    def update_table_column_widths(self):
        """테이블 1.5 : 2.5 : 3 : 3 비율 지정"""
        total_width = self.table.viewport().width()
        if total_width > 0:
            w0 = int(total_width * 0.15)
            w1 = int(total_width * 0.25)
            w2 = int(total_width * 0.30)
            w3 = total_width - (w0 + w1 + w2)

            self.table.setColumnWidth(0, w0)
            self.table.setColumnWidth(1, w1)
            self.table.setColumnWidth(2, w2)
            self.table.setColumnWidth(3, w3)

    def format_phone_number(self, line_edit: QLineEdit, text: str):
        """전화번호 입력 시 자동 하이픈(-) 포맷팅"""
        digits = "".join(filter(str.isdigit, text))
        if len(digits) > 11:
            digits = digits[:11]

        formatted = digits
        if digits.startswith("02"):
            if len(digits) <= 2:
                formatted = digits
            elif len(digits) <= 5:
                formatted = f"{digits[:2]}-{digits[2:]}"
            elif len(digits) <= 9:
                formatted = f"{digits[:2]}-{digits[2:-4]}-{digits[-4:]}"
            else:
                formatted = f"{digits[:2]}-{digits[2:6]}-{digits[6:]}"
        else:
            if len(digits) <= 3:
                formatted = digits
            elif len(digits) <= 7:
                formatted = f"{digits[:3]}-{digits[3:]}"
            else:
                formatted = f"{digits[:3]}-{digits[3:-4]}-{digits[-4:]}"

        line_edit.blockSignals(True)
        line_edit.setText(formatted)
        line_edit.blockSignals(False)

    def load_customer_list(self):
        """DB에서 활성 고객 목록을 조회하여 테이블에 로드"""
        self.all_customers = self.db_manager.get_all_customers()
        self.filter_customer_list()

    def filter_customer_list(self):
        """검색어(이름/전화번호) 기반 실시간 필터링"""
        query = self.txt_search.text().strip().lower()
        self.table.setRowCount(0)

        row_count = 0
        for cust in self.all_customers:
            name = cust["name"]
            phone = cust["phone"]

            if query and (query not in name.lower() and query not in phone.lower()):
                continue

            self.table.insertRow(row_count)

            item_no = QTableWidgetItem(str(row_count + 1))
            item_no.setTextAlignment(Qt.AlignCenter)
            item_no.setData(Qt.UserRole, cust["id"])
            self.table.setItem(row_count, 0, item_no)

            item_name = QTableWidgetItem(name)
            item_name.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_count, 1, item_name)

            item_phone = QTableWidgetItem(phone)
            item_phone.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_count, 2, item_phone)

            item_recent = QTableWidgetItem(cust["recent_visit"])
            item_recent.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_count, 3, item_recent)

            row_count += 1

    def on_table_selection_changed(self):
        """테이블 행 선택 시 우측 영역을 '고객 정보 조회' 화면으로 전환 및 데이터 동기화"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            return

        row = self.table.currentRow()
        item_id = self.table.item(row, 0)
        if not item_id:
            return

        cust_id = item_id.data(Qt.UserRole)
        target_cust = next((c for c in self.all_customers if int(c["id"]) == int(cust_id)), None)
        if not target_cust:
            return

        self.selected_customer_id = int(cust_id)

        self.lbl_info_id.setText(str(target_cust["id"]))
        self.txt_info_name.setText(target_cust["name"])
        self.txt_info_phone.setText(target_cust["phone"])
        self.lbl_info_point.setText(f"{target_cust['point']:,}P")
        self.txt_info_memo.setText(target_cust["memo"])

        self.right_stack.setCurrentIndex(1)
        self.load_customer_stats(self.selected_customer_id)

    def reselect_customer(self, customer_id: int):
        """목록 갱신 후 해당 고객 행 자동 재선택하여 우측 상세 뷰 갱신"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and int(item.data(Qt.UserRole)) == int(customer_id):
                self.table.selectRow(row)
                break

    def load_customer_stats(self, customer_id: int):
        """고객 방문 이력 및 선호도 통계 갱신"""
        history = self.db_manager.get_customer_visit_history(customer_id)
        self.visit_table.setRowCount(0)
        for idx, item in enumerate(history):
            self.visit_table.insertRow(idx)
            self.visit_table.setItem(idx, 0, QTableWidgetItem(item["customer_name"]))
            self.visit_table.setItem(idx, 1, QTableWidgetItem(item["visit_date"]))
            self.visit_table.setItem(idx, 2, QTableWidgetItem(item["amount"]))
            self.visit_table.setItem(idx, 3, QTableWidgetItem(item["services"]))
            self.visit_table.setItem(idx, 4, QTableWidgetItem(item["designer"]))

        stats = self.db_manager.get_customer_stats(customer_id)
        self.update_stat_card_val(self.card_visits, f"{stats['total_visits']}회")
        self.update_stat_card_val(self.card_total, f"{stats['total_amount']:,}원")
        self.update_stat_card_val(self.card_avg, f"{stats['avg_amount']:,}원")

        while self.pref_container.count():
            item = self.pref_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        prefs = stats["preferences"]
        max_cnt = max([p["count"] for p in prefs], default=1) if prefs else 1

        for p in prefs:
            row_w = QWidget()
            row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(0, 0, 0, 0)
            row_l.setSpacing(6)

            lbl_cat = QLabel(p["category"], row_w)
            lbl_cat.setFont(QFont("Inter", 9, QFont.Bold))
            lbl_cat.setFixedWidth(40)

            pbar = QProgressBar(row_w)
            pbar.setFixedHeight(12)
            pbar.setMaximum(max_cnt)
            pbar.setValue(p["count"])
            pbar.setTextVisible(False)
            pbar.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    background-color: #EFEFEF;
                    border-radius: 6px;
                }}
                QProgressBar::chunk {{
                    background-color: {Colors.PRIMARY};
                    border-radius: 6px;
                }}
            """)

            lbl_cnt = QLabel(f"{p['count']}회", row_w)
            lbl_cnt.setFont(QFont("Inter", 9))
            lbl_cnt.setFixedWidth(30)

            row_l.addWidget(lbl_cat)
            row_l.addWidget(pbar, 1)
            row_l.addWidget(lbl_cnt)

            self.pref_container.addWidget(row_w)

    def reset_form(self):
        """신규 고객 등록 모드로 전환"""
        self.selected_customer_id = None
        self.table.clearSelection()

        self.txt_reg_name.clear()
        self.txt_reg_phone.clear()
        self.txt_reg_memo.clear()

        self.right_stack.setCurrentIndex(0)

    def save_new_customer(self):
        """신규 고객 등록 처리"""
        name = self.txt_reg_name.text().strip()
        phone = self.txt_reg_phone.text().strip()
        memo = self.txt_reg_memo.text().strip()

        if not name:
            QMessageBox.warning(self, "입력 오류", "이름을 입력해 주세요.")
            self.txt_reg_name.setFocus()
            return

        if not phone:
            QMessageBox.warning(self, "입력 오류", "전화번호를 입력해 주세요.")
            self.txt_reg_phone.setFocus()
            return

        success, err_msg = self.db_manager.add_customer(name, phone, memo)
        if success:
            QMessageBox.information(self, "등록 완료", f"'{name}' 고객이 성공적으로 등록되었습니다.")
            self.load_customer_list()
            self.reset_form()
        else:
            QMessageBox.warning(self, "등록 실패", err_msg)

    def update_customer_info(self):
        """고객 정보 수정 처리 (수정 후 재선택을 통해 데이터 동기화)"""
        if self.selected_customer_id is None:
            QMessageBox.warning(self, "선택 오류", "수정할 고객을 먼저 목록에서 선택해 주세요.")
            return

        name = self.txt_info_name.text().strip()
        phone = self.txt_info_phone.text().strip()
        memo = self.txt_info_memo.toPlainText().strip()

        if not name:
            QMessageBox.warning(self, "입력 오류", "이름을 입력해 주세요.")
            self.txt_info_name.setFocus()
            return

        if not phone:
            QMessageBox.warning(self, "입력 오류", "전화번호를 입력해 주세요.")
            self.txt_info_phone.setFocus()
            return

        target_id = int(self.selected_customer_id)
        success, err_msg = self.db_manager.update_customer(target_id, name, phone, memo)
        if success:
            QMessageBox.information(self, "수정 완료", f"'{name}' 고객의 정보가 수정되었습니다.")
            self.load_customer_list()
            self.reselect_customer(target_id)
        else:
            QMessageBox.warning(self, "수정 실패", err_msg)

    def delete_customer_info(self):
        """커스텀 팝업을 통한 고객 논리적 삭제 처리"""
        if self.selected_customer_id is None:
            return

        dialog = ConfirmCustomerDeleteDialog(self)
        if dialog.exec() == QDialog.Accepted:
            if self.db_manager.delete_customer(self.selected_customer_id):
                QMessageBox.information(self, "삭제 완료", "고객 정보가 삭제되었습니다.")
                self.load_customer_list()
                self.reset_form()
            else:
                QMessageBox.critical(self, "오류", "고객 삭제 처리 중 오류가 발생했습니다.")