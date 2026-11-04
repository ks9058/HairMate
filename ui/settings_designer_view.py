from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QFrame, QMessageBox, QAbstractItemView, QDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ui.theme import Colors, Styles, get_icon
from core.db_manager import DBManager


class ConfirmDeleteDialog(QDialog):
    """와이어프레임 디자인 스펙과 1:1 매칭되는 커스텀 삭제 확인 팝업"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("직원 삭제 확인")
        self.setFixedSize(380, 180)
        self.setStyleSheet("background-color: #FFFFFF;")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 25)
        layout.setSpacing(25)

        lbl_msg = QLabel("해당 직원을 정말로 <span style='color:#E53E3E; font-weight:bold;'>삭제</span> 하시겠습니까?", self)
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


class SettingsDesignerView(QWidget):
    """설정 > 디자이너/직원 관리 뷰 (사용자 너비 조절 고정 및 1.5:2.5:3:3 비율 반영)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DBManager()
        self.selected_user_id = None
        self.all_designers = []

        self.setup_ui()
        self.load_designer_list()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(25, 15, 25, 25)
        main_layout.setSpacing(20)

        # -------------------------------------------------------------
        # 1. 좌측 디자이너 목록 & 검색 패널
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

        # 1.1 검색바
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
        self.txt_search.textChanged.connect(self.filter_designer_list)

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
        self.table.setHorizontalHeaderLabels(["번호", "이름", "전화번호", "직급"])
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
            
            /* 세로 커스텀 스크롤바 */
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

        # 사용자가 마우스로 헤더 경계면을 늘리거나 줄이지 못하도록 Fixed 고정
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)

        self.table.itemSelectionChanged.connect(self.on_table_selection_changed)
        table_layout.addWidget(self.table)

        left_layout.addWidget(table_container, 1)
        main_layout.addWidget(left_outer, 3)

        # -------------------------------------------------------------
        # 2. 우측 입력/수정/삭제 폼 패널
        # -------------------------------------------------------------
        right_container = QWidget(self)
        right_container.setFixedWidth(380)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(16)

        right_layout.addStretch(1)

        # 메인 타이틀
        self.lbl_form_title = QLabel("신규 직원 등록", right_container)
        self.lbl_form_title.setFont(QFont("Inter", 20, QFont.Bold))
        self.lbl_form_title.setStyleSheet("color: #000000; background: transparent;")
        self.lbl_form_title.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.lbl_form_title)

        # 회색 둥근 외부 박스
        right_outer = QFrame(right_container)
        right_outer.setStyleSheet("""
            QFrame {
                background-color: #DCDCDC;
                border-radius: 10px;
            }
        """)
        right_outer.setAttribute(Qt.WA_StyledBackground, True)

        right_outer_layout = QVBoxLayout(right_outer)
        right_outer_layout.setContentsMargins(8, 8, 8, 8)

        # 흰색 내부 폼 박스
        right_inner = QFrame(right_outer)
        right_inner.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 6px;
            }
        """)
        right_inner.setAttribute(Qt.WA_StyledBackground, True)

        inner_layout = QVBoxLayout(right_inner)
        inner_layout.setContentsMargins(25, 30, 25, 30)
        inner_layout.setSpacing(22)

        # 2.1 이름 입력 행
        frame_name = QFrame(right_inner)
        frame_name.setStyleSheet("""
            QFrame {
                border: none;
                border-bottom: 1.5px solid #7A7A7A;
                border-radius: 0px;
                background-color: transparent;
            }
        """)
        row_name = QHBoxLayout(frame_name)
        row_name.setContentsMargins(0, 0, 0, 4)
        row_name.setSpacing(10)

        lbl_name = QLabel("이름<sup style='color:red;'>*</sup> :", frame_name)
        lbl_name.setFont(QFont("Inter", 12, QFont.Bold))
        lbl_name.setStyleSheet("color: #000000; border: none; background: transparent;")
        
        self.txt_name = QLineEdit(frame_name)
        self.txt_name.setPlaceholderText("예) 홍길동")
        self.txt_name.setFont(QFont("Inter", 12))
        self.txt_name.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.txt_name.setStyleSheet("""
            QLineEdit {
                border: none;
                background-color: transparent;
                color: #000000;
                padding: 0px;
            }
        """)

        row_name.addWidget(lbl_name)
        row_name.addWidget(self.txt_name, 1)
        inner_layout.addWidget(frame_name)

        # 2.2 전화번호 입력 행
        frame_phone = QFrame(right_inner)
        frame_phone.setStyleSheet("""
            QFrame {
                border: none;
                border-bottom: 1.5px solid #7A7A7A;
                border-radius: 0px;
                background-color: transparent;
            }
        """)
        row_phone = QHBoxLayout(frame_phone)
        row_phone.setContentsMargins(0, 0, 0, 4)
        row_phone.setSpacing(10)

        lbl_phone = QLabel("전화번호<sup style='color:red;'>*</sup> :", frame_phone)
        lbl_phone.setFont(QFont("Inter", 12, QFont.Bold))
        lbl_phone.setStyleSheet("color: #000000; border: none; background: transparent;")

        self.txt_phone = QLineEdit(frame_phone)
        self.txt_phone.setPlaceholderText("예) 010-1234-5678")
        self.txt_phone.setFont(QFont("Inter", 12))
        self.txt_phone.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.txt_phone.setStyleSheet("""
            QLineEdit {
                border: none;
                background-color: transparent;
                color: #000000;
                padding: 0px;
            }
        """)
        self.txt_phone.textChanged.connect(self.on_phone_number_changed)

        row_phone.addWidget(lbl_phone)
        row_phone.addWidget(self.txt_phone, 1)
        inner_layout.addWidget(frame_phone)

        # 2.3 직급 입력 행
        frame_position = QFrame(right_inner)
        frame_position.setStyleSheet("""
            QFrame {
                border: none;
                border-bottom: 1.5px solid #7A7A7A;
                border-radius: 0px;
                background-color: transparent;
            }
        """)
        row_position = QHBoxLayout(frame_position)
        row_position.setContentsMargins(0, 0, 0, 4)
        row_position.setSpacing(10)

        lbl_position = QLabel("직급<sup style='color:red;'>*</sup> :", frame_position)
        lbl_position.setFont(QFont("Inter", 12, QFont.Bold))
        lbl_position.setStyleSheet("color: #000000; border: none; background: transparent;")

        self.txt_position = QLineEdit(frame_position)
        self.txt_position.setPlaceholderText("예) 시니어 디자이너")
        self.txt_position.setFont(QFont("Inter", 12))
        self.txt_position.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.txt_position.setStyleSheet("""
            QLineEdit {
                border: none;
                background-color: transparent;
                color: #000000;
                padding: 0px;
            }
        """)

        row_position.addWidget(lbl_position)
        row_position.addWidget(self.txt_position, 1)
        inner_layout.addWidget(frame_position)

        right_outer_layout.addWidget(right_inner)
        right_layout.addWidget(right_outer)

        # 2.4 하단 버튼 그룹
        self.btn_submit = QPushButton("등록하기", right_container)
        self.btn_submit.setFixedHeight(48)
        self.btn_submit.setCursor(Qt.PointingHandCursor)
        self.btn_submit.setFont(QFont("Inter", 13, QFont.Bold))
        self.btn_submit.setStyleSheet(f"""
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
        self.btn_submit.clicked.connect(self.save_designer)

        self.btn_delete = QPushButton("직원 정보 삭제하기", right_container)
        self.btn_delete.setFixedHeight(44)
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        self.btn_delete.setFont(QFont("Inter", 12, QFont.Bold))
        self.btn_delete.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.DANGER};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: #B30000;
            }}
        """)
        self.btn_delete.setVisible(False)
        self.btn_delete.clicked.connect(self.delete_designer)

        self.btn_reset = QPushButton("← 신규 등록 모드", right_container)
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        self.btn_reset.setStyleSheet(f"color: {Colors.TEXT_MUTED}; border: none; font-size: 12px; font-weight: bold;")
        self.btn_reset.setVisible(False)
        self.btn_reset.clicked.connect(self.reset_form)

        right_layout.addWidget(self.btn_submit)
        right_layout.addWidget(self.btn_delete)
        right_layout.addWidget(self.btn_reset)

        right_layout.addStretch(1)

        main_layout.addWidget(right_container, 2)

    def showEvent(self, event):
        super().showEvent(event)
        self.update_table_column_widths()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_table_column_widths()

    def update_table_column_widths(self):
        """테이블 전체 너비를 기준 비율 1.5 : 2.5 : 3 : 3 (15%, 25%, 30%, 30%)으로 강제 지정"""
        total_width = self.table.viewport().width()
        if total_width > 0:
            w0 = int(total_width * 0.15)  # 번호 (15%)
            w1 = int(total_width * 0.25)  # 이름 (25%)
            w2 = int(total_width * 0.30)  # 전화번호 (30%)
            w3 = total_width - (w0 + w1 + w2)  # 직급 (30% + 잔여 픽셀 처리)

            self.table.setColumnWidth(0, w0)
            self.table.setColumnWidth(1, w1)
            self.table.setColumnWidth(2, w2)
            self.table.setColumnWidth(3, w3)

    def on_phone_number_changed(self, text: str):
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

        self.txt_phone.blockSignals(True)
        self.txt_phone.setText(formatted)
        self.txt_phone.blockSignals(False)

    def load_designer_list(self):
        """DB에서 활성 직원의 목록을 불러와 저장 및 실시간 검색 필터 적용"""
        self.all_designers = self.db_manager.get_all_designers()
        self.filter_designer_list()

    def filter_designer_list(self):
        """검색어(이름 또는 전화번호) 입력에 따른 테이블 리스트 필터링"""
        search_query = self.txt_search.text().strip().lower()
        self.table.setRowCount(0)

        row_count = 0
        for user in self.all_designers:
            name = user["name"]
            phone = user["phone"]
            position = user["position"]

            if search_query and (search_query not in name.lower() and search_query not in phone.lower()):
                continue

            self.table.insertRow(row_count)

            item_no = QTableWidgetItem(str(row_count + 1))
            item_no.setTextAlignment(Qt.AlignCenter)
            item_no.setData(Qt.UserRole, user["id"])
            self.table.setItem(row_count, 0, item_no)

            item_name = QTableWidgetItem(name)
            item_name.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_count, 1, item_name)

            item_phone = QTableWidgetItem(phone)
            item_phone.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_count, 2, item_phone)

            item_pos = QTableWidgetItem(position)
            item_pos.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_count, 3, item_pos)

            row_count += 1

    def on_table_selection_changed(self):
        """테이블 행 클릭 시 우측 폼을 직원 수정 모드로 전환"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            return

        row = self.table.currentRow()
        user_id = self.table.item(row, 0).data(Qt.UserRole)
        name = self.table.item(row, 1).text()
        phone = self.table.item(row, 2).text()
        position = self.table.item(row, 3).text()

        self.selected_user_id = user_id
        self.txt_name.setText(name)
        self.txt_phone.setText(phone)
        self.txt_position.setText(position)

        self.lbl_form_title.setText("직원 정보 수정")
        self.btn_submit.setText("직원 정보 수정하기")
        self.btn_delete.setVisible(True)
        self.btn_reset.setVisible(True)

    def reset_form(self):
        """신규 등록 모드로 전환"""
        self.selected_user_id = None
        self.table.clearSelection()
        self.txt_name.clear()
        self.txt_phone.clear()
        self.txt_position.clear()

        self.lbl_form_title.setText("신규 직원 등록")
        self.btn_submit.setText("등록하기")
        self.btn_delete.setVisible(False)
        self.btn_reset.setVisible(False)

    def save_designer(self):
        """신규 등록 및 수정 처리"""
        name = self.txt_name.text().strip()
        phone = self.txt_phone.text().strip()
        position = self.txt_position.text().strip()

        if not name:
            QMessageBox.warning(self, "입력 오류", "이름을 입력해 주세요.")
            self.txt_name.setFocus()
            return

        if not phone:
            QMessageBox.warning(self, "입력 오류", "전화번호를 입력해 주세요.")
            self.txt_phone.setFocus()
            return

        if not position:
            QMessageBox.warning(self, "입력 오류", "직급을 입력해 주세요.")
            self.txt_position.setFocus()
            return

        if self.selected_user_id is None:
            success, err_msg = self.db_manager.add_designer(name, phone, position)
            if success:
                QMessageBox.information(self, "등록 완료", f"'{name}' 직원이 성공적으로 등록되었습니다.")
                self.load_designer_list()
                self.reset_form()
            else:
                QMessageBox.critical(self, "오류", f"직원 등록 중 오류가 발생했습니다.\n\n[상세 내용]: {err_msg}")
        else:
            success, err_msg = self.db_manager.update_designer(self.selected_user_id, name, phone, position)
            if success:
                QMessageBox.information(self, "수정 완료", f"'{name}' 직원의 정보가 수정되었습니다.")
                self.load_designer_list()
                self.reset_form()
            else:
                QMessageBox.critical(self, "오류", f"직원 정보 수정 중 오류가 발생했습니다.\n\n[상세 내용]: {err_msg}")

    def delete_designer(self):
        """커스텀 팝업 창을 통한 직원 논리적 삭제 처리"""
        if self.selected_user_id is None:
            return

        dialog = ConfirmDeleteDialog(self)
        if dialog.exec() == QDialog.Accepted:
            if self.db_manager.delete_designer(self.selected_user_id):
                QMessageBox.information(self, "삭제 완료", f"'{self.txt_name.text().strip()}' 직원이 삭제되었습니다.")
                self.load_designer_list()
                self.reset_form()
            else:
                QMessageBox.critical(self, "오류", "직원 삭제 처리 중 오류가 발생했습니다.")