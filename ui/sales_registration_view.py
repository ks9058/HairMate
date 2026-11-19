import os
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QFrame, QAbstractItemView, QStackedWidget,
    QComboBox, QDateEdit, QGridLayout, QScrollArea, QDialog, QSizePolicy,
    QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, QDate, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QPainterPath, QTextDocument, QPixmap
from ui.theme import Colors, get_icon
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


def get_checkmark_icon_path() -> str:
    """프로젝트 루트의 resources 폴더에 흰색 체크(✓) PNG 아이콘을 생성하고 절대 경로 반환"""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    res_dir = os.path.join(project_root, "resources")
    os.makedirs(res_dir, exist_ok=True)

    file_path = os.path.join(res_dir, "check_white.png")
    if not os.path.exists(file_path):
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor("#FFFFFF"), 2.6)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(5, 12, 10, 17)
        painter.drawLine(10, 17, 19, 7)
        painter.end()
        pixmap.save(file_path, "PNG")

    return file_path.replace("\\", "/")


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
    QScrollBar:horizontal {
        border: none;
        background: #EAEAEA;
        height: 10px;
        margin: 0px;
        border-radius: 5px;
    }
    QScrollBar::handle:horizontal {
        background: #B0B0B0;
        min-width: 25px;
        border-radius: 5px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #888888;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        background: none;
        width: 0px;
    }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none;
    }
"""

SLIM_H_SCROLLBAR_STYLE = """
    QScrollArea {
        border: none;
        background: transparent;
    }
    QScrollBar:horizontal {
        border: none;
        background: #EAEAEA;
        height: 6px;
        margin: 0px;
        border-radius: 3px;
    }
    QScrollBar::handle:horizontal {
        background: #B0B0B0;
        min-width: 24px;
        border-radius: 3px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #888888;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        background: none;
        width: 0px;
    }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none;
    }
"""


class HorizontalScrollArea(QScrollArea):
    """마우스 휠 조작 시 가로 스크롤로 동작하는 커스텀 QScrollArea"""

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta != 0:
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta
            )
            event.accept()
        else:
            super().wheelEvent(event)


class CustomAlertDialog(QDialog):
    """커스텀 알림/안내 팝업"""

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMinimumWidth(480)

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
        c_layout.setContentsMargins(35, 30, 35, 25)
        c_layout.setSpacing(22)

        formatted_msg = message.replace("\n", "<br>")
        lbl_msg = QLabel(f"<div style='line-height: 150%; text-align: center;'>{formatted_msg}</div>", container)
        lbl_msg.setFont(QFont("Inter", 13, QFont.Bold))
        lbl_msg.setAlignment(Qt.AlignCenter)
        lbl_msg.setStyleSheet("border: none; background: transparent; color: #000000;")

        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignCenter)

        btn_confirm = QPushButton("확인", container)
        btn_confirm.setFixedSize(130, 42)
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

        btn_layout.addWidget(btn_confirm)
        c_layout.addWidget(lbl_msg)
        c_layout.addLayout(btn_layout)
        outer_layout.addWidget(container)


class PaymentMethodModal(QDialog):
    """[결제하기] 클릭 시 카드/현금 결제 수단을 선택하는 모달 팝업"""

    def __init__(self, amount: int, parent=None):
        super().__init__(parent)
        self.selected_method = None
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(460, 320)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(5, 5, 5, 5)

        container = QFrame(self)
        container.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1.5px solid #B0B0B0;
            }
        """)
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(24, 16, 24, 28)
        c_layout.setSpacing(12)

        top_bar = QHBoxLayout()
        top_bar.addStretch(1)
        btn_close = QPushButton("✕", container)
        btn_close.setFixedSize(30, 30)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setFont(QFont("Inter", 14, QFont.Bold))
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #333333;
                border: none;
            }
            QPushButton:hover {
                color: #E53E3E;
            }
        """)
        btn_close.clicked.connect(self.reject)
        top_bar.addWidget(btn_close)
        c_layout.addLayout(top_bar)

        lbl_amount = QLabel(
            f"결제 금액: <font color='#E53E3E'>{amount:,}원</font>",
            container
        )
        lbl_amount.setFont(QFont("Inter", 16, QFont.Bold))
        lbl_amount.setAlignment(Qt.AlignCenter)
        lbl_amount.setStyleSheet("border: none; background: transparent; color: #000000;")
        c_layout.addWidget(lbl_amount)

        lbl_guide = QLabel("결제수단을 선택해주세요", container)
        lbl_guide.setFont(QFont("Inter", 15, QFont.Bold))
        lbl_guide.setAlignment(Qt.AlignCenter)
        lbl_guide.setStyleSheet("border: none; background: transparent; color: #000000;")
        c_layout.addWidget(lbl_guide)

        c_layout.addSpacing(8)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)
        btn_row.setAlignment(Qt.AlignCenter)

        btn_style = f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
            }}
        """

        btn_cash = QPushButton("현금", container)
        btn_cash.setFixedSize(145, 130)
        btn_cash.setCursor(Qt.PointingHandCursor)
        btn_cash.setFont(QFont("Inter", 20, QFont.Bold))
        btn_cash.setStyleSheet(btn_style)
        btn_cash.clicked.connect(lambda: self.choose("현금"))

        btn_card = QPushButton("카드", container)
        btn_card.setFixedSize(145, 130)
        btn_card.setCursor(Qt.PointingHandCursor)
        btn_card.setFont(QFont("Inter", 20, QFont.Bold))
        btn_card.setStyleSheet(btn_style)
        btn_card.clicked.connect(lambda: self.choose("카드"))

        btn_row.addWidget(btn_cash)
        btn_row.addWidget(btn_card)
        c_layout.addLayout(btn_row)

        outer_layout.addWidget(container)

    def choose(self, method: str):
        self.selected_method = method
        self.accept()


