import csv
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QFileDialog, QDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ui.theme import Colors
from core.db_manager import DBManager

class CustomAlertDialog(QDialog):
    """HairMate 테마가 적용된 안내 알림 팝업"""
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)

        is_error = "오류" in title
        accent_color = "#D32F2F" if is_error else Colors.PRIMARY

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame(self)
        container.setObjectName("alertContainer")
        container.setStyleSheet("""
            QFrame#alertContainer {
                background-color: #FFFFFF;
                border: 1px solid #D0D0D0;
                border-radius: 12px;
            }
        """)

        card_layout = QVBoxLayout(container)
        card_layout.setContentsMargins(26, 22, 26, 22)
        card_layout.setSpacing(14)

        # 상단 타이틀 (배경 투명 처리)
        lbl_title = QLabel(title, container)
        lbl_title.setFont(QFont("Inter", 14, QFont.Bold))
        lbl_title.setStyleSheet(f"background: transparent; color: {accent_color}; border: none;")
        card_layout.addWidget(lbl_title)

        # 본문 메시지 (배경 투명 처리 + 긴 경로 줄바꿈)
        lbl_msg = QLabel(message, container)
        lbl_msg.setFont(QFont("Inter", 11))
        lbl_msg.setWordWrap(True)
        lbl_msg.setMinimumWidth(340)
        lbl_msg.setMaximumWidth(450)
        lbl_msg.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lbl_msg.setStyleSheet("background: transparent; color: #333333; border: none; line-height: 150%;")
        card_layout.addWidget(lbl_msg)

        # 하단 확인 버튼
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 6, 0, 0)
        btn_layout.addStretch(1)

        btn_ok = QPushButton("확인", container)
        btn_ok.setFixedSize(100, 38)
        btn_ok.setFont(QFont("Inter", 11, QFont.Bold))
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setStyleSheet(f"""
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
        btn_ok.clicked.connect(self.accept)

        btn_layout.addWidget(btn_ok)
        card_layout.addLayout(btn_layout)

        outer_layout.addWidget(container)


class SettingsCsvExportView(QWidget):
    """설정 > CSV 데이터 내보내기/출력 탭 뷰"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DBManager()
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)

        # 1. 상단 헤더
        header_box = QVBoxLayout()
        header_box.setSpacing(6)

        lbl_title = QLabel("데이터 CSV 파일 내보내기", self)
        lbl_title.setFont(QFont("Inter", 22, QFont.Bold))
        lbl_title.setStyleSheet("color: #000000;")

        lbl_sub = QLabel("시스템에 저장된 고객 정보, 동의 이력 및 매출 결제 내역을 MS Excel 호환 CSV 파일로 저장합니다.", self)
        lbl_sub.setFont(QFont("Inter", 11))
        lbl_sub.setStyleSheet("color: #666666;")

        header_box.addWidget(lbl_title)
        header_box.addWidget(lbl_sub)
        main_layout.addLayout(header_box)

        # 2. 내보내기 카드 컨테이너
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        # [카드 1] 고객 정보 및 동의 내역
        card_cust = QFrame(self)
        card_cust.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #D0D0D0;
                border-radius: 12px;
            }
        """)
        c_layout1 = QVBoxLayout(card_cust)
        c_layout1.setContentsMargins(25, 25, 25, 25)
        c_layout1.setSpacing(15)

        lbl_c1_title = QLabel("고객 및 동의 내역 CSV", card_cust)
        lbl_c1_title.setFont(QFont("Inter", 16, QFont.Bold))
        lbl_c1_title.setStyleSheet(f"color: {Colors.PRIMARY}; border: none;")

        lbl_c1_desc = QLabel(
            "• 고객 번호, 성명, 전화번호, 보유 포인트\n"
            "• 개인정보 수집 필수 동의 여부 및 일시\n"
            "• 마케팅 활용 선택 동의 여부 및 일시\n"
            "• 고객 메모 및 최초 등록일자",
            card_cust
        )
        lbl_c1_desc.setFont(QFont("Inter", 11))
        lbl_c1_desc.setStyleSheet("color: #444444; border: none; line-height: 160%;")

        btn_exp_cust = QPushButton("고객 목록 CSV 다운로드", card_cust)
        btn_exp_cust.setFixedHeight(46)
        btn_exp_cust.setFont(QFont("Inter", 12, QFont.Bold))
        btn_exp_cust.setCursor(Qt.PointingHandCursor)
        btn_exp_cust.setStyleSheet(f"""
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
        btn_exp_cust.clicked.connect(self.export_customers_csv)

        c_layout1.addWidget(lbl_c1_title)
        c_layout1.addWidget(lbl_c1_desc, 1)
        c_layout1.addWidget(btn_exp_cust)

        # [카드 2] 매출 및 결제 이력
        card_sales = QFrame(self)
        card_sales.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #D0D0D0;
                border-radius: 12px;
            }
        """)
        c_layout2 = QVBoxLayout(card_sales)
        c_layout2.setContentsMargins(25, 25, 25, 25)
        c_layout2.setSpacing(15)

        lbl_c2_title = QLabel("매출 및 결제 이력 CSV", card_sales)
        lbl_c2_title.setFont(QFont("Inter", 16, QFont.Bold))
        lbl_c2_title.setStyleSheet(f"color: {Colors.PRIMARY}; border: none;")

        lbl_c2_desc = QLabel(
            "• 방문 결제 번호, 고객명, 연락처\n"
            "• 담당 디자이너 및 소요 시간\n"
            "• 선택 시술 항목, 결제 금액, 사용 포인트\n"
            "• 결제 수단(카드/현금/포인트) 및 방문 일시",
            card_sales
        )
        lbl_c2_desc.setFont(QFont("Inter", 11))
        lbl_c2_desc.setStyleSheet("color: #444444; border: none; line-height: 160%;")

        btn_exp_sales = QPushButton("매출 이력 CSV 다운로드", card_sales)
        btn_exp_sales.setFixedHeight(46)
        btn_exp_sales.setFont(QFont("Inter", 12, QFont.Bold))
        btn_exp_sales.setCursor(Qt.PointingHandCursor)
        btn_exp_sales.setStyleSheet(f"""
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
        btn_exp_sales.clicked.connect(self.export_sales_csv)

        c_layout2.addWidget(lbl_c2_title)
        c_layout2.addWidget(lbl_c2_desc, 1)
        c_layout2.addWidget(btn_exp_sales)

        cards_layout.addWidget(card_cust, 1)
        cards_layout.addWidget(card_sales, 1)

        main_layout.addLayout(cards_layout)
        main_layout.addStretch(1)

    def export_customers_csv(self):
        """고객 목록 CSV 파일 생성"""
        rows = self.db_manager.get_customers_csv_data()
        if not rows:
            CustomAlertDialog("내보내기 안내", "내보낼 고객 데이터가 없습니다.", self).exec()
            return

        today_str = datetime.now().strftime("%Y%m%d")
        default_name = f"HairMate_고객목록_{today_str}.csv"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "고객 목록 CSV 파일 저장",
            default_name,
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        headers = ["고객번호", "고객명", "전화번호", "보유포인트", "필수동의여부", "필수동의일시", "마케팅동의여부", "마케팅동의일시", "특이사항메모", "최초등록일시"]

        try:
            # utf-8-sig 인코딩으로 엑셀 한글 깨짐 방지
            with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)

            CustomAlertDialog("출력 완료", f"총 {len(rows)}건의 고객 데이터가 CSV 파일로 저장되었습니다.\n\n저장 경로:\n{file_path}", self).exec()
        except Exception as e:
            CustomAlertDialog("오류 발생", f"CSV 파일 저장 중 오류가 발생했습니다:\n{str(e)}", self).exec()

    def export_sales_csv(self):
        """매출 및 결제 이력 CSV 파일 생성"""
        rows = self.db_manager.get_sales_csv_data()
        if not rows:
            CustomAlertDialog("내보내기 안내", "내보낼 매출 데이터가 없습니다.", self).exec()
            return

        today_str = datetime.now().strftime("%Y%m%d")
        default_name = f"HairMate_매출결제내역_{today_str}.csv"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "매출 및 결제 이력 CSV 파일 저장",
            default_name,
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        headers = ["방문번호", "고객명", "전화번호", "담당디자이너", "결제금액", "사용포인트", "소요시간(분)", "시술항목", "결제수단", "방문결제일시"]

        try:
            # utf-8-sig 인코딩으로 엑셀 한글 깨짐 방지
            with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)

            CustomAlertDialog("출력 완료", f"총 {len(rows)}건의 매출 데이터가 CSV 파일로 저장되었습니다.\n\n저장 경로:\n{file_path}", self).exec()
        except Exception as e:
            CustomAlertDialog("오류 발생", f"CSV 파일 저장 중 오류가 발생했습니다:\n{str(e)}", self).exec()