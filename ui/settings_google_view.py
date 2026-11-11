from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QSize, QThread
from PySide6.QtGui import QFont
from ui.theme import Colors, Styles, get_icon
from core.google_drive_service import GoogleDriveService


class AuthWorker(QThread):
    """구글 계정 비동기 인증 스레드"""
    finished_signal = Signal(bool, str)

    def run(self):
        try:
            drive_service = GoogleDriveService()
            if drive_service.authenticate():
                self.finished_signal.emit(True, "인증 성공")
            else:
                self.finished_signal.emit(False, "구글 인증에 실패했습니다.")
        except Exception as e:
            self.finished_signal.emit(False, str(e))


class SettingsGoogleView(QWidget):
    """설정 > 구글 계정 인증 뷰"""
    auth_requested = Signal()

    def __init__(self):
        super().__init__()
        self.drive_service = GoogleDriveService()
        self.worker = None
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.setSpacing(15)

        # 상단 타이틀
        self.lbl_title = QLabel("구글 계정 인증", self)
        self.lbl_title.setFont(QFont("Inter", 22, QFont.Weight.Bold))
        self.lbl_title.setStyleSheet(f"color: {Colors.TEXT_MAIN};")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.lbl_title)

        # 동적 컨텐트 컨테이너
        self.content_widget = QWidget(self)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignCenter)
        self.content_layout.setSpacing(12)
        
        self.layout.addWidget(self.content_widget)
        self.refresh_auth_status()

    def refresh_auth_status(self):
        """현재 토큰 상태 확인 후 UI 재렌더링"""
        self.drive_service = GoogleDriveService()
        self.render_view()

    def render_view(self):
        """인증 완료 / 미인증 상태 렌더링"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        is_auth = self.drive_service.is_authenticated()

        if is_auth:
            # 1. 인증 완료 상태 UI
            acc_info = self.drive_service.get_account_info()
            last_date = self.drive_service.get_last_auth_date()

            lbl_email = QLabel(f"연동 계정 : {acc_info.get('email', '-')}", self)
            lbl_email.setFont(QFont("Inter", 13, QFont.Weight.Bold))
            lbl_email.setStyleSheet(f"color: {Colors.TEXT_MAIN}; margin-top: 10px;")
            lbl_email.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(lbl_email)

            lbl_date = QLabel(f"최근 인증일시 : {last_date}", self)
            lbl_date.setFont(QFont("Inter", 11))
            lbl_date.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
            lbl_date.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(lbl_date)

            lbl_status = QLabel("구글 드라이브 클라우드 백업 서비스가 연결되어 있습니다.", self)
            lbl_status.setFont(QFont("Inter", 11, QFont.Weight.Bold))
            lbl_status.setStyleSheet(f"color: {Colors.PRIMARY}; margin-top: 5px;")
            lbl_status.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(lbl_status)

            # 연동 해제 버튼
            btn_logout = QPushButton("구글 계정 연동 해제", self)
            btn_logout.setFixedSize(300, 45)
            btn_logout.setCursor(Qt.PointingHandCursor)
            btn_logout.setFont(QFont("Inter", 11, QFont.Weight.Bold))
            btn_logout.setStyleSheet("""
                QPushButton {
                    background-color: #FFF0F0;
                    color: #E53E3E;
                    border: 1px solid #FEB2B2;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #FED7D7;
                }
            """)
            btn_logout.clicked.connect(self.on_disconnect_click)
            self.content_layout.addWidget(btn_logout, alignment=Qt.AlignCenter)

        else:
            # 2. 미인증 상태 UI
            btn_login = QPushButton("     구글 계정 인증하기", self)
            btn_login.setFixedSize(300, 45)
            btn_login.setCursor(Qt.PointingHandCursor)
            btn_login.setIcon(get_icon("google.svg"))
            btn_login.setIconSize(QSize(20, 20))
            btn_login.setStyleSheet(Styles.PRIMARY_BUTTON)
            btn_login.clicked.connect(self.on_auth_click)
            self.content_layout.addWidget(btn_login, alignment=Qt.AlignCenter)

            lbl_warn = QLabel("백업 및 복원 기능을 사용하려면 구글 계정 인증이 필요합니다.", self)
            lbl_warn.setFont(QFont("Inter", 10, QFont.Weight.Bold))
            lbl_warn.setStyleSheet(f"color: {Colors.DANGER}; margin-top: 5px;")
            lbl_warn.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(lbl_warn)

    def on_auth_click(self):
        """인증 버튼 클릭 핸들러"""
        self.worker = AuthWorker()
        self.worker.finished_signal.connect(self.on_auth_finished)
        self.worker.start()

    def on_auth_finished(self, success: bool, msg: str):
        if success:
            self.refresh_auth_status()
            self.auth_requested.emit()
            QMessageBox.information(self, "인증 성공", "구글 계정 연동이 완료되었습니다.")
        else:
            QMessageBox.critical(self, "인증 실패", f"구글 계정 연동 실패:\n\n{msg}")

    def on_disconnect_click(self):
        """연동 해제 버튼 클릭 핸들러"""
        reply = QMessageBox.question(
            self,
            "계정 연동 해제",
            "구글 계정 연동을 해제하시겠습니까?\n해제 시 클라우드 백업 및 복원 기능을 이용할 수 없습니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.drive_service.disconnect():
                self.refresh_auth_status()
                QMessageBox.information(self, "해제 완료", "구글 계정 연동이 성공적으로 해제되었습니다.")