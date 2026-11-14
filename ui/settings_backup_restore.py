import os
import re
import shutil
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QStackedWidget, QProgressBar, QDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QColor, QPainterPath, QTextDocument
from ui.theme import Colors
from core.db_manager import DBManager
from core.backup_manager import BackupManager
from core.encryption_service import EncryptionService
from core.google_drive_service import GoogleDriveService


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


class CustomAlertDialog(QDialog):
    """커스텀 단일 알림 팝업 모달"""
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(400, 200)

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
    """커스텀 확인/취소 선택 팝업 모달"""
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(410, 230)

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


class ProgressPopupDialog(QDialog):
    """백업/삭제 작업 시 표시하는 진행 안내 모달"""
    def __init__(self, title_text: str, desc_text: str, parent=None):
        super().__init__(parent)
        self._can_close = False
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setModal(True)
        self.setFixedSize(410, 200)

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
        c_layout.setContentsMargins(25, 25, 25, 25)
        c_layout.setSpacing(15)

        lbl_title = QLabel(title_text, container)
        lbl_title.setFont(QFont("Inter", 15, QFont.Bold))
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("border: none; background: transparent; color: #000000;")
        c_layout.addWidget(lbl_title)

        lbl_desc = QLabel(desc_text, container)
        lbl_desc.setFont(QFont("Inter", 11, QFont.Bold))
        lbl_desc.setAlignment(Qt.AlignCenter)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("border: none; background: transparent; color: #E53E3E;")
        c_layout.addWidget(lbl_desc)

        progress = QProgressBar(container)
        progress.setFixedSize(290, 8)
        progress.setRange(0, 0)
        progress.setTextVisible(False)
        progress.setStyleSheet(f"""
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
        c_layout.addWidget(progress, 0, Qt.AlignCenter)

        outer_layout.addWidget(container)

    def finish_close(self):
        self._can_close = True
        self.accept()

    def closeEvent(self, event):
        if not self._can_close:
            event.ignore()
        else:
            super().closeEvent(event)


class RoundedHeader(QHeaderView):
    """상단 양쪽 모서리 라운드 적용 및 세로 구분선 제거 커스텀 헤더 뷰"""
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setDefaultAlignment(Qt.AlignCenter)

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()

        r = 8.0
        x, y, w, h = float(rect.x()), float(rect.y()), float(rect.width()), float(rect.height())
        count = self.count()

        path = QPainterPath()
        if count == 1:
            path.moveTo(x + r, y)
            path.lineTo(x + w - r, y)
            path.quadTo(x + w, y, x + w, y + r)
            path.lineTo(x + w, y + h)
            path.lineTo(x, y + h)
            path.lineTo(x, y + r)
            path.quadTo(x, y, x + r, y)
        elif logicalIndex == 0:
            path.moveTo(x + r, y)
            path.lineTo(x + w, y)
            path.lineTo(x + w, y + h)
            path.lineTo(x, y + h)
            path.lineTo(x, y + r)
            path.quadTo(x, y, x + r, y)
        elif logicalIndex == count - 1:
            path.moveTo(x, y)
            path.lineTo(x + w - r, y)
            path.quadTo(x + w, y, x + w, y + r)
            path.lineTo(x + w, y + h)
            path.lineTo(x, y + h)
            path.closeSubpath()
        else:
            path.addRect(rect)

        painter.fillPath(path, QColor(Colors.PRIMARY))

        text = self.model().headerData(logicalIndex, self.orientation(), Qt.DisplayRole)
        if text:
            doc = QTextDocument()
            doc.setHtml(
                f"<div style='color: #FFFFFF; font-weight: bold; font-size: 13px; text-align: center;'>{text}</div>"
            )
            doc.setTextWidth(rect.width())

            y_offset = (rect.height() - doc.size().height()) / 2
            painter.translate(rect.x(), rect.y() + y_offset)
            doc.drawContents(painter)

        painter.restore()


class BackupWorker(QThread):
    """수동 백업 처리 비동기 스레드"""
    finished_signal = Signal(str, str, str)  # (file_name, file_size_str, date_str)
    failed_signal = Signal(str)

    def run(self):
        try:
            db_path = os.getenv("DB_PATH", "hairmate.db")
            backup_mgr = BackupManager(db_path=db_path)

            if not os.path.exists(backup_mgr.db_path):
                self.failed_signal.emit("SQLite DB 파일(hairmate.db)을 찾을 수 없습니다.")
                return

            success, msg, info = backup_mgr.run_manual_backup(
                upload_to_drive=True,
                require_drive=True
            )

            if not success:
                self.failed_signal.emit(msg)
                return

            self.finished_signal.emit(
                info["filename"],
                info["file_size_str"],
                info["date_display"]
            )
        except Exception as e:
            self.failed_signal.emit(str(e))


class RestoreWorker(QThread):
    """구글 드라이브 백업 파일 다운로드 및 DB 복호화 교체 비동기 스레드"""
    finished_signal = Signal(str)
    failed_signal = Signal(str)

    def __init__(self, file_id: str, file_name: str, parent=None):
        super().__init__(parent)
        self.file_id = file_id
        self.file_name = file_name

    def run(self):
        temp_enc_path = f"temp_{self.file_name}"
        temp_dec_path = "temp_restored_hairmate.db"
        backup_mgr = BackupManager(db_path=os.getenv("DB_PATH", "hairmate.db"))
        db_path = backup_mgr.db_path
        backup_db_path = f"{db_path}.bak"

        try:
            drive_service = GoogleDriveService()
            enc_service = EncryptionService()

            if not drive_service.download_backup(self.file_id, temp_enc_path):
                self.failed_signal.emit("구글 드라이브에서 백업 파일 다운로드에 실패했습니다.")
                return

            if not enc_service.decrypt_db(temp_enc_path, temp_dec_path):
                self.failed_signal.emit("백업 파일 복호화에 실패했습니다. 암호화 키를 확인하세요.")
                return

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


class DeleteBackupWorker(QThread):
    """구글 드라이브 백업 파일 삭제 비동기 스레드"""
    finished_signal = Signal(str)
    failed_signal = Signal(str)

    def __init__(self, file_id: str, file_name: str, parent=None):
        super().__init__(parent)
        self.file_id = file_id
        self.file_name = file_name

    def run(self):
        try:
            drive_service = GoogleDriveService()
            if drive_service.delete_backup(self.file_id):
                self.finished_signal.emit(self.file_name)
            else:
                self.failed_signal.emit("구글 드라이브에서 백업 파일을 삭제하지 못했습니다.")
        except Exception as e:
            self.failed_signal.emit(str(e))


class SettingsBackupRestoreView(QWidget):
    """설정 > 백업 및 복원 단일 통합 화면"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DBManager()
        self.drive_service = GoogleDriveService()
        self.backup_worker = None
        self.restore_worker = None
        self.delete_worker = None
        self.progress_popup = None
        self.backup_files_data = []

        self.setup_ui()
        self.refresh_all()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.stack = QStackedWidget(self)
        self.stack.setStyleSheet(f"background-color: {Colors.BACKGROUND};")

        # State 0: 단일 백업 및 복원 관리 메인 화면
        page_main = QWidget()
        l_main = QVBoxLayout(page_main)
        l_main.setContentsMargins(40, 30, 40, 30)
        l_main.setSpacing(18)

        header_row = QHBoxLayout()
        header_box = QVBoxLayout()
        header_box.setSpacing(6)

        lbl_title = QLabel("데이터 백업 및 복원", page_main)
        lbl_title.setFont(QFont("Inter", 22, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #000000;")

        lbl_sub = QLabel(
            "구글 드라이브에 저장된 백업 파일을 복원하거나 삭제할 수 있으며, 현재 데이터를 즉시 백업할 수 있습니다.",
            page_main
        )
        lbl_sub.setFont(QFont("Inter", 11))
        lbl_sub.setStyleSheet("color: #666666;")

        header_box.addWidget(lbl_title)
        header_box.addWidget(lbl_sub)
        header_row.addLayout(header_box)
        header_row.addStretch()

        right_header_box = QVBoxLayout()
        right_header_box.setSpacing(6)
        right_header_box.setAlignment(Qt.AlignRight | Qt.AlignBottom)

        self.lbl_last_backup = QLabel("최근 백업일 : -", page_main)
        self.lbl_last_backup.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        self.lbl_last_backup.setAlignment(Qt.AlignRight)
        self.lbl_last_backup.setStyleSheet("color: #555555;")

        self.btn_quick_backup = QPushButton("+ 현재 데이터 백업", page_main)
        self.btn_quick_backup.setFixedSize(165, 42)
        self.btn_quick_backup.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        self.btn_quick_backup.setCursor(Qt.PointingHandCursor)
        self.btn_quick_backup.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: {Colors.PRIMARY};
                border: 2px solid {Colors.PRIMARY};
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: #E8F5E9;
            }}
        """)
        self.btn_quick_backup.clicked.connect(self.start_backup)

        right_header_box.addWidget(self.lbl_last_backup)
        right_header_box.addWidget(self.btn_quick_backup)
        header_row.addLayout(right_header_box)

        l_main.addLayout(header_row)

        table_container = QFrame(page_main)
        table_container.setStyleSheet("background-color: #FFFFFF; border-radius: 10px;")
        table_container.setAttribute(Qt.WA_StyledBackground, True)

        t_layout = QVBoxLayout(table_container)
        t_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(table_container)

        custom_header = RoundedHeader(Qt.Horizontal, self.table)
        custom_header.setFixedHeight(42)
        self.table.setHorizontalHeader(custom_header)

        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["번호", "백업 파일명", "파일 크기", "생성 일시"])

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)

        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 180)

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.verticalHeader().setDefaultSectionSize(40)

        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #FFFFFF;
                border: 1px solid #D0D0D0;
                border-radius: 10px;
                outline: none;
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
        self.table.verticalScrollBar().setStyleSheet(SCROLLBAR_STYLE)

        t_layout.addWidget(self.table)
        l_main.addWidget(table_container, 1)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.btn_refresh = QPushButton("목록 새로고침", page_main)
        self.btn_refresh.setFixedSize(135, 46)
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
        self.btn_refresh.clicked.connect(self.refresh_all)

        self.btn_delete_backup = QPushButton("선택한 백업 삭제", page_main)
        self.btn_delete_backup.setFixedSize(155, 46)
        self.btn_delete_backup.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        self.btn_delete_backup.setCursor(Qt.PointingHandCursor)
        self.btn_delete_backup.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #E53E3E;
                border: 1.5px solid #E53E3E;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #FFF5F5;
            }
        """)
        self.btn_delete_backup.clicked.connect(self.delete_selected_backup)

        self.btn_start_restore = QPushButton("선택한 백업으로 복원하기", page_main)
        self.btn_start_restore.setFixedSize(210, 46)
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
        btn_layout.addWidget(self.btn_delete_backup)
        btn_layout.addWidget(self.btn_start_restore)
        l_main.addLayout(btn_layout)

        self.stack.addWidget(page_main)

        # State 1: 복원 진행 중 화면
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

        self.restore_progress_bar = QProgressBar(page_progress)
        self.restore_progress_bar.setFixedSize(280, 8)
        self.restore_progress_bar.setRange(0, 0)
        self.restore_progress_bar.setTextVisible(False)
        self.restore_progress_bar.setStyleSheet(f"""
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
        l_prog.addWidget(self.restore_progress_bar, 0, Qt.AlignCenter)
        self.stack.addWidget(page_progress)

        # State 2: 복원 완료 화면
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

        self.lbl_restore_result_info = QLabel("복원된 백업 파일: -", page_complete)
        self.lbl_restore_result_info.setFont(QFont("Inter", 12))
        self.lbl_restore_result_info.setAlignment(Qt.AlignCenter)
        self.lbl_restore_result_info.setStyleSheet("color: #333333;")

        self.btn_restore_done = QPushButton("확인", page_complete)
        self.btn_restore_done.setFixedSize(360, 52)
        self.btn_restore_done.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        self.btn_restore_done.setCursor(Qt.PointingHandCursor)
        self.btn_restore_done.setStyleSheet(f"""
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
        self.btn_restore_done.clicked.connect(self.finish_restore)

        l_comp.addWidget(lbl_title3)
        l_comp.addWidget(lbl_success)
        l_comp.addSpacing(5)
        l_comp.addWidget(self.lbl_restore_result_info)
        l_comp.addSpacing(15)
        l_comp.addWidget(self.btn_restore_done, 0, Qt.AlignCenter)
        self.stack.addWidget(page_complete)

        main_layout.addWidget(self.stack)
        self.stack.setCurrentIndex(0)

    def refresh_all(self):
        """화면 진입 및 새로고침 시 백업 목록과 최근 백업일 동시 갱신"""
        self.load_backup_list()
        self.load_last_backup_date()

    def load_last_backup_date(self):
        """DB 기록 + 클라우드/로컬 백업(자동·수동 포함) 중 가장 최근 백업일 표시"""
        candidates = []

        db_date = self.db_manager.get_setting("last_backup_date", default="")
        if db_date:
            candidates.append(db_date.strip()[:10])

        # 클라우드 백업 목록(자동·수동 전체)의 최신 생성일 확인
        for f in self.backup_files_data:
            created_raw = f.get("createdTime", "")
            if created_raw:
                try:
                    dt = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
                    candidates.append(dt.strftime("%Y-%m-%d"))
                except Exception:
                    pass

        # 로컬 자동·수동 백업 폴더의 파일명 날짜(YYYYMMDD) 확인
        for sub_dir in (os.path.join("백업", "자동백업"), os.path.join("백업", "수동백업")):
            if os.path.isdir(sub_dir):
                for fname in os.listdir(sub_dir):
                    match = re.search(r"(\d{8})", fname)
                    if match:
                        raw = match.group(1)
                        candidates.append(f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}")

        if candidates:
            latest_date = max(candidates)
            self.lbl_last_backup.setText(f"최근 백업일 : {latest_date}")
        else:
            self.lbl_last_backup.setText("최근 백업일 : 내역 없음")

    def load_backup_list(self):
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

    # =========================================================================
    # 수동 백업 실행
    # =========================================================================
    def start_backup(self):
        dialog = CustomConfirmDialog(
            "데이터 백업 확인",
            "현재 데이터를 로컬 및 구글 드라이브에 백업하시겠습니까?",
            self
        )
        if dialog.exec() != QDialog.Accepted:
            return

        self.progress_popup = ProgressPopupDialog(
            "데이터 백업 중...",
            "암호화된 백업 파일을 생성하여 구글 드라이브에 업로드하고 있습니다.",
            self
        )
        self.progress_popup.show()

        self.backup_worker = BackupWorker(self)
        self.backup_worker.finished_signal.connect(self.on_backup_success)
        self.backup_worker.failed_signal.connect(self.on_backup_failed)
        self.backup_worker.start()

    def on_backup_success(self, file_name: str, file_size_str: str, date_str: str):
        if self.progress_popup:
            self.progress_popup.finish_close()
            self.progress_popup = None

        self.db_manager.set_setting("last_backup_date", date_str)
        self.refresh_all()

        CustomAlertDialog(
            "백업 완료",
            f"백업이 완료되었습니다.\n\n파일명: {file_name}\n크기: {file_size_str}",
            self
        ).exec()

    def on_backup_failed(self, error_msg: str):
        if self.progress_popup:
            self.progress_popup.finish_close()
            self.progress_popup = None

        CustomAlertDialog("백업 실패", f"데이터 백업 중 오류가 발생했습니다:\n\n{error_msg}", self).exec()

    # =========================================================================
    # 선택한 백업 파일 삭제
    # =========================================================================
    def delete_selected_backup(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            CustomAlertDialog("백업 미선택", "삭제할 백업 파일을 목록에서 선택해 주세요.", self).exec()
            return

        row = selected_rows[0].row()
        file_info = self.backup_files_data[row]
        file_id = file_info['id']
        file_name = file_info['name']

        msg_html = (
            f"선택한 백업 <b>[{file_name}]</b> 파일을 삭제하시겠습니까?<br><br>"
            f"<font color='#E53E3E'><b>⚠️ 주의:</b> 삭제된 클라우드 백업 파일은 되돌릴 수 없습니다.</font>"
        )

        dialog = CustomConfirmDialog("백업 파일 삭제 확인", msg_html, self)
        if dialog.exec() != QDialog.Accepted:
            return

        self.progress_popup = ProgressPopupDialog(
            "백업 파일 삭제 중...",
            "구글 드라이브에서 선택한 백업 파일을 삭제하고 있습니다.",
            self
        )
        self.progress_popup.show()

        self.delete_worker = DeleteBackupWorker(file_id, file_name, self)
        self.delete_worker.finished_signal.connect(self.on_delete_success)
        self.delete_worker.failed_signal.connect(self.on_delete_failed)
        self.delete_worker.start()

    def on_delete_success(self, file_name: str):
        if self.progress_popup:
            self.progress_popup.finish_close()
            self.progress_popup = None

        self.refresh_all()
        CustomAlertDialog("삭제 완료", f"백업 파일이 삭제되었습니다.\n({file_name})", self).exec()

    def on_delete_failed(self, error_msg: str):
        if self.progress_popup:
            self.progress_popup.finish_close()
            self.progress_popup = None

        CustomAlertDialog("삭제 실패", f"백업 파일 삭제 중 오류가 발생했습니다:\n\n{error_msg}", self).exec()

    # =========================================================================
    # 선택한 백업 파일로 복원
    # =========================================================================
    def start_restore(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            CustomAlertDialog("백업 미선택", "복원할 백업 파일을 목록에서 선택해 주세요.", self).exec()
            return

        row = selected_rows[0].row()
        file_info = self.backup_files_data[row]
        file_id = file_info['id']
        file_name = file_info['name']

        msg_html = (
            f"선택한 백업 <b>[{file_name}]</b> 파일로 데이터베이스를 복원하시겠습니까?<br><br>"
            f"<font color='#E53E3E'><b>⚠️ 주의:</b> 복원 진행 시 현재 작성된 최신 데이터는 덮어씌워집니다.</font>"
        )

        dialog = CustomConfirmDialog("데이터 복원 확인", msg_html, self)
        if dialog.exec() != QDialog.Accepted:
            return

        self.stack.setCurrentIndex(1)

        self.restore_worker = RestoreWorker(file_id, file_name, self)
        self.restore_worker.finished_signal.connect(self.on_restore_success)
        self.restore_worker.failed_signal.connect(self.on_restore_failed)
        self.restore_worker.start()

    def on_restore_success(self, file_name: str):
        self.lbl_restore_result_info.setText(f"복원된 백업 파일명: {file_name}")
        self.stack.setCurrentIndex(2)

    def on_restore_failed(self, error_msg: str):
        self.stack.setCurrentIndex(0)
        CustomAlertDialog("복원 실패", f"데이터 복원 중 오류가 발생했습니다:\n\n{error_msg}", self).exec()

    def finish_restore(self):
        self.stack.setCurrentIndex(0)
        self.refresh_all()