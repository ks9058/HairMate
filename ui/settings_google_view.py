from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDialog, QFrame
)
from PySide6.QtCore import Qt, Signal, QSize, QThread
from PySide6.QtGui import QFont
from ui.theme import Colors, Styles, get_icon
from core.google_drive_service import GoogleDriveService


class CustomAlertDialog(QDialog):
    """커스텀 단일 알림 팝업 모달 (텍스트 굵게 수정)"""
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(380, 190)

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

        lbl_msg = QLabel(message, container)
        lbl_msg.setFont(QFont("Inter", 12, QFont.Bold))
        lbl_msg.setAlignment(Qt.AlignCenter)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet("border: none; background: transparent; color: #000000; font-weight: bold;")
        c_layout.addWidget(lbl_msg)

        btn_confirm = QPushButton("확인", container)
        btn_confirm.setFixedHeight(40)
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
        c_layout.addWidget(btn_confirm)

        outer_layout.addWidget(container)


class CustomConfirmDialog(QDialog):
    """커스텀 확인/취소 선택 팝업 모달 (텍스트 굵게 수정)"""
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(400, 220)

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

        lbl_msg = QLabel(message, container)
        lbl_msg.setFont(QFont("Inter", 12, QFont.Bold))
        lbl_msg.setAlignment(Qt.AlignCenter)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet("border: none; background: transparent; color: #000000; font-weight: bold;")
        c_layout.addWidget(lbl_msg)

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

        self.lbl_title = QLabel("구글 계정 인증", self)
        self.lbl_title.setFont(QFont("Inter", 22, QFont.Weight.Bold))
        self.lbl_title.setStyleSheet(f"color: {Colors.TEXT_MAIN};")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.lbl_title)

        self.content_widget = QWidget(self)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignCenter)
        self.content_layout.setSpacing(12)
        
        self.layout.addWidget(self.content_widget)
        self.refresh_auth_status()

    def refresh_auth_status(self):
        self.drive_service = GoogleDriveService()
        self.render_view()

    def render_view(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        is_auth = self.drive_service.is_authenticated()

        if is_auth:
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
        self.worker = AuthWorker()
        self.worker.finished_signal.connect(self.on_auth_finished)
        self.worker.start()

    def on_auth_finished(self, success: bool, msg: str):
        if success:
            self.refresh_auth_status()
            self.auth_requested.emit()
            CustomAlertDialog("인증 성공", "구글 계정 연동이 완료되었습니다.", self).exec()
        else:
            CustomAlertDialog("인증 실패", f"구글 계정 연동 실패:\n\n{msg}", self).exec()

    def on_disconnect_click(self):
        dialog = CustomConfirmDialog(
            "계정 연동 해제",
            "구글 계정 연동을 해제하시겠습니까?<br>해제 시 클라우드 백업 및 복원 기능을 이용할 수 없습니다.",
            self
        )
        if dialog.exec() == QDialog.Accepted:
            if self.drive_service.disconnect():
                self.refresh_auth_status()
                CustomAlertDialog("해제 완료", "구글 계정 연동이 성공적으로 해제되었습니다.", self).exec()