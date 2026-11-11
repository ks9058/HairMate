import os
import shutil
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QStackedWidget, QProgressBar, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from ui.theme import Colors
from core.db_manager import DBManager
from core.encryption_service import EncryptionService
from core.google_drive_service import GoogleDriveService


class RestoreWorker(QThread):
    """구글 드라이브 백업 파일 다운로드 및 DB 복호화 교체 비동기 스레드"""
    finished_signal = Signal(str)  # (restored_file_name)
    failed_signal = Signal(str)    # (error_message)

    def __init__(self, file_id: str, file_name: str, parent=None):
        super().__init__(parent)
        self.file_id = file_id
        self.file_name = file_name

    def run(self):
        temp_enc_path = f"temp_{self.file_name}"
        temp_dec_path = "temp_restored_hairmate.db"
        db_path = os.getenv("DB_PATH", "hairmate.db")
        backup_db_path = f"{db_path}.bak"

        try:
            drive_service = GoogleDriveService()
            enc_service = EncryptionService()

            # 1. 구글 드라이브에서 임시 암호화 백업 파일(.enc) 다운로드
            if not drive_service.download_backup(self.file_id, temp_enc_path):
                self.failed_signal.emit("구글 드라이브에서 백업 파일 다운로드에 실패했습니다.")
                return

            # 2. 임시 파일 복호화 (AES / Fernet)
            if not enc_service.decrypt_db(temp_enc_path, temp_dec_path):
                self.failed_signal.emit("백업 파일 복호화에 실패했습니다. 암호화 키를 확인하세요.")
                return

            # 3. 안전한 DB 교체 트랜잭션
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_db_path)

            shutil.move(temp_dec_path, db_path)

            if os.path.exists(backup_db_path):
                os.remove(backup_db_path)

            self.finished_signal.emit(self.file_name)

        except Exception as e:
            if os.path.exists(backup_db_path):
                try:
                    shutil.move(backup_db_path, db_path)
                except Exception:
                    pass
            self.failed_signal.emit(str(e))

        finally:
            for p in [temp_enc_path, temp_dec_path]:
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass


