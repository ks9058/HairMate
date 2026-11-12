from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QLineEdit, QDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from ui.theme import Colors, Styles
from core.db_manager import DBManager


class CustomAlertDialog(QDialog):
    """시스템 기본 QMessageBox를 대체하는 테마 커스텀 안내/알림 팝업"""

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMinimumWidth(460)

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


class ArrowSpinBox(QWidget):
    """
    QSpinBox의 내부 스크롤/텍스트 사라짐 버그를 해결한 커스텀 스핀박스 위젯.
    높이를 44px로 확대하여 시인성을 높였습니다.
    """
    valueChanged = Signal(int)

    def __init__(self, default_val=10, parent=None):
        super().__init__(parent)
        self._value = default_val
        self.setFixedHeight(44)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 1. 숫자 입력/표시 전용 필드
        self.edit = QLineEdit(f"{self._value} %", self)
        self.edit.setFont(QFont("Inter", 14, QFont.Bold))
        self.edit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.edit.setFixedWidth(95)
        self.edit.setStyleSheet("""
            QLineEdit {
                border: none;
                background-color: transparent;
                color: #000000;
                padding: 0px;
                margin: 0px;
            }
            QLineEdit:focus {
                border: none;
                background-color: transparent;
            }
        """)
        self.edit.textChanged.connect(self._on_text_changed)
        self.edit.editingFinished.connect(self._on_editing_finished)

        # 2. ▲ / ▼ 삼각형 버튼 영역
        btn_container = QWidget(self)
        btn_container.setFixedWidth(26)
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(3)

        self.btn_up = QPushButton("▲", btn_container)
        self.btn_up.setFixedSize(24, 19)
        self.btn_up.setCursor(Qt.PointingHandCursor)
        self.btn_up.setFont(QFont("Inter", 8, QFont.Bold))
        self.btn_up.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: #E5E7EB;
                color: #374151;
                border-radius: 3px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #D1D5DB;
                color: #111827;
            }
        """)
        self.btn_up.clicked.connect(self.step_up)

        self.btn_down = QPushButton("▼", btn_container)
        self.btn_down.setFixedSize(24, 19)
        self.btn_down.setCursor(Qt.PointingHandCursor)
        self.btn_down.setFont(QFont("Inter", 8, QFont.Bold))
        self.btn_down.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: #E5E7EB;
                color: #374151;
                border-radius: 3px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #D1D5DB;
                color: #111827;
            }
        """)
        self.btn_down.clicked.connect(self.step_down)

        btn_layout.addWidget(self.btn_up)
        btn_layout.addWidget(self.btn_down)

        layout.addWidget(self.edit)
        layout.addWidget(btn_container)

    def _on_text_changed(self, text: str):
        """실시간 타이핑 중에도 값 변경 감지 시그널 발생"""
        self.valueChanged.emit(self.current_display_value())

    def _on_editing_finished(self):
        """직접 타이핑 입력 시 숫자 추출 및 0~100 범위 제한 적용"""
        text = self.edit.text()
        digits = "".join(filter(str.isdigit, text))
        if digits:
            self.setValue(int(digits))
        else:
            self.setValue(self._value)

    def step_up(self):
        if self._value < 100:
            self.setValue(self._value + 1)

    def step_down(self):
        if self._value > 0:
            self.setValue(self._value - 1)

    def current_display_value(self) -> int:
        """현재 입력창에 표시된 숫자 반환 (미입력 상태면 -1)"""
        digits = "".join(filter(str.isdigit, self.edit.text()))
        if not digits:
            return -1
        return max(0, min(100, int(digits)))

    def value(self) -> int:
        return self._value

    def setValue(self, val: int):
        self._value = max(0, min(100, int(val)))
        self.edit.blockSignals(True)
        self.edit.setText(f"{self._value} %")
        self.edit.blockSignals(False)
        self.valueChanged.emit(self._value)


