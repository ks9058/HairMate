import re
from copy import deepcopy
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QTextEdit, QScrollArea, QCheckBox,
    QButtonGroup, QApplication, QStyle, QStyleOptionButton, QStylePainter
)
from PySide6.QtCore import Qt, QRectF, QTimer
from PySide6.QtGui import QFont, QPainter, QColor, QFontMetrics, QPalette
from ui.theme import Colors
from ui.customer_view import CustomAlertDialog
from core.db_manager import DBManager
from core.sms_service import (
    DEFAULT_TEMPLATES,
    render_sms_template,
    get_euckr_byte_length,
    SmsBalanceWorker,
    SmsSendWorker,
)


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


class DirtySaveButton(QPushButton):
    """변경 사항이 있을 때 글자 오른쪽 위에 빨간색 '*' 위첨자를 표시하는 저장 버튼"""

    def __init__(self, text: str = "설정 저장", parent=None):
        super().__init__(text, parent)
        self._is_dirty = False

    def set_dirty(self, dirty: bool):
        if self._is_dirty != dirty:
            self._is_dirty = dirty
            self.update()

    def paintEvent(self, event):
        painter = QStylePainter(self)
        option = QStyleOptionButton()
        self.initStyleOption(option)

        base_text = option.text
        option.text = ""  # 버튼 배경·테두리·hover 스타일만 먼저 렌더링
        painter.drawControl(QStyle.ControlElement.CE_PushButton, option)

        # 기본 버튼 글자 중앙 정렬로 그리기
        rect = self.rect()
        fm = QFontMetrics(self.font())
        text_width = fm.horizontalAdvance(base_text)
        text_height = fm.height()

        painter.setFont(self.font())
        painter.setPen(option.palette.color(QPalette.ColorRole.ButtonText))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, base_text)

        # 변경 사항이 있으면 글자 오른쪽 위에 빨간색 '*' 그리기
        if self._is_dirty:
            text_right_x = (rect.width() + text_width) / 2
            text_top_y = (rect.height() - text_height) / 2

            star_font = QFont(self.font())
            star_font.setBold(True)
            if star_font.pointSize() > 0:
                star_font.setPointSize(star_font.pointSize() + 1)
            painter.setFont(star_font)
            painter.setPen(QColor("#FF4D4F"))

            star_rect = QRectF(text_right_x + 2, text_top_y - 3, 14, 16)
            painter.drawText(
                star_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                "*",
            )


class ToggleSwitch(QCheckBox):
    """ON/OFF 녹색 알약형 토글 스위치"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(62, 28)
        self.setCursor(Qt.PointingHandCursor)

    def hitButton(self, pos):
        return self.contentsRect().contains(pos)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(0, 0, self.width(), self.height())
        bg_color = QColor(Colors.PRIMARY) if self.isChecked() else QColor("#CBD5E1")
        painter.setPen(Qt.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(rect, 14, 14)

        painter.setPen(QColor("#FFFFFF"))
        font = QFont("Inter", 8, QFont.Weight.Bold)
        painter.setFont(font)
        if self.isChecked():
            painter.drawText(QRectF(8, 0, 28, self.height()), Qt.AlignCenter, "ON")
            knob_x = self.width() - 24
        else:
            painter.drawText(QRectF(26, 0, 30, self.height()), Qt.AlignCenter, "OFF")
            knob_x = 4

        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(QRectF(knob_x, 4, 20, 20))
        painter.end()


class PhonePreviewWidget(QFrame):
    """우측 스마트폰 문자 수신 미리보기 프레임"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(235, 290)
        self.setObjectName("PhoneOuter")
        self.setStyleSheet("""
            QFrame#PhoneOuter {
                background-color: #1E293B;
                border-radius: 26px;
                padding: 8px;
            }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(7, 7, 7, 7)

        screen = QFrame(self)
        screen.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 20px;
            }
        """)
        s_layout = QVBoxLayout(screen)
        s_layout.setContentsMargins(12, 8, 12, 12)
        s_layout.setSpacing(6)

        top_bar = QHBoxLayout()
        lbl_time = QLabel("9:41", screen)
        lbl_time.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        lbl_time.setStyleSheet("color: #0F172A; border: none;")
        lbl_signal = QLabel("LTE  100%", screen)
        lbl_signal.setFont(QFont("Inter", 7, QFont.Weight.Bold))
        lbl_signal.setStyleSheet("color: #475569; border: none;")
        top_bar.addWidget(lbl_time)
        top_bar.addStretch()
        top_bar.addWidget(lbl_signal)
        s_layout.addLayout(top_bar)

        header_box = QVBoxLayout()
        header_box.setSpacing(2)
        avatar = QLabel("👤", screen)
        avatar.setFixedSize(26, 26)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("""
            background-color: #E2E8F0;
            border-radius: 13px;
            font-size: 13px;
            border: none;
        """)
        self.lbl_sender = QLabel("02-1234-5678", screen)
        self.lbl_sender.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        self.lbl_sender.setAlignment(Qt.AlignCenter)
        self.lbl_sender.setStyleSheet("color: #334155; border: none;")

        header_box.addWidget(avatar, 0, Qt.AlignCenter)
        header_box.addWidget(self.lbl_sender, 0, Qt.AlignCenter)
        s_layout.addLayout(header_box)

        line = QFrame(screen)
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #E2E8F0; max-height: 1px; border: none;")
        s_layout.addWidget(line)

        bubble = QFrame(screen)
        bubble.setStyleSheet("""
            QFrame {
                background-color: #F1F5F9;
                border-radius: 12px;
                border: 1px solid #E2E8F0;
            }
        """)
        b_layout = QVBoxLayout(bubble)
        b_layout.setContentsMargins(10, 9, 10, 9)

        self.lbl_preview_text = QLabel(screen)
        self.lbl_preview_text.setFont(QFont("Inter", 8))
        self.lbl_preview_text.setWordWrap(True)
        self.lbl_preview_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.lbl_preview_text.setStyleSheet("color: #0F172A; background: transparent; border: none; line-height: 1.35;")
        b_layout.addWidget(self.lbl_preview_text)

        s_layout.addWidget(bubble)
        s_layout.addStretch(1)
        outer.addWidget(screen)

    def update_preview(self, sender_phone: str, rendered_text: str):
        clean_sender = (sender_phone or "").strip() or "02-1234-5678"
        self.lbl_sender.setText(clean_sender)
        self.lbl_preview_text.setText(rendered_text)


