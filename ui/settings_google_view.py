from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont
from ui.theme import Colors, Styles, get_icon

class SettingsGoogleView(QWidget):
    """설정 > 구글 계정 인증 뷰"""
    auth_requested = Signal()

    def __init__(self):
        super().__init__()
        self.is_authenticated = False
        self.last_auth_date = "2025-08-26"
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.setSpacing(15)

        # 상단 타이틀
        self.lbl_title = QLabel("구글 계정 인증", self)
        self.lbl_title.setFont(QFont("Malgun Gothic", 22, QFont.Bold))
        self.lbl_title.setStyleSheet(f"color: {Colors.TEXT_MAIN};")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.lbl_title)

        # 동적 컨텐츠 동적 컨테이너
        self.content_widget = QWidget(self)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignCenter)
        self.content_layout.setSpacing(12)
        
        self.layout.addWidget(self.content_widget)
        self.render_view()

    def render_view(self):
        """인증 완료 / 인증 필요 상태 렌더링"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if self.is_authenticated:
            # 인증 완료 상태 뷰
            lbl_date = QLabel(f"최근 인증일 : {self.last_auth_date}", self)
            lbl_date.setFont(QFont("Malgun Gothic", 14, QFont.Bold))
            lbl_date.setStyleSheet(f"color: {Colors.TEXT_MAIN}; margin-top: 10px;")
            lbl_date.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(lbl_date)

            lbl_status = QLabel("구글 계정 인증이 완료되었습니다.", self)
            lbl_status.setFont(QFont("Malgun Gothic", 11, QFont.Bold))
            lbl_status.setStyleSheet(f"color: {Colors.PRIMARY}; margin-top: 5px;")
            lbl_status.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(lbl_status)

        else:
            # 인증 필요 상태 뷰 (로그인 인증 버튼 + 안내 문구)
            btn_login = QPushButton("     로그인 인증", self)
            btn_login.setFixedSize(300, 45)
            btn_login.setCursor(Qt.PointingHandCursor)
            btn_login.setIcon(get_icon("google.svg"))
            btn_login.setIconSize(QSize(20, 20))
            btn_login.setStyleSheet(Styles.PRIMARY_BUTTON)
            btn_login.clicked.connect(self.on_auth_click)
            self.content_layout.addWidget(btn_login, alignment=Qt.AlignCenter)

            lbl_warn = QLabel("구글 계정 인증이 필요합니다.", self)
            lbl_warn.setFont(QFont("Malgun Gothic", 10, QFont.Bold))
            lbl_warn.setStyleSheet(f"color: {Colors.DANGER}; margin-top: 5px;")
            lbl_warn.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(lbl_warn)

    def on_auth_click(self):
        """인증 버튼 클릭 토글 시뮬레이션"""
        print("[OAuth Stub] 계정 인증 진행...")
        self.is_authenticated = True
        self.render_view()
        self.auth_requested.emit()