import os
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QStackedWidget, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QColor
from ui.theme import Colors
from core.db_manager import DBManager
from core.encryption_service import EncryptionService
from core.google_drive_service import GoogleDriveService


class BackupWorker(QThread):
    """백업 처리 비동기 스레드 (UI 멈춤 방지)"""
    finished_signal = Signal(str, str, str)  # (file_name, file_size_str, date_str)
    failed_signal = Signal(str)              # (error_message)

    def run(self):
        try:
            enc_service = EncryptionService()
            drive_service = GoogleDriveService()

            # 1. DB 파일 존재 확인
            db_path = os.getenv("DB_PATH", "hairmate.db")
            if not os.path.exists(db_path):
                self.failed_signal.emit("SQLite DB 파일(hairmate.db)을 찾을 수 없습니다.")
                return

            # 2. 당일 백업 순번(1, 2, 3...) 자동 산출하여 파일명 생성
            now = datetime.now()
            date_str_file = now.strftime("%Y%m%d")      # 예: 20261111
            date_str_display = now.strftime("%Y-%m-%d")  # 예: 2026-11-11

            # 구글 드라이브 내 기존 백업 파일 목록 조회 후 당일 최대 차수 계산
            existing_files = drive_service.list_backups()
            prefix = f"HairMate_Backup_{date_str_file}_"
            max_index = 0

            for f in existing_files:
                f_name = f.get('name', '')
                if f_name.startswith(prefix) and f_name.endswith('.enc'):
                    # 'HairMate_Backup_20261111_' 와 '.enc' 사이의 숫자를 추출
                    num_part = f_name[len(prefix):-4]
                    if num_part.isdigit():
                        max_index = max(max_index, int(num_part))

            next_index = max_index + 1
            file_name = f"HairMate_Backup_{date_str_file}_{next_index}.enc"
            
            # 현재 작업 디렉터리에 임시 백업 파일 생성
            temp_enc_path = os.path.abspath(file_name)

            # 3. Fernet AES 암호화 수행
            if not enc_service.encrypt_db(db_path, temp_enc_path):
                self.failed_signal.emit("로컬 DB 암호화에 실패했습니다.")
                return

            # 4. 파일 크기 계산
            file_size_bytes = os.path.getsize(temp_enc_path)
            file_size_mb = round(file_size_bytes / (1024 * 1024), 1)
            if file_size_mb < 0.1:
                file_size_str = f"{round(file_size_bytes / 1024, 1)} KB"
            else:
                file_size_str = f"{int(file_size_mb) if file_size_mb.is_integer() else file_size_mb} MB"

            # 5. 구글 드라이브 업로드
            drive_service.upload_backup(temp_enc_path)

            # 6. 임시 로컬 암호화 파일 삭제
            if os.path.exists(temp_enc_path):
                os.remove(temp_enc_path)

            self.finished_signal.emit(file_name, file_size_str, date_str_display)

        except Exception as e:
            # 에러 발생 시 남아있는 임시 파일 정리
            if 'temp_enc_path' in locals() and os.path.exists(temp_enc_path):
                try:
                    os.remove(temp_enc_path)
                except Exception:
                    pass
            self.failed_signal.emit(str(e))


