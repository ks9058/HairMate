import os
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, 
    QFrame, QStackedWidget, QComboBox, QDateEdit, QProgressBar, QToolTip
)
from PySide6.QtCore import Qt, QDate, QPoint
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QPainterPath, QPixmap
from ui.theme import Colors
from core.db_manager import DBManager


def get_resource_arrow_path(direction: str = "down") -> str:
    """프로젝트 루트의 resources 폴더에 깔끔한 화살표 PNG를 생성하고 절대 경로 반환"""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    res_dir = os.path.join(project_root, "resources")
    os.makedirs(res_dir, exist_ok=True)

    file_path = os.path.join(res_dir, f"arrow_{direction}.png")
    if not os.path.exists(file_path):
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor("#444444"), 2)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)

        if direction == "down":
            painter.drawLine(5, 9, 12, 16)
            painter.drawLine(12, 16, 19, 9)
        elif direction == "up":
            painter.drawLine(5, 15, 12, 8)
            painter.drawLine(12, 8, 19, 15)

        painter.end()
        pixmap.save(file_path, "PNG")

    return file_path.replace("\\", "/")


class SalesTrendChartWidget(QWidget):
    """기간 조건에 따른 dynamic 꺾은선 그래프 및 마우스 호버 툴팁 지원 위젯"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.trend_data = []
        self.days_span = 1
        self.pts_data = []
        self.setMinimumHeight(180)
        self.setMouseTracking(True)

    def set_data(self, trend_data: list, days_span: int):
        self.trend_data = trend_data
        self.days_span = days_span
        self.pts_data.clear()
        self.update()

    def mouseMoveEvent(self, event):
        """마우스가 그래프 점 근처에 진입하면 툴팁(날짜 + 금액) 표시 및 손가락 커서 변경"""
        if not self.pts_data:
            super().mouseMoveEvent(event)
            return

        pos = event.position().toPoint()
        hovered = False

        for x, y, label, amount in self.pts_data:
            if (pos.x() - x) ** 2 + (pos.y() - y) ** 2 <= 100:
                tooltip_text = f"날짜 : {label}\n매출 : {amount:,}원"
                QToolTip.showText(event.globalPosition().toPoint(), tooltip_text, self)
                self.setCursor(Qt.PointingHandCursor)
                hovered = True
                break

        if not hovered:
            QToolTip.hideText()
            self.setCursor(Qt.ArrowCursor)

        super().mouseMoveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        self.pts_data.clear()

        if not self.trend_data:
            painter.setFont(QFont("Inter", 11, QFont.Weight.Bold))
            painter.setPen(QPen(QColor("#777777")))
            painter.drawText(self.rect(), Qt.AlignCenter, "해당 기간에 조회된 결제/매출 내역이 없습니다.")
            return

        margin_left = 85
        margin_right = 35
        margin_top = 25
        margin_bottom = 35

        chart_w = w - margin_left - margin_right
        chart_h = h - margin_top - margin_bottom

        max_val = max([item["amount"] for item in self.trend_data], default=1)
        if max_val == 0:
            max_val = 1

        painter.setPen(QPen(QColor("#EAEAEA"), 1, Qt.DashLine))
        for i in range(4):
            y = margin_top + (chart_h / 3) * i
            painter.drawLine(margin_left, int(y), w - margin_right, int(y))
            val_txt = f"{int(max_val * (3 - i) / 3):,}원"
            painter.setFont(QFont("Inter", 8, QFont.Weight.Normal))
            painter.setPen(QPen(QColor("#888888")))
            painter.drawText(5, int(y) - 10, margin_left - 12, 20, Qt.AlignRight | Qt.AlignVCenter, val_txt)

        n_pts = len(self.trend_data)
        pts = []

        step_x = chart_w / (n_pts - 1) if n_pts > 1 else chart_w / 2

        label_step = 1
        if n_pts > 15:
            label_step = max(1, n_pts // 8)

        for idx, item in enumerate(self.trend_data):
            x = margin_left + (step_x * idx if n_pts > 1 else chart_w / 2)
            y = margin_top + chart_h - (item["amount"] / max_val * chart_h)
            pts.append((x, y))

            self.pts_data.append((x, y, item["label"], item["amount"]))

            if idx % label_step == 0 or idx == n_pts - 1:
                painter.setFont(QFont("Inter", 8, QFont.Weight.Bold))
                painter.setPen(QPen(QColor("#555555")))
                lbl_w = 55
                lbl_rect_x = int(x - lbl_w / 2)
                lbl_rect_x = max(5, min(lbl_rect_x, w - lbl_w - 5))
                painter.drawText(lbl_rect_x, int(h - margin_bottom + 8), lbl_w, 20, Qt.AlignCenter, item["label"])

        path = QPainterPath()
        if pts:
            path.moveTo(pts[0][0], pts[0][1])
            for pt in pts[1:]:
                path.lineTo(pt[0], pt[1])

        painter.setPen(QPen(QColor(Colors.PRIMARY), 2.5))
        painter.drawPath(path)

        for x, y in pts:
            painter.setPen(QPen(QColor(Colors.PRIMARY), 2))
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.drawEllipse(int(x) - 4, int(y) - 4, 8, 8)


class SalesAnalyticsView(QWidget):
    """매출 분석 & 기간별 상세 분석 통합 뷰"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DBManager()
        self.setup_ui()
        self.load_designers()
        self.refresh_daily_analysis()
        self.refresh_period_analysis()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 10, 25, 20)
        main_layout.setSpacing(10)

        arrow_down_path = get_resource_arrow_path("down")

        # 1. 상단 타이틀 Header Frame
        self.header_frame = QFrame(self)
        self.header_frame.setFixedHeight(65)
        h_layout = QHBoxLayout(self.header_frame)
        h_layout.setContentsMargins(0, 15, 0, 15)

        self.lbl_title = QLabel("금일 매출 분석", self.header_frame)
        self.lbl_title.setFont(QFont("Inter", 22, QFont.Weight.Bold))
        self.lbl_title.setStyleSheet("color: #000000;")
        h_layout.addWidget(self.lbl_title, 0, Qt.AlignCenter)

        main_layout.addWidget(self.header_frame)

        # 2. 탭 전환 버튼 영역
        tab_btn_layout = QHBoxLayout()
        tab_btn_layout.setSpacing(10)

        self.btn_tab_daily = QPushButton("매출 분석", self)
        self.btn_tab_daily.setFixedHeight(38)
        self.btn_tab_daily.setCursor(Qt.PointingHandCursor)
        self.btn_tab_daily.setFont(QFont("Inter", 12, QFont.Weight.Bold))

        self.btn_tab_period = QPushButton("기간별 상세분석", self)
        self.btn_tab_period.setFixedHeight(38)
        self.btn_tab_period.setCursor(Qt.PointingHandCursor)
        self.btn_tab_period.setFont(QFont("Inter", 12, QFont.Weight.Bold))

        self.btn_tab_daily.clicked.connect(lambda: self.switch_tab(0))
        self.btn_tab_period.clicked.connect(lambda: self.switch_tab(1))

        tab_btn_layout.addWidget(self.btn_tab_daily, 1)
        tab_btn_layout.addWidget(self.btn_tab_period, 1)
        main_layout.addLayout(tab_btn_layout)

        # 3. Period Filter Bar (회색 외곽 컨테이너)
        self.period_filter_bar = QFrame(self)
        self.period_filter_bar.setFixedHeight(54)
        self.period_filter_bar.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        self.period_filter_bar.setAttribute(Qt.WA_StyledBackground, True)

        pf_layout = QHBoxLayout(self.period_filter_bar)
        pf_layout.setContentsMargins(6, 6, 6, 6)
        pf_layout.setSpacing(10)

        # 선택 영역 자체에만 들어가는 테두리 공통 스타일
        unified_input_border = """
            border: 1.5px solid #C0C0C0;
            border-radius: 4px;
            background-color: #FAFAFA;
            color: #000000;
        """

        # 콤보박스 스타일 (전체 디자이너 + 아래 화살표 포함 테두리)
        bordered_combo_style = f"""
            QComboBox {{
                {unified_input_border}
                padding-left: 8px;
                padding-right: 22px;
            }}
            QComboBox:focus {{
                border: 1.5px solid {Colors.PRIMARY};
                background-color: #FFFFFF;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: border;
                subcontrol-position: center right;
                width: 22px;
                border: none;
                background: transparent;
            }}
            QComboBox::down-arrow {{
                image: url("{arrow_down_path}");
                width: 11px;
                height: 11px;
                margin-right: 4px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #FFFFFF;
                color: #000000;
                border: 1px solid #B0B0B0;
                selection-background-color: #E8F5E9;
                selection-color: #000000;
            }}
        """

        # 날짜 입력창 스타일 (날짜 + 아래 화살표 포함 테두리)
        bordered_date_style = f"""
            QDateEdit {{
                {unified_input_border}
                padding-left: 6px;
                padding-right: 20px;
            }}
            QDateEdit:focus {{
                border: 1.5px solid {Colors.PRIMARY};
                background-color: #FFFFFF;
            }}
            QDateEdit::drop-down {{
                subcontrol-origin: border;
                subcontrol-position: center right;
                width: 20px;
                border: none;
                background: transparent;
            }}
            QDateEdit::down-arrow {{
                image: url("{arrow_down_path}");
                width: 10px;
                height: 10px;
                margin-right: 4px;
            }}
            QCalendarWidget QWidget#qt_calendar_navigationbar {{
                background-color: {Colors.PRIMARY};
                min-height: 40px;
            }}
            QCalendarWidget QToolButton {{
                color: #FFFFFF;
                font-size: 13px;
                font-weight: bold;
                background-color: transparent;
                border: none;
                margin: 2px;
                padding: 4px 6px;
            }}
            QCalendarWidget QToolButton#qt_calendar_monthbutton,
            QCalendarWidget QToolButton#qt_calendar_yearbutton {{
                padding-right: 18px;
            }}
            QCalendarWidget QToolButton#qt_calendar_monthbutton::menu-indicator,
            QCalendarWidget QToolButton#qt_calendar_yearbutton::menu-indicator {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                right: 4px;
                top: 0px;
            }}
            QCalendarWidget QToolButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
                border-radius: 4px;
            }}
            QCalendarWidget QMenu {{
                background-color: #FFFFFF;
                color: #000000;
                font-size: 12px;
                border: 1px solid #B0B0B0;
            }}
            QCalendarWidget QMenu::item {{
                padding: 6px 20px;
                color: #000000;
            }}
            QCalendarWidget QMenu::item:selected {{
                background-color: #555555;
                color: #FFFFFF;
                font-weight: bold;
            }}
            QCalendarWidget QSpinBox {{
                color: #FFFFFF;
                background-color: transparent;
                font-weight: bold;
                font-size: 13px;
                selection-background-color: {Colors.PRIMARY_HOVER};
                selection-color: #FFFFFF;
            }}
            QCalendarWidget QAbstractItemView:enabled {{
                color: #000000;
                background-color: #FFFFFF;
                selection-background-color: {Colors.PRIMARY};
                selection-color: #FFFFFF;
                font-size: 12px;
            }}
            QCalendarWidget QAbstractItemView::item:hover {{
                background-color: #666666;
                color: #FFFFFF;
            }}
            QCalendarWidget QWidget#qt_calendar_calendarview {{
                background-color: #FFFFFF;
            }}
        """

        # 3.1 디자이너 선택 영역 (바깥 흰색 배경 카드 내 배치)
        designer_box = QFrame(self.period_filter_bar)
        designer_box.setFixedHeight(42)
        designer_box.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        designer_box.setAttribute(Qt.WA_StyledBackground, True)

        des_l = QHBoxLayout(designer_box)
        des_l.setContentsMargins(12, 6, 12, 6)
        des_l.setSpacing(10)

        lbl_des_title = QLabel("디자이너 :", designer_box)
        lbl_des_title.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        lbl_des_title.setStyleSheet("background: transparent; border: none; color: #333333;")

        self.cb_designer = QComboBox(designer_box)
        self.cb_designer.setFixedHeight(30)
        self.cb_designer.setFont(QFont("Inter", 10))
        self.cb_designer.setStyleSheet(bordered_combo_style)
        self.cb_designer.currentIndexChanged.connect(self.refresh_period_analysis)

        des_l.addWidget(lbl_des_title)
        des_l.addWidget(self.cb_designer, 1)

        # 3.2 기간 선택 영역 (바깥 흰색 배경 카드 내 배치)
        date_box = QFrame(self.period_filter_bar)
        date_box.setFixedHeight(42)
        date_box.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        date_box.setAttribute(Qt.WA_StyledBackground, True)

        date_l = QHBoxLayout(date_box)
        date_l.setContentsMargins(12, 6, 12, 6)
        date_l.setSpacing(8)

        lbl_date_title = QLabel("조회기간 :", date_box)
        lbl_date_title.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        lbl_date_title.setStyleSheet("background: transparent; border: none; color: #333333;")

        self.date_start = QDateEdit(date_box)
        self.date_start.setDisplayFormat("yyyy-MM-dd")
        self.date_start.setFixedHeight(30)
        self.date_start.setFont(QFont("Inter", 9))
        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(QDate.currentDate().addDays(-30))
        self.date_start.setStyleSheet(bordered_date_style)
        if self.date_start.calendarWidget():
            self.date_start.calendarWidget().setNavigationBarVisible(True)
        self.date_start.dateChanged.connect(self.refresh_period_analysis)

        lbl_tilde = QLabel("~", date_box)
        lbl_tilde.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        lbl_tilde.setAlignment(Qt.AlignCenter)
        lbl_tilde.setStyleSheet("background: transparent; border: none; color: #333333;")

        self.date_end = QDateEdit(date_box)
        self.date_end.setDisplayFormat("yyyy-MM-dd")
        self.date_end.setFixedHeight(30)
        self.date_end.setFont(QFont("Inter", 9))
        self.date_end.setCalendarPopup(True)
        self.date_end.setDate(QDate.currentDate())
        self.date_end.setStyleSheet(bordered_date_style)
        if self.date_end.calendarWidget():
            self.date_end.calendarWidget().setNavigationBarVisible(True)
        self.date_end.dateChanged.connect(self.refresh_period_analysis)

        date_l.addWidget(lbl_date_title)
        date_l.addWidget(self.date_start, 1)
        date_l.addWidget(lbl_tilde)
        date_l.addWidget(self.date_end, 1)

        pf_layout.addWidget(designer_box, 1)
        pf_layout.addWidget(date_box, 1)

        self.period_filter_bar.setVisible(False)
        main_layout.addWidget(self.period_filter_bar)

        # 4. 메인 스택 뷰
        self.stack = QStackedWidget(self)

        # -------------------------------------------------------------
        # Tab 0: 매출 분석
        # -------------------------------------------------------------
        page_daily = QWidget()
        pd_layout = QVBoxLayout(page_daily)
        pd_layout.setContentsMargins(0, 10, 0, 0)
        pd_layout.setSpacing(10)

        # 1행: 4종 요약 KPI 카드
        box1_outer = QFrame(page_daily)
        box1_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        b1_layout = QHBoxLayout(box1_outer)
        b1_layout.setContentsMargins(8, 8, 8, 8)
        b1_layout.setSpacing(8)

        self.card_total_sales = self._create_kpi_single_card("총 매출액", "0원")
        self.card_spend_per_cust = self._create_kpi_single_card("객 단 가", "0원")
        self.card_visitors = self._create_kpi_single_card("방문자 수", "0명")
        self.card_avg_sales = self._create_kpi_single_card("일평균 매출액", "0원")

        b1_layout.addWidget(self.card_total_sales, 1)
        b1_layout.addWidget(self.card_spend_per_cust, 1)
        b1_layout.addWidget(self.card_visitors, 1)
        b1_layout.addWidget(self.card_avg_sales, 1)

        # 2행: 결제 수단별 금액 및 비율 카드
        box_pay_outer = QFrame(page_daily)
        box_pay_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        bpay_layout = QHBoxLayout(box_pay_outer)
        bpay_layout.setContentsMargins(8, 8, 8, 8)
        bpay_layout.setSpacing(8)

        self.card_pay_card = self._create_kpi_single_card("카드 매출", "0원 (0.0%)")
        self.card_pay_cash = self._create_kpi_single_card("현금 매출", "0원 (0.0%)")
        self.card_pay_point = self._create_kpi_single_card("포인트/선결제", "0원 (0.0%)")

        bpay_layout.addWidget(self.card_pay_card, 1)
        bpay_layout.addWidget(self.card_pay_cash, 1)
        bpay_layout.addWidget(self.card_pay_point, 1)

        # 3행: 전월 대비 매출 비교
        box2_outer = QFrame(page_daily)
        box2_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        b2_outer_layout = QVBoxLayout(box2_outer)
        b2_outer_layout.setContentsMargins(8, 8, 8, 8)

        box2_inner = QFrame(box2_outer)
        box2_inner.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        b2_inner_layout = QHBoxLayout(box2_inner)
        b2_inner_layout.setContentsMargins(20, 12, 20, 12)
        b2_inner_layout.setSpacing(20)

        bars_container = QVBoxLayout()
        bars_container.setSpacing(10)

        r_curr = QHBoxLayout()
        self.lbl_curr_month_name = QLabel("11월", box2_inner)
        self.lbl_curr_month_name.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        self.lbl_curr_month_name.setFixedWidth(35)
        self.pbar_curr = QProgressBar(box2_inner)
        self.pbar_curr.setFixedHeight(22)
        self.pbar_curr.setTextVisible(False)
        self.pbar_curr.setStyleSheet("""
            QProgressBar { border: none; background: #EFEFEF; border-radius: 4px; }
            QProgressBar::chunk { background: #2563EB; border-radius: 4px; }
        """)
        self.lbl_curr_month_val = QLabel("0원", box2_inner)
        self.lbl_curr_month_val.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        self.lbl_curr_month_val.setFixedWidth(100)
        self.lbl_curr_month_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        r_curr.addWidget(self.lbl_curr_month_name)
        r_curr.addWidget(self.pbar_curr, 1)
        r_curr.addWidget(self.lbl_curr_month_val)

        r_prev = QHBoxLayout()
        self.lbl_prev_month_name = QLabel("10월", box2_inner)
        self.lbl_prev_month_name.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        self.lbl_prev_month_name.setFixedWidth(35)
        self.pbar_prev = QProgressBar(box2_inner)
        self.pbar_prev.setFixedHeight(22)
        self.pbar_prev.setTextVisible(False)
        self.pbar_prev.setStyleSheet("""
            QProgressBar { border: none; background: #EFEFEF; border-radius: 4px; }
            QProgressBar::chunk { background: #888888; border-radius: 4px; }
        """)
        self.lbl_prev_month_val = QLabel("0원", box2_inner)
        self.lbl_prev_month_val.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        self.lbl_prev_month_val.setFixedWidth(100)
        self.lbl_prev_month_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        r_prev.addWidget(self.lbl_prev_month_name)
        r_prev.addWidget(self.pbar_prev, 1)
        r_prev.addWidget(self.lbl_prev_month_val)

        bars_container.addLayout(r_curr)
        bars_container.addLayout(r_prev)

        self.lbl_compare_comment = QLabel("지난 달 같은 기간 대비 매출이 0% 늘었어요!", box2_inner)
        self.lbl_compare_comment.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        self.lbl_compare_comment.setStyleSheet("color: #000000;")
        self.lbl_compare_comment.setAlignment(Qt.AlignCenter)

        b2_inner_layout.addLayout(bars_container, 6)
        b2_inner_layout.addWidget(self.lbl_compare_comment, 4)
        b2_outer_layout.addWidget(box2_inner)

        # 4행: 오늘 가장 많이 판매된 시술 TOP 3
        box3_outer = QFrame(page_daily)
        box3_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        b3_outer_layout = QVBoxLayout(box3_outer)
        b3_outer_layout.setContentsMargins(8, 8, 8, 8)

        box3_inner = QFrame(box3_outer)
        box3_inner.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        b3_inner_layout = QHBoxLayout(box3_inner)
        b3_inner_layout.setContentsMargins(20, 12, 20, 12)

        lbl_top_title = QLabel("오늘 가장 많이 판매된 시술 TOP3", box3_inner)
        lbl_top_title.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        lbl_top_title.setStyleSheet("color: #000000;")

        self.top3_container = QHBoxLayout()
        self.top3_container.setSpacing(15)

        b3_inner_layout.addWidget(lbl_top_title, 4)
        b3_inner_layout.addLayout(self.top3_container, 6)
        b3_outer_layout.addWidget(box3_inner)

        # 4개 행 균등 높이 배치 (1 : 1 : 1 : 1)
        pd_layout.addWidget(box1_outer, 1)
        pd_layout.addWidget(box_pay_outer, 1)
        pd_layout.addWidget(box2_outer, 1)
        pd_layout.addWidget(box3_outer, 1)

        self.stack.addWidget(page_daily)

        # -------------------------------------------------------------
        # Tab 1: 기간별 상세분석
        # -------------------------------------------------------------
        page_period = QWidget()
        pp_layout = QVBoxLayout(page_period)
        pp_layout.setContentsMargins(0, 10, 0, 0)
        pp_layout.setSpacing(10)

        # KPI Row 1
        kpi1_outer = QFrame(page_period)
        kpi1_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        k1_layout = QHBoxLayout(kpi1_outer)
        k1_layout.setContentsMargins(8, 8, 8, 8)
        k1_layout.setSpacing(8)

        self.card_kpi_total = self._create_kpi_card("총 매출액", "0원")
        self.card_kpi_count = self._create_kpi_card("시술자 수", "0명")
        self.card_kpi_avg = self._create_kpi_card("일평균 매출액", "0원")

        k1_layout.addWidget(self.card_kpi_total, 1)
        k1_layout.addWidget(self.card_kpi_count, 1)
        k1_layout.addWidget(self.card_kpi_avg, 1)
        pp_layout.addWidget(kpi1_outer, 2)

        # KPI Row 2
        kpi2_outer = QFrame(page_period)
        kpi2_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        k2_layout = QHBoxLayout(kpi2_outer)
        k2_layout.setContentsMargins(8, 8, 8, 8)
        k2_layout.setSpacing(8)

        self.card_kpi_dur = self._create_kpi_card("시술 시간", "0시간")
        self.card_kpi_contrib = self._create_kpi_card("매출 기여도", "100%")

        k2_layout.addWidget(self.card_kpi_dur, 1)
        k2_layout.addWidget(self.card_kpi_contrib, 1)
        pp_layout.addWidget(kpi2_outer, 2)

        # 결제 수단별 매출액 Card
        pay_method_outer = QFrame(page_period)
        pay_method_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        pm_outer_layout = QVBoxLayout(pay_method_outer)
        pm_outer_layout.setContentsMargins(8, 8, 8, 8)

        pm_inner = QFrame(pay_method_outer)
        pm_inner.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        pm_inner_layout = QHBoxLayout(pm_inner)
        pm_inner_layout.setContentsMargins(20, 10, 20, 10)

        lbl_pm_title = QLabel("결제 수단별 매출액", pm_inner)
        lbl_pm_title.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        lbl_pm_title.setStyleSheet("color: #000000;")

        pm_breakdown_layout = QHBoxLayout()
        pm_breakdown_layout.setSpacing(25)

        self.lbl_pm_card = self._create_pm_item("카드", "0원")
        self.lbl_pm_cash = self._create_pm_item("현금", "0원")
        self.lbl_pm_point = self._create_pm_item("포인트", "0원")

        pm_breakdown_layout.addWidget(self.lbl_pm_card)
        pm_breakdown_layout.addWidget(self.lbl_pm_cash)
        pm_breakdown_layout.addWidget(self.lbl_pm_point)

        pm_inner_layout.addWidget(lbl_pm_title, 4)
        pm_inner_layout.addLayout(pm_breakdown_layout, 6)
        pm_outer_layout.addWidget(pm_inner)
        pp_layout.addWidget(pay_method_outer, 2)

        # 추이 꺾은선 그래프
        chart_outer = QFrame(page_period)
        chart_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        co_layout = QVBoxLayout(chart_outer)
        co_layout.setContentsMargins(8, 8, 8, 8)

        chart_inner = QFrame(chart_outer)
        chart_inner.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        ci_layout = QVBoxLayout(chart_inner)
        ci_layout.setContentsMargins(8, 8, 8, 8)

        self.chart_widget = SalesTrendChartWidget(chart_inner)
        ci_layout.addWidget(self.chart_widget)

        co_layout.addWidget(chart_inner)
        pp_layout.addWidget(chart_outer, 5)

        self.stack.addWidget(page_period)
        main_layout.addWidget(self.stack, 1)

        self.switch_tab(0)

    # -------------------------------------------------------------
    # 헬퍼 UI 생성 함수
    # -------------------------------------------------------------
    def _create_kpi_single_card(self, title: str, default_val: str) -> QFrame:
        """5종/4종 단일 KPI 요약 카드"""
        card = QFrame(self)
        card.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(6, 12, 6, 12)
        layout.setSpacing(4)

        lbl_title = QLabel(title, card)
        lbl_title.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("color: #666666;")

        lbl_val = QLabel(default_val, card)
        lbl_val.setObjectName("kpi_val")
        lbl_val.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        lbl_val.setAlignment(Qt.AlignCenter)
        lbl_val.setStyleSheet("color: #000000;")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        return card

    def _create_kpi_card(self, title: str, val: str) -> QFrame:
        card = QFrame(self)
        card.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 10, 20, 10)

        lbl_t = QLabel(title, card)
        lbl_t.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        lbl_t.setStyleSheet("color: #000000;")

        lbl_v = QLabel(val, card)
        lbl_v.setObjectName("kpi_val")
        lbl_v.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        lbl_v.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_v.setStyleSheet("color: #000000;")

        layout.addWidget(lbl_t)
        layout.addWidget(lbl_v, 1)
        return card

    def _create_pm_item(self, title: str, default_val: str) -> QWidget:
        w = QWidget(self)
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        lbl_t = QLabel(title, w)
        lbl_t.setFont(QFont("Inter", 9, QFont.Weight.Bold))
        lbl_t.setAlignment(Qt.AlignCenter)
        lbl_t.setStyleSheet("color: #666666;")

        lbl_v = QLabel(default_val, w)
        lbl_v.setObjectName("pm_val")
        lbl_v.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        lbl_v.setAlignment(Qt.AlignCenter)
        lbl_v.setStyleSheet("color: #000000;")

        layout.addWidget(lbl_t)
        layout.addWidget(lbl_v)
        return w

    def switch_tab(self, index: int):
        self.stack.setCurrentIndex(index)
        if index == 0:
            self.lbl_title.setText("금일 매출 분석")
            self.period_filter_bar.setVisible(False)
            self.btn_tab_daily.setStyleSheet(f"background-color: {Colors.PRIMARY}; color: #FFFFFF; border: none; border-radius: 6px; font-weight: bold;")
            self.btn_tab_period.setStyleSheet("background-color: #E0E0E0; color: #333333; border: none; border-radius: 6px; font-weight: bold;")
            self.refresh_daily_analysis()
        else:
            self.lbl_title.setText("기간별 매출 분석")
            self.period_filter_bar.setVisible(True)
            self.btn_tab_period.setStyleSheet(f"background-color: {Colors.PRIMARY}; color: #FFFFFF; border: none; border-radius: 6px; font-weight: bold;")
            self.btn_tab_daily.setStyleSheet("background-color: #E0E0E0; color: #333333; border: none; border-radius: 6px; font-weight: bold;")
            self.refresh_period_analysis()

    def load_designers(self):
        self.cb_designer.blockSignals(True)
        self.cb_designer.clear()
        self.cb_designer.addItem("전체 디자이너", "all")
        designers = self.db_manager.get_all_designers()
        for d in designers:
            self.cb_designer.addItem(f"{d['name']} ({d['position']})", d['id'])
        self.cb_designer.blockSignals(False)

    # -------------------------------------------------------------
    # 데이터 새로고침
    # -------------------------------------------------------------
    def refresh_daily_analysis(self):
        """금일 매출 분석 4종 KPI 카드, 결제 수단별 금액/비율 카드 및 동적 증감 막대 색상 반영"""
        data = self.db_manager.get_daily_sales_analysis()

        # 1. 상단 1행 4종 KPI 카드 값 갱신
        self.card_total_sales.findChild(QLabel, "kpi_val").setText(f"{data['today_sales']:,}원")
        self.card_spend_per_cust.findChild(QLabel, "kpi_val").setText(f"{data['today_customer_spend']:,}원")
        self.card_visitors.findChild(QLabel, "kpi_val").setText(f"{data['today_visitors']}명")
        self.card_avg_sales.findChild(QLabel, "kpi_val").setText(f"{data['avg_daily_sales']:,}원")

        # 2. 2행 결제 수단별 금액 및 비율 카드 갱신
        pay_info = data['today_payments']
        self.card_pay_card.findChild(QLabel, "kpi_val").setText(f"{pay_info['card_amount']:,}원 ({pay_info['card_share']}%)")
        self.card_pay_cash.findChild(QLabel, "kpi_val").setText(f"{pay_info['cash_amount']:,}원 ({pay_info['cash_share']}%)")
        self.card_pay_point.findChild(QLabel, "kpi_val").setText(f"{pay_info['point_amount']:,}원 ({pay_info['point_share']}%)")

        # 3. 3행 전월 대비 증감 바 차트 및 코멘트 색상 갱신
        curr_sales = data['this_month_sales']
        prev_sales = data['prev_month_sales']
        max_bar_val = max(curr_sales, prev_sales, 1)

        self.lbl_curr_month_name.setText(f"{data['this_month']}월")
        self.pbar_curr.setMaximum(max_bar_val)
        self.pbar_curr.setValue(curr_sales)
        self.lbl_curr_month_val.setText(f"{curr_sales:,}원")

        self.lbl_prev_month_name.setText(f"{data['prev_month']}월")
        self.pbar_prev.setMaximum(max_bar_val)
        self.pbar_prev.setValue(prev_sales)
        self.lbl_prev_month_val.setText(f"{prev_sales:,}원")

        diff = data['diff_percent']
        if diff >= 0:
            bar_color = "#2563EB"
            self.lbl_compare_comment.setText(f"지난 달 같은 기간 대비 매출이 <font color='{bar_color}'>{diff}% 늘었어요!</font>")
        else:
            bar_color = "#E53E3E"
            self.lbl_compare_comment.setText(f"지난 달 같은 기간 대비 매출이 <font color='{bar_color}'>{abs(diff)}% 줄었어요!</font>")

        self.pbar_curr.setStyleSheet(f"""
            QProgressBar {{ border: none; background: #EFEFEF; border-radius: 4px; }}
            QProgressBar::chunk {{ background: {bar_color}; border-radius: 4px; }}
        """)

        # 4. 4행 오늘 판매 TOP 3
        while self.top3_container.count():
            item = self.top3_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        badge_colors = ["#FFC107", "#D0D0D0", "#E08A3C"]

        top3 = data['top3']
        if not top3:
            lbl_none = QLabel("오늘 판매된 시술 내역이 없습니다.", self)
            lbl_none.setFont(QFont("Inter", 10, QFont.Weight.Normal))
            lbl_none.setStyleSheet("color: #777777;")
            self.top3_container.addWidget(lbl_none)
        else:
            for idx, item in enumerate(top3):
                item_w = QWidget(self)
                i_layout = QVBoxLayout(item_w)
                i_layout.setContentsMargins(0, 0, 0, 0)
                i_layout.setSpacing(2)
                i_layout.setAlignment(Qt.AlignCenter)

                lbl_name = QLabel(f"{item['name']} - {item['count']}명", item_w)
                lbl_name.setFont(QFont("Inter", 9, QFont.Weight.Bold))
                lbl_name.setAlignment(Qt.AlignCenter)

                lbl_price = QLabel(f"{item['price']:,}원", item_w)
                lbl_price.setFont(QFont("Inter", 9, QFont.Weight.Bold))
                lbl_price.setAlignment(Qt.AlignCenter)

                lbl_badge = QLabel(str(idx + 1), item_w)
                lbl_badge.setFixedSize(26, 26)
                lbl_badge.setFont(QFont("Inter", 11, QFont.Weight.Bold))
                lbl_badge.setAlignment(Qt.AlignCenter)
                bg_c = badge_colors[idx] if idx < len(badge_colors) else "#CCCCCC"
                lbl_badge.setStyleSheet(f"background-color: {bg_c}; color: #FFFFFF; border-radius: 13px;")

                i_layout.addWidget(lbl_name)
                i_layout.addWidget(lbl_price)
                i_layout.addWidget(lbl_badge, 0, Qt.AlignCenter)

                self.top3_container.addWidget(item_w)

    def refresh_period_analysis(self):
        """기간별 상세분석 탭 데이터 바인딩"""
        start_date = self.date_start.date().toString("yyyy-MM-dd")
        end_date = self.date_end.date().toString("yyyy-MM-dd")
        designer_id = self.cb_designer.currentData()

        data = self.db_manager.get_period_sales_analysis(start_date, end_date, designer_id)

        self.card_kpi_total.findChild(QLabel, "kpi_val").setText(f"{data['total_sales']:,}원")
        self.card_kpi_count.findChild(QLabel, "kpi_val").setText(f"{data['visit_count']}명")
        self.card_kpi_avg.findChild(QLabel, "kpi_val").setText(f"{data['avg_daily_sales']:,}원")

        dur_min = data['total_duration']
        if dur_min >= 60:
            h = dur_min // 60
            m = dur_min % 60
            dur_str = f"{h}시간" if m == 0 else f"{h}시간 {m}분"
        else:
            dur_str = f"{dur_min}분"

        self.card_kpi_dur.findChild(QLabel, "kpi_val").setText(dur_str)
        self.card_kpi_contrib.findChild(QLabel, "kpi_val").setText(f"{data['contribution']}%")

        self.lbl_pm_card.findChild(QLabel, "pm_val").setText(f"{data['payments']['카드']:,}원")
        self.lbl_pm_cash.findChild(QLabel, "pm_val").setText(f"{data['payments']['현금']:,}원")
        self.lbl_pm_point.findChild(QLabel, "pm_val").setText(f"{data['payments']['포인트']:,}원")

        self.chart_widget.set_data(data['trend_data'], data['days_span'])