class SettingsRestoreView(QWidget):
    """설정 > 복원 화면 (클라우드 백업 목록 선택 및 DB 복원)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DBManager()
        self.drive_service = GoogleDriveService()
        self.worker = None
        self.backup_files_data = []
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.stack = QStackedWidget(self)

        # -------------------------------------------------------------
        # State 0: 백업 파일 선택 복원 화면
        # -------------------------------------------------------------
        page_select = QWidget()
        l_select = QVBoxLayout(page_select)
        l_select.setContentsMargins(40, 30, 40, 30)
        l_select.setSpacing(20)

        # 헤더 타이틀 및 설명
        header_box = QVBoxLayout()
        lbl_title = QLabel("데이터 복원하기", page_select)
        lbl_title.setFont(QFont("Inter", 22, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #000000;")

        lbl_sub = QLabel("구글 드라이브에 저장된 백업 파일을 선택하여 현재 데이터를 복원합니다.", page_select)
        lbl_sub.setFont(QFont("Inter", 11))
        lbl_sub.setStyleSheet("color: #666666;")

        header_box.addWidget(lbl_title)
        header_box.addWidget(lbl_sub)
        l_select.addLayout(header_box)

        # -------------------------------------------------------------
        # 백업 파일 목록 테이블
        # -------------------------------------------------------------
        self.table = QTableWidget(page_select)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["번호", "백업 파일명", "파일 크기", "생성 일시"])
        
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        
        self.table.setColumnWidth(0, 70)   # 번호 컬럼
        self.table.setColumnWidth(2, 120)  # 파일 크기
        self.table.setColumnWidth(3, 180)  # 생성 일시

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        # 헤더 높이 및 행 기본 높이 설정
        self.table.horizontalHeader().setFixedHeight(42)
        self.table.verticalHeader().setDefaultSectionSize(40)

        # 💡 헤더 라운드와 세로선 제거를 위한 개선된 스타일시트
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #FFFFFF;
                border: 1px solid #D0D0D0;
                border-radius: 10px;
                outline: none;
            }}
            QHeaderView {{
                background-color: {Colors.PRIMARY};
                border-top-left-radius: 9px;
                border-top-right-radius: 9px;
                border: none;
            }}
            QHeaderView::section {{
                background-color: transparent;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 13px;
                border: none;
                padding: 4px;
            }}
            QHeaderView::section:first {{
                border-top-left-radius: 9px;
            }}
            QHeaderView::section:last {{
                border-top-right-radius: 9px;
            }}
            QTableWidget::item {{
                color: #333333;
                font-size: 13px;
                border-bottom: 1px solid #F0F0F0;
                border-right: none;
                border-left: none;
                padding: 4px;
            }}
            QTableWidget::item:selected {{
                background-color: #E8F5E9;
                color: {Colors.PRIMARY};
                font-weight: bold;
            }}
        """)
        l_select.addWidget(self.table, 1)

        # 하단 버튼 패널
        btn_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("목록 새로고침", page_select)
        self.btn_refresh.setFixedSize(140, 46)
        self.btn_refresh.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F5;
                color: #333333;
                border: 1px solid #CCCCCC;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #EAEAEA;
            }
        """)
        self.btn_refresh.clicked.connect(self.load_backup_list)

        self.btn_start_restore = QPushButton("선택한 백업으로 복원하기", page_select)
        self.btn_start_restore.setFixedSize(220, 46)
        self.btn_start_restore.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        self.btn_start_restore.setCursor(Qt.PointingHandCursor)
        self.btn_start_restore.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
            }}
        """)
        self.btn_start_restore.clicked.connect(self.start_restore)

        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_start_restore)
        l_select.addLayout(btn_layout)

        self.stack.addWidget(page_select)

        # -------------------------------------------------------------
        # State 1: 복원 진행 중 화면
        # -------------------------------------------------------------
        page_progress = QWidget()
        l_prog = QVBoxLayout(page_progress)
        l_prog.setAlignment(Qt.AlignCenter)
        l_prog.setSpacing(25)

        lbl_title2 = QLabel("데이터 복원하기", page_progress)
        lbl_title2.setFont(QFont("Inter", 24, QFont.Weight.Bold))
        lbl_title2.setAlignment(Qt.AlignCenter)
        lbl_title2.setStyleSheet("color: #000000;")

        lbl_warning = QLabel("복원 중입니다. 이 창을 벗어나거나 프로그램을 종료하지 마세요", page_progress)
        lbl_warning.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        lbl_warning.setAlignment(Qt.AlignCenter)
        lbl_warning.setStyleSheet("color: #E53E3E;")

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
        # State 2: 복원 완료 화면
        # -------------------------------------------------------------
        page_complete = QWidget()
        l_comp = QVBoxLayout(page_complete)
        l_comp.setAlignment(Qt.AlignCenter)
        l_comp.setSpacing(18)

        lbl_title3 = QLabel("데이터 복원하기", page_complete)
        lbl_title3.setFont(QFont("Inter", 24, QFont.Weight.Bold))
        lbl_title3.setAlignment(Qt.AlignCenter)

        lbl_success = QLabel("복원이 완벽하게 완료되었습니다!", page_complete)
        lbl_success.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        lbl_success.setAlignment(Qt.AlignCenter)
        lbl_success.setStyleSheet(f"color: {Colors.PRIMARY};")

        self.lbl_result_info = QLabel("복원된 백업 파일: -", page_complete)
        self.lbl_result_info.setFont(QFont("Inter", 12))
        self.lbl_result_info.setAlignment(Qt.AlignCenter)
        self.lbl_result_info.setStyleSheet("color: #333333;")

        self.btn_done = QPushButton("확인", page_complete)
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
        self.btn_done.clicked.connect(self.finish_restore)

        l_comp.addWidget(lbl_title3)
        l_comp.addWidget(lbl_success)
        l_comp.addSpacing(5)
        l_comp.addWidget(self.lbl_result_info)
        l_comp.addSpacing(15)
        l_comp.addWidget(self.btn_done, 0, Qt.AlignCenter)

        self.stack.addWidget(page_complete)

        main_layout.addWidget(self.stack)
        self.stack.setCurrentIndex(0)

    def load_backup_list(self):
        """구글 드라이브 내 백업 파일 목록을 조회하여 최신 순 번호(역순)와 함께 바인딩"""
        self.table.setRowCount(0)
        self.backup_files_data = self.drive_service.list_all_backups()

        if not self.backup_files_data:
            return

        total_count = len(self.backup_files_data)
        self.table.setRowCount(total_count)

        for row, f in enumerate(self.backup_files_data):
            row_num_str = str(total_count - row)

            name = f.get('name', '')
            size_bytes = int(f.get('size', 0)) if f.get('size') else 0
            size_mb = round(size_bytes / (1024 * 1024), 1)
            size_str = f"{size_mb} MB" if size_mb >= 0.1 else f"{round(size_bytes / 1024, 1)} KB"

            created_raw = f.get('createdTime', '')
            created_str = created_raw
            if created_raw:
                try:
                    dt = datetime.fromisoformat(created_raw.replace('Z', '+00:00'))
                    created_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass

            item_num = QTableWidgetItem(row_num_str)
            item_num.setTextAlignment(Qt.AlignCenter)

            item_name = QTableWidgetItem(name)
            item_name.setTextAlignment(Qt.AlignCenter)

            item_size = QTableWidgetItem(size_str)
            item_size.setTextAlignment(Qt.AlignCenter)

            item_created = QTableWidgetItem(created_str)
            item_created.setTextAlignment(Qt.AlignCenter)

            self.table.setItem(row, 0, item_num)
            self.table.setItem(row, 1, item_name)
            self.table.setItem(row, 2, item_size)
            self.table.setItem(row, 3, item_created)

    def start_restore(self):
        """선택한 백업 파일로 데이터 복원 시작"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "백업 미선택", "복원할 백업 파일을 목록에서 선택해 주세요.")
            return

        row = selected_rows[0].row()
        file_info = self.backup_files_data[row]
        file_id = file_info['id']
        file_name = file_info['name']

        reply = QMessageBox.question(
            self, 
            "데이터 복원 확인", 
            f"선택한 백업 [{file_name}] 파일로 데이터베이스를 복원하시겠습니까?\n\n"
            "⚠️ 주의: 복원 진행 시 현재 작성된 최신 데이터는 덮어씌워집니다.",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        self.stack.setCurrentIndex(1)

        self.worker = RestoreWorker(file_id, file_name)
        self.worker.finished_signal.connect(self.on_restore_success)
        self.worker.failed_signal.connect(self.on_restore_failed)
        self.worker.start()

    def on_restore_success(self, file_name: str):
        self.lbl_result_info.setText(f"복원된 백업 파일명: {file_name}")
        self.stack.setCurrentIndex(2)

    def on_restore_failed(self, error_msg: str):
        self.stack.setCurrentIndex(0)
        QMessageBox.critical(self, "복원 실패", f"데이터 복원 중 오류가 발생했습니다:\n\n{error_msg}")

    def finish_restore(self):
        self.stack.setCurrentIndex(0)
        self.load_backup_list()