class SettingsBackupView(QWidget):
    """설정 > 백업 화면 (3가지 상태 전환 및 백업 연동)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DBManager()
        self.worker = None
        self.setup_ui()
        self.load_last_backup_date()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 3개 상태 페이지 관리를 위한 StackedWidget
        self.stack = QStackedWidget(self)

        # -------------------------------------------------------------
        # State 0: 백업 대기 화면 (초기 상태)
        # -------------------------------------------------------------
        page_ready = QWidget()
        l_ready = QVBoxLayout(page_ready)
        l_ready.setAlignment(Qt.AlignCenter)
        l_ready.setSpacing(25)

        lbl_title1 = QLabel("데이터 백업하기", page_ready)
        lbl_title1.setFont(QFont("Inter", 24, QFont.Weight.Bold))
        lbl_title1.setAlignment(Qt.AlignCenter)
        lbl_title1.setStyleSheet("color: #000000;")

        self.lbl_last_backup = QLabel("최근 백업일 : -", page_ready)
        self.lbl_last_backup.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        self.lbl_last_backup.setAlignment(Qt.AlignCenter)
        self.lbl_last_backup.setStyleSheet("color: #333333;")

        self.btn_start_backup = QPushButton("현재 데이터 백업하기", page_ready)
        self.btn_start_backup.setFixedSize(360, 52)
        self.btn_start_backup.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        self.btn_start_backup.setCursor(Qt.PointingHandCursor)
        self.btn_start_backup.setStyleSheet(f"""
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
        self.btn_start_backup.clicked.connect(self.start_backup)

        l_ready.addWidget(lbl_title1)
        l_ready.addWidget(self.lbl_last_backup)
        l_ready.addSpacing(10)
        l_ready.addWidget(self.btn_start_backup, 0, Qt.AlignCenter)

        self.stack.addWidget(page_ready)

        # -------------------------------------------------------------
        # State 1: 백업 진행 중 화면
        # -------------------------------------------------------------
        page_progress = QWidget()
        l_prog = QVBoxLayout(page_progress)
        l_prog.setAlignment(Qt.AlignCenter)
        l_prog.setSpacing(25)

        lbl_title2 = QLabel("데이터 백업하기", page_progress)
        lbl_title2.setFont(QFont("Inter", 24, QFont.Weight.Bold))
        lbl_title2.setAlignment(Qt.AlignCenter)
        lbl_title2.setStyleSheet("color: #000000;")

        lbl_warning = QLabel("백업 중입니다. 이 창을 벗어나지 마세요", page_progress)
        lbl_warning.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        lbl_warning.setAlignment(Qt.AlignCenter)
        lbl_warning.setStyleSheet("color: #E53E3E;")

        # 무한 로딩 인디케이터 바
        self.progress_bar = QProgressBar(page_progress)
        self.progress_bar.setFixedSize(280, 8)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: #E0E0E0;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {Colors.PRIMARY};
                border-radius: 4px;
            }}
        """)

        l_prog.addWidget(lbl_title2)
        l_prog.addWidget(lbl_warning)
        l_prog.addSpacing(10)
        l_prog.addWidget(self.progress_bar, 0, Qt.AlignCenter)

        self.stack.addWidget(page_progress)

        # -------------------------------------------------------------
        # State 2: 백업 완료 화면
        # -------------------------------------------------------------
        page_complete = QWidget()
        l_comp = QVBoxLayout(page_complete)
        l_comp.setAlignment(Qt.AlignCenter)
        l_comp.setSpacing(18)

        lbl_title3 = QLabel("데이터 백업하기", page_complete)
        lbl_title3.setFont(QFont("Inter", 24, QFont.Weight.Bold))
        lbl_title3.setAlignment(Qt.AlignCenter)
        lbl_title3.setStyleSheet("color: #000000;")

        lbl_success = QLabel("백업이 완료되었습니다.", page_complete)
        lbl_success.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        lbl_success.setAlignment(Qt.AlignCenter)
        lbl_success.setStyleSheet(f"color: {Colors.PRIMARY};")

        self.lbl_result_filename = QLabel("백업 파일명: -", page_complete)
        self.lbl_result_filename.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        self.lbl_result_filename.setAlignment(Qt.AlignCenter)
        self.lbl_result_filename.setStyleSheet("color: #222222;")

        self.lbl_result_filesize = QLabel("파일크기: -", page_complete)
        self.lbl_result_filesize.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        self.lbl_result_filesize.setAlignment(Qt.AlignCenter)
        self.lbl_result_filesize.setStyleSheet("color: #222222;")

        self.btn_done = QPushButton("완료", page_complete)
        self.btn_done.setFixedSize(360, 52)
        self.btn_done.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        self.btn_done.setCursor(Qt.PointingHandCursor)
        self.btn_done.setStyleSheet(f"""
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
        self.btn_done.clicked.connect(self.finish_backup)

        l_comp.addWidget(lbl_title3)
        l_comp.addWidget(lbl_success)
        l_comp.addSpacing(5)
        l_comp.addWidget(self.lbl_result_filename)
        l_comp.addWidget(self.lbl_result_filesize)
        l_comp.addSpacing(10)
        l_comp.addWidget(self.btn_done, 0, Qt.AlignCenter)

        self.stack.addWidget(page_complete)

        main_layout.addWidget(self.stack)
        self.stack.setCurrentIndex(0)

    def load_last_backup_date(self):
        """DB 설정 테이블에서 최근 백업 일자 조회"""
        last_date = self.db_manager.get_setting("last_backup_date", default="")
        if last_date:
            self.lbl_last_backup.setText(f"최근 백업일 : {last_date}")
        else:
            self.lbl_last_backup.setText("최근 백업일 : 내역 없음")

    def start_backup(self):
        """백업 시작 핸들러"""
        self.stack.setCurrentIndex(1)

        self.worker = BackupWorker()
        self.worker.finished_signal.connect(self.on_backup_success)
        self.worker.failed_signal.connect(self.on_backup_failed)
        self.worker.start()

    def on_backup_success(self, file_name: str, file_size_str: str, date_str: str):
        """백업 성공 시 정보 표시 및 DB 설정 갱신"""
        self.db_manager.set_setting("last_backup_date", date_str)
        self.load_last_backup_date()

        self.lbl_result_filename.setText(f"백업 파일명: {file_name}")
        self.lbl_result_filesize.setText(f"파일크기: {file_size_str}")

        self.stack.setCurrentIndex(2)

    def on_backup_failed(self, error_msg: str):
        """백업 실패 처리"""
        self.stack.setCurrentIndex(0)
        QMessageBox.critical(self, "백업 실패", f"구글 드라이브 데이터 백업 중 오류가 발생했습니다:\n\n{error_msg}")

    def finish_backup(self):
        """완료 버튼 클릭 시 대기 화면으로 복귀"""
        self.stack.setCurrentIndex(0)