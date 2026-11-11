import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QFrame, QAbstractItemView, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextDocument, QPageSize
from PySide6.QtPrintSupport import QPrinter
from ui.theme import Colors, get_icon
from core.db_manager import DBManager
from ui.customer_view import CustomAlertDialog, RoundedHeader, SCROLLBAR_STYLE


class SettingsConsentView(QWidget):
    """설정 > 개인정보 및 마케팅 동의서 출력 뷰"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DBManager()
        self.customers_data = []
        self.selected_customer = None

        self.setup_ui()
        self.load_customer_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(20)

        # 상단 헤더
        header_box = QVBoxLayout()
        header_box.setSpacing(6)

        lbl_title = QLabel("개인정보 수집 및 마케팅 동의서 출력", self)
        lbl_title.setFont(QFont("Inter", 22, QFont.Bold))
        lbl_title.setStyleSheet("color: #000000;")

        lbl_sub = QLabel("등록된 고객의 개인정보 수집 및 마케팅 동의 내역을 확인하고 A4 규격 PDF 파일로 출력 및 저장합니다.", self)
        lbl_sub.setFont(QFont("Inter", 11))
        lbl_sub.setStyleSheet("color: #666666;")

        header_box.addWidget(lbl_title)
        header_box.addWidget(lbl_sub)
        main_layout.addLayout(header_box)

        # 상단 검색바
        search_box = QFrame(self)
        search_box.setFixedHeight(42)
        search_box.setStyleSheet("background-color: #FFFFFF; border: 1px solid #D0D0D0; border-radius: 8px;")
        search_layout = QHBoxLayout(search_box)
        search_layout.setContentsMargins(12, 0, 12, 0)
        search_layout.setSpacing(10)

        lbl_search_icon = QLabel(search_box)
        lbl_search_icon.setPixmap(get_icon("search.svg").pixmap(18, 18))
        lbl_search_icon.setStyleSheet("background: transparent; border: none;")

        self.txt_search = QLineEdit(search_box)
        self.txt_search.setPlaceholderText("고객 이름 또는 전화번호 검색")
        self.txt_search.setFont(QFont("Inter", 11))
        self.txt_search.setStyleSheet("border: none; background: transparent; color: #000000;")
        self.txt_search.textChanged.connect(self.filter_customer_list)

        search_layout.addWidget(lbl_search_icon)
        search_layout.addWidget(self.txt_search, 1)
        main_layout.addWidget(search_box)

        # 테이블 영역
        table_container = QFrame(self)
        table_container.setStyleSheet("background-color: #FFFFFF; border-radius: 10px;")
        table_container.setAttribute(Qt.WA_StyledBackground, True)

        t_layout = QVBoxLayout(table_container)
        t_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(table_container)
        
        custom_header = RoundedHeader(Qt.Horizontal, self.table)
        custom_header.setFixedHeight(42)
        self.table.setHorizontalHeader(custom_header)

        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["고객번호", "고객이름", "전화번호", "필수동의", "마케팅동의", "등록일시"])
        
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        
        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 150)

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

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
                padding: 6px;
            }}
            QTableWidget::item:selected {{
                background-color: #E8F5E9;
                color: {Colors.PRIMARY};
                font-weight: bold;
            }}
        """)
        self.table.verticalScrollBar().setStyleSheet(SCROLLBAR_STYLE)

        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        t_layout.addWidget(self.table)
        main_layout.addWidget(table_container, 1)

        # 하단 버튼 패널
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)

        self.btn_export_pdf = QPushButton("선택 고객 동의서 PDF 출력", self)
        self.btn_export_pdf.setFixedSize(240, 48)
        self.btn_export_pdf.setFont(QFont("Inter", 12, QFont.Bold))
        self.btn_export_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_export_pdf.setEnabled(False)
        self.btn_export_pdf.setStyleSheet("""
            QPushButton {
                background-color: #888888;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
            }
        """)
        self.btn_export_pdf.clicked.connect(self.export_consent_pdf)
        btn_layout.addWidget(self.btn_export_pdf)

        main_layout.addLayout(btn_layout)

    def load_customer_data(self):
        query = self.txt_search.text().strip()
        self.customers_data = self.db_manager.get_consented_customers(query=query)
        self.render_table()

    def filter_customer_list(self):
        self.load_customer_data()

    def render_table(self):
        self.table.setRowCount(0)
        self.selected_customer = None
        self.update_button_state(False)

        for idx, cust in enumerate(self.customers_data):
            self.table.insertRow(idx)

            item_id = QTableWidgetItem(str(cust["id"]))
            item_id.setTextAlignment(Qt.AlignCenter)
            item_id.setData(Qt.UserRole, cust)
            self.table.setItem(idx, 0, item_id)

            item_name = QTableWidgetItem(cust["name"])
            item_name.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(idx, 1, item_name)

            item_phone = QTableWidgetItem(cust["phone"])
            item_phone.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(idx, 2, item_phone)

            # 필수 동의
            item_consent = QTableWidgetItem("동의" if cust["is_consent"] == 1 else "미동의")
            item_consent.setTextAlignment(Qt.AlignCenter)
            if cust["is_consent"] == 1:
                item_consent.setForeground(Qt.darkGreen)
            self.table.setItem(idx, 3, item_consent)

            # 마케팅 동의
            item_mkt = QTableWidgetItem("동의" if cust["is_marketing_consent"] == 1 else "미동의")
            item_mkt.setTextAlignment(Qt.AlignCenter)
            if cust["is_marketing_consent"] == 1:
                item_mkt.setForeground(Qt.darkGreen)
            self.table.setItem(idx, 4, item_mkt)

            item_date = QTableWidgetItem(cust["consent_at"])
            item_date.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(idx, 5, item_date)

    def on_selection_changed(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            self.selected_customer = None
            self.update_button_state(False)
            return

        row = self.table.currentRow()
        item_id = self.table.item(row, 0)
        if item_id:
            self.selected_customer = item_id.data(Qt.UserRole)
            self.update_button_state(True)

    def update_button_state(self, enabled: bool):
        self.btn_export_pdf.setEnabled(enabled)
        if enabled:
            self.btn_export_pdf.setStyleSheet(f"""
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
        else:
            self.btn_export_pdf.setStyleSheet("""
                QPushButton {
                    background-color: #888888;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 8px;
                }
            """)

    def export_consent_pdf(self):
            if not self.selected_customer:
                return

            cust = self.selected_customer
            c_name = cust["name"]
            c_phone = cust["phone"]
            
            # 동의 여부에 따라 상태 및 일시 분기 처리
            is_c = (cust["is_consent"] == 1)
            is_m = (cust["is_marketing_consent"] == 1)

            c_status = "동의 완료 (전자 동의)" if is_c else "미동의"
            m_status = "동의 완료 (전자 동의)" if is_m else "미동의"

            # 미동의 시 시간을 출력하지 않고 '-' 처리
            c_date = cust["consent_at"] if is_c else "-"
            m_date = cust["marketing_consent_at"] if is_m else "-"

            # 하단 확인 문구 분기
            sign_status = "(전자 동의 완료)" if (is_c or is_m) else "(미동의)"

            default_filename = f"개인정보및마케팅동의서_{c_name}_{c_phone.replace('-', '')}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "개인정보 및 마케팅 동의서 PDF 저장",
                default_filename,
                "PDF Files (*.pdf)"
            )

            if not file_path:
                return

            try:
                printer = QPrinter(QPrinter.PrinterResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(file_path)
                printer.setPageSize(QPageSize(QPageSize.A4))

                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{
                            font-family: '맑은 고딕', 'Malgun Gothic', sans-serif;
                            padding: 15pt 20pt;
                            color: #111111;
                        }}
                        .main-title {{
                            text-align: center;
                            font-size: 22pt;
                            font-weight: bold;
                            color: #00594C;
                            letter-spacing: 2pt;
                            padding-bottom: 8pt;
                            border-bottom: 2pt solid #00594C;
                            margin-bottom: 20pt;
                        }}
                        .info-table {{
                            width: 100%;
                            border-collapse: collapse;
                            margin-bottom: 18pt;
                        }}
                        .info-table th {{
                            background-color: #EBF3F1;
                            color: #00594C;
                            font-size: 10pt;
                            font-weight: bold;
                            text-align: center;
                            padding: 7pt 4pt;
                        }}
                        .info-table td {{
                            font-size: 10pt;
                            text-align: center;
                            padding: 7pt 6pt;
                            color: #222222;
                        }}
                        .section-header {{
                            font-size: 11pt;
                            font-weight: bold;
                            color: #00594C;
                            margin-top: 12pt;
                            margin-bottom: 4pt;
                        }}
                        .section-body {{
                            font-size: 9.5pt;
                            line-height: 145%;
                            color: #333333;
                            padding-left: 8pt;
                            margin-bottom: 6pt;
                        }}
                        .declaration-table {{
                            width: 100%;
                            border-collapse: collapse;
                            margin-top: 20pt;
                            background-color: #F8FAF9;
                        }}
                        .declaration-header {{
                            background-color: #EBF3F1;
                            text-align: center;
                            font-size: 11pt;
                            font-weight: bold;
                            color: #111111;
                            padding: 10pt 8pt;
                        }}
                        .sub-box {{
                            background-color: #FFFFFF;
                            text-align: center;
                            padding: 10pt;
                        }}
                        .sub-box-title {{
                            font-size: 9.5pt;
                            font-weight: bold;
                            color: #00594C;
                            margin-bottom: 4pt;
                        }}
                        .sub-box-val {{
                            font-size: 10pt;
                            font-weight: bold;
                            color: #222222;
                        }}
                        .sign-cell {{
                            text-align: center;
                            font-size: 10.5pt;
                            padding: 12pt 8pt;
                            background-color: #F8FAF9;
                            color: #222222;
                        }}
                        .brand-logo {{
                            text-align: right;
                            margin-top: 25pt;
                            font-size: 14pt;
                            font-weight: bold;
                            color: #00594C;
                        }}
                    </style>
                </head>
                <body>
                    <div class="main-title">개인정보 수집 및 마케팅 활용 동의서<br></div>

                    <!-- 상단 고객 정보 및 동의 상태 표 -->
                    <table class="info-table" border="1" cellspacing="0" cellpadding="6" bordercolor="#A0A0A0">
                        <tr>
                            <th width="18%">고객 성명</th>
                            <td width="32%">{c_name}</td>
                            <th width="18%">전화번호</th>
                            <td width="32%">{c_phone}</td>
                        </tr>
                        <tr>
                            <th>[필수]<br>개인정보</th>
                            <td><b style="color: #222222;">{c_status}</b><br><span style="font-size: 8.5pt; color: #555555;">({c_date})</span></td>
                            <th>[선택]<br>마케팅 활용</th>
                            <td><b style="color: #222222;">{m_status}</b><br><span style="font-size: 8.5pt; color: #555555;">({m_date})</span></td>
                        </tr>
                    </table>

                    <div class="section-header"><br>1. 개인정보 수집 및 이용 목적 (필수)</div>
                    <div class="section-body">
                        HairMate 미용실 관리 시스템을 통한 고객 회원 관리, 맞춤 헤어 시술 서비스 제공, 시술 이력 조회 및 상담, 포인트 적립·차감 관리, 주요 방문 및 예약 안내 메시지 발송
                    </div>

                    <div class="section-header">2. 수집하는 개인정보 항목 (필수)</div>
                    <div class="section-body">
                        성명, 전화번호, 시술 내역, 결제 금액, 포인트 적립 및 사용 이력
                    </div>

                    <div class="section-header">3. 개인정보 보유 및 이용 기간 (필수)</div>
                    <div class="section-body">
                        회원 등록일로부터 회원 탈퇴 요청 또는 고객 정보 삭제 처리 시까지 보유 및 이용합니다.<br>
                        <span style="color: #666666;">(단, 관계 법령에 따라 보관이 필요한 경우 해당 법정 기간 동안 안전하게 보관됩니다.)</span>
                    </div>

                    <div class="section-header">4. 마케팅 활용 및 광고성 정보 수신 동의 (선택)</div>
                    <div class="section-body">
                        신규 시술 안내, 할인 쿠폰 발송, 맞춤형 이벤트 홍보 등 마케팅 목적의 SMS/LMS 안내 문자 발송에 동의합니다.<br>
                        <span style="color: #666666;">※ 선택 항목에 동의하지 않으셔도 일반 회원 서비스 및 포인트 적립 이용에는 아무런 제한이 없습니다.</span>
                    </div>

                    <div class="section-header">5. 클라우드 백업 및 보안 관리</div>
                    <div class="section-body">
                        수집된 개인정보 데이터는 암호화(AES-256 / Fernet) 처리되어 Google Drive 클라우드 백업 시스템을 통해 안전하게 보관 및 관리됩니다. <br>
                    </div>

                    <!-- 하단 동의 선언 및 전자 동의 확약 박스 -->
                    <table class="declaration-table" border="1" cellspacing="0" cellpadding="0" bordercolor="#00594C">
                        <tr>
                            <td colspan="2" class="declaration-header">
                                본인은 위 개인정보 수집·이용 및 마케팅 활용 안내 사항을 확인하였습니다.
                            </td>
                        </tr>
                        <tr>
                            <td width="50%" class="sub-box" style="border-right: 1px solid #00594C; border-bottom: 1px solid #00594C;">
                                <div class="sub-box-title">[필수] 개인정보 수집·이용</div>
                                <div class="sub-box-val">{c_status}</div>
                            </td>
                            <td width="50%" class="sub-box" style="border-bottom: 1px solid #00594C;">
                                <div class="sub-box-title">[선택] 마케팅 정보 수신</div>
                                <div class="sub-box-val">{m_status}</div>
                            </td>
                        </tr>
                        <tr>
                            <td colspan="2" class="sign-cell">
                                <b>동의자 성명 :</b> {c_name} &nbsp;&nbsp;<b>{sign_status}</b>
                            </td>
                        </tr>
                    </table>

                    <div class="brand-logo">
                        <br>HairMate 미용실 관리 시스템
                    </div>
                </body>
                </html>
                """

                doc = QTextDocument()
                doc.setPageSize(printer.pageRect(QPrinter.Point).size())
                doc.setHtml(html_content)
                doc.print_(printer)

                CustomAlertDialog("출력 완료", f"'{c_name}' 고객의 개인정보 및 마케팅 동의서가 저장되었습니다.\n\n저장 경로:\n{file_path}", self).exec()

            except Exception as e:
                CustomAlertDialog("출력 오류", f"PDF 파일 생성 중 오류가 발생했습니다:\n\n{str(e)}", self).exec()