from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont
from ui.theme import Colors, Styles, get_icon, load_fonts

class LoginView(QWidget):
    """Kaushan Script 로고 및 Google SVG가 적용된 로그인 화면"""
    login_requested = Signal()

    def __init__(self):
        super().__init__()
        self.kaushan_font_family = load_fonts()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("HairMate - 로그인")
        self.resize(800, 500)
        self.setStyleSheet(f"background-color: {Colors.BACKGROUND};")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(35)

        # 1. HairMate 브랜드 로고 (Kaushan Script)
        title_label = QLabel("HairMate", self)
        title_font = QFont(self.kaushan_font_family, 48)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {Colors.TEXT_MAIN}; background: transparent;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 2. 구글 로그인 버튼
        self.btn_google_login = QPushButton("      구글 계정으로 로그인", self)
        self.btn_google_login.setFixedSize(350, 48)
        self.btn_google_login.setCursor(Qt.PointingHandCursor)
        
        icon = get_icon("google.svg")
        if not icon.isNull():
            self.btn_google_login.setIcon(icon)
            self.btn_google_login.setIconSize(QSize(22, 22))

        self.btn_google_login.setStyleSheet(Styles.PRIMARY_BUTTON)
        self.btn_google_login.clicked.connect(self.on_google_login_clicked)
        
        layout.addWidget(self.btn_google_login, alignment=Qt.AlignCenter)

    def on_google_login_clicked(self):
        print("[OAuth Stub] 구글 로그인 요청...")
        self.login_requested.emit()