class MessageManagementView(QWidget):
    """설정 > 문자 전송 관리 (매장 정보 및 솔라피 API 연동) 페이지"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DBManager()
        self.current_tpl_key = "use"
        self.templates = {
            "use": DEFAULT_TEMPLATES["use"],
            "charge": DEFAULT_TEMPLATES["charge"],
            "cancel_use": DEFAULT_TEMPLATES["cancel_use"],
            "cancel_charge": DEFAULT_TEMPLATES["cancel_charge"],
        }
        self._saved_snapshot = None
        self._balance_worker = None
        self._test_worker = None

        self._setup_ui()
        self.load_settings()

    def _setup_ui(self):
        self.setStyleSheet(f"background-color: {Colors.BACKGROUND};")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(f"QScrollArea {{ background-color: {Colors.BACKGROUND}; border: none; }}")
        scroll.verticalScrollBar().setStyleSheet(SCROLLBAR_STYLE)

        content = QWidget()
        content.setStyleSheet(f"background-color: {Colors.BACKGROUND};")
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(28, 22, 28, 28)
        main_layout.setSpacing(16)

        # 상단 페이지 타이틀 (검정색)
        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        lbl_page_title = QLabel("문자 전송 관리 (솔라피 API 연동)", content)
        lbl_page_title.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        lbl_page_title.setStyleSheet("color: #000000; border: none;")

        lbl_page_desc = QLabel(
            "매장 상호명 등록 및 선결제 충전·사용·취소 시 고객에게 자동으로 안내 문자를 발송하는 기능입니다.",
            content,
        )
        lbl_page_desc.setFont(QFont("Inter", 10))
        lbl_page_desc.setStyleSheet(f"color: {Colors.TEXT_MUTED}; border: none;")

        title_box.addWidget(lbl_page_title)
        title_box.addWidget(lbl_page_desc)
        main_layout.addLayout(title_box)

        # =====================================================================
        # 카드 1: 매장 정보 및 API 인증 설정
        # =====================================================================
        card1 = self._create_card(content)
        c1_layout = QVBoxLayout(card1)
        c1_layout.setContentsMargins(22, 18, 22, 18)
        c1_layout.setSpacing(12)

        lbl_c1_title = QLabel("1. 매장 정보 및 API 인증 설정", card1)
        lbl_c1_title.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        lbl_c1_title.setStyleSheet("color: #0F172A; border: none;")
        c1_layout.addWidget(lbl_c1_title)

        # Row 0: 매장명 (상호명)
        row_shop = QHBoxLayout()
        row_shop.setSpacing(10)
        lbl_r0 = self._form_label("매장명 (상호명)", card1)
        self.input_shop_name = QLineEdit(card1)
        self.input_shop_name.setPlaceholderText("예: OO헤어 (문자 발송 및 동의서 출력에 사용)")
        self.input_shop_name.setFixedSize(320, 36)
        self.input_shop_name.setStyleSheet(self._input_style())
        self.input_shop_name.textChanged.connect(self._update_live_preview)
        self.input_shop_name.textChanged.connect(self._update_dirty_state)

        lbl_shop_hint = QLabel("* 입력한 매장명은 안내 문자와 개인정보 동의서에 자동 반영됩니다.", card1)
        lbl_shop_hint.setFont(QFont("Inter", 9))
        lbl_shop_hint.setStyleSheet("color: #64748B; border: none;")

        row_shop.addWidget(lbl_r0)
        row_shop.addWidget(self.input_shop_name)
        row_shop.addWidget(lbl_shop_hint)
        row_shop.addStretch()
        c1_layout.addLayout(row_shop)

        # Row 1: 자동 문자 발송 활성화
        row_toggle = QHBoxLayout()
        row_toggle.setSpacing(12)
        lbl_r1 = self._form_label("자동 문자 발송 활성화", card1)
        self.toggle_enabled = ToggleSwitch(card1)
        self.toggle_enabled.toggled.connect(self._update_dirty_state)
        self.lbl_toggle_desc = QLabel("선결제 충전/사용/취소 시 자동으로 고객 문자 발송", card1)
        self.lbl_toggle_desc.setFont(QFont("Inter", 10))
        self.lbl_toggle_desc.setStyleSheet("color: #334155; border: none;")

        row_toggle.addWidget(lbl_r1)
        row_toggle.addWidget(self.toggle_enabled)
        row_toggle.addWidget(self.lbl_toggle_desc)
        row_toggle.addStretch()
        c1_layout.addLayout(row_toggle)

        # Row 2: API Key
        row_key = QHBoxLayout()
        row_key.setSpacing(10)
        lbl_r2 = self._form_label("API Key (솔라피)", card1)
        self.input_api_key = QLineEdit(card1)
        self.input_api_key.setPlaceholderText("sol_key_xxxxxxxxxxxxxxx")
        self.input_api_key.setFixedSize(320, 36)
        self.input_api_key.setStyleSheet(self._input_style())
        self.input_api_key.textChanged.connect(self._update_dirty_state)

        btn_copy_key = QPushButton("복사", card1)
        btn_copy_key.setFixedSize(56, 36)
        btn_copy_key.setCursor(Qt.PointingHandCursor)
        btn_copy_key.setStyleSheet(self._secondary_btn_style())
        btn_copy_key.clicked.connect(self._copy_api_key)

        row_key.addWidget(lbl_r2)
        row_key.addWidget(self.input_api_key)
        row_key.addWidget(btn_copy_key)
        row_key.addStretch()
        c1_layout.addLayout(row_key)

        # Row 3: API Secret
        row_secret = QHBoxLayout()
        row_secret.setSpacing(10)
        lbl_r3 = self._form_label("API Secret", card1)
        self.input_api_secret = QLineEdit(card1)
        self.input_api_secret.setPlaceholderText("API Secret 키를 입력하세요")
        self.input_api_secret.setEchoMode(QLineEdit.Password)
        self.input_api_secret.setFixedSize(320, 36)
        self.input_api_secret.setStyleSheet(self._input_style())
        self.input_api_secret.textChanged.connect(self._update_dirty_state)

        self.btn_toggle_secret = QPushButton("보기", card1)
        self.btn_toggle_secret.setCheckable(True)
        self.btn_toggle_secret.setFixedSize(56, 36)
        self.btn_toggle_secret.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_secret.setStyleSheet(self._secondary_btn_style())
        self.btn_toggle_secret.toggled.connect(self._toggle_secret_visibility)

        row_secret.addWidget(lbl_r3)
        row_secret.addWidget(self.input_api_secret)
        row_secret.addWidget(self.btn_toggle_secret)
        row_secret.addStretch()
        c1_layout.addLayout(row_secret)

        # Row 4: 발신번호
        row_sender = QHBoxLayout()
        row_sender.setSpacing(10)
        lbl_r4 = self._form_label("발신번호 (등록된 매장 번호)", card1)
        self.input_sender_phone = QLineEdit(card1)
        self.input_sender_phone.setPlaceholderText("02-1234-5678 또는 010-1234-5678")
        self.input_sender_phone.setFixedSize(320, 36)
        self.input_sender_phone.setStyleSheet(self._input_style())
        self.input_sender_phone.textChanged.connect(self._on_sender_changed)
        self.input_sender_phone.textChanged.connect(self._update_dirty_state)

        self.lbl_sender_badge = QLabel("발신번호 미입력", card1)
        self.lbl_sender_badge.setFixedHeight(28)
        self.lbl_sender_badge.setAlignment(Qt.AlignCenter)
        self.lbl_sender_badge.setStyleSheet(self._badge_style(active=False))

        row_sender.addWidget(lbl_r4)
        row_sender.addWidget(self.input_sender_phone)
        row_sender.addWidget(self.lbl_sender_badge)
        row_sender.addStretch()
        c1_layout.addLayout(row_sender)

        # 하단 구분선 및 상태/포인트/저장 바
        divider1 = QFrame(card1)
        divider1.setFrameShape(QFrame.HLine)
        divider1.setStyleSheet("background-color: #E2E8F0; max-height: 1px; border: none;")
        c1_layout.addWidget(divider1)

        bottom_bar1 = QHBoxLayout()
        bottom_bar1.setSpacing(14)

        self.lbl_api_status = QLabel("API 연동 상태: 미확인", card1)
        self.lbl_api_status.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        self.lbl_api_status.setStyleSheet("color: #475569; border: none;")

        self.lbl_balance = QLabel("잔여 발송 포인트: 조회 전", card1)
        self.lbl_balance.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        self.lbl_balance.setStyleSheet("color: #0F172A; border: none;")

        self.btn_refresh_balance = QPushButton("↻ 잔액 새로고침", card1)
        self.btn_refresh_balance.setFixedHeight(34)
        self.btn_refresh_balance.setCursor(Qt.PointingHandCursor)
        self.btn_refresh_balance.setStyleSheet(self._secondary_btn_style())
        self.btn_refresh_balance.clicked.connect(self.refresh_balance)

        self.btn_save_settings = DirtySaveButton("설정 저장", card1)
        self.btn_save_settings.setFixedSize(110, 36)
        self.btn_save_settings.setCursor(Qt.PointingHandCursor)
        self.btn_save_settings.setStyleSheet(self._primary_btn_style())
        self.btn_save_settings.clicked.connect(self.save_settings)

        bottom_bar1.addWidget(self.lbl_api_status)
        bottom_bar1.addSpacing(8)
        bottom_bar1.addWidget(self.lbl_balance)
        bottom_bar1.addWidget(self.btn_refresh_balance)
        bottom_bar1.addStretch()
        bottom_bar1.addWidget(self.btn_save_settings)
        c1_layout.addLayout(bottom_bar1)

        main_layout.addWidget(card1)

        # =====================================================================
        # 카드 2: 문자 발송 템플릿 및 미리보기 (사용 / 충전 / 사용 취소 / 충전 취소)
        # =====================================================================
        card2 = self._create_card(content)
        c2_layout = QHBoxLayout(card2)
        c2_layout.setContentsMargins(22, 18, 22, 18)
        c2_layout.setSpacing(24)

        left_tpl_col = QVBoxLayout()
        left_tpl_col.setSpacing(10)

        lbl_c2_title = QLabel("2. 문자 발송 템플릿 및 미리보기", card2)
        lbl_c2_title.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        lbl_c2_title.setStyleSheet("color: #0F172A; border: none;")
        left_tpl_col.addWidget(lbl_c2_title)

        tab_row = QHBoxLayout()
        tab_row.setSpacing(6)
        self.tpl_btn_group = QButtonGroup(self)
        self.tpl_btn_group.setExclusive(True)

        self.btn_tab_use = self._create_tab_button("선결제 사용 시", "use", card2)
        self.btn_tab_charge = self._create_tab_button("선결제 충전 시", "charge", card2)
        self.btn_tab_cancel_use = self._create_tab_button("선결제 사용 취소 시", "cancel_use", card2)
        self.btn_tab_cancel_charge = self._create_tab_button("선결제 충전 취소 시", "cancel_charge", card2)

        for idx, btn in enumerate([
            self.btn_tab_use,
            self.btn_tab_charge,
            self.btn_tab_cancel_use,
            self.btn_tab_cancel_charge,
        ]):
            self.tpl_btn_group.addButton(btn, idx)
            tab_row.addWidget(btn)
        tab_row.addStretch()
        left_tpl_col.addLayout(tab_row)

        self.txt_template = QTextEdit(card2)
        self.txt_template.setFixedHeight(175)
        self.txt_template.setFont(QFont("Inter", 10))
        self.txt_template.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                border: 1.5px solid #CBD5E1;
                border-radius: 8px;
                padding: 10px;
                color: #0F172A;
            }
            QTextEdit:focus {
                border: 1.5px solid #0D5C46;
            }
        """)
        self.txt_template.verticalScrollBar().setStyleSheet(SCROLLBAR_STYLE)
        self.txt_template.textChanged.connect(self._on_template_text_changed)
        left_tpl_col.addWidget(self.txt_template)

        meta_row = QHBoxLayout()
        lbl_vars = QLabel(
            "사용 가능 변수: {매장명}, {방문일시}, {취소일시}, {시술명}, {사용금액}, {충전금액}, {잔여금액}",
            card2,
        )
        lbl_vars.setFont(QFont("Inter", 8))
        lbl_vars.setStyleSheet("color: #64748B; border: none;")

        self.lbl_byte_count = QLabel("84 / 90 바이트 (SMS 단문 발송)", card2)
        self.lbl_byte_count.setFont(QFont("Inter", 9, QFont.Weight.Bold))
        self.lbl_byte_count.setStyleSheet(f"color: {Colors.PRIMARY}; border: none;")

        meta_row.addWidget(lbl_vars)
        meta_row.addStretch()
        meta_row.addWidget(self.lbl_byte_count)
        left_tpl_col.addLayout(meta_row)

        c2_layout.addLayout(left_tpl_col, 1)

        self.phone_preview = PhonePreviewWidget(card2)
        c2_layout.addWidget(self.phone_preview, 0, Qt.AlignVCenter)

        main_layout.addWidget(card2)

        # =====================================================================
        # 카드 3: 수동 테스트 발송
        # =====================================================================
        card3 = self._create_card(content)
        c3_layout = QVBoxLayout(card3)
        c3_layout.setContentsMargins(22, 16, 22, 16)
        c3_layout.setSpacing(8)

        lbl_c3_title = QLabel("3. 수동 테스트 발송", card3)
        lbl_c3_title.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        lbl_c3_title.setStyleSheet("color: #0F172A; border: none;")
        c3_layout.addWidget(lbl_c3_title)

        test_row = QHBoxLayout()
        test_row.setSpacing(12)

        lbl_test_phone = self._form_label("수신 테스트 휴대폰 번호", card3)
        self.input_test_phone = QLineEdit(card3)
        self.input_test_phone.setPlaceholderText("010-1234-5678")
        self.input_test_phone.setFixedSize(280, 36)
        self.input_test_phone.setStyleSheet(self._input_style())

        self.btn_send_test = QPushButton("➤  테스트 문자 발송", card3)
        self.btn_send_test.setFixedSize(165, 36)
        self.btn_send_test.setCursor(Qt.PointingHandCursor)
        self.btn_send_test.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: {Colors.PRIMARY};
                border: 1.5px solid {Colors.PRIMARY};
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY};
                color: #FFFFFF;
                border: 1.5px solid {Colors.PRIMARY};
            }}
            QPushButton:disabled {{
                background-color: #F8FAFC;
                color: #94A3B8;
                border-color: #E2E8F0;
            }}
        """)
        self.btn_send_test.clicked.connect(self.send_test_sms)

        test_row.addWidget(lbl_test_phone)
        test_row.addWidget(self.input_test_phone)
        test_row.addStretch()
        test_row.addWidget(self.btn_send_test)
        c3_layout.addLayout(test_row)

        lbl_notice = QLabel(
            "* 네트워크 오류, API 잔액 부족 시에도 매장 결제는 정상 저장되며 경고 알림만 표시됩니다.",
            card3,
        )
        lbl_notice.setFont(QFont("Inter", 8))
        lbl_notice.setStyleSheet("color: #64748B; border: none;")
        c3_layout.addWidget(lbl_notice)

        main_layout.addWidget(card3)
        main_layout.addStretch(1)

        scroll.setWidget(content)
        root_layout.addWidget(scroll)

        self.btn_tab_use.setChecked(True)

    # -------------------------------------------------------------------------
    # UI 스타일 헬퍼
    # -------------------------------------------------------------------------
    def _create_card(self, parent) -> QFrame:
        card = QFrame(parent)
        card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #DCE3DF;
                border-radius: 12px;
            }
        """)
        return card

    def _form_label(self, text: str, parent) -> QLabel:
        lbl = QLabel(text, parent)
        lbl.setFixedWidth(185)
        lbl.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #1E293B; border: none;")
        return lbl

    def _input_style(self) -> str:
        return f"""
            QLineEdit {{
                background-color: #FFFFFF;
                border: 1.5px solid #CBD5E1;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 13px;
                color: #0F172A;
            }}
            QLineEdit:focus {{
                border: 1.5px solid {Colors.PRIMARY};
            }}
        """

    def _primary_btn_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 14px;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
            }}
            QPushButton:disabled {{
                background-color: #94A3B8;
            }}
        """

    def _secondary_btn_style(self, border_color="#CBD5E1", text_color="#1E293B") -> str:
        return f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: {text_color};
                border: 1.5px solid {border_color};
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: #F1F5F9;
            }}
            QPushButton:disabled {{
                color: #94A3B8;
                border-color: #E2E8F0;
            }}
        """

    def _badge_style(self, active: bool) -> str:
        if active:
            return f"""
                QLabel {{
                    background-color: #ECFDF5;
                    color: {Colors.PRIMARY};
                    border: 1px solid #A7F3D0;
                    border-radius: 6px;
                    padding: 0 10px;
                    font-size: 11px;
                    font-weight: bold;
                }}
            """
        return """
            QLabel {
                background-color: #F8FAFC;
                color: #64748B;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 11px;
                font-weight: bold;
            }
        """

    def _create_tab_button(self, text: str, key: str, parent) -> QPushButton:
        btn = QPushButton(text, parent)
        btn.setCheckable(True)
        btn.setFixedHeight(32)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #F1F5F9;
                color: #475569;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 0 11px;
                font-size: 11.5px;
                font-weight: bold;
            }}
            QPushButton:checked {{
                background-color: #FFFFFF;
                color: {Colors.PRIMARY};
                border: 1.5px solid {Colors.PRIMARY};
            }}
            QPushButton:hover:!checked {{
                background-color: #E2E8F0;
            }}
        """)
        btn.clicked.connect(lambda: self._switch_template_tab(key))
        return btn

    # -------------------------------------------------------------------------
    # 변경 감지 (Dirty State) 관리
    # -------------------------------------------------------------------------
    def _get_current_snapshot(self) -> dict:
        current_templates = deepcopy(self.templates)
        current_templates[self.current_tpl_key] = self.txt_template.toPlainText()

        return {
            "shop_name": self.input_shop_name.text().strip(),
            "enabled": bool(self.toggle_enabled.isChecked()),
            "api_key": self.input_api_key.text().strip(),
            "api_secret": self.input_api_secret.text().strip(),
            "sender_phone": self.input_sender_phone.text().strip(),
            "templates": current_templates,
        }

    def _update_dirty_state(self):
        if self._saved_snapshot is None:
            return
        is_changed = self._get_current_snapshot() != self._saved_snapshot
        self.btn_save_settings.set_dirty(is_changed)

    def _sync_saved_snapshot(self):
        self._saved_snapshot = self._get_current_snapshot()
        self.btn_save_settings.set_dirty(False)

    # -------------------------------------------------------------------------
    # 이벤트 및 데이터 연동
    # -------------------------------------------------------------------------
    def _copy_api_key(self):
        text = self.input_api_key.text().strip()
        if text:
            QApplication.clipboard().setText(text)
            CustomAlertDialog("복사 완료", "API Key가 클립보드에 복사되었습니다.", self).exec()

    def _toggle_secret_visibility(self, checked: bool):
        if checked:
            self.input_api_secret.setEchoMode(QLineEdit.Normal)
            self.btn_toggle_secret.setText("숨김")
        else:
            self.input_api_secret.setEchoMode(QLineEdit.Password)
            self.btn_toggle_secret.setText("보기")

    def _on_sender_changed(self, text: str):
        digits = re.sub(r"[^0-9]", "", text or "")
        if len(digits) >= 8:
            self.lbl_sender_badge.setText("발신번호 입력됨 (사전등록 필수)")
            self.lbl_sender_badge.setStyleSheet(self._badge_style(active=True))
        else:
            self.lbl_sender_badge.setText("발신번호 미입력")
            self.lbl_sender_badge.setStyleSheet(self._badge_style(active=False))
        self._update_live_preview()

    def _switch_template_tab(self, new_key: str):
        self.templates[self.current_tpl_key] = self.txt_template.toPlainText()
        self.current_tpl_key = new_key
        self.txt_template.blockSignals(True)
        self.txt_template.setPlainText(self.templates.get(new_key, ""))
        self.txt_template.blockSignals(False)
        self._update_live_preview()

    def _on_template_text_changed(self):
        self.templates[self.current_tpl_key] = self.txt_template.toPlainText()
        self._update_live_preview()
        self._update_dirty_state()

    def _build_sample_rendered_text(self) -> str:
        shop_name = (
            self.input_shop_name.text().strip()
            or self.db_manager.get_setting("shop_name", "")
            or "OO헤어"
        )
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        sample_context = {
            "매장명": shop_name,
            "방문일시": now_str,
            "취소일시": now_str,
            "시술명": "여성 컷 + 클리닉",
            "사용금액": "35,000",
            "충전금액": "100,000",
            "잔여금액": "85,000",
        }
        raw_tpl = self.txt_template.toPlainText()
        return render_sms_template(raw_tpl, sample_context)

    def _update_live_preview(self):
        rendered = self._build_sample_rendered_text()
        self.phone_preview.update_preview(self.input_sender_phone.text(), rendered)

        byte_len = get_euckr_byte_length(rendered)
        if byte_len <= 90:
            self.lbl_byte_count.setText(f"{byte_len} / 90 바이트 (SMS 단문 발송)")
            self.lbl_byte_count.setStyleSheet(f"color: {Colors.PRIMARY}; border: none;")
        else:
            self.lbl_byte_count.setText(f"{byte_len} / 2,000 바이트 (LMS 장문 자동 전환)")
            self.lbl_byte_count.setStyleSheet("color: #D97706; border: none;")

    def load_settings(self):
        """DB settings 테이블에서 매장명, 문자 설정 및 템플릿 불러오기"""
        shop_name = self.db_manager.get_setting("shop_name", "")
        enabled = self.db_manager.get_setting("sms_enabled", "1") == "1"
        api_key = self.db_manager.get_setting("sms_api_key", "")
        api_secret = self.db_manager.get_setting("sms_api_secret", "")
        sender_phone = self.db_manager.get_setting("sms_sender_phone", "")

        self.templates["use"] = (
            self.db_manager.get_setting("sms_tpl_use", "")
            or self.db_manager.get_setting("sms_template_use", "")
            or DEFAULT_TEMPLATES["use"]
        )
        self.templates["charge"] = (
            self.db_manager.get_setting("sms_tpl_charge", "")
            or self.db_manager.get_setting("sms_template_charge", "")
            or DEFAULT_TEMPLATES["charge"]
        )
        self.templates["cancel_use"] = (
            self.db_manager.get_setting("sms_tpl_cancel_use", "")
            or self.db_manager.get_setting("sms_template_cancel_use", "")
            or DEFAULT_TEMPLATES["cancel_use"]
        )
        self.templates["cancel_charge"] = (
            self.db_manager.get_setting("sms_tpl_cancel_charge", "")
            or self.db_manager.get_setting("sms_template_cancel_charge", "")
            or DEFAULT_TEMPLATES["cancel_charge"]
        )

        self.input_shop_name.setText(shop_name)
        self.toggle_enabled.setChecked(enabled)
        self.input_api_key.setText(api_key)
        self.input_api_secret.setText(api_secret)
        self.input_sender_phone.setText(sender_phone)

        self.txt_template.blockSignals(True)
        self.txt_template.setPlainText(self.templates[self.current_tpl_key])
        self.txt_template.blockSignals(False)

        self._on_sender_changed(sender_phone)
        self._update_live_preview()
        self._sync_saved_snapshot()

        if api_key and api_secret:
            QTimer.singleShot(150, self.refresh_balance)

    def save_settings(self):
        """현재 화면의 매장명, API 키, 발신번호, 자동발송 여부, 템플릿을 DB settings 테이블에 저장"""
        self.templates[self.current_tpl_key] = self.txt_template.toPlainText()
        clean_sender = re.sub(r"[^0-9-]", "", self.input_sender_phone.text().strip())

        results = [
            self.db_manager.set_setting("shop_name", self.input_shop_name.text().strip()),
            self.db_manager.set_setting("sms_enabled", "1" if self.toggle_enabled.isChecked() else "0"),
            self.db_manager.set_setting("sms_api_key", self.input_api_key.text().strip()),
            self.db_manager.set_setting("sms_api_secret", self.input_api_secret.text().strip()),
            self.db_manager.set_setting("sms_sender_phone", clean_sender),
            self.db_manager.set_setting("sms_tpl_use", self.templates["use"]),
            self.db_manager.set_setting("sms_tpl_charge", self.templates["charge"]),
            self.db_manager.set_setting("sms_tpl_cancel_use", self.templates["cancel_use"]),
            self.db_manager.set_setting("sms_tpl_cancel_charge", self.templates["cancel_charge"]),
            self.db_manager.set_setting("sms_template_use", self.templates["use"]),
            self.db_manager.set_setting("sms_template_charge", self.templates["charge"]),
            self.db_manager.set_setting("sms_template_cancel_use", self.templates["cancel_use"]),
            self.db_manager.set_setting("sms_template_cancel_charge", self.templates["cancel_charge"]),
        ]

        if all(results):
            self.input_sender_phone.setText(clean_sender)
            self._sync_saved_snapshot()
            CustomAlertDialog("저장 완료", "매장 정보 및 문자 발송 설정이 DB에 안전하게 저장되었습니다.", self).exec()
            if self.input_api_key.text().strip() and self.input_api_secret.text().strip():
                self.refresh_balance()
        else:
            CustomAlertDialog("저장 오류", "설정 저장 중 일부 항목을 DB에 기록하지 못했습니다.", self).exec()

    def refresh_balance(self):
        """솔라피 잔여 포인트 비동기 조회"""
        api_key = self.input_api_key.text().strip()
        api_secret = self.input_api_secret.text().strip()
        if not api_key or not api_secret:
            self.lbl_api_status.setText("API 연동 상태: 키 미입력")
            self.lbl_api_status.setStyleSheet("color: #64748B; border: none;")
            self.lbl_balance.setText("잔여 발송 포인트: API 키를 먼저 입력하세요")
            return

        self.btn_refresh_balance.setEnabled(False)
        self.btn_refresh_balance.setText("조회 중...")

        self._balance_worker = SmsBalanceWorker(api_key, api_secret, parent=self)
        self._balance_worker.finished_signal.connect(self._on_balance_result)
        self._balance_worker.start()

    def _on_balance_result(self, ok: bool, msg: str, total: int):
        self.btn_refresh_balance.setEnabled(True)
        self.btn_refresh_balance.setText("↻ 잔액 새로고침")

        if ok:
            self.lbl_api_status.setText("API 연동 상태: 정상 연결됨 (SOLAPI)")
            self.lbl_api_status.setStyleSheet(f"color: {Colors.PRIMARY}; border: none;")
            self.lbl_balance.setText(f"잔여 발송 포인트: {msg}")
        else:
            self.lbl_api_status.setText("API 연동 상태: 연결 확인 필요")
            self.lbl_api_status.setStyleSheet("color: #DC2626; border: none;")
            self.lbl_balance.setText(f"잔여 발송 포인트: 조회 실패 ({msg})")

    def send_test_sms(self):
        """수동 테스트 문자 비동기 발송"""
        to_phone = self.input_test_phone.text().strip()
        if len(re.sub(r"[^0-9]", "", to_phone)) < 10:
            CustomAlertDialog("입력 확인", "수신 테스트 휴대폰 번호를 정확히 입력해 주세요.", self).exec()
            self.input_test_phone.setFocus()
            return

        api_key = self.input_api_key.text().strip()
        api_secret = self.input_api_secret.text().strip()
        sender_phone = self.input_sender_phone.text().strip()
        preview_text = self._build_sample_rendered_text()

        self.btn_send_test.setEnabled(False)
        self.btn_send_test.setText("발송 중...")

        self._test_worker = SmsSendWorker(
            api_key=api_key,
            api_secret=api_secret,
            sender_phone=sender_phone,
            to_phone=to_phone,
            text=preview_text,
            parent=self,
        )
        self._test_worker.finished_signal.connect(self._on_test_sms_result)
        self._test_worker.start()

    def _on_test_sms_result(self, ok: bool, msg: str):
        self.btn_send_test.setEnabled(True)
        self.btn_send_test.setText("➤  테스트 문자 발송")

        if ok:
            CustomAlertDialog("테스트 발송 성공", f"{msg}\n휴대폰 수신함을 확인해 주세요.", self).exec()
            self.refresh_balance()
        else:
            CustomAlertDialog("테스트 발송 실패", f"테스트 문자를 발송하지 못했습니다.\n사유: {msg}", self).exec()