class ZeroAmountConfirmModal(QDialog):
    """선결제·포인트 전액 차감으로 카드/현금 결제 금액이 0원일 때 노출되는 최종 확인 모달"""

    def __init__(self, total_amount: int, use_prepaid: int, use_point: int, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(480, 260)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(5, 5, 5, 5)

        container = QFrame(self)
        container.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1.5px solid #B0B0B0;
            }
        """)
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(28, 26, 28, 24)
        c_layout.setSpacing(16)

        details = []
        if use_prepaid > 0:
            details.append(f"선결제 {use_prepaid:,}원")
        if use_point > 0:
            details.append(f"포인트 {use_point:,}P")
        detail_str = " + ".join(details) if details else "전액 차감"

        msg = (
            f"<div style='line-height: 155%; text-align: center;'>"
            f"총 결제 금액 <b>{total_amount:,}원</b> ({detail_str})<br>"
            f"추가 카드/현금 결제 금액이 <font color='#0D705C'><b>0원</b></font>입니다.<br>"
            f"결제를 완료하시겠습니까?"
            f"</div>"
        )
        lbl_msg = QLabel(msg, container)
        lbl_msg.setFont(QFont("Inter", 13, QFont.Bold))
        lbl_msg.setAlignment(Qt.AlignCenter)
        lbl_msg.setStyleSheet("border: none; background: transparent; color: #000000;")
        c_layout.addWidget(lbl_msg)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(14)
        btn_layout.setAlignment(Qt.AlignCenter)

        btn_ok = QPushButton("결제 완료", container)
        btn_ok.setFixedSize(130, 42)
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setFont(QFont("Inter", 12, QFont.Bold))
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

        btn_cancel = QPushButton("취소", container)
        btn_cancel.setFixedSize(130, 42)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setFont(QFont("Inter", 12, QFont.Bold))
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #E0E0E0;
                color: #333333;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #C0C0C0;
            }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        c_layout.addLayout(btn_layout)

        outer_layout.addWidget(container)


class CustomConsentDialog(QDialog):
    """이관 고객 첫 결제 시 개인정보 수집 및 선택 마케팅 동의 확인 모달"""

    def __init__(self, name: str, phone: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(500, 480)

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
        c_layout.setContentsMargins(28, 24, 28, 22)
        c_layout.setSpacing(14)

        lbl_title = QLabel("개인정보 수집 및 마케팅 동의", container)
        lbl_title.setFont(QFont("Inter", 15, QFont.Bold))
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("border: none; background: transparent; color: #000000; font-weight: bold;")
        c_layout.addWidget(lbl_title)

        info_box = QFrame(container)
        info_box.setStyleSheet("background-color: #F8F9FA; border-radius: 8px; border: 1px solid #E0E0E0;")
        i_layout = QVBoxLayout(info_box)
        i_layout.setContentsMargins(16, 12, 16, 12)
        i_layout.setSpacing(6)

        terms_html = f"""
        <div style='line-height: 145%; font-size: 11.5px; color: #222222;'>
            <b>• 대상 고객 :</b> {name} ({phone})<br>
            <b>[필수] 수집·이용 목적 :</b> 고객 관리, 시술 이력 조회, 포인트 적립/차감<br>
            <b>[필수] 수집 항목 :</b> 성명, 전화번호, 시술 및 결제 내역<br>
            <b>[필수] 보유 및 이용 기간 :</b> 회원 탈퇴 또는 고객 정보 삭제 시까지<br>
            <b>[선택] 마케팅 활용 :</b> 할인 쿠폰, 이벤트 홍보, 신규 시술 광고 SMS 발송
        </div>
        """
        lbl_terms = QLabel(terms_html, info_box)
        lbl_terms.setWordWrap(True)
        lbl_terms.setStyleSheet("border: none; background: transparent;")
        i_layout.addWidget(lbl_terms)
        c_layout.addWidget(info_box)

        check_icon_path = get_checkmark_icon_path()

        self.chk_consent = QCheckBox(" [필수] 개인정보 수집 및 이용에 동의합니다.", container)
        self.chk_consent.setFont(QFont("Inter", 11, QFont.Bold))
        self.chk_consent.setCursor(Qt.PointingHandCursor)
        self.chk_consent.setStyleSheet(f"""
            QCheckBox {{ color: #000000; border: none; background: transparent; font-weight: bold; }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1.5px solid #A0A0A0;
                background-color: #FFFFFF;
            }}
            QCheckBox::indicator:checked {{
                background-color: {Colors.PRIMARY};
                border-color: {Colors.PRIMARY};
                image: url("{check_icon_path}");
            }}
        """)
        c_layout.addWidget(self.chk_consent)

        self.chk_marketing = QCheckBox(" [선택] 마케팅 활용 및 광고성 정보 수신에 동의합니다.", container)
        self.chk_marketing.setFont(QFont("Inter", 11, QFont.Bold))
        self.chk_marketing.setCursor(Qt.PointingHandCursor)
        self.chk_marketing.setStyleSheet(f"""
            QCheckBox {{ color: #00594C; border: none; background: transparent; font-weight: bold; }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1.5px solid #A0A0A0;
                background-color: #FFFFFF;
            }}
            QCheckBox::indicator:checked {{
                background-color: {Colors.PRIMARY};
                border-color: {Colors.PRIMARY};
                image: url("{check_icon_path}");
            }}
        """)
        c_layout.addWidget(self.chk_marketing)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        btn_confirm = QPushButton("동의 완료", container)
        btn_confirm.setFixedHeight(42)
        btn_confirm.setCursor(Qt.PointingHandCursor)
        btn_confirm.setFont(QFont("Inter", 12, QFont.Bold))
        btn_confirm.setStyleSheet(f"""
            QPushButton {{ background-color: {Colors.PRIMARY}; color: #FFFFFF; border: none; border-radius: 8px; }}
            QPushButton:hover {{ background-color: {Colors.PRIMARY_HOVER}; }}
        """)
        btn_confirm.clicked.connect(self.on_confirm)

        btn_cancel = QPushButton("취소", container)
        btn_cancel.setFixedHeight(42)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setFont(QFont("Inter", 12, QFont.Bold))
        btn_cancel.setStyleSheet("""
            QPushButton { background-color: #E0E0E0; color: #333333; border: none; border-radius: 8px; }
            QPushButton:hover { background-color: #C0C0C0; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_confirm, 1)
        btn_layout.addWidget(btn_cancel, 1)
        c_layout.addLayout(btn_layout)

        outer_layout.addWidget(container)

    def on_confirm(self):
        if not self.chk_consent.isChecked():
            CustomAlertDialog("동의 필요", "[필수] 개인정보 수집 및 이용 동의 항목에 체크해 주세요.", self).exec()
            return
        self.accept()


class ConfirmCancelDialog(QDialog):
    """뒤로가기 클릭 시 노출되는 결제 취소 확인 팝업"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(540, 220)

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
        c_layout.setContentsMargins(30, 35, 30, 25)
        c_layout.setSpacing(25)

        lbl_msg = QLabel("현재 등록중인 결제건을 <font color='#E53E3E'>취소</font> 하시겠습니까?", container)
        lbl_msg.setFont(QFont("Inter", 16, QFont.Bold))
        lbl_msg.setAlignment(Qt.AlignCenter)
        lbl_msg.setStyleSheet("border: none; background: transparent; color: #000000;")

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)
        btn_layout.setAlignment(Qt.AlignCenter)

        btn_confirm = QPushButton("확인", container)
        btn_confirm.setFixedSize(130, 42)
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
        btn_cancel.setFixedSize(130, 42)
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

        btn_layout.addWidget(btn_confirm)
        btn_layout.addWidget(btn_cancel)

        c_layout.addWidget(lbl_msg)
        c_layout.addLayout(btn_layout)

        outer_layout.addWidget(container)


class RoundedHeader(QHeaderView):
    """상단 양쪽 모서리만 라운드 적용 커스텀 헤더 뷰"""

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
            doc.setHtml(f"<div style='color: #FFFFFF; font-weight: bold; font-size: 13px; text-align: center;'>{text}</div>")
            doc.setTextWidth(rect.width())

            y_offset = (rect.height() - doc.size().height()) / 2
            painter.translate(rect.x(), rect.y() + y_offset)
            doc.drawContents(painter)

        painter.restore()


class YellowStarHeader(QHeaderView):
    """상단 양쪽 모서리만 라운드 적용 및 별표(*) 노란색 커스텀 헤더 뷰"""

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
            formatted_text = text.replace("*", " <font color='#FFD700'>*</font>")
            doc = QTextDocument()
            doc.setHtml(f"<div style='color: #FFFFFF; font-weight: bold; font-size: 13px; text-align: center;'>{formatted_text}</div>")
            doc.setTextWidth(rect.width())

            y_offset = (rect.height() - doc.size().height()) / 2
            painter.translate(rect.x(), rect.y() + y_offset)
            doc.drawContents(painter)

        painter.restore()


class QuantityControlWidget(QWidget):
    """장바구니 표의 증감 컬럼 내 + / - 버튼"""

    def __init__(self, service_id: int, on_increase, on_decrease, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        layout.setAlignment(Qt.AlignCenter)

        btn_plus = QPushButton("+", self)
        btn_plus.setFixedSize(22, 22)
        btn_plus.setCursor(Qt.PointingHandCursor)
        btn_plus.setFont(QFont("Inter", 10, QFont.Bold))
        btn_plus.setStyleSheet(f"""
            QPushButton {{
                background-color: #E0E0E0;
                color: #000000;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY};
                color: #FFFFFF;
            }}
        """)
        btn_plus.clicked.connect(lambda: on_increase(service_id))

        btn_minus = QPushButton("-", self)
        btn_minus.setFixedSize(22, 22)
        btn_minus.setCursor(Qt.PointingHandCursor)
        btn_minus.setFont(QFont("Inter", 10, QFont.Bold))
        btn_minus.setStyleSheet(f"""
            QPushButton {{
                background-color: #E0E0E0;
                color: #000000;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {Colors.DANGER};
                color: #FFFFFF;
            }}
        """)
        btn_minus.clicked.connect(lambda: on_decrease(service_id))

        layout.addWidget(btn_plus)
        layout.addWidget(btn_minus)


class SalesRegistrationView(QWidget):
    """매출 등록 메인 뷰 (선결제 잔액 · 일반 포인트 독립 차감 및 [결제하기] 수단 선택 모달 지원)"""

    page_changed = Signal(bool)

    KEY_GENERAL_RATE = "point_rate_general"
    KEY_PREPAID_RATE = "point_rate_prepaid"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DBManager()
        self.selected_customer = None
        self.cart_items = []
        self.categories_data = []
        self.services_map = {}
        self.active_category_name = None

        self.total_amount = 0
        self.remaining_amount = 0
        self.payments_history = []  # 현금/카드 분할결제 내역 기록

        self.setup_ui()
        self.load_customer_list()
        self.load_menu_data()
        self.load_designers()

    def get_point_rates(self) -> tuple[float, float]:
        """DB 설정 테이블에서 일반 및 선결제 적립률 비율 조회 (기본값: 일반 10%, 선결제 20%)"""
        gen_str = self.db_manager.get_setting(self.KEY_GENERAL_RATE, default="10")
        prep_str = self.db_manager.get_setting(self.KEY_PREPAID_RATE, default="20")

        try:
            gen_rate = float(gen_str) / 100.0
        except ValueError:
            gen_rate = 0.10

        try:
            prep_rate = float(prep_str) / 100.0
        except ValueError:
            prep_rate = 0.20

        return gen_rate, prep_rate

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(25, 15, 25, 25)
        main_layout.setSpacing(0)

        self.main_stack = QStackedWidget(self)

        # ---------------------------------------------------------
        # Page 0: 고객 선택 화면
        # ---------------------------------------------------------
        page_select_cust = QWidget()
        select_layout = QHBoxLayout(page_select_cust)
        select_layout.setContentsMargins(0, 0, 0, 0)
        select_layout.setSpacing(20)

        left_outer = QFrame(page_select_cust)
        left_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        left_outer.setAttribute(Qt.WA_StyledBackground, True)

        left_layout = QVBoxLayout(left_outer)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(8)

        search_box = QFrame(left_outer)
        search_box.setFixedHeight(42)
        search_box.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        search_box.setAttribute(Qt.WA_StyledBackground, True)

        search_layout = QHBoxLayout(search_box)
        search_layout.setContentsMargins(12, 0, 12, 0)
        search_layout.setSpacing(10)

        lbl_search_icon = QLabel(search_box)
        lbl_search_icon.setPixmap(get_icon("search.svg").pixmap(18, 18))
        lbl_search_icon.setStyleSheet("background: transparent;")

        self.txt_search = QLineEdit(search_box)
        self.txt_search.setPlaceholderText("이름 또는 전화번호")
        self.txt_search.setFont(QFont("Inter", 12))
        self.txt_search.setStyleSheet("border: none; background: transparent; color: #000000;")
        self.txt_search.textChanged.connect(self.filter_customer_list)

        search_layout.addWidget(lbl_search_icon)
        search_layout.addWidget(self.txt_search, 1)
        left_layout.addWidget(search_box)

        table_container = QFrame(left_outer)
        table_container.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        table_container.setAttribute(Qt.WA_StyledBackground, True)

        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.cust_table = QTableWidget(table_container)

        custom_cust_header = RoundedHeader(Qt.Horizontal, self.cust_table)
        custom_cust_header.setFixedHeight(40)
        self.cust_table.setHorizontalHeader(custom_cust_header)

        self.cust_table.setColumnCount(4)
        self.cust_table.setHorizontalHeaderLabels(["번호", "이름", "전화번호", "최근 방문일자"])
        self.cust_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cust_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.cust_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cust_table.verticalHeader().setVisible(False)
        self.cust_table.setShowGrid(False)
        self.cust_table.setFocusPolicy(Qt.NoFocus)
        self.cust_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cust_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.cust_table.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: #FFFFFF;
                border-radius: 6px;
                font-size: 13px;
                color: #000000;
                outline: none;
            }
            QTableWidget::item {
                border-bottom: 1px solid #E0E0E0;
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #E8F5E9;
                color: #000000;
                font-weight: bold;
            }
        """)
        self.cust_table.verticalScrollBar().setStyleSheet(SCROLLBAR_STYLE)
        self.cust_table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.cust_table.itemSelectionChanged.connect(self.on_customer_selected)

        table_layout.addWidget(self.cust_table)
        left_layout.addWidget(table_container, 1)
        select_layout.addWidget(left_outer, 2)

        page_empty = QWidget()
        page_empty_layout = QVBoxLayout(page_empty)
        lbl_empty = QLabel("매출 등록할 고객을 선택해 주세요", page_empty)
        lbl_empty.setFont(QFont("Inter", 20, QFont.Bold))
        lbl_empty.setStyleSheet("color: #000000; background: transparent;")
        lbl_empty.setAlignment(Qt.AlignCenter)
        page_empty_layout.addWidget(lbl_empty)

        select_layout.addWidget(page_empty, 3)
        self.main_stack.addWidget(page_select_cust)

        # ---------------------------------------------------------
        # Page 1: 매출 등록 대시보드
        # ---------------------------------------------------------
        page_sales = QWidget()
        sales_layout = QHBoxLayout(page_sales)
        sales_layout.setContentsMargins(0, 0, 0, 0)
        sales_layout.setSpacing(20)

        left_sales_panel = QWidget(page_sales)
        left_sales_panel.setMinimumWidth(0)
        left_s_layout = QVBoxLayout(left_sales_panel)
        left_s_layout.setContentsMargins(0, 0, 0, 0)
        left_s_layout.setSpacing(0)

        # 좌측 통합 회색 패널 (담당 디자이너 행 + 고객 정보 행 + 결제탭 + 결제하기 버튼 포함)
        left_sales_outer = QFrame(left_sales_panel)
        left_sales_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        left_sales_outer.setAttribute(Qt.WA_StyledBackground, True)
        left_outer_layout = QVBoxLayout(left_sales_outer)
        left_outer_layout.setContentsMargins(8, 8, 8, 8)
        left_outer_layout.setSpacing(8)

        # 1. 상단 옵션 바 (담당 디자이너 / 결제일 / 시술 시간)
        ctrl_frame = QFrame(left_sales_outer)
        ctrl_frame.setFixedHeight(64)
        ctrl_frame.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        ctrl_frame.setAttribute(Qt.WA_StyledBackground, True)
        ctrl_layout = QHBoxLayout(ctrl_frame)
        ctrl_layout.setContentsMargins(10, 6, 10, 6)
        ctrl_layout.setSpacing(6)

        arrow_down_path = get_resource_arrow_path("down")
        arrow_up_path = get_resource_arrow_path("up")

        unified_input_border = """
            border: 1.5px solid #C0C0C0;
            border-radius: 4px;
            background-color: #FAFAFA;
            color: #000000;
        """

        widget_designer = QWidget(ctrl_frame)
        widget_designer.setStyleSheet("background: transparent; border: none;")
        widget_designer.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        widget_designer.setMinimumWidth(0)

        v_designer = QVBoxLayout(widget_designer)
        v_designer.setContentsMargins(0, 0, 0, 0)
        v_designer.setSpacing(2)

        lbl_d = QLabel("담당 디자이너", widget_designer)
        lbl_d.setFont(QFont("Inter", 9, QFont.Bold))
        lbl_d.setStyleSheet("color: #666666; border: none; background: transparent;")

        self.cb_designer = QComboBox(widget_designer)
        self.cb_designer.setFixedHeight(30)
        self.cb_designer.setFont(QFont("Inter", 10))
        self.cb_designer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cb_designer.setMinimumWidth(0)
        self.cb_designer.view().setMinimumWidth(180)
        self.cb_designer.setStyleSheet(f"""
            QComboBox {{
                {unified_input_border}
                padding-left: 8px;
                padding-right: 24px;
            }}
            QComboBox:focus {{
                border: 1.5px solid {Colors.PRIMARY};
                background-color: #FFFFFF;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 24px;
                border: none;
                background: transparent;
            }}
            QComboBox::down-arrow {{
                image: url("{arrow_down_path}");
                width: 11px;
                height: 11px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #FFFFFF;
                color: #000000;
                border: 1px solid #B0B0B0;
                selection-background-color: #E8F5E9;
                selection-color: #000000;
            }}
        """)
        v_designer.addWidget(lbl_d)
        v_designer.addWidget(self.cb_designer)

        widget_date = QWidget(ctrl_frame)
        widget_date.setStyleSheet("background: transparent; border: none;")
        widget_date.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        widget_date.setMinimumWidth(0)

        v_date = QVBoxLayout(widget_date)
        v_date.setContentsMargins(0, 0, 0, 0)
        v_date.setSpacing(2)

        lbl_dt = QLabel("결제일", widget_date)
        lbl_dt.setFont(QFont("Inter", 9, QFont.Bold))
        lbl_dt.setStyleSheet("color: #666666; border: none; background: transparent;")

        self.date_visit = QDateEdit(widget_date)
        self.date_visit.setDate(QDate.currentDate())
        self.date_visit.setDisplayFormat("yyyy-MM-dd")
        self.date_visit.setFixedHeight(30)
        self.date_visit.setFont(QFont("Inter", 10))
        self.date_visit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.date_visit.setMinimumWidth(0)
        self.date_visit.setCalendarPopup(True)

        cal = self.date_visit.calendarWidget()
        if cal:
            cal.setNavigationBarVisible(True)

        self.date_visit.setStyleSheet(f"""
            QDateEdit {{
                {unified_input_border}
                padding-left: 6px;
                padding-right: 22px;
            }}
            QDateEdit:focus {{
                border: 1.5px solid {Colors.PRIMARY};
                background-color: #FFFFFF;
            }}
            QDateEdit::drop-down {{
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 22px;
                border: none;
                background: transparent;
            }}
            QDateEdit::down-arrow {{
                image: url("{arrow_down_path}");
                width: 10px;
                height: 10px;
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
        """)
        v_date.addWidget(lbl_dt)
        v_date.addWidget(self.date_visit)

        widget_dur = QWidget(ctrl_frame)
        widget_dur.setStyleSheet("background: transparent; border: none;")
        widget_dur.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        widget_dur.setMinimumWidth(0)

        v_dur = QVBoxLayout(widget_dur)
        v_dur.setContentsMargins(0, 0, 0, 0)
        v_dur.setSpacing(2)

        lbl_dur = QLabel("시술 시간", widget_dur)
        lbl_dur.setFont(QFont("Inter", 9, QFont.Bold))
        lbl_dur.setStyleSheet("color: #666666; border: none; background: transparent;")

        h_dur_box = QHBoxLayout()
        h_dur_box.setContentsMargins(0, 0, 0, 0)
        h_dur_box.setSpacing(4)

        self.spn_duration = QSpinBox(widget_dur)
        self.spn_duration.setRange(0, 1440)
        self.spn_duration.setSingleStep(30)
        self.spn_duration.setValue(30)
        self.spn_duration.setAlignment(Qt.AlignCenter)
        self.spn_duration.setFixedHeight(30)
        self.spn_duration.setFont(QFont("Inter", 10))
        self.spn_duration.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.spn_duration.setMinimumWidth(0)
        self.spn_duration.setStyleSheet(f"""
            QSpinBox {{
                {unified_input_border}
                padding-left: 4px;
                padding-right: 18px;
            }}
            QSpinBox:focus {{
                border: 1.5px solid {Colors.PRIMARY};
                background-color: #FFFFFF;
            }}
            QSpinBox::up-button {{
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 18px;
                height: 14px;
                border: none;
                background: transparent;
            }}
            QSpinBox::up-arrow {{
                image: url("{arrow_up_path}");
                width: 10px;
                height: 10px;
            }}
            QSpinBox::down-button {{
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 18px;
                height: 14px;
                border: none;
                background: transparent;
            }}
            QSpinBox::down-arrow {{
                image: url("{arrow_down_path}");
                width: 10px;
                height: 10px;
            }}
        """)

        lbl_min_unit = QLabel("분", widget_dur)
        lbl_min_unit.setFont(QFont("Inter", 10, QFont.Bold))
        lbl_min_unit.setStyleSheet("color: #333333; border: none; background: transparent;")

        h_dur_box.addWidget(self.spn_duration, 1)
        h_dur_box.addWidget(lbl_min_unit)

        v_dur.addWidget(lbl_dur)
        v_dur.addLayout(h_dur_box)

        ctrl_layout.addWidget(widget_designer, 42)
        ctrl_layout.addWidget(widget_date, 36)
        ctrl_layout.addWidget(widget_dur, 22)
        left_outer_layout.addWidget(ctrl_frame)

        # 2. 고객 정보 박스 (이름 / 전화번호 / 메모)
        c_inner = QFrame(left_sales_outer)
        c_inner.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        c_inner.setAttribute(Qt.WA_StyledBackground, True)
        ci_layout = QVBoxLayout(c_inner)
        ci_layout.setContentsMargins(14, 10, 14, 10)
        ci_layout.setSpacing(8)

        row_qss = """
            QFrame {
                border: none;
                border-bottom: 1.5px solid #7A7A7A;
                border-radius: 0px;
                background-color: transparent;
            }
            QLabel {
                border: none;
                background: transparent;
                font-weight: bold;
            }
        """

        f_name = QFrame(c_inner)
        f_name.setFixedHeight(26)
        f_name.setStyleSheet(row_qss)
        r_name = QHBoxLayout(f_name)
        r_name.setContentsMargins(0, 0, 0, 0)
        lbl_name = QLabel("이 름 :", f_name)
        lbl_name.setFont(QFont("Inter", 10, QFont.Bold))
        lbl_name.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbl_info_name = QLabel("-", f_name)
        self.lbl_info_name.setFont(QFont("Inter", 10, QFont.Bold))
        self.lbl_info_name.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        r_name.addWidget(lbl_name)
        r_name.addWidget(self.lbl_info_name, 1)
        ci_layout.addWidget(f_name)

        f_phone = QFrame(c_inner)
        f_phone.setFixedHeight(26)
        f_phone.setStyleSheet(row_qss)
        r_phone = QHBoxLayout(f_phone)
        r_phone.setContentsMargins(0, 0, 0, 0)
        lbl_phone = QLabel("전화번호 :", f_phone)
        lbl_phone.setFont(QFont("Inter", 10, QFont.Bold))
        lbl_phone.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbl_info_phone = QLabel("-", f_phone)
        self.lbl_info_phone.setFont(QFont("Inter", 10, QFont.Bold))
        self.lbl_info_phone.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        r_phone.addWidget(lbl_phone)
        r_phone.addWidget(self.lbl_info_phone, 1)
        ci_layout.addWidget(f_phone)

        lbl_m_title = QLabel("메모 :", c_inner)
        lbl_m_title.setFont(QFont("Inter", 10, QFont.Bold))
        lbl_m_title.setStyleSheet("border: none; background: transparent; color: #000000; font-weight: bold;")
        ci_layout.addWidget(lbl_m_title)

        self.txt_info_memo = QTextEdit(c_inner)
        self.txt_info_memo.setPlaceholderText("특이사항 및 메모 입력")
        self.txt_info_memo.setFont(QFont("Inter", 10, QFont.Bold))
        self.txt_info_memo.setMinimumHeight(55)
        self.txt_info_memo.setStyleSheet("""
            QTextEdit {
                background-color: #FAFAFA;
                border: 1.5px solid #7A7A7A;
                border-radius: 6px;
                padding: 6px;
                color: #333333;
                font-weight: bold;
            }
            QTextEdit:focus {
                border: 1.5px solid #0D705C;
                background-color: #FFFFFF;
            }
        """)
        self.txt_info_memo.verticalScrollBar().setStyleSheet(SCROLLBAR_STYLE)
        ci_layout.addWidget(self.txt_info_memo, 1)

        left_outer_layout.addWidget(c_inner, 1)

        # 3. 통합 결제 정보 카드 (선결제 잔액 사용 · 포인트 사용 독립 입력)
        pay_card = QFrame(left_sales_outer)
        pay_card.setStyleSheet(f"background-color: #FFFFFF; border: 2px solid {Colors.PRIMARY}; border-radius: 6px;")
        pay_card.setAttribute(Qt.WA_StyledBackground, True)
        pay_card_layout = QVBoxLayout(pay_card)
        pay_card_layout.setContentsMargins(14, 12, 14, 12)
        pay_card_layout.setSpacing(7)

        # 총 결제 금액
        r_total = QHBoxLayout()
        lbl_t_title = QLabel("총 결제 금액 :", pay_card)
        lbl_t_title.setFont(QFont("Inter", 12, QFont.Bold))
        lbl_t_title.setStyleSheet("border: none; background: transparent; color: #000000;")
        self.lbl_total_amount = QLabel("0 원", pay_card)
        self.lbl_total_amount.setFont(QFont("Inter", 14, QFont.Bold))
        self.lbl_total_amount.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_total_amount.setStyleSheet("border: none; background: transparent; color: #000000;")
        r_total.addWidget(lbl_t_title)
        r_total.addWidget(self.lbl_total_amount, 1)
        pay_card_layout.addLayout(r_total)

        deduct_input_style = f"""
            QLineEdit {{
                border: 1.5px solid #B0B0B0;
                border-radius: 5px;
                padding: 2px 6px;
                background-color: #FAFAFA;
                color: #000000;
            }}
            QLineEdit:focus {{
                border: 1.5px solid {Colors.PRIMARY};
                background-color: #FFFFFF;
            }}
        """
        use_all_btn_style = f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 0px 8px;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
            }}
        """

        # 선결제 잔액 사용
        r_prepaid = QHBoxLayout()
        r_prepaid.setSpacing(5)
        lbl_pr_title = QLabel("선결제 잔액 사용 :", pay_card)
        lbl_pr_title.setFont(QFont("Inter", 10, QFont.Bold))
        lbl_pr_title.setStyleSheet("border: none; background: transparent; color: #000000;")

        self.lbl_avail_prepaid = QLabel("0원 중", pay_card)
        self.lbl_avail_prepaid.setFont(QFont("Inter", 9, QFont.Bold))
        self.lbl_avail_prepaid.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_avail_prepaid.setStyleSheet("border: none; background: transparent; color: #444444;")

        self.txt_use_prepaid = QLineEdit("0", pay_card)
        self.txt_use_prepaid.setFixedSize(78, 26)
        self.txt_use_prepaid.setFont(QFont("Inter", 10, QFont.Bold))
        self.txt_use_prepaid.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.txt_use_prepaid.setStyleSheet(deduct_input_style)
        self.txt_use_prepaid.textChanged.connect(self.on_use_prepaid_changed)

        self.btn_use_all_prepaid = QPushButton("전액 사용", pay_card)
        self.btn_use_all_prepaid.setFixedHeight(26)
        self.btn_use_all_prepaid.setCursor(Qt.PointingHandCursor)
        self.btn_use_all_prepaid.setFont(QFont("Inter", 9, QFont.Bold))
        self.btn_use_all_prepaid.setStyleSheet(use_all_btn_style)
        self.btn_use_all_prepaid.clicked.connect(self.apply_all_prepaid)

        r_prepaid.addWidget(lbl_pr_title)
        r_prepaid.addWidget(self.lbl_avail_prepaid, 1)
        r_prepaid.addWidget(self.txt_use_prepaid)
        r_prepaid.addWidget(self.btn_use_all_prepaid)
        pay_card_layout.addLayout(r_prepaid)

        # 포인트 사용
        r_point = QHBoxLayout()
        r_point.setSpacing(5)
        lbl_pt_title = QLabel("포인트 사용 :", pay_card)
        lbl_pt_title.setFont(QFont("Inter", 10, QFont.Bold))
        lbl_pt_title.setStyleSheet("border: none; background: transparent; color: #000000;")

        self.lbl_avail_point = QLabel("0P 중", pay_card)
        self.lbl_avail_point.setFont(QFont("Inter", 9, QFont.Bold))
        self.lbl_avail_point.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_avail_point.setStyleSheet("border: none; background: transparent; color: #444444;")

        self.txt_use_point = QLineEdit("0", pay_card)
        self.txt_use_point.setFixedSize(78, 26)
        self.txt_use_point.setFont(QFont("Inter", 10, QFont.Bold))
        self.txt_use_point.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.txt_use_point.setStyleSheet(deduct_input_style)
        self.txt_use_point.textChanged.connect(self.on_use_point_changed)

        self.btn_use_all_point = QPushButton("전액 사용", pay_card)
        self.btn_use_all_point.setFixedHeight(26)
        self.btn_use_all_point.setCursor(Qt.PointingHandCursor)
        self.btn_use_all_point.setFont(QFont("Inter", 9, QFont.Bold))
        self.btn_use_all_point.setStyleSheet(use_all_btn_style)
        self.btn_use_all_point.clicked.connect(self.apply_all_point)

        r_point.addWidget(lbl_pt_title)
        r_point.addWidget(self.lbl_avail_point, 1)
        r_point.addWidget(self.txt_use_point)
        r_point.addWidget(self.btn_use_all_point)
        pay_card_layout.addLayout(r_point)

        # 할인/차감 합계
        r_deduct = QHBoxLayout()
        lbl_dd_title = QLabel("할인/차감 :", pay_card)
        lbl_dd_title.setFont(QFont("Inter", 9, QFont.Bold))
        lbl_dd_title.setStyleSheet("border: none; background: transparent; color: #666666;")

        self.lbl_deduct_amount = QLabel("0원", pay_card)
        self.lbl_deduct_amount.setFont(QFont("Inter", 9, QFont.Bold))
        self.lbl_deduct_amount.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_deduct_amount.setStyleSheet("border: none; background: transparent; color: #666666;")

        r_deduct.addWidget(lbl_dd_title)
        r_deduct.addWidget(self.lbl_deduct_amount, 1)
        pay_card_layout.addLayout(r_deduct)

        # 구분선
        divider = QFrame(pay_card)
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #DCDCDC; border: none;")
        pay_card_layout.addWidget(divider)

        # 받을 금액 (카드/현금)
        r_recv = QHBoxLayout()
        r_recv.setSpacing(5)
        lbl_rc_title = QLabel("받을 금액(카드/현금) :", pay_card)
        lbl_rc_title.setFont(QFont("Inter", 11, QFont.Bold))
        lbl_rc_title.setStyleSheet("border: none; background: transparent; color: #000000;")

        self.txt_received_amount = QLineEdit("0", pay_card)
        self.txt_received_amount.setFont(QFont("Inter", 12, QFont.Bold))
        self.txt_received_amount.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.txt_received_amount.setStyleSheet("""
            QLineEdit {
                border: 1.5px solid #C0C0C0;
                border-radius: 6px;
                padding: 3px 8px;
                background-color: #FAFAFA;
                color: #000000;
            }
            QLineEdit:focus {
                border: 2px solid #0D705C;
                background-color: #FFFFFF;
            }
        """)
        self.txt_received_amount.textChanged.connect(self.on_received_amount_changed)

        lbl_won_unit = QLabel("원", pay_card)
        lbl_won_unit.setFont(QFont("Inter", 11, QFont.Bold))
        lbl_won_unit.setStyleSheet("border: none; background: transparent; color: #000000;")

        r_recv.addWidget(lbl_rc_title)
        r_recv.addWidget(self.txt_received_amount, 1)
        r_recv.addWidget(lbl_won_unit)
        pay_card_layout.addLayout(r_recv)

        # 남은 금액 / 거스름돈
        r_status = QHBoxLayout()
        self.lbl_status_title = QLabel("남은금액 :", pay_card)
        self.lbl_status_title.setFont(QFont("Inter", 12, QFont.Bold))
        self.lbl_status_title.setStyleSheet("border: none; background: transparent; color: #E53E3E;")

        self.lbl_status_val = QLabel("0 원", pay_card)
        self.lbl_status_val.setFont(QFont("Inter", 13, QFont.Bold))
        self.lbl_status_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_status_val.setStyleSheet("border: none; background: transparent; color: #E53E3E;")

        r_status.addWidget(self.lbl_status_title)
        r_status.addWidget(self.lbl_status_val, 1)
        pay_card_layout.addLayout(r_status)

        # 적립 / 충전 예정 안내
        r_earn_point = QHBoxLayout()
        self.lbl_earn_title = QLabel("적립 예정 포인트 :", pay_card)
        self.lbl_earn_title.setFont(QFont("Inter", 9, QFont.Bold))
        self.lbl_earn_title.setStyleSheet("border: none; background: transparent; color: #2B6CB0;")

        self.lbl_earn_point_val = QLabel("0 P", pay_card)
        self.lbl_earn_point_val.setFont(QFont("Inter", 9, QFont.Bold))
        self.lbl_earn_point_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_earn_point_val.setStyleSheet("border: none; background: transparent; color: #2B6CB0;")

        r_earn_point.addWidget(self.lbl_earn_title)
        r_earn_point.addWidget(self.lbl_earn_point_val, 1)
        pay_card_layout.addLayout(r_earn_point)

        # 분할결제 진행 내역 요약 (가로 스크롤 지원)
        self.history_scroll = HorizontalScrollArea(pay_card)
        self.history_scroll.setFixedHeight(26)
        self.history_scroll.setMinimumWidth(0)
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.history_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.history_scroll.setStyleSheet(SLIM_H_SCROLLBAR_STYLE)
        self.history_scroll.setVisible(False)

        self.lbl_history_summary = QLabel("")
        self.lbl_history_summary.setFont(QFont("Inter", 9, QFont.Bold))
        self.lbl_history_summary.setStyleSheet("color: #0D705C; border: none; background: transparent; padding-bottom: 2px;")
        self.lbl_history_summary.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.history_scroll.setWidget(self.lbl_history_summary)

        pay_card_layout.addWidget(self.history_scroll)

        left_outer_layout.addWidget(pay_card)

        # 4. 단일 [결제하기] 버튼 (좌측 회색 바탕 내부에 포함)
        self.btn_pay_submit = QPushButton("결제하기", left_sales_outer)
        self.btn_pay_submit.setFixedHeight(44)
        self.btn_pay_submit.setCursor(Qt.PointingHandCursor)
        self.btn_pay_submit.setFont(QFont("Inter", 13, QFont.Bold))
        self.btn_pay_submit.setStyleSheet(f"""
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
        self.btn_pay_submit.clicked.connect(self.on_click_pay_submit)
        left_outer_layout.addWidget(self.btn_pay_submit)

        left_s_layout.addWidget(left_sales_outer, 1)

        # ---------------------------------------------------------
        # 우측 패널 (상단: 카테고리 및 시술 메뉴 / 하단: 장바구니 테이블)
        # ---------------------------------------------------------
        right_sales_panel = QWidget(page_sales)
        right_sales_panel.setMinimumWidth(0)
        right_s_layout = QVBoxLayout(right_sales_panel)
        right_s_layout.setContentsMargins(0, 0, 0, 0)
        right_s_layout.setSpacing(10)

        # 카테고리 탭 및 시술 메뉴 그리드 (상단)
        menu_outer = QFrame(right_sales_panel)
        menu_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        menu_outer.setAttribute(Qt.WA_StyledBackground, True)
        menu_o_layout = QVBoxLayout(menu_outer)
        menu_o_layout.setContentsMargins(8, 8, 8, 8)
        menu_o_layout.setSpacing(8)

        category_scroll = HorizontalScrollArea(menu_outer)
        category_scroll.setFixedHeight(66)
        category_scroll.setWidgetResizable(True)
        category_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        category_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        category_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        category_widget = QWidget()
        category_widget.setStyleSheet("background: transparent;")
        self.category_bar_layout = QHBoxLayout(category_widget)
        self.category_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.category_bar_layout.setSpacing(8)
        self.category_bar_layout.setAlignment(Qt.AlignLeft)
        category_scroll.setWidget(category_widget)

        menu_o_layout.addWidget(category_scroll)

        menu_inner = QFrame(menu_outer)
        menu_inner.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        menu_inner.setAttribute(Qt.WA_StyledBackground, True)
        menu_i_layout = QVBoxLayout(menu_inner)
        menu_i_layout.setContentsMargins(6, 6, 6, 6)

        scroll_area = QScrollArea(menu_inner)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.service_grid_widget = QWidget()
        self.service_grid_widget.setStyleSheet("background: transparent;")
        
        self.service_grid_layout = QGridLayout(self.service_grid_widget)
        self.service_grid_layout.setContentsMargins(2, 2, 2, 2)
        self.service_grid_layout.setSpacing(6)
        self.service_grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        for c in range(4):
            self.service_grid_layout.setColumnStretch(c, 1)

        scroll_area.setWidget(self.service_grid_widget)
        menu_i_layout.addWidget(scroll_area)

        menu_o_layout.addWidget(menu_inner, 1)
        right_s_layout.addWidget(menu_outer, 1)

        # 장바구니 영역 패널 (하단)
        cart_outer = QFrame(right_sales_panel)
        cart_outer.setStyleSheet("background-color: #DCDCDC; border-radius: 10px;")
        cart_outer.setAttribute(Qt.WA_StyledBackground, True)
        cart_o_layout = QVBoxLayout(cart_outer)
        cart_o_layout.setContentsMargins(8, 8, 8, 8)

        cart_inner = QFrame(cart_outer)
        cart_inner.setStyleSheet("background-color: #FFFFFF; border-radius: 6px;")
        cart_inner.setAttribute(Qt.WA_StyledBackground, True)
        cart_i_layout = QVBoxLayout(cart_inner)
        cart_i_layout.setContentsMargins(0, 0, 0, 8)
        cart_i_layout.setSpacing(6)

        self.cart_table = QTableWidget(cart_inner)
        
        custom_header = YellowStarHeader(Qt.Horizontal, self.cart_table)
        custom_header.setFixedHeight(38)
        self.cart_table.setHorizontalHeader(custom_header)

        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(["메뉴명", "단가*", "수량*", "금액", "증감"])
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.setDefaultDropAction(Qt.IgnoreAction)
        self.cart_table.verticalHeader().setDefaultSectionSize(40)
        self.cart_table.setShowGrid(False)
        self.cart_table.setFocusPolicy(Qt.NoFocus)
        self.cart_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.cart_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.cart_table.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: #FFFFFF;
                border-radius: 6px;
                font-size: 13px;
                color: #000000;
            }
            QTableWidget::item {
                border-bottom: 1px solid #E0E0E0;
                padding: 4px;
            }
        """)
        self.cart_table.verticalScrollBar().setStyleSheet(SCROLLBAR_STYLE)
        self.cart_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cart_table.itemChanged.connect(self.on_cart_cell_changed)
        cart_i_layout.addWidget(self.cart_table, 1)

        lbl_cart_tip = QLabel("* 단가와 수량은 더블클릭 후 키보드로 수정할 수 있습니다 *", cart_inner)
        lbl_cart_tip.setFont(QFont("Inter", 11, QFont.Bold))
        lbl_cart_tip.setStyleSheet("color: #E53E3E; background: transparent;")
        lbl_cart_tip.setAlignment(Qt.AlignCenter)
        cart_i_layout.addWidget(lbl_cart_tip)

        cart_o_layout.addWidget(cart_inner)
        right_s_layout.addWidget(cart_outer, 1)

        sales_layout.addWidget(left_sales_panel, 36)
        sales_layout.addWidget(right_sales_panel, 64)

        self.main_stack.addWidget(page_sales)

        main_layout.addWidget(self.main_stack)
        self.main_stack.setCurrentIndex(0)

    # -------------------------------------------------------------
    # 숫자 파싱 헬퍼
    # -------------------------------------------------------------
    @staticmethod
    def _parse_int(text: str) -> int:
        digits = "".join(filter(str.isdigit, text or ""))
        return int(digits) if digits else 0

    def _get_non_prepaid_cart_total(self) -> int:
        """선결제 충전 상품을 제외한 일반 시술 합계 금액"""
        return sum(
            item["price"] * item["qty"]
            for item in self.cart_items
            if item.get("category_name") != "선결제"
        )

    def _get_prepaid_charge_cart_total(self) -> int:
        """'선결제' 카테고리 충전 시술 합계 금액"""
        return sum(
            item["price"] * item["qty"]
            for item in self.cart_items
            if item.get("category_name") == "선결제"
        )

    # -------------------------------------------------------------
    # 고객 목록 / 메뉴 / 디자이너 로딩
    # -------------------------------------------------------------
    def confirm_and_clear_selection(self):
        """뒤로가기 클릭 시 취소 확인 팝업 노출"""
        dialog = ConfirmCancelDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.clear_customer_selection()

    def load_customer_list(self):
        self.all_customers = self.db_manager.get_all_customers()
        self.filter_customer_list()

    def filter_customer_list(self):
        query = self.txt_search.text().strip().lower()
        self.cust_table.setRowCount(0)

        row_count = 0
        for cust in self.all_customers:
            name = cust["name"]
            phone = cust["phone"]
            if query and (query not in name.lower() and query not in phone.lower()):
                continue

            self.cust_table.insertRow(row_count)

            item_no = QTableWidgetItem(str(cust["id"]))
            item_no.setTextAlignment(Qt.AlignCenter)
            item_no.setData(Qt.UserRole, cust["id"])
            self.cust_table.setItem(row_count, 0, item_no)

            item_name = QTableWidgetItem(name)
            item_name.setTextAlignment(Qt.AlignCenter)
            self.cust_table.setItem(row_count, 1, item_name)

            item_phone = QTableWidgetItem(phone)
            item_phone.setTextAlignment(Qt.AlignCenter)
            self.cust_table.setItem(row_count, 2, item_phone)

            item_visit = QTableWidgetItem(cust["recent_visit"] or "-")
            item_visit.setTextAlignment(Qt.AlignCenter)
            self.cust_table.setItem(row_count, 3, item_visit)

            row_count += 1

    def update_table_column_widths(self):
        total_width = self.cust_table.viewport().width()
        if total_width > 0:
            w0 = int(total_width * 0.15)
            w1 = int(total_width * 0.25)
            w2 = int(total_width * 0.30)
            w3 = total_width - (w0 + w1 + w2)
            self.cust_table.setColumnWidth(0, w0)
            self.cust_table.setColumnWidth(1, w1)
            self.cust_table.setColumnWidth(2, w2)
            self.cust_table.setColumnWidth(3, w3)

    def showEvent(self, event):
        super().showEvent(event)
        self.update_table_column_widths()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_table_column_widths()

    def load_designers(self):
        self.cb_designer.clear()
        designers = self.db_manager.get_all_designers()
        for d in designers:
            self.cb_designer.addItem(f"{d['name']} ({d['position']})", d['id'])

    def load_menu_data(self):
        self.categories_data, self.services_map = self.db_manager.fetch_active_categories_and_services()
        self.render_category_buttons()

    def render_category_buttons(self):
        while self.category_bar_layout.count():
            item = self.category_bar_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.categories_data:
            return

        for cat in self.categories_data:
            cat_name = cat["name"]
            btn = QPushButton(cat_name, self)
            btn.setFixedSize(95, 50)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFont(QFont("Inter", 11, QFont.Bold))
            btn.clicked.connect(lambda _, name=cat_name: self.select_category(name))
            self.category_bar_layout.addWidget(btn)

        if self.categories_data:
            self.select_category(self.categories_data[0]["name"])

    def select_category(self, category_name: str):
        self.active_category_name = category_name
        for i in range(self.category_bar_layout.count()):
            btn = self.category_bar_layout.itemAt(i).widget()
            if isinstance(btn, QPushButton):
                if btn.text() == category_name:
                    btn.setStyleSheet(f"background-color: {Colors.PRIMARY}; color: #FFFFFF; border: none; border-radius: 10px;")
                else:
                    btn.setStyleSheet("background-color: #888888; color: #FFFFFF; border: none; border-radius: 10px;")
        self.render_service_grid(category_name)

    def render_service_grid(self, category_name: str):
        while self.service_grid_layout.count():
            item = self.service_grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        services = self.services_map.get(category_name, [])
        col_count = 4

        for idx, svc in enumerate(services):
            row = idx // col_count
            col = idx % col_count

            btn_text = f"{svc['name']}\n{svc['price']:,}"
            btn = QPushButton(btn_text, self.service_grid_widget)
            
            btn.setFixedHeight(60)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFont(QFont("Inter", 11, QFont.Bold))
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.PRIMARY};
                    color: #FFFFFF;
                    border: none;
                    border-radius: 10px;
                    text-align: center;
                    padding: 4px 4px;
                }}
                QPushButton:hover {{
                    background-color: {Colors.PRIMARY_HOVER};
                }}
            """)
            btn.clicked.connect(lambda _, item=svc, cat=category_name: self.add_to_cart(item, cat))
            self.service_grid_layout.addWidget(btn, row, col)

    def on_customer_selected(self):
        selected_items = self.cust_table.selectedItems()
        if not selected_items:
            return

        row = self.cust_table.currentRow()
        cust_id = self.cust_table.item(row, 0).data(Qt.UserRole)
        target_cust = next((c for c in self.all_customers if int(c["id"]) == int(cust_id)), None)

        if target_cust:
            self.selected_customer = dict(target_cust)
            self.lbl_info_name.setText(self.selected_customer["name"])
            self.lbl_info_phone.setText(self.selected_customer["phone"])
            self.txt_info_memo.setPlainText(self.selected_customer.get("memo", "") or "")

            avail_prepaid = self.selected_customer.get("prepaid_balance", 0)
            avail_point = self.selected_customer.get("point", 0)
            self.lbl_avail_prepaid.setText(f"{avail_prepaid:,}원 중")
            self.lbl_avail_point.setText(f"{avail_point:,}P 중")

            self._set_deduction_inputs(0, 0)
            self.payments_history.clear()
            self.lbl_history_summary.setText("")
            self.history_scroll.setVisible(False)
            self.update_cart_table()

            self.main_stack.setCurrentIndex(1)
            self.page_changed.emit(True)

    def clear_customer_selection(self):
        self.selected_customer = None
        self.cust_table.clearSelection()
        self.cart_items.clear()
        self.payments_history.clear()
        self._set_deduction_inputs(0, 0)
        self.lbl_history_summary.setText("")
        self.history_scroll.setVisible(False)
        self.update_cart_table()
        self.main_stack.setCurrentIndex(0)
        
        self.page_changed.emit(False)

    # -------------------------------------------------------------
    # 선결제 잔액 · 포인트 독립 입력 및 금액 계산 로직
    # -------------------------------------------------------------
    def _set_deduction_inputs(self, use_prepaid: int, use_point: int):
        self.txt_use_prepaid.blockSignals(True)
        self.txt_use_prepaid.setText(f"{max(0, use_prepaid):,}")
        self.txt_use_prepaid.blockSignals(False)

        self.txt_use_point.blockSignals(True)
        self.txt_use_point.setText(f"{max(0, use_point):,}")
        self.txt_use_point.blockSignals(False)

    def apply_all_prepaid(self):
        """[선결제 잔액 사용] 전액 사용 버튼 클릭"""
        if not self.selected_customer:
            return
        avail_prepaid = self.selected_customer.get("prepaid_balance", 0)
        already_cash_card = sum(p["amount"] for p in self.payments_history)
        use_point = self._parse_int(self.txt_use_point.text())

        # 선결제 충전 상품은 선결제 잔액으로 재결제 불가하도록 일반 시술 금액 한도 적용
        non_prepaid_total = self._get_non_prepaid_cart_total()
        max_for_prepaid = max(0, non_prepaid_total - use_point - already_cash_card)
        target_val = min(avail_prepaid, max_for_prepaid)

        self.txt_use_prepaid.setText(f"{target_val:,}")

    def apply_all_point(self):
        """[포인트 사용] 전액 사용 버튼 클릭"""
        if not self.selected_customer:
            return
        avail_point = self.selected_customer.get("point", 0)
        already_cash_card = sum(p["amount"] for p in self.payments_history)
        use_prepaid = self._parse_int(self.txt_use_prepaid.text())

        non_prepaid_total = self._get_non_prepaid_cart_total()
        max_for_point = max(0, non_prepaid_total - use_prepaid - already_cash_card)
        target_val = min(avail_point, max_for_point)

        self.txt_use_point.setText(f"{target_val:,}")

    def on_use_prepaid_changed(self, text: str):
        avail_prepaid = self.selected_customer.get("prepaid_balance", 0) if self.selected_customer else 0
        already_cash_card = sum(p["amount"] for p in self.payments_history)
        use_point = self._parse_int(self.txt_use_point.text())

        non_prepaid_total = self._get_non_prepaid_cart_total()
        max_allowed = min(avail_prepaid, max(0, non_prepaid_total - use_point - already_cash_card))

        raw_val = self._parse_int(text)
        clamped_val = min(raw_val, max_allowed)

        self.txt_use_prepaid.blockSignals(True)
        self.txt_use_prepaid.setText(f"{clamped_val:,}")
        self.txt_use_prepaid.blockSignals(False)

        self.sync_balances_and_status(reset_received=True)

    def on_use_point_changed(self, text: str):
        avail_point = self.selected_customer.get("point", 0) if self.selected_customer else 0
        already_cash_card = sum(p["amount"] for p in self.payments_history)
        use_prepaid = self._parse_int(self.txt_use_prepaid.text())

        non_prepaid_total = self._get_non_prepaid_cart_total()
        max_allowed = min(avail_point, max(0, non_prepaid_total - use_prepaid - already_cash_card))

        raw_val = self._parse_int(text)
        clamped_val = min(raw_val, max_allowed)

        self.txt_use_point.blockSignals(True)
        self.txt_use_point.setText(f"{clamped_val:,}")
        self.txt_use_point.blockSignals(False)

        self.sync_balances_and_status(reset_received=True)

    def on_received_amount_changed(self, text: str):
        val = self._parse_int(text)
        self.txt_received_amount.blockSignals(True)
        self.txt_received_amount.setText(f"{val:,}")
        self.txt_received_amount.blockSignals(False)

        self.recalculate_payment_status()

    def calculate_expected_rewards(self) -> tuple[int, int]:
        """
        장바구니 기준 (일반 적립 예정 포인트, 충전 예정 선결제 금액) 계산
        - '선결제' 카테고리 시술: 원금 + 보너스(point_rate_prepaid) 합산하여 선결제 잔액 충전 (일반 포인트 이중 적립 제외)
        - 일반 시술: 선결제 잔액 사용 여부와 무관하게 일반 포인트 별도 적립 (단, 무료 포인트 사용분은 제외)
        """
        if self.total_amount <= 0 or not self.cart_items:
            return 0, 0

        gen_rate, prep_rate = self.get_point_rates()
        use_point = self._parse_int(self.txt_use_point.text())

        prepaid_item_total = self._get_prepaid_charge_cart_total()
        general_item_total = self._get_non_prepaid_cart_total()

        charged_prepaid = int(round(prepaid_item_total * (1.0 + prep_rate))) if prepaid_item_total > 0 else 0
        eligible_general_amt = max(0, general_item_total - use_point)
        earned_point = int(round(eligible_general_amt * gen_rate)) if eligible_general_amt > 0 else 0

        return earned_point, charged_prepaid

    def sync_balances_and_status(self, reset_received: bool = True):
        """총 결제 금액, 선결제/포인트 차감액, 남은 금액, 적립/충전 예정 표시 동기화"""
        avail_prepaid = self.selected_customer.get("prepaid_balance", 0) if self.selected_customer else 0
        avail_point = self.selected_customer.get("point", 0) if self.selected_customer else 0
        already_cash_card = sum(p["amount"] for p in self.payments_history)
        non_prepaid_total = self._get_non_prepaid_cart_total()

        use_prepaid = min(self._parse_int(self.txt_use_prepaid.text()), avail_prepaid, max(0, non_prepaid_total - already_cash_card))
        use_point = min(self._parse_int(self.txt_use_point.text()), avail_point, max(0, non_prepaid_total - already_cash_card - use_prepaid))
        self._set_deduction_inputs(use_prepaid, use_point)

        total_deducted = use_prepaid + use_point
        self.lbl_deduct_amount.setText(f"-{total_deducted:,}원" if total_deducted > 0 else "0원")

        self.remaining_amount = max(0, self.total_amount - total_deducted - already_cash_card)

        if reset_received:
            self.txt_received_amount.blockSignals(True)
            self.txt_received_amount.setText(f"{self.remaining_amount:,}")
            self.txt_received_amount.blockSignals(False)

        self.recalculate_payment_status()

    def recalculate_payment_status(self):
        received_val = self._parse_int(self.txt_received_amount.text())
        diff = received_val - self.remaining_amount

        if diff > 0:
            self.lbl_status_title.setText("거스름돈 :")
            self.lbl_status_title.setStyleSheet("border: none; background: transparent; color: #0D705C;")
            self.lbl_status_val.setText(f"{diff:,} 원")
            self.lbl_status_val.setStyleSheet("border: none; background: transparent; color: #0D705C;")
        else:
            rem = abs(diff)
            self.lbl_status_title.setText("남은금액 :")
            self.lbl_status_title.setStyleSheet("border: none; background: transparent; color: #E53E3E;")
            self.lbl_status_val.setText(f"{rem:,} 원")
            self.lbl_status_val.setStyleSheet("border: none; background: transparent; color: #E53E3E;")

        earned_point, charged_prepaid = self.calculate_expected_rewards()
        gen_rate, prep_rate = self.get_point_rates()

        if charged_prepaid > 0 and earned_point > 0:
            self.lbl_earn_title.setText("충전 / 적립 예정 :")
            self.lbl_earn_point_val.setText(f"선결제 +{charged_prepaid:,}원 / 포인트 +{earned_point:,}P")
        elif charged_prepaid > 0:
            self.lbl_earn_title.setText("충전 예정 선결제 :")
            self.lbl_earn_point_val.setText(f"+{charged_prepaid:,} 원 (보너스 {int(prep_rate * 100)}% 포함)")
        else:
            self.lbl_earn_title.setText("적립 예정 포인트 :")
            self.lbl_earn_point_val.setText(f"{earned_point:,} P (일반 {int(gen_rate * 100)}%)")

    # -------------------------------------------------------------
    # 장바구니 조작
    # -------------------------------------------------------------
    def add_to_cart(self, service: dict, category_name: str = ""):
        service_id = service["id"]
        cat_name = category_name or self.active_category_name or ""

        existing = next((item for item in self.cart_items if item["id"] == service_id), None)

        if existing:
            existing["qty"] += 1
        else:
            self.cart_items.append({
                "id": service_id,
                "name": service["name"],
                "price": service["price"],
                "category_name": cat_name,
                "qty": 1
            })
        self.update_cart_table()

    def increase_qty(self, service_id: int):
        for item in self.cart_items:
            if item["id"] == service_id:
                item["qty"] += 1
                break
        self.update_cart_table()

    def decrease_qty(self, service_id: int):
        for idx, item in enumerate(self.cart_items):
            if item["id"] == service_id:
                item["qty"] -= 1
                if item["qty"] <= 0:
                    self.cart_items.pop(idx)
                break
        self.update_cart_table()

    def on_cart_cell_changed(self, item: QTableWidgetItem):
        row = item.row()
        col = item.column()

        if row < 0 or row >= len(self.cart_items):
            return

        val_str = item.text().replace(",", "").strip()
        if not val_str.isdigit():
            self.update_cart_table()
            return

        val = int(val_str)
        if col == 1:
            self.cart_items[row]["price"] = val
        elif col == 2:
            if val <= 0:
                self.cart_items.pop(row)
            else:
                self.cart_items[row]["qty"] = val

        self.update_cart_table()

    def update_cart_table(self):
        self.cart_table.blockSignals(True)
        self.cart_table.setRowCount(0)
        
        self.total_amount = sum(item["price"] * item["qty"] for item in self.cart_items)

        for row, item in enumerate(self.cart_items):
            line_total = item["price"] * item["qty"]
            self.cart_table.insertRow(row)

            it_name = QTableWidgetItem(item["name"])
            it_name.setFlags(it_name.flags() & ~Qt.ItemIsEditable)
            it_name.setTextAlignment(Qt.AlignCenter)
            self.cart_table.setItem(row, 0, it_name)

            it_price = QTableWidgetItem(f"{item['price']:,}")
            it_price.setTextAlignment(Qt.AlignCenter)
            self.cart_table.setItem(row, 1, it_price)

            it_qty = QTableWidgetItem(str(item["qty"]))
            it_qty.setTextAlignment(Qt.AlignCenter)
            self.cart_table.setItem(row, 2, it_qty)

            it_total = QTableWidgetItem(f"{line_total:,}")
            it_total.setFlags(it_total.flags() & ~Qt.ItemIsEditable)
            it_total.setTextAlignment(Qt.AlignCenter)
            self.cart_table.setItem(row, 3, it_total)

            ctrl_widget = QuantityControlWidget(item["id"], self.increase_qty, self.decrease_qty)
            self.cart_table.setCellWidget(row, 4, ctrl_widget)

        self.cart_table.blockSignals(False)

        self.lbl_total_amount.setText(f"{self.total_amount:,} 원")
        self.sync_balances_and_status(reset_received=True)

    # -------------------------------------------------------------
    # [결제하기] 단일 진입점 및 모달 결제 처리
    # -------------------------------------------------------------
    def on_click_pay_submit(self):
        if not self.cart_items:
            CustomAlertDialog("결제 오류", "장바구니에 담긴 시술이 없습니다.", self).exec()
            return

        # 이관 고객 및 미동의 고객 첫 결제 시 동의 모달 팝업
        if self.selected_customer and self.selected_customer.get("is_consent", 0) == 0:
            c_name = self.selected_customer.get("name", "")
            c_phone = self.selected_customer.get("phone", "")

            consent_dialog = CustomConsentDialog(c_name, c_phone, self)
            if consent_dialog.exec() == QDialog.Accepted:
                is_mkt = 1 if consent_dialog.chk_marketing.isChecked() else 0
                cust_id = self.selected_customer["id"]

                self.db_manager.update_customer_consent(cust_id, is_consent=1, is_marketing_consent=is_mkt)
                self.selected_customer["is_consent"] = 1
                self.selected_customer["is_marketing_consent"] = is_mkt
            else:
                CustomAlertDialog("결제 중단", "개인정보 수집 및 이용 동의가 완료되지 않아 결제가 취소되었습니다.", self).exec()
                return

        self.sync_balances_and_status(reset_received=False)

        use_prepaid = self._parse_int(self.txt_use_prepaid.text())
        use_point = self._parse_int(self.txt_use_point.text())

        # Case 1: 선결제·포인트 전액 차감으로 카드/현금 받을 금액이 0원인 경우
        if self.remaining_amount <= 0:
            confirm_modal = ZeroAmountConfirmModal(self.total_amount, use_prepaid, use_point, self)
            if confirm_modal.exec() == QDialog.Accepted:
                self._finalize_sale_to_db(change_amt=0)
            return

        # Case 2: 카드/현금으로 결제할 잔액이 남아있는 경우
        received_val = self._parse_int(self.txt_received_amount.text())
        if received_val <= 0:
            CustomAlertDialog("결제 오류", "받을 금액(카드/현금)을 입력해 주세요.", self).exec()
            return

        pay_amt = min(received_val, self.remaining_amount)
        change_amt = max(0, received_val - self.remaining_amount)

        method_modal = PaymentMethodModal(pay_amt, self)
        if method_modal.exec() != QDialog.Accepted or not method_modal.selected_method:
            return

        chosen_method = method_modal.selected_method
        self.payments_history.append({"method": chosen_method, "amount": pay_amt})
        self.remaining_amount -= pay_amt

        history_str = " | ".join([f"{p['method']} {p['amount']:,}원" for p in self.payments_history])
        self.lbl_history_summary.setText(f"결제 내역: {history_str}")
        self.history_scroll.setVisible(True)
        QTimer.singleShot(
            0,
            lambda: self.history_scroll.horizontalScrollBar().setValue(
                self.history_scroll.horizontalScrollBar().maximum()
            ),
        )

        if self.remaining_amount <= 0:
            self._finalize_sale_to_db(change_amt=change_amt)
        else:
            CustomAlertDialog(
                "부분 결제 완료",
                f"[{chosen_method}] {pay_amt:,}원 결제 승인되었습니다.\n남은 결제 금액: {self.remaining_amount:,}원",
                self
            ).exec()
            self.sync_balances_and_status(reset_received=True)

    def _finalize_sale_to_db(self, change_amt: int = 0):
        """최종 결제 수단 합산 후 DB 저장 및 완료 안내"""
        use_prepaid = self._parse_int(self.txt_use_prepaid.text())
        use_point = self._parse_int(self.txt_use_point.text())
        earned_point, charged_prepaid = self.calculate_expected_rewards()

        final_payments = list(self.payments_history)
        if use_prepaid > 0:
            final_payments.append({"method": "선결제", "amount": use_prepaid})
        if use_point > 0:
            final_payments.append({"method": "포인트", "amount": use_point})

        cust_id = self.selected_customer["id"]
        new_memo = self.txt_info_memo.toPlainText().strip()
        designer_id = self.cb_designer.currentData()
        duration_minutes = self.spn_duration.value()
        selected_date = self.date_visit.date().toString("yyyy-MM-dd")
        current_time_str = datetime.now().strftime("%H:%M:%S")
        visited_at_str = f"{selected_date} {current_time_str}"

        save_success = self.db_manager.record_sale(
            customer_id=cust_id,
            user_id=designer_id,
            duration_minutes=duration_minutes,
            total_amount=self.total_amount,
            used_point=use_point,
            earned_point=earned_point,
            visited_at_str=visited_at_str,
            memo=new_memo,
            cart_items=self.cart_items,
            payments_history=final_payments,
            used_prepaid=use_prepaid,
            charged_prepaid=charged_prepaid
        )

        if not save_success:
            CustomAlertDialog("저장 오류", "DB 매출 저장 중 오류가 발생했습니다.", self).exec()
            return

        prev_prepaid = self.selected_customer.get("prepaid_balance", 0)
        prev_point = self.selected_customer.get("point", 0)
        final_prepaid = max(0, prev_prepaid - use_prepaid + charged_prepaid)
        final_point = max(0, prev_point - use_point + earned_point)

        msg = f"결제가 성공적으로 완료되었습니다!\n\n• 총 결제 금액: {self.total_amount:,}원"
        if use_prepaid > 0:
            msg += f"\n• 선결제 차감: -{use_prepaid:,}원"
        if charged_prepaid > 0:
            msg += f"\n• 선결제 충전: +{charged_prepaid:,}원"
        if use_point > 0:
            msg += f"\n• 포인트 사용: -{use_point:,} P"
        if earned_point > 0:
            msg += f"\n• 일반 포인트 적립: +{earned_point:,} P"

        msg += f"\n\n• 최종 선결제 잔액: {final_prepaid:,}원"
        msg += f"\n• 최종 보유 포인트: {final_point:,} P"

        if change_amt > 0:
            msg += f"\n\n※ 거스름돈: {change_amt:,}원"

        CustomAlertDialog("결제 완료", msg, self).exec()

        self.load_customer_list()
        self.clear_customer_selection()