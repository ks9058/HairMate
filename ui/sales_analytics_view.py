import os
import calendar
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QFrame, QStackedWidget, QComboBox, QDateEdit, QGridLayout
)
from PySide6.QtCore import Qt, QDate, Signal
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


class ClickableDayCell(QFrame):
    """클릭 시 해당 날짜(yyyy-MM-dd) 시그널을 방출하는 매출 캘린더 일자 카드"""
    clicked = Signal(str)

    def __init__(self, date_str: str, parent=None):
        super().__init__(parent)
        self.date_str = date_str
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.date_str)
        super().mousePressEvent(event)


class SalesTrendChartWidget(QWidget):
    """추이 꺾은선 그래프 + 상단 범례 헤더 + 우측 여백 평균 기준선 + 금액 상시 표시 위젯"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.trend_data = []
        self.days_span = 1
        self.avg_amount = 0
        self.setMinimumHeight(200)

    def set_data(self, trend_data: list, days_span: int, avg_amount: int = 0):
        self.trend_data = trend_data
        self.days_span = days_span
        self.avg_amount = int(avg_amount or 0)
        self.update()

    def _draw_legend_header(self, painter: QPainter, w: int):
        """차트 상단 범례 바 (그래프 영역과 완전히 분리되어 시인성 극대화)"""
        painter.setFont(QFont("Inter", 8.5, QFont.Weight.Bold))
        fm = painter.fontMetrics()

        y_center = 14

        avg_label = f"평균 매출액 ({self.avg_amount:,}원)"
        avg_w = fm.horizontalAdvance(avg_label)

        prefix_txt = "일별 매출액 ("
        above_txt = "평균 이상  "
        below_txt = "평균 미만)"

        total_line_w = (
            fm.horizontalAdvance(prefix_txt)
            + 12 + fm.horizontalAdvance(above_txt)
            + 12 + fm.horizontalAdvance(below_txt)
        )
        draw_x = (w - 24) - avg_w - 24 - 20 - total_line_w

        # 초록 실선 아이콘
        painter.setPen(QPen(QColor(Colors.PRIMARY), 2.5))
        painter.drawLine(draw_x - 24, y_center, draw_x - 6, y_center)

        painter.setPen(QPen(QColor("#334155")))
        w1 = fm.horizontalAdvance(prefix_txt)
        painter.drawText(draw_x, 4, w1, 20, Qt.AlignVCenter | Qt.AlignLeft, prefix_txt)
        draw_x += w1

        # 평균 이상 초록 원
        painter.setPen(QPen(QColor("#059669"), 2.0))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(draw_x + 1, y_center - 4, 8, 8)
        draw_x += 12

        w2 = fm.horizontalAdvance(above_txt)
        painter.setPen(QPen(QColor("#059669")))
        painter.drawText(draw_x, 4, w2, 20, Qt.AlignVCenter | Qt.AlignLeft, above_txt)
        draw_x += w2

        # 평균 미만 주황 원
        painter.setPen(QPen(QColor("#EA580C"), 2.0))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(draw_x + 1, y_center - 4, 8, 8)
        draw_x += 12

        w3 = fm.horizontalAdvance(below_txt)
        painter.setPen(QPen(QColor("#EA580C")))
        painter.drawText(draw_x, 4, w3, 20, Qt.AlignVCenter | Qt.AlignLeft, below_txt)
        draw_x += w3 + 20

        # 빨간 점선 - 평균 매출액
        painter.setPen(QPen(QColor("#DC2626"), 2.0, Qt.DashLine))
        painter.drawLine(draw_x, y_center, draw_x + 18, y_center)
        draw_x += 24

        painter.setPen(QPen(QColor("#B91C1C")))
        painter.drawText(draw_x, 4, avg_w, 20, Qt.AlignVCenter | Qt.AlignLeft, avg_label)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        if not self.trend_data:
            painter.setFont(QFont("Inter", 11, QFont.Weight.Bold))
            painter.setPen(QPen(QColor("#777777")))
            painter.drawText(self.rect(), Qt.AlignCenter, "해당 기간에 조회된 결제/매출 내역이 없습니다.")
            return

        # 상단 범례 헤더 그리기
        self._draw_legend_header(painter, w)

        margin_left = 88
        margin_right = 112
        margin_top = 42
        margin_bottom = 34

        chart_w = w - margin_left - margin_right
        chart_h = h - margin_top - margin_bottom

        data_max = max([item["amount"] for item in self.trend_data], default=0)
        max_val = max(data_max, self.avg_amount, 1)

        # Y축 가로 눈금선 및 좌측 눈금 금액
        for i in range(4):
            y = margin_top + (chart_h / 3) * i
            painter.setPen(QPen(QColor("#EAEAEA"), 1, Qt.DashLine))
            painter.drawLine(margin_left, int(y), w - margin_right, int(y))

            val_txt = f"{int(max_val * (3 - i) / 3):,}원"
            painter.setFont(QFont("Inter", 8, QFont.Weight.Normal))
            painter.setPen(QPen(QColor("#888888")))
            painter.drawText(4, int(y) - 10, margin_left - 12, 20, Qt.AlignRight | Qt.AlignVCenter, val_txt)

        n_pts = len(self.trend_data)
        pts = []
        step_x = chart_w / (n_pts - 1) if n_pts > 1 else chart_w / 2
        label_step = max(1, n_pts // 8) if n_pts > 15 else 1

        # X축 라벨 그리기
        painter.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        fm_x = painter.fontMetrics()

        for idx, item in enumerate(self.trend_data):
            x = margin_left + (step_x * idx if n_pts > 1 else chart_w / 2)
            y = margin_top + chart_h - (item["amount"] / max_val * chart_h)
            pts.append((x, y, item["amount"], idx))

            if idx % label_step == 0 or idx == n_pts - 1:
                painter.setFont(QFont("Inter", 8, QFont.Weight.Bold))
                painter.setPen(QPen(QColor("#555555")))
                lbl_w = max(58, fm_x.horizontalAdvance(item["label"]) + 12)
                lbl_rect_x = max(5, min(int(x - lbl_w / 2), w - margin_right - lbl_w // 2))
                painter.drawText(lbl_rect_x, int(h - margin_bottom + 8), lbl_w, 20, Qt.AlignCenter, item["label"])

        # 일별 매출 꺾은선 경로 그리기
        path = QPainterPath()
        if pts:
            path.moveTo(pts[0][0], pts[0][1])
            for pt in pts[1:]:
                path.lineTo(pt[0], pt[1])

        painter.setPen(QPen(QColor(Colors.PRIMARY), 2.5))
        painter.drawPath(path)

        # 평균 매출액 빨간 가로 점선 + 우측 여백 끝 라벨 배지
        avg_y_int = None
        if self.avg_amount > 0:
            avg_y = margin_top + chart_h - (self.avg_amount / max_val * chart_h)
            avg_y_int = int(avg_y)

            avg_pen = QPen(QColor("#DC2626"), 1.8, Qt.DashLine)
            painter.setPen(avg_pen)
            painter.drawLine(margin_left, avg_y_int, w - margin_right, avg_y_int)

            badge_text = f"평균 {self.avg_amount:,}원"
            painter.setFont(QFont("Inter", 8, QFont.Weight.Bold))
            badge_x = w - margin_right + 8
            badge_w = margin_right - 14
            badge_h = 20
            badge_y = max(margin_top - 6, min(avg_y_int - badge_h // 2, h - margin_bottom - badge_h + 4))

            painter.setPen(QPen(QColor("#FCA5A5"), 1))
            painter.setBrush(QBrush(QColor("#FEF2F2")))
            painter.drawRoundedRect(int(badge_x), int(badge_y), int(badge_w), badge_h, 4, 4)

            painter.setPen(QPen(QColor("#B91C1C")))
            painter.drawText(int(badge_x), int(badge_y), int(badge_w), badge_h, Qt.AlignCenter, badge_text)

        # 1단계: 모든 데이터 포인트 원 먼저 그리기
        for x, y, amt, idx in pts:
            is_above = amt >= self.avg_amount and self.avg_amount > 0
            pt_color = QColor("#059669") if is_above else QColor("#EA580C")
            if self.avg_amount == 0:
                pt_color = QColor(Colors.PRIMARY)

            painter.setPen(QPen(pt_color, 2.2))
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.drawEllipse(int(x) - 4, int(y) - 4, 8, 8)

        # 2단계: 금액 라벨 충돌 회피 배치
        painter.setFont(QFont("Inter", 7.5, QFont.Weight.Bold))
        fm = painter.fontMetrics()
        placed_rects = []

        def is_colliding(rx1, ry1, rx2, ry2):
            for px1, py1, px2, py2 in placed_rects:
                if not (rx2 + 3 < px1 or rx1 - 3 > px2 or ry2 + 2 < py1 or ry1 - 2 > py2):
                    return True
            return False

        ordered_pts = [p for p in pts if p[2] > 0] + [p for p in pts if p[2] == 0]

        for x, y, amt, idx in ordered_pts:
            if amt == 0 and n_pts > 10 and (idx % label_step != 0 and idx != n_pts - 1):
                continue

            is_above = amt >= self.avg_amount and self.avg_amount > 0
            pt_color = QColor("#059669") if is_above else (QColor("#EA580C") if amt > 0 else QColor("#64748B"))
            if self.avg_amount == 0 and amt > 0:
                pt_color = QColor(Colors.PRIMARY)

            amt_txt = f"{amt:,}원"
            txt_w = fm.horizontalAdvance(amt_txt) + 6
            txt_h = 15
            txt_x = int(x - txt_w / 2)
            txt_x = max(margin_left - 8, min(txt_x, w - margin_right - txt_w + 8))

            candidate_ys = [
                int(y) - txt_h - 6,
                int(y) + 7,
                int(y) - (txt_h * 2) - 10,
                int(y) + txt_h + 11,
            ]

            chosen_y = None
            for cy in candidate_ys:
                if cy < margin_top - 18 or cy + txt_h > h - margin_bottom + 2:
                    continue
                if amt == 0 and avg_y_int is not None:
                    if cy <= avg_y_int <= cy + txt_h:
                        continue
                if not is_colliding(txt_x, cy, txt_x + txt_w, cy + txt_h):
                    chosen_y = cy
                    break

            if chosen_y is None:
                if amt > 0:
                    chosen_y = max(margin_top - 18, min(candidate_ys[0], h - margin_bottom - txt_h))
                else:
                    continue

            placed_rects.append((txt_x, chosen_y, txt_x + txt_w, chosen_y + txt_h))

            if abs((chosen_y + txt_h // 2) - int(y)) > txt_h + 6:
                painter.setPen(QPen(QColor("#CBD5E1"), 1, Qt.DotLine))
                line_end_y = chosen_y + txt_h if chosen_y < y else chosen_y
                painter.drawLine(int(x), int(y), int(x), line_end_y)

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 255, 225)))
            painter.drawRoundedRect(txt_x, chosen_y, txt_w, txt_h, 3, 3)

            painter.setPen(QPen(pt_color))
            painter.drawText(txt_x, chosen_y, txt_w, txt_h, Qt.AlignCenter, amt_txt)


class SalesAnalyticsView(QWidget):
    """매출 캘린더 & 상세 분석 통합 뷰"""
    calendar_date_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DBManager()
        self.setup_ui()
        self.load_designers()
        self.refresh_calendar_analysis()
        self.refresh_period_analysis()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 6, 25, 14)
        main_layout.setSpacing(6)

        arrow_down_path = get_resource_arrow_path("down")

        # 1. 상단 타이틀 Header Frame
        self.header_frame = QFrame(self)
        self.header_frame.setFixedHeight(44)
        h_layout = QHBoxLayout(self.header_frame)
        h_layout.setContentsMargins(0, 4, 0, 4)

        self.lbl_title = QLabel("매출 캘린더", self.header_frame)
        self.lbl_title.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        self.lbl_title.setStyleSheet("color: #000000;")
        h_layout.addWidget(self.lbl_title, 0, Qt.AlignCenter)

        main_layout.addWidget(self.header_frame)

        # 2. 탭 전환 버튼 영역
        tab_btn_layout = QHBoxLayout()
        tab_btn_layout.setSpacing(8)

        self.btn_tab_calendar = QPushButton("매출 캘린더", self)
        self.btn_tab_calendar.setFixedHeight(34)
        self.btn_tab_calendar.setCursor(Qt.PointingHandCursor)
        self.btn_tab_calendar.setFont(QFont("Inter", 11.5, QFont.Weight.Bold))

        self.btn_tab_detail = QPushButton("상세 분석", self)
        self.btn_tab_detail.setFixedHeight(34)
        self.btn_tab_detail.setCursor(Qt.PointingHandCursor)
        self.btn_tab_detail.setFont(QFont("Inter", 11.5, QFont.Weight.Bold))

        self.btn_tab_calendar.clicked.connect(lambda: self.switch_tab(0))
        self.btn_tab_detail.clicked.connect(lambda: self.switch_tab(1))

        tab_btn_layout.addWidget(self.btn_tab_calendar, 1)
        tab_btn_layout.addWidget(self.btn_tab_detail, 1)
        main_layout.addLayout(tab_btn_layout)

        # 공통 입력 스타일
        unified_input_border = """
            border: 1.5px solid #C0C0C0;
            border-radius: 4px;
            background-color: #FAFAFA;
            color: #000000;
        """

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

        bordered_date_style = f"""
            QDateEdit {{
                {unified_input_border}
                padding-left: 8px;
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

        # 3. 필터 바 스택 (0: 매출 캘린더 필터 바 / 1: 상세 분석 필터 바)
        self.filter_stack = QStackedWidget(self)
        self.filter_stack.setFixedHeight(46)

        # [0] 매출 캘린더 필터 바 (디자이너 + 조회 년/월 콤보박스)
        self.cal_filter_bar = QFrame(self)
        self.cal_filter_bar.setStyleSheet("background-color: #DCDCDC; border-radius: 8px;")
        self.cal_filter_bar.setAttribute(Qt.WA_StyledBackground, True)
        cf_layout = QHBoxLayout(self.cal_filter_bar)
        cf_layout.setContentsMargins(5, 4, 5, 4)
        cf_layout.setSpacing(8)

        cal_des_box = QFrame(self.cal_filter_bar)
        cal_des_box.setFixedHeight(38)
        cal_des_box.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        cal_des_box.setAttribute(Qt.WA_StyledBackground, True)
        cd_l = QHBoxLayout(cal_des_box)
        cd_l.setContentsMargins(12, 4, 12, 4)
        cd_l.setSpacing(8)

        lbl_cal_des = QLabel("디자이너 :", cal_des_box)
        lbl_cal_des.setFont(QFont("Inter", 10.5, QFont.Weight.Bold))
        lbl_cal_des.setStyleSheet("background: transparent; border: none; color: #333333;")

        self.cb_cal_designer = QComboBox(cal_des_box)
        self.cb_cal_designer.setFixedHeight(28)
        self.cb_cal_designer.setFont(QFont("Inter", 10))
        self.cb_cal_designer.setStyleSheet(bordered_combo_style)
        self.cb_cal_designer.currentIndexChanged.connect(self.refresh_calendar_analysis)

        cd_l.addWidget(lbl_cal_des)
        cd_l.addWidget(self.cb_cal_designer, 1)

        cal_month_box = QFrame(self.cal_filter_bar)
        cal_month_box.setFixedHeight(38)
        cal_month_box.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        cal_month_box.setAttribute(Qt.WA_StyledBackground, True)
        cm_l = QHBoxLayout(cal_month_box)
        cm_l.setContentsMargins(12, 4, 12, 4)
        cm_l.setSpacing(6)

        lbl_cal_month = QLabel("조회 년/월 :", cal_month_box)
        lbl_cal_month.setFont(QFont("Inter", 10.5, QFont.Weight.Bold))
        lbl_cal_month.setStyleSheet("background: transparent; border: none; color: #333333;")

        btn_prev_month = QPushButton("‹", cal_month_box)
        btn_prev_month.setFixedSize(26, 28)
        btn_prev_month.setCursor(Qt.PointingHandCursor)
        btn_prev_month.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                color: #334155;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #E2E8F0; }
        """)
        btn_prev_month.clicked.connect(lambda: self._shift_calendar_month(-1))

        today = QDate.currentDate()
        curr_year = today.year()
        curr_month = today.month()

        self.cb_cal_year = QComboBox(cal_month_box)
        self.cb_cal_year.setFixedHeight(28)
        self.cb_cal_year.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        self.cb_cal_year.setStyleSheet(bordered_combo_style)
        for y in range(curr_year - 5, curr_year + 6):
            self.cb_cal_year.addItem(f"{y}년", y)
        y_idx = self.cb_cal_year.findData(curr_year)
        if y_idx >= 0:
            self.cb_cal_year.setCurrentIndex(y_idx)
        self.cb_cal_year.currentIndexChanged.connect(self.refresh_calendar_analysis)

        self.cb_cal_month = QComboBox(cal_month_box)
        self.cb_cal_month.setFixedHeight(28)
        self.cb_cal_month.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        self.cb_cal_month.setStyleSheet(bordered_combo_style)
        for m in range(1, 13):
            self.cb_cal_month.addItem(f"{m}월", m)
        m_idx = self.cb_cal_month.findData(curr_month)
        if m_idx >= 0:
            self.cb_cal_month.setCurrentIndex(m_idx)
        self.cb_cal_month.currentIndexChanged.connect(self.refresh_calendar_analysis)

        btn_next_month = QPushButton("›", cal_month_box)
        btn_next_month.setFixedSize(26, 28)
        btn_next_month.setCursor(Qt.PointingHandCursor)
        btn_next_month.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                color: #334155;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #E2E8F0; }
        """)
        btn_next_month.clicked.connect(lambda: self._shift_calendar_month(1))

        cm_l.addWidget(lbl_cal_month)
        cm_l.addWidget(btn_prev_month)
        cm_l.addWidget(self.cb_cal_year, 1)
        cm_l.addWidget(self.cb_cal_month, 1)
        cm_l.addWidget(btn_next_month)

        cf_layout.addWidget(cal_des_box, 1)
        cf_layout.addWidget(cal_month_box, 1)
        self.filter_stack.addWidget(self.cal_filter_bar)

        # [1] 상세 분석 필터 바 (디자이너 + 조회 기간)
        self.period_filter_bar = QFrame(self)
        self.period_filter_bar.setStyleSheet("background-color: #DCDCDC; border-radius: 8px;")
        self.period_filter_bar.setAttribute(Qt.WA_StyledBackground, True)
        pf_layout = QHBoxLayout(self.period_filter_bar)
        pf_layout.setContentsMargins(5, 4, 5, 4)
        pf_layout.setSpacing(8)

        designer_box = QFrame(self.period_filter_bar)
        designer_box.setFixedHeight(38)
        designer_box.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        designer_box.setAttribute(Qt.WA_StyledBackground, True)
        des_l = QHBoxLayout(designer_box)
        des_l.setContentsMargins(12, 4, 12, 4)
        des_l.setSpacing(8)

        lbl_des_title = QLabel("디자이너 :", designer_box)
        lbl_des_title.setFont(QFont("Inter", 10.5, QFont.Weight.Bold))
        lbl_des_title.setStyleSheet("background: transparent; border: none; color: #333333;")

        self.cb_designer = QComboBox(designer_box)
        self.cb_designer.setFixedHeight(28)
        self.cb_designer.setFont(QFont("Inter", 10))
        self.cb_designer.setStyleSheet(bordered_combo_style)
        self.cb_designer.currentIndexChanged.connect(self.refresh_period_analysis)

        des_l.addWidget(lbl_des_title)
        des_l.addWidget(self.cb_designer, 1)

        date_box = QFrame(self.period_filter_bar)
        date_box.setFixedHeight(38)
        date_box.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        date_box.setAttribute(Qt.WA_StyledBackground, True)
        date_l = QHBoxLayout(date_box)
        date_l.setContentsMargins(12, 4, 12, 4)
        date_l.setSpacing(6)

        lbl_date_title = QLabel("조회기간 :", date_box)
        lbl_date_title.setFont(QFont("Inter", 10.5, QFont.Weight.Bold))
        lbl_date_title.setStyleSheet("background: transparent; border: none; color: #333333;")

        self.date_start = QDateEdit(date_box)
        self.date_start.setDisplayFormat("yyyy-MM-dd")
        self.date_start.setFixedHeight(28)
        self.date_start.setFont(QFont("Inter", 9))
        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(QDate.currentDate().addDays(-30))
        self.date_start.setStyleSheet(bordered_date_style)
        if self.date_start.calendarWidget():
            self.date_start.calendarWidget().setNavigationBarVisible(True)
        self.date_start.dateChanged.connect(self.refresh_period_analysis)

        lbl_tilde = QLabel("~", date_box)
        lbl_tilde.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        lbl_tilde.setAlignment(Qt.AlignCenter)
        lbl_tilde.setStyleSheet("background: transparent; border: none; color: #333333;")

        self.date_end = QDateEdit(date_box)
        self.date_end.setDisplayFormat("yyyy-MM-dd")
        self.date_end.setFixedHeight(28)
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
        self.filter_stack.addWidget(self.period_filter_bar)

        main_layout.addWidget(self.filter_stack)

        # 4. 메인 스택 뷰
        self.stack = QStackedWidget(self)

        # =============================================================
        # Tab 0: 매출 캘린더
        # =============================================================
        page_calendar = QWidget()
        pc_layout = QVBoxLayout(page_calendar)
        pc_layout.setContentsMargins(0, 2, 0, 0)
        pc_layout.setSpacing(6)

        # 월간 요약 바 (선택 월 총 매출액 / 선택 월 실매출액 / 방문 고객수 / 예약건 / 결제건)
        cal_summary_outer = QFrame(page_calendar)
        cal_summary_outer.setFixedHeight(44)
        cal_summary_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 8px;")
        cs_o_layout = QHBoxLayout(cal_summary_outer)
        cs_o_layout.setContentsMargins(5, 4, 5, 4)
        cs_o_layout.setSpacing(6)

        self.card_cal_month_sales = self._create_kpi_card("선택 월 총 매출액", "0원", compact=True)
        self.card_cal_month_net_sales = self._create_kpi_card("선택 월 실매출액", "0원", compact=True)
        self.card_cal_month_visitors = self._create_kpi_card("방문 고객수", "0명", compact=True)
        self.card_cal_month_reservations = self._create_kpi_card("예약건", "0건", compact=True)
        self.card_cal_month_payments = self._create_kpi_card("결제건", "0건", compact=True)

        cs_o_layout.addWidget(self.card_cal_month_sales, 1)
        cs_o_layout.addWidget(self.card_cal_month_net_sales, 1)
        cs_o_layout.addWidget(self.card_cal_month_visitors, 1)
        cs_o_layout.addWidget(self.card_cal_month_reservations, 1)
        cs_o_layout.addWidget(self.card_cal_month_payments, 1)
        pc_layout.addWidget(cal_summary_outer)

        # 한달 매출 캘린더 그리드 컨테이너
        cal_grid_outer = QFrame(page_calendar)
        cal_grid_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        cgo_layout = QVBoxLayout(cal_grid_outer)
        cgo_layout.setContentsMargins(6, 6, 6, 6)
        cgo_layout.setSpacing(0)

        cal_grid_inner = QFrame(cal_grid_outer)
        cal_grid_inner.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        cgi_layout = QVBoxLayout(cal_grid_inner)
        cgi_layout.setContentsMargins(6, 6, 6, 6)
        cgi_layout.setSpacing(4)

        # 요일 헤더 (일 ~ 토)
        dow_row = QHBoxLayout()
        dow_row.setSpacing(5)
        dow_names = ["일", "월", "화", "수", "목", "금", "토"]
        for idx, d_name in enumerate(dow_names):
            lbl_dow = QLabel(d_name, cal_grid_inner)
            lbl_dow.setFixedHeight(25)
            lbl_dow.setAlignment(Qt.AlignCenter)
            lbl_dow.setFont(QFont("Inter", 9.5, QFont.Weight.Bold))
            if idx == 0:
                fg = "#DC2626"
                bg = "#FEF2F2"
            elif idx == 6:
                fg = "#2563EB"
                bg = "#EFF6FF"
            else:
                fg = "#FFFFFF"
                bg = Colors.PRIMARY
            lbl_dow.setStyleSheet(f"""
                QLabel {{
                    background-color: {bg};
                    color: {fg};
                    border-radius: 5px;
                }}
            """)
            dow_row.addWidget(lbl_dow, 1)
        cgi_layout.addLayout(dow_row)

        # 날짜 셀 그리드
        self.cal_cells_widget = QWidget(cal_grid_inner)
        self.cal_cells_widget.setStyleSheet("background: transparent;")
        self.cal_grid_layout = QGridLayout(self.cal_cells_widget)
        self.cal_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.cal_grid_layout.setSpacing(4)
        cgi_layout.addWidget(self.cal_cells_widget, 1)

        cgo_layout.addWidget(cal_grid_inner)
        pc_layout.addWidget(cal_grid_outer, 1)
        self.stack.addWidget(page_calendar)

        # =============================================================
        # Tab 1: 상세 분석
        # =============================================================
        page_period = QWidget()
        pp_layout = QVBoxLayout(page_period)
        pp_layout.setContentsMargins(0, 2, 0, 0)
        pp_layout.setSpacing(6)

        # KPI 1행: 총 매출액, 실매출액, 일평균 매출액
        kpi1_outer = QFrame(page_period)
        kpi1_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        k1_layout = QHBoxLayout(kpi1_outer)
        k1_layout.setContentsMargins(6, 6, 6, 6)
        k1_layout.setSpacing(6)

        self.card_kpi_total = self._create_kpi_card("총 매출액", "0원")
        self.card_kpi_net = self._create_kpi_card("실매출액", "0원")
        self.card_kpi_avg = self._create_kpi_card("일평균 매출액", "0원")

        k1_layout.addWidget(self.card_kpi_total, 1)
        k1_layout.addWidget(self.card_kpi_net, 1)
        k1_layout.addWidget(self.card_kpi_avg, 1)
        pp_layout.addWidget(kpi1_outer, 2)

        # KPI 2행: 시술자 수, 예약자 수, 시술 시간, 매출 기여도
        kpi2_outer = QFrame(page_period)
        kpi2_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        k2_layout = QHBoxLayout(kpi2_outer)
        k2_layout.setContentsMargins(6, 6, 6, 6)
        k2_layout.setSpacing(6)

        self.card_kpi_count = self._create_kpi_card("시술자 수", "0명", compact=True)
        self.card_kpi_reserved = self._create_kpi_card("예약자 수", "0명", compact=True)
        self.card_kpi_dur = self._create_kpi_card("시술 시간", "0시간", compact=True)
        self.card_kpi_contrib = self._create_kpi_card("매출 기여도", "0.0%", compact=True)

        k2_layout.addWidget(self.card_kpi_count, 1)
        k2_layout.addWidget(self.card_kpi_reserved, 1)
        k2_layout.addWidget(self.card_kpi_dur, 1)
        k2_layout.addWidget(self.card_kpi_contrib, 1)
        pp_layout.addWidget(kpi2_outer, 2)

        # KPI 3행: 결제 수단별 매출 (카드, 현금, 선결제, 포인트)
        pay_method_outer = QFrame(page_period)
        pay_method_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        k3_layout = QHBoxLayout(pay_method_outer)
        k3_layout.setContentsMargins(6, 6, 6, 6)
        k3_layout.setSpacing(6)

        self.card_pm_card = self._create_kpi_card("카드", "0원 (0명)")
        self.card_pm_cash = self._create_kpi_card("현금", "0원 (0명)")
        self.card_pm_prepaid = self._create_kpi_card("선결제", "0원 (0명)")
        self.card_pm_point = self._create_kpi_card("포인트", "0원 (0명)")

        k3_layout.addWidget(self.card_pm_card, 1)
        k3_layout.addWidget(self.card_pm_cash, 1)
        k3_layout.addWidget(self.card_pm_prepaid, 1)
        k3_layout.addWidget(self.card_pm_point, 1)
        pp_layout.addWidget(pay_method_outer, 2)

        # 추이 꺾은선 그래프
        chart_outer = QFrame(page_period)
        chart_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        co_layout = QVBoxLayout(chart_outer)
        co_layout.setContentsMargins(6, 6, 6, 6)

        chart_inner = QFrame(chart_outer)
        chart_inner.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        ci_layout = QVBoxLayout(chart_inner)
        ci_layout.setContentsMargins(8, 6, 8, 6)

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
    def _create_kpi_card(self, title: str, val: str, compact: bool = False, highlight_color: str = None) -> QFrame:
        card = QFrame(self)
        card.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        layout = QHBoxLayout(card)
        if compact:
            layout.setContentsMargins(12, 4, 12, 4)
            layout.setSpacing(4)
            title_font = QFont("Inter", 9.5, QFont.Weight.Bold)
            val_font = QFont("Inter", 10.5, QFont.Weight.Bold)
        else:
            layout.setContentsMargins(16, 6, 16, 6)
            layout.setSpacing(6)
            title_font = QFont("Inter", 10, QFont.Weight.Bold)
            val_font = QFont("Inter", 11, QFont.Weight.Bold)

        lbl_t = QLabel(title, card)
        lbl_t.setFont(title_font)
        lbl_t.setStyleSheet("color: #333333; background: transparent; border: none;")

        lbl_v = QLabel(val, card)
        lbl_v.setObjectName("kpi_val")
        lbl_v.setFont(val_font)
        lbl_v.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        v_color = highlight_color if highlight_color else "#000000"
        lbl_v.setStyleSheet(f"color: {v_color}; background: transparent; border: none;")

        layout.addWidget(lbl_t)
        layout.addWidget(lbl_v, 1)
        return card

    def _create_calendar_day_cell(self, date_str: str, day_num: int, dow_idx: int, day_info: dict, is_today: bool) -> QFrame:
        """매출 캘린더 개별 일자 카드 (일 · 건수 / 매출 / 실매출 / 누적 표시)"""
        cell = ClickableDayCell(date_str, self.cal_cells_widget)
        cell.clicked.connect(self.calendar_date_selected.emit)

        has_activity = (
            day_info.get("daily_sales", 0) > 0
            or day_info.get("payment_count", 0) > 0
            or day_info.get("reservation_count", 0) > 0
        )

        if is_today:
            border_css = f"2px solid {Colors.PRIMARY}"
            bg_css = "#ECFDF5"
            hover_bg = "#D1FAE5"
        elif has_activity:
            border_css = "1.5px solid #CBD5E1"
            bg_css = "#FFFFFF"
            hover_bg = "#F1F5F9"
        else:
            border_css = "1px solid #E2E8F0"
            bg_css = "#FAFAFA"
            hover_bg = "#F1F5F9"

        cell.setStyleSheet(f"""
            ClickableDayCell {{
                background-color: {bg_css};
                border: {border_css};
                border-radius: 6px;
            }}
            ClickableDayCell:hover {{
                background-color: {hover_bg};
                border: 1.5px solid {Colors.PRIMARY};
            }}
        """)

        c_layout = QVBoxLayout(cell)
        c_layout.setContentsMargins(6, 4, 6, 4)
        c_layout.setSpacing(1)

        # 1행: 날짜 숫자 + 방문 / 예약 / 결제 건수
        top_row = QHBoxLayout()
        top_row.setSpacing(2)

        lbl_day = QLabel(f"{day_num}일", cell)
        lbl_day.setFont(QFont("Inter", 8.5, QFont.Weight.Bold))
        if dow_idx == 0:
            day_color = "#DC2626"
        elif dow_idx == 6:
            day_color = "#2563EB"
        else:
            day_color = "#0F172A"
        lbl_day.setStyleSheet(f"color: {day_color}; border: none; background: transparent;")

        v_cnt = day_info.get("visitor_count", 0)
        r_cnt = day_info.get("reservation_count", 0)
        p_cnt = day_info.get("payment_count", 0)
        lbl_counts = QLabel(f"방문 {v_cnt} · 예약 {r_cnt} · 결제 {p_cnt}", cell)
        lbl_counts.setFont(QFont("Inter", 7.2))
        lbl_counts.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_counts.setStyleSheet(
            f"color: {'#0F172A' if has_activity else '#94A3B8'}; border: none; background: transparent;"
        )

        top_row.addWidget(lbl_day)
        top_row.addWidget(lbl_counts, 1)
        c_layout.addLayout(top_row)

        # 2행: 하루 총 매출액
        d_sales = day_info.get("daily_sales", 0)
        lbl_daily = QLabel(f"매출: {d_sales:,}원", cell)
        lbl_daily.setFont(QFont("Inter", 8.5, QFont.Weight.Bold))
        lbl_daily.setStyleSheet(
            f"color: {Colors.PRIMARY if d_sales > 0 else '#94A3B8'}; border: none; background: transparent;"
        )
        c_layout.addWidget(lbl_daily)

        # 3행: 하루 실매출액 (선결제·포인트 사용 제외)
        d_net_sales = day_info.get("daily_net_sales", 0)
        lbl_net = QLabel(f"실매출: {d_net_sales:,}원", cell)
        lbl_net.setFont(QFont("Inter", 8.5, QFont.Weight.Bold))
        lbl_net.setStyleSheet(
            f"color: {"#DB0808" if d_net_sales > 0 else '#94A3B8'}; border: none; background: transparent;"
        )
        c_layout.addWidget(lbl_net)

        # 4행: 누적 매출액
        c_sales = day_info.get("cumulative_sales", 0)
        lbl_cum = QLabel(f"누적: {c_sales:,}원", cell)
        lbl_cum.setFont(QFont("Inter", 8.5, QFont.Weight.Bold))
        lbl_cum.setStyleSheet(
            f"color: {'#334155' if c_sales > 0 else '#CBD5E1'}; border: none; background: transparent;"
        )
        c_layout.addWidget(lbl_cum)
        c_layout.addStretch()

        return cell

    def _create_adjacent_month_cell(self, day_num: int, label_prefix: str = "") -> QFrame:
        """전월 말일 / 익월 초일 표시용 비활성 달력 셀"""
        cell = QFrame(self.cal_cells_widget)
        cell.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px dashed #E2E8F0;
                border-radius: 6px;
            }
        """)
        c_layout = QVBoxLayout(cell)
        c_layout.setContentsMargins(6, 4, 6, 4)
        c_layout.setSpacing(1)

        lbl_day = QLabel(f"{label_prefix}{day_num}일", cell)
        lbl_day.setFont(QFont("Inter", 8.5))
        lbl_day.setStyleSheet("color: #CBD5E1; border: none; background: transparent;")
        c_layout.addWidget(lbl_day)
        c_layout.addStretch()
        return cell

    def set_calendar_year_month(self, year: int, month: int):
        """외부(뒤로가기 복귀 등)에서 특정 연도와 월을 선택하고 캘린더 갱신"""
        if self.cb_cal_year.findData(year) < 0:
            self.cb_cal_year.blockSignals(True)
            if year < (self.cb_cal_year.itemData(0) or year):
                self.cb_cal_year.insertItem(0, f"{year}년", year)
            else:
                self.cb_cal_year.addItem(f"{year}년", year)
            self.cb_cal_year.blockSignals(False)

        self.cb_cal_year.blockSignals(True)
        self.cb_cal_month.blockSignals(True)
        self.cb_cal_year.setCurrentIndex(self.cb_cal_year.findData(year))
        self.cb_cal_month.setCurrentIndex(self.cb_cal_month.findData(month))
        self.cb_cal_year.blockSignals(False)
        self.cb_cal_month.blockSignals(False)

        self.switch_tab(0)

    def _shift_calendar_month(self, step: int):
        year = self.cb_cal_year.currentData() or QDate.currentDate().year()
        month = self.cb_cal_month.currentData() or QDate.currentDate().month()

        new_month = month + step
        new_year = year
        if new_month < 1:
            new_month = 12
            new_year -= 1
        elif new_month > 12:
            new_month = 1
            new_year += 1

        self.set_calendar_year_month(new_year, new_month)

    def switch_tab(self, index: int):
        self.stack.setCurrentIndex(index)
        self.filter_stack.setCurrentIndex(index)
        if index == 0:
            self.lbl_title.setText("매출 캘린더")
            self.btn_tab_calendar.setStyleSheet(
                f"background-color: {Colors.PRIMARY}; color: #FFFFFF; border: none; border-radius: 6px; font-weight: bold;"
            )
            self.btn_tab_detail.setStyleSheet(
                "background-color: #E0E0E0; color: #333333; border: none; border-radius: 6px; font-weight: bold;"
            )
            self.refresh_calendar_analysis()
        else:
            self.lbl_title.setText("상세 분석")
            self.btn_tab_detail.setStyleSheet(
                f"background-color: {Colors.PRIMARY}; color: #FFFFFF; border: none; border-radius: 6px; font-weight: bold;"
            )
            self.btn_tab_calendar.setStyleSheet(
                "background-color: #E0E0E0; color: #333333; border: none; border-radius: 6px; font-weight: bold;"
            )
            self.refresh_period_analysis()

    def load_designers(self):
        designers = self.db_manager.get_all_designers()
        for combo in (self.cb_cal_designer, self.cb_designer):
            curr_val = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("전체 디자이너", "all")
            for d in designers:
                pos = (d.get("position") or "").strip()
                label = f"{d['name']} ({pos})" if pos else d["name"]
                combo.addItem(label, d["id"])
            if curr_val is not None:
                idx = combo.findData(curr_val)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            combo.blockSignals(False)

    # -------------------------------------------------------------
    # 데이터 새로고침
    # -------------------------------------------------------------
    def refresh_daily_analysis(self):
        """기존 외부 호출 호환용 별칭"""
        self.refresh_calendar_analysis()

    def refresh_calendar_analysis(self):
        """매출 캘린더 탭 데이터 바인딩 및 월간 그리드 렌더링"""
        today = QDate.currentDate()
        year = self.cb_cal_year.currentData() or today.year()
        month = self.cb_cal_month.currentData() or today.month()
        designer_id = self.cb_cal_designer.currentData() or "all"

        data = self.db_manager.get_monthly_sales_calendar(year, month, str(designer_id))

        self.card_cal_month_sales.findChild(QLabel, "kpi_val").setText(f"{data['monthly_total_sales']:,}원")
        self.card_cal_month_net_sales.findChild(QLabel, "kpi_val").setText(f"{data.get('monthly_total_net_sales', 0):,}원")
        self.card_cal_month_visitors.findChild(QLabel, "kpi_val").setText(f"{data['monthly_total_visitors']}명")
        self.card_cal_month_reservations.findChild(QLabel, "kpi_val").setText(f"{data['monthly_total_reservations']}건")
        self.card_cal_month_payments.findChild(QLabel, "kpi_val").setText(f"{data['monthly_total_payments']}건")

        while self.cal_grid_layout.count():
            item = self.cal_grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for r in range(6):
            self.cal_grid_layout.setRowStretch(r, 0)

        first_weekday_mon0, days_in_month = calendar.monthrange(year, month)
        start_col = (first_weekday_mon0 + 1) % 7

        prev_year = year - 1 if month == 1 else year
        prev_month = 12 if month == 1 else month - 1
        prev_days_in_month = calendar.monthrange(prev_year, prev_month)[1]

        daily_map = data.get("daily_map", {})

        total_cells = start_col + days_in_month
        num_rows = (total_cells + 6) // 7

        for r in range(num_rows):
            self.cal_grid_layout.setRowStretch(r, 1)
        for c in range(7):
            self.cal_grid_layout.setColumnStretch(c, 1)

        for cell_idx in range(num_rows * 7):
            row = cell_idx // 7
            col = cell_idx % 7
            day_num = cell_idx - start_col + 1

            if 1 <= day_num <= days_in_month:
                date_str = f"{year:04d}-{month:02d}-{day_num:02d}"
                day_info = daily_map.get(day_num, {
                    "daily_sales": 0,
                    "daily_net_sales": 0,
                    "cumulative_sales": 0,
                    "visitor_count": 0,
                    "reservation_count": 0,
                    "payment_count": 0,
                })
                is_today = (today.year() == year and today.month() == month and today.day() == day_num)
                cell_widget = self._create_calendar_day_cell(date_str, day_num, col, day_info, is_today)
            elif day_num < 1:
                prev_day = prev_days_in_month + day_num
                cell_widget = self._create_adjacent_month_cell(prev_day, f"{prev_month}/")
            else:
                next_day = day_num - days_in_month
                next_month = 1 if month == 12 else month + 1
                cell_widget = self._create_adjacent_month_cell(next_day, f"{next_month}/")

            self.cal_grid_layout.addWidget(cell_widget, row, col)

    def refresh_period_analysis(self):
        """상세 분석 탭 데이터 바인딩"""
        start_date = self.date_start.date().toString("yyyy-MM-dd")
        end_date = self.date_end.date().toString("yyyy-MM-dd")
        designer_id = self.cb_designer.currentData() or "all"

        data = self.db_manager.get_period_sales_analysis(start_date, end_date, str(designer_id))

        # 1행: 총 매출액, 실매출액, 일평균 매출액
        self.card_kpi_total.findChild(QLabel, "kpi_val").setText(f"{data['total_sales']:,}원")
        self.card_kpi_net.findChild(QLabel, "kpi_val").setText(f"{data.get('net_sales', 0):,}원")
        self.card_kpi_avg.findChild(QLabel, "kpi_val").setText(f"{data['avg_daily_sales']:,}원")

        # 2행: 시술자 수, 예약자 수, 시술 시간, 매출 기여도
        self.card_kpi_count.findChild(QLabel, "kpi_val").setText(f"{data['treated_customer_count']}명")
        self.card_kpi_reserved.findChild(QLabel, "kpi_val").setText(f"{data['reserved_count']}명")

        dur_min = data["total_duration"]
        if dur_min >= 60:
            h = dur_min // 60
            m = dur_min % 60
            dur_str = f"{h}시간" if m == 0 else f"{h}시간 {m}분"
        else:
            dur_str = f"{dur_min}분"
        self.card_kpi_dur.findChild(QLabel, "kpi_val").setText(dur_str)
        self.card_kpi_contrib.findChild(QLabel, "kpi_val").setText(f"{data.get('contribution', 0.0):.1f}%")

        # 3행: 결제 수단별 매출액 + 이용 고객 수
        payments = data["payments"]
        p_counts = data["payment_counts"]

        self.card_pm_card.findChild(QLabel, "kpi_val").setText(
            f"{payments['카드']:,}원 ({p_counts['카드']}명)"
        )
        self.card_pm_cash.findChild(QLabel, "kpi_val").setText(
            f"{payments['현금']:,}원 ({p_counts['현금']}명)"
        )
        self.card_pm_prepaid.findChild(QLabel, "kpi_val").setText(
            f"{payments['선결제']:,}원 ({p_counts['선결제']}명)"
        )
        self.card_pm_point.findChild(QLabel, "kpi_val").setText(
            f"{payments['포인트']:,}원 ({p_counts['포인트']}명)"
        )

        # 추이 그래프
        self.chart_widget.set_data(
            data["trend_data"],
            data["days_span"],
            data.get("chart_avg_sales", 0),
        )