class SettingsPointView(QWidget):
    """설정 > 포인트 관리 뷰"""

    KEY_GENERAL_RATE = "point_rate_general"
    KEY_PREPAID_RATE = "point_rate_prepaid"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DBManager()
        self.original_rates = None

        self.setup_ui()
        self.load_point_rates()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 20, 40, 20)
        main_layout.setAlignment(Qt.AlignCenter)

        main_layout.addStretch(1)

        # -------------------------------------------------------------
        # 중앙 카드 컨테이너 (폭 520px 고정)
        # -------------------------------------------------------------
        center_container = QWidget(self)
        center_container.setFixedWidth(520)
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(25)

        # 1. 메인 타이틀
        lbl_main_title = QLabel("포인트 적립 비율 변경", center_container)
        lbl_main_title.setFont(QFont("Inter", 22, QFont.Bold))
        lbl_main_title.setStyleSheet("color: #000000; background: transparent;")
        lbl_main_title.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(lbl_main_title)

        # 2. 회색 둥근 외부 박스
        outer_box = QFrame(center_container)
        outer_box.setStyleSheet("""
            QFrame {
                background-color: #DCDCDC;
                border-radius: 14px;
            }
        """)
        outer_box.setAttribute(Qt.WA_StyledBackground, True)
        
        outer_layout = QVBoxLayout(outer_box)
        outer_layout.setContentsMargins(14, 14, 14, 14)

        # 3. 흰색 내부 폼 박스
        inner_box = QFrame(outer_box)
        inner_box.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 10px;
            }
        """)
        inner_box.setAttribute(Qt.WA_StyledBackground, True)

        inner_layout = QVBoxLayout(inner_box)
        inner_layout.setContentsMargins(35, 35, 35, 35)
        inner_layout.setSpacing(20)

        # 3.1 일반 적립 비율 행
        row_general = QHBoxLayout()
        lbl_general = QLabel("일반 적립 비율:   ", inner_box)
        lbl_general.setFont(QFont("Inter", 13, QFont.Bold))
        lbl_general.setStyleSheet("color: #000000; background: transparent;")

        self.spn_general = ArrowSpinBox(default_val=10, parent=inner_box)
        self.spn_general.valueChanged.connect(self.check_rates_modified)

        row_general.addWidget(lbl_general)
        row_general.addStretch()
        row_general.addWidget(self.spn_general)
        inner_layout.addLayout(row_general)

        # 구분선 1
        line1 = QFrame(inner_box)
        line1.setFrameShape(QFrame.HLine)
        line1.setStyleSheet("color: #E0E0E0; background-color: #E0E0E0; max-height: 1px;")
        inner_layout.addWidget(line1)

        # 3.2 선결제 적립 비율 행
        row_prepaid = QHBoxLayout()
        lbl_prepaid = QLabel("선결제 적립 비율:", inner_box)
        lbl_prepaid.setFont(QFont("Inter", 13, QFont.Bold))
        lbl_prepaid.setStyleSheet("color: #000000; background: transparent;")

        self.spn_prepaid = ArrowSpinBox(default_val=20, parent=inner_box)
        self.spn_prepaid.valueChanged.connect(self.check_rates_modified)

        row_prepaid.addWidget(lbl_prepaid)
        row_prepaid.addStretch()
        row_prepaid.addWidget(self.spn_prepaid)
        inner_layout.addLayout(row_prepaid)

        # 구분선 2
        line2 = QFrame(inner_box)
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet("color: #E0E0E0; background-color: #E0E0E0; max-height: 1px;")
        inner_layout.addWidget(line2)

        outer_layout.addWidget(inner_box)
        center_layout.addWidget(outer_box)

        # 4. 하단 저장하기 버튼
        self.btn_save = QPushButton("", center_container)
        self.btn_save.setFixedHeight(52)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setStyleSheet(f"""
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
        btn_save_layout = QHBoxLayout(self.btn_save)
        btn_save_layout.setContentsMargins(10, 0, 10, 0)
        btn_save_layout.setAlignment(Qt.AlignCenter)

        self.lbl_btn_save_text = QLabel("저장하기", self.btn_save)
        self.lbl_btn_save_text.setFont(QFont("Inter", 14, QFont.Bold))
        self.lbl_btn_save_text.setAlignment(Qt.AlignCenter)
        self.lbl_btn_save_text.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.lbl_btn_save_text.setStyleSheet("color: #FFFFFF; background: transparent; border: none;")
        btn_save_layout.addWidget(self.lbl_btn_save_text)

        self.btn_save.clicked.connect(self.save_point_rates)

        center_layout.addWidget(self.btn_save)
        main_layout.addWidget(center_container)

        main_layout.addStretch(1)

    def set_save_button_dirty(self, is_dirty: bool):
        """변경 사항 존재 여부에 따라 저장하기 버튼 텍스트에 빨간색 * 표시"""
        if is_dirty:
            self.lbl_btn_save_text.setText(
                "저장하기 <span style='color:#FF4D4F; font-weight:bold;'>*</span>"
            )
        else:
            self.lbl_btn_save_text.setText("저장하기")

    def check_rates_modified(self):
        """현재 입력된 적립 비율이 초기 로드/저장된 값과 다른지 확인"""
        if self.original_rates is None:
            self.set_save_button_dirty(False)
            return

        current_rates = (
            self.spn_general.current_display_value(),
            self.spn_prepaid.current_display_value(),
        )
        self.set_save_button_dirty(current_rates != self.original_rates)

    def load_point_rates(self):
        """DB에서 설정값 조회 (기본값: 일반 10%, 선결제 20%)"""
        general_str = self.db_manager.get_setting(self.KEY_GENERAL_RATE, default="10")
        prepaid_str = self.db_manager.get_setting(self.KEY_PREPAID_RATE, default="20")

        try:
            general_val = int(general_str)
        except ValueError:
            general_val = 10

        try:
            prepaid_val = int(prepaid_str)
        except ValueError:
            prepaid_val = 20

        self.spn_general.setValue(general_val)
        self.spn_prepaid.setValue(prepaid_val)

        self.original_rates = (general_val, prepaid_val)
        self.set_save_button_dirty(False)

    def save_point_rates(self):
        """[저장하기] 버튼 클릭 시 입력값 DB 저장"""
        self.spn_general._on_editing_finished()
        self.spn_prepaid._on_editing_finished()

        general_val = self.spn_general.value()
        prepaid_val = self.spn_prepaid.value()

        if not (0 <= general_val <= 100) or not (0 <= prepaid_val <= 100):
            CustomAlertDialog("입력 오류", "적립률은 0%에서 100% 사이의 값이어야 합니다.", self).exec()
            return

        res_general = self.db_manager.set_setting(self.KEY_GENERAL_RATE, str(general_val))
        res_prepaid = self.db_manager.set_setting(self.KEY_PREPAID_RATE, str(prepaid_val))

        if res_general and res_prepaid:
            self.original_rates = (general_val, prepaid_val)
            self.set_save_button_dirty(False)
            CustomAlertDialog("저장 완료", "포인트 적립 비율이 성공적으로 저장되었습니다.", self).exec()
        else:
            CustomAlertDialog("저장 실패", "포인트 적립 비율 저장 중 오류가 발생했습니다.", self).exec()