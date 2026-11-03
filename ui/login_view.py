from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt

class LoginView(QWidget):
    """초기 진입용 로그인 화면 UI"""
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("HairMate - 미용실 관리 시스템")
        self.resize(400, 300)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # 타이틀 로고
        title_label = QLabel("HairMate", self)
        title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #005F4B; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 구글 로그인 버튼
        self.btn_google_login = QPushButton("G 구글 계정으로 로그인", self)
        self.btn_google_login.setFixedSize(260, 42)
        self.btn_google_login.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
            }
        """)
        layout.addWidget(self.btn_google_login)