import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox, QProgressBar
from PySide6.QtCore import Qt, Signal, QSize, QThread
from PySide6.QtGui import QFont
from ui.theme import Colors, Styles, get_icon, load_fonts
from core.google_drive_service import GoogleDriveService


class LoginWorker(QThread):
    """구글 로그인 OAuth 브라우저 인증 비동기 스레드"""
    success_signal = Signal(str)  # email
    failed_signal = Signal(str)   # error_msg

    def run(self):
        try:
            drive_service = GoogleDriveService()
            # 강제로 구글 인증 실행 (token.json 생성 및 계정 선택)
            if drive_service.authenticate():
                acc_info = drive_service.get_account_info()
                self.success_signal.emit(acc_info.get("email", ""))
            else:
                self.failed_signal.emit("구글 계정 인증에 실패했습니다.")
        except Exception as e:
            self.failed_signal.emit(str(e))


class LoginView(QWidget):
    """Kaushan Script 로고 및 Google OAuth 연동 로그인 화면"""
    login_requested = Signal()
    login_success = Signal(str)

    def __init__(self):
        super().__init__()
        self.kaushan_font_family = load_fonts()
        self.worker = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("HairMate - 로그인")
        self.resize(800, 500)
        self.setStyleSheet(f"background-color: {Colors.BACKGROUND};")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(25)

        # 1. HairMate 브랜드 로고
        title_label = QLabel("HairMate", self)
        title_font = QFont(self.kaushan_font_family, 48)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {Colors.TEXT_MAIN}; background: transparent;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 2. 상태 안내 라벨
        self.lbl_status = QLabel("서비스 이용을 위해 구글 계정으로 로그인해 주세요.", self)
        self.lbl_status.setFont(QFont("Inter", 11))
        self.lbl_status.setStyleSheet(f"color: {Colors.TEXT_MUTED}; background: transparent;")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_status)

        # 3. 진행바 (인증 중 표시)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setFixedSize(280, 6)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: #E0E0E0;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {Colors.PRIMARY};
                border-radius: 3px;
            }}
        """)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)

        # 4. 구글 로그인 버튼
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
        """실제 구글 OAuth 인증 진행"""
        self.btn_google_login.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.lbl_status.setText("웹 브라우저에서 구글 계정을 선택해 주세요...")
        self.lbl_status.setStyleSheet(f"color: {Colors.PRIMARY}; font-weight: bold;")

        self.worker = LoginWorker()
        self.worker.success_signal.connect(self.on_login_success)
        self.worker.failed_signal.connect(self.on_login_failed)
        self.worker.start()

    def on_login_success(self, email: str):
        self.btn_google_login.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.login_success.emit(email)
        self.login_requested.emit()

    def on_login_failed(self, error_msg: str):
        self.btn_google_login.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("구글 계정 인증이 필요합니다.")
        self.lbl_status.setStyleSheet(f"color: {Colors.DANGER}; font-weight: bold;")
        QMessageBox.critical(self, "로그인 실패", f"구글 OAuth 인증 중 오류가 발생했습니다:\n\n{error_msg}")