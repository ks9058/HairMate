import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QMenu, QDialog, QLineEdit, QSpinBox,
    QScrollArea, QGridLayout, QApplication
)
from PySide6.QtCore import Qt, Signal, QMimeData, QPoint, QTimer
from PySide6.QtGui import QFont, QWheelEvent, QDrag, QPixmap, QPainter, QPainterPath
from ui.theme import Colors, Styles
from core.db_manager import DBManager


# -------------------------------------------------------------
# 1. 마우스 스크롤 헬퍼 클래스
# -------------------------------------------------------------
class HorizontalScrollArea(QScrollArea):
    """마우스 휠 조작 시 좌/우(가로)로 스크롤되는 커스텀 ScrollArea"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:horizontal {
                height: 6px;
                background: #E5E7EB;
                border-radius: 3px;
            }
            QScrollBar::handle:horizontal {
                background: #B0B0B0;
                border-radius: 3px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #0C604F;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        if delta != 0:
            current_val = self.horizontalScrollBar().value()
            self.horizontalScrollBar().setValue(current_val - delta)
            event.accept()
        else:
            super().wheelEvent(event)


class VerticalScrollArea(QScrollArea):
    """마우스 휠 조작 시 위/아래(세로)로 스크롤되는 커스텀 ScrollArea"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #FFFFFF;
                border-radius: 8px;
            }
            QScrollBar:vertical {
                width: 6px;
                background: #E5E7EB;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #B0B0B0;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #0C604F;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)


# -------------------------------------------------------------
# 2. 커스텀 모달 다이얼로그 (안내 / 입력 / 수정 팝업)
# -------------------------------------------------------------
class CustomAlertDialog(QDialog):
    """시스템 기본 QMessageBox를 대체하는 테마 커스텀 안내/알림 팝업"""

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMinimumWidth(460)

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


class CustomInputDialog(QDialog):
    """카테고리/시술 입력용 맞춤형 모달 팝업"""
    def __init__(self, title: str, label_text: str, default_text: str = "", is_price: bool = False, default_price: int = 1000, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(400, 230)

        self.is_price = is_price

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

        lbl_info = QLabel(label_text, container)
        lbl_info.setFont(QFont("Inter", 13, QFont.Bold))
        lbl_info.setStyleSheet("color: #000000; border: none; background: transparent;")
        lbl_info.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(lbl_info)

        if not is_price:
            self.input_widget = QLineEdit(default_text, container)
            self.input_widget.setPlaceholderText("명칭을 입력하세요")
            self.input_widget.setFixedHeight(40)
            self.input_widget.setStyleSheet(f"""
                QLineEdit {{
                    border: 1.5px solid {Colors.BORDER};
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 13px;
                    color: #000000;
                    background-color: #FAFAFA;
                }}
                QLineEdit:focus {{
                    border: 1.5px solid {Colors.PRIMARY};
                    background-color: #FFFFFF;
                }}
            """)
        else:
            self.input_widget = QSpinBox(container)
            self.input_widget.setRange(0, 10000000)
            self.input_widget.setSingleStep(1000)
            self.input_widget.setValue(default_price)
            self.input_widget.setFixedHeight(40)
            self.input_widget.setStyleSheet(f"""
                QSpinBox {{
                    border: 1.5px solid {Colors.BORDER};
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 13px;
                    color: #000000;
                    background-color: #FAFAFA;
                }}
                QSpinBox:focus {{
                    border: 1.5px solid {Colors.PRIMARY};
                    background-color: #FFFFFF;
                }}
            """)

        c_layout.addWidget(self.input_widget)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.setAlignment(Qt.AlignCenter)

        self.btn_confirm = QPushButton("확인", container)
        self.btn_confirm.setFixedSize(130, 42)
        self.btn_confirm.setCursor(Qt.PointingHandCursor)
        self.btn_confirm.setFont(QFont("Inter", 12, QFont.Bold))
        self.btn_confirm.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: {Colors.PRIMARY};
                border: 2px solid {Colors.PRIMARY};
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: #F2F9F7;
            }}
        """)
        self.btn_confirm.clicked.connect(self.accept)

        self.btn_cancel = QPushButton("취소", container)
        self.btn_cancel.setFixedSize(130, 42)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setFont(QFont("Inter", 12, QFont.Bold))
        self.btn_cancel.setStyleSheet(f"""
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
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_confirm)
        btn_layout.addWidget(self.btn_cancel)
        c_layout.addLayout(btn_layout)

        outer_layout.addWidget(container)

    def get_value(self):
        if not self.is_price:
            return self.input_widget.text().strip()
        return self.input_widget.value()


class CustomServiceEditDialog(QDialog):
    """시술 명칭 및 가격 통합 수정 맞춤형 모달 팝업"""
    def __init__(self, default_name: str, default_price: int, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(400, 270)

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
        c_layout.setSpacing(14)

        lbl_info = QLabel("시술 정보를 수정합니다", container)
        lbl_info.setFont(QFont("Inter", 13, QFont.Bold))
        lbl_info.setStyleSheet("color: #000000; border: none; background: transparent;")
        lbl_info.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(lbl_info)

        self.txt_name = QLineEdit(default_name, container)
        self.txt_name.setFixedHeight(38)
        self.txt_name.setStyleSheet(f"""
            QLineEdit {{
                border: 1.5px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
                color: #000000;
                background-color: #FAFAFA;
            }}
            QLineEdit:focus {{
                border: 1.5px solid {Colors.PRIMARY};
                background-color: #FFFFFF;
            }}
        """)
        c_layout.addWidget(self.txt_name)

        self.spn_price = QSpinBox(container)
        self.spn_price.setRange(0, 10000000)
        self.spn_price.setSingleStep(1000)
        self.spn_price.setValue(default_price)
        self.spn_price.setFixedHeight(38)
        self.spn_price.setStyleSheet(f"""
            QSpinBox {{
                border: 1.5px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
                color: #000000;
                background-color: #FAFAFA;
            }}
            QSpinBox:focus {{
                border: 1.5px solid {Colors.PRIMARY};
                background-color: #FFFFFF;
            }}
        """)
        c_layout.addWidget(self.spn_price)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.setAlignment(Qt.AlignCenter)

        self.btn_confirm = QPushButton("확인", container)
        self.btn_confirm.setFixedSize(130, 42)
        self.btn_confirm.setCursor(Qt.PointingHandCursor)
        self.btn_confirm.setFont(QFont("Inter", 12, QFont.Bold))
        self.btn_confirm.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: {Colors.PRIMARY};
                border: 2px solid {Colors.PRIMARY};
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: #F2F9F7;
            }}
        """)
        self.btn_confirm.clicked.connect(self.accept)

        self.btn_cancel = QPushButton("취소", container)
        self.btn_cancel.setFixedSize(130, 42)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setFont(QFont("Inter", 12, QFont.Bold))
        self.btn_cancel.setStyleSheet(f"""
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
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_confirm)
        btn_layout.addWidget(self.btn_cancel)
        c_layout.addLayout(btn_layout)

        outer_layout.addWidget(container)

    def get_data(self):
        return self.txt_name.text().strip(), self.spn_price.value()


# -------------------------------------------------------------
# 3. 드래그 앤 드롭 지원 카드 위젯 구성
# -------------------------------------------------------------
class BaseCard(QFrame):
    """카테고리/시술 카드의 공통 부모 위젯"""
    updated = Signal()
    deleted_toggled = Signal()

    def __init__(self, card_type: str, index: int, parent=None):
        super().__init__(parent)
        self.card_type = card_type
        self.index = index
        self.is_edited = False
        self.is_deleted = False
        self.is_selected = False

        self.drag_start_pos = QPoint()

        self.setCursor(Qt.PointingHandCursor)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.lbl_asterisk = QLabel("*", self)
        self.lbl_asterisk.setStyleSheet(f"color: {Colors.DANGER}; font-weight: bold; font-size: 14px; background: transparent; border: none;")
        self.lbl_asterisk.setAlignment(Qt.AlignCenter)
        self.lbl_asterisk.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.lbl_asterisk.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'lbl_asterisk'):
            self.lbl_asterisk.setGeometry(self.width() - 16, 2, 12, 14)
            self.lbl_asterisk.raise_()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def create_drag_pixmap(self) -> QPixmap:
        """High DPI 배율 보정 및 선명한 고화질 드래그 픽스맵 생성"""
        class_name = self.metaObject().className()
        
        self.setStyleSheet(f"""
            {class_name} {{
                background-color: #FFFFFF;
                border: 2px solid {Colors.PRIMARY};
                border-radius: 8px;
            }}
            QLabel {{
                color: #000000;
                background: transparent;
                border: none;
            }}
        """)
        self.repaint()
        QApplication.processEvents()

        raw_pixmap = self.grab()

        self.update_style()

        dpr = self.devicePixelRatio()

        rounded_pixmap = QPixmap(raw_pixmap.size())
        rounded_pixmap.setDevicePixelRatio(dpr)
        rounded_pixmap.fill(Qt.transparent)

        painter = QPainter(rounded_pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        w = self.width()
        h = self.height()
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, 8, 8)
        
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, raw_pixmap)
        painter.end()

        return rounded_pixmap

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if (event.pos() - self.drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"{self.card_type}:{self.index}")
        drag.setMimeData(mime_data)

        pixmap = self.create_drag_pixmap()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())

        drag.exec_(Qt.MoveAction)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER};
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 20px;
                font-size: 12px;
                color: {Colors.TEXT_MAIN};
                font-family: 'Inter', 'Malgun Gothic', sans-serif;
            }}
            QMenu::item:selected {{
                background-color: {Colors.BACKGROUND};
                color: {Colors.TEXT_MAIN};
            }}
        """)

        action_edit = menu.addAction("수정하기")
        action_delete = menu.addAction("삭제 취소" if self.is_deleted else "삭제하기")

        selected_action = menu.exec_(self.mapToGlobal(pos))

        if selected_action == action_edit:
            self.on_edit()
        elif selected_action == action_delete:
            self.on_toggle_delete()

    def on_edit(self):
        pass

    def on_toggle_delete(self):
        self.is_deleted = not self.is_deleted
        self.update_style()
        self.deleted_toggled.emit()

    def update_style(self):
        pass


class CategoryCard(BaseCard):
    """상단 카테고리 카드 ('선결제' 수정/삭제 보호 적용)"""
    selected = Signal(object)

    def __init__(self, category_name: str, index: int, is_edited: bool = False, is_deleted: bool = False, is_system: bool = False, parent=None):
        super().__init__("category", index, parent)
        self.name = category_name
        self.is_edited = is_edited
        self.is_deleted = is_deleted
        self.is_system = is_system or (category_name == "선결제")
        self.setFixedSize(100, 70)
        self.setup_ui()
        self.update_style()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setAlignment(Qt.AlignCenter)

        self.lbl_name = QLabel(self.name, self)
        self.lbl_name.setAlignment(Qt.AlignCenter)
        self.lbl_name.setFont(QFont("Inter", 12, QFont.Bold))
        self.lbl_name.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.lbl_name)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selected.emit(self)
        super().mousePressEvent(event)

    def on_edit(self):
        if self.is_system or self.name == "선결제":
            CustomAlertDialog("수정 불가", "'선결제' 카테고리 명칭은 수정할 수 없습니다.", self).exec()
            return

        dlg = CustomInputDialog("카테고리 수정", "카테고리 명칭을 수정하세요", default_text=self.name, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            new_name = dlg.get_value()
            if new_name == "선결제":
                CustomAlertDialog("중복 금지", "'선결제' 이름으로는 변경할 수 없습니다.", self).exec()
                return
            if new_name and new_name != self.name:
                self.name = new_name
                self.lbl_name.setText(self.name)
                self.is_edited = True
                self.update_style()
                self.updated.emit()

    def on_toggle_delete(self):
        if self.is_system or self.name == "선결제":
            CustomAlertDialog("삭제 불가", "'선결제' 카테고리는 시스템 기본 항목이므로 삭제할 수 없습니다.", self).exec()
            return
        super().on_toggle_delete()

    def update_style(self):
        self.lbl_asterisk.setVisible(self.is_edited or self.is_deleted)

        if self.is_deleted:
            bg_color = Colors.GRAY
            text_color = Colors.TEXT_MUTED
        elif self.is_selected:
            bg_color = Colors.PRIMARY
            text_color = Colors.WHITE
        else:
            bg_color = Colors.PRIMARY_HOVER
            text_color = Colors.WHITE

        self.setStyleSheet(f"""
            CategoryCard {{
                background-color: {bg_color};
                border-radius: 8px;
                border: none;
            }}
            QLabel {{
                color: {text_color};
                background: transparent;
                border: none;
            }}
        """)


class CategoryBadgeTab(BaseCard):
    """하단 카테고리 탭 뱃지 ('선결제' 수정/삭제 보호 적용)"""
    selected = Signal(object)

    def __init__(self, category_name: str, index: int, is_edited: bool = False, is_deleted: bool = False, is_system: bool = False, parent=None):
        super().__init__("category", index, parent)
        self.name = category_name
        self.is_edited = is_edited
        self.is_deleted = is_deleted
        self.is_system = is_system or (category_name == "선결제")
        self.setFixedSize(80, 48)
        self.setup_ui()
        self.update_style()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setAlignment(Qt.AlignCenter)

        self.lbl_name = QLabel(self.name, self)
        self.lbl_name.setAlignment(Qt.AlignCenter)
        self.lbl_name.setFont(QFont("Inter", 11, QFont.Bold))
        self.lbl_name.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.lbl_name)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selected.emit(self)
        super().mousePressEvent(event)

    def on_edit(self):
        if self.is_system or self.name == "선결제":
            CustomAlertDialog("수정 불가", "'선결제' 카테고리 명칭은 수정할 수 없습니다.", self).exec()
            return

        dlg = CustomInputDialog("카테고리 수정", "카테고리 명칭을 수정하세요", default_text=self.name, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            new_name = dlg.get_value()
            if new_name == "선결제":
                CustomAlertDialog("중복 금지", "'선결제' 이름으로는 변경할 수 없습니다.", self).exec()
                return
            if new_name and new_name != self.name:
                self.name = new_name
                self.lbl_name.setText(self.name)
                self.is_edited = True
                self.update_style()
                self.updated.emit()

    def on_toggle_delete(self):
        if self.is_system or self.name == "선결제":
            CustomAlertDialog("삭제 불가", "'선결제' 카테고리는 시스템 기본 항목이므로 삭제할 수 없습니다.", self).exec()
            return
        super().on_toggle_delete()

    def update_style(self):
        self.lbl_asterisk.setVisible(self.is_edited or self.is_deleted)

        if self.is_deleted:
            bg_color = Colors.GRAY
            text_color = Colors.TEXT_MUTED
        elif self.is_selected:
            bg_color = Colors.PRIMARY
            text_color = Colors.WHITE
        else:
            bg_color = Colors.SUB
            text_color = Colors.WHITE

        self.setStyleSheet(f"""
            CategoryBadgeTab {{
                background-color: {bg_color};
                border-radius: 6px;
                border: none;
            }}
            QLabel {{
                color: {text_color};
                background: transparent;
                border: none;
            }}
        """)


class ServiceCard(BaseCard):
    """시술 항목 카드"""

    def __init__(self, service_name: str, price: int, index: int, is_edited: bool = False, is_deleted: bool = False, parent=None):
        super().__init__("service", index, parent)
        self.name = service_name
        self.price = price
        self.is_edited = is_edited
        self.is_deleted = is_deleted
        self.setFixedSize(120, 80)
        self.setup_ui()
        self.update_style()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(4)

        self.lbl_name = QLabel(self.name, self)
        self.lbl_name.setAlignment(Qt.AlignCenter)
        self.lbl_name.setFont(QFont("Inter", 11, QFont.Bold))
        self.lbl_name.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.lbl_name)

        self.lbl_price = QLabel(f"{self.price:,}", self)
        self.lbl_price.setAlignment(Qt.AlignCenter)
        self.lbl_price.setFont(QFont("Inter", 10))
        self.lbl_price.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.lbl_price)

    def on_edit(self):
        dlg = CustomServiceEditDialog(self.name, self.price, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            new_name, new_price = dlg.get_data()
            if new_name and (new_name != self.name or new_price != self.price):
                self.name = new_name
                self.price = new_price
                self.lbl_name.setText(self.name)
                self.lbl_price.setText(f"{self.price:,}")
                self.is_edited = True
                self.update_style()
                self.updated.emit()

    def update_style(self):
        self.lbl_asterisk.setVisible(self.is_edited or self.is_deleted)

        if self.is_deleted:
            bg_color = Colors.GRAY
            text_color = Colors.TEXT_MUTED
        else:
            bg_color = Colors.PRIMARY
            text_color = Colors.WHITE

        self.setStyleSheet(f"""
            ServiceCard {{
                background-color: {bg_color};
                border-radius: 8px;
                border: none;
            }}
            QLabel {{
                color: {text_color};
                background: transparent;
                border: none;
            }}
        """)


class AddCardButton(QFrame):
    """'+' 카테고리/시술 추가 전용 카드 버튼"""
    clicked = Signal()

    def __init__(self, title_text: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(100 if "카테고리" in title_text else 120, 70 if "카테고리" in title_text else 80)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            AddCardButton {{
                background-color: {Colors.PRIMARY};
                border-radius: 8px;
                border: none;
            }}
            AddCardButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(2)

        lbl_title = QLabel(title_text, self)
        lbl_title.setFont(QFont("Inter", 10, QFont.Bold))
        lbl_title.setStyleSheet("color: white; background: transparent; border: none;")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        lbl_plus = QLabel("+", self)
        lbl_plus.setFont(QFont("Inter", 18, QFont.Bold))
        lbl_plus.setStyleSheet("color: white; background: transparent; border: none;")
        lbl_plus.setAlignment(Qt.AlignCenter)
        lbl_plus.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_plus)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


# -------------------------------------------------------------
# 4. 드롭 수신 컨테이너 위젯
# -------------------------------------------------------------
class DropAreaWidget(QFrame):
    """드롭 이벤트를 처리하는 커스텀 패널 (QFrame 상속으로 QSS background-color 정상 렌더링)"""
    item_dropped = Signal(str, int, int)

    def __init__(self, target_type: str, parent=None):
        super().__init__(parent)
        self.target_type = target_type
        self.setAcceptDrops(True)
        self.setAttribute(Qt.WA_StyledBackground, True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith(self.target_type):
                event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            text = event.mimeData().text()
            parts = text.split(":")
            if len(parts) == 2 and parts[0] == self.target_type:
                src_idx = int(parts[1])
                target_idx = self.calculate_target_index(event.pos())
                self.item_dropped.emit(self.target_type, src_idx, target_idx)
                event.acceptProposedAction()

    def calculate_target_index(self, drop_pos: QPoint) -> int:
        layout = self.layout()
        if not layout:
            return 0

        cards = []
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if isinstance(w, BaseCard):
                    cards.append(w)

        if not cards:
            return 0

        min_dist = float('inf')
        closest_idx = 0

        for card in cards:
            card_center = card.geometry().center()
            dist = (drop_pos - card_center).manhattanLength()
            if dist < min_dist:
                min_dist = dist
                closest_idx = card.index

        return closest_idx


# -------------------------------------------------------------
# 5. 설정 > 시술 카테고리 관리 메인 뷰
# -------------------------------------------------------------
class SettingsCategoryView(QWidget):
    """설정 > 시술 카테고리 관리 뷰"""

    def __init__(self):
        super().__init__()
        self.db_manager = DBManager()
        
        # DB에서 기존 저장 데이터 로드
        self.categories_data, self.services_map = self.db_manager.fetch_active_categories_and_services()
        self.current_category = self.categories_data[0]["name"] if self.categories_data else None
        self.original_state = self._get_current_state_snapshot()

        self.category_widgets = []
        self.badge_widgets = []
        self.service_widgets = []

        self.setup_ui()

    def _get_current_state_snapshot(self):
        """현재 카테고리/시술 데이터의 상태 스냅샷 반환 (순서, 이름, 가격, 수정/삭제 플래그 포함)"""
        cat_snapshot = [
            (
                c.get("id"),
                c.get("name"),
                bool(c.get("edited", False)),
                bool(c.get("deleted", False)),
            )
            for c in self.categories_data
        ]
        svc_snapshot = {}
        for c in self.categories_data:
            cat_name = c.get("name")
            svcs = self.services_map.get(cat_name, [])
            svc_snapshot[cat_name] = [
                (
                    s.get("id"),
                    s.get("name"),
                    s.get("price"),
                    bool(s.get("edited", False)),
                    bool(s.get("deleted", False)),
                )
                for s in svcs
            ]
        return (cat_snapshot, svc_snapshot)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(15)

        # 1. 상단 가이드 영역
        top_section = QWidget(self)
        top_layout = QHBoxLayout(top_section)
        top_layout.setContentsMargins(0, 5, 0, 5)

        lbl_title = QLabel("설명", top_section)
        lbl_title.setFont(QFont("Inter", 13, QFont.Bold))
        lbl_title.setFixedWidth(140)
        lbl_title.setAlignment(Qt.AlignCenter)
        top_layout.addWidget(lbl_title)

        top_guides_container = QWidget(top_section)
        top_guides_layout = QHBoxLayout(top_guides_container)
        top_guides_layout.setContentsMargins(0, 0, 0, 0)
        top_guides_layout.setSpacing(8)

        guide1_box = QFrame(top_guides_container)
        guide1_box.setStyleSheet(f"background-color: {Colors.WHITE}; border: 1.5px solid {Colors.PRIMARY}; border-radius: 8px;")
        g1_layout = QHBoxLayout(guide1_box)
        g1_layout.setContentsMargins(10, 8, 10, 8)
        g1_layout.setAlignment(Qt.AlignCenter)

        lbl_g1 = QLabel("1. 메뉴 우클릭시 수정 및 삭제가 가능합니다.", guide1_box)
        lbl_g1.setFont(QFont("Inter", 10, QFont.Bold))
        lbl_g1.setStyleSheet("border: none; color: #000000; background: transparent;")
        lbl_g1.setAlignment(Qt.AlignCenter)
        g1_layout.addWidget(lbl_g1)

        top_guides_layout.addWidget(guide1_box, 1)

        guide2_box = QFrame(top_guides_container)
        guide2_box.setStyleSheet(f"background-color: {Colors.WHITE}; border: 1.5px solid {Colors.PRIMARY}; border-radius: 8px;")
        g2_layout = QHBoxLayout(guide2_box)
        g2_layout.setContentsMargins(10, 8, 10, 8)
        g2_layout.setAlignment(Qt.AlignCenter)

        lbl_g2 = QLabel("2. 메뉴를 드래그해서 순서를 바꿀 수 있습니다.", guide2_box)
        lbl_g2.setFont(QFont("Inter", 10, QFont.Bold))
        lbl_g2.setStyleSheet("border: none; color: #000000; background: transparent;")
        lbl_g2.setAlignment(Qt.AlignCenter)
        g2_layout.addWidget(lbl_g2)

        top_guides_layout.addWidget(guide2_box, 1)

        guide3_box = QFrame(top_guides_container)
        guide3_box.setStyleSheet(f"background-color: {Colors.WHITE}; border: 1.5px solid {Colors.PRIMARY}; border-radius: 8px;")
        g3_layout = QHBoxLayout(guide3_box)
        g3_layout.setContentsMargins(10, 8, 10, 8)
        g3_layout.setAlignment(Qt.AlignCenter)

        lbl_g3 = QLabel("3. 변경사항 모두 저장 버튼을 클릭해야 최종 저장됩니다.", guide3_box)
        lbl_g3.setFont(QFont("Inter", 10, QFont.Bold))
        lbl_g3.setStyleSheet("border: none; color: #000000; background: transparent;")
        lbl_g3.setAlignment(Qt.AlignCenter)
        g3_layout.addWidget(lbl_g3)

        top_guides_layout.addWidget(guide3_box, 1)

        top_layout.addWidget(top_guides_container, 1)
        main_layout.addWidget(top_section)

        line1 = QFrame(self)
        line1.setFrameShape(QFrame.HLine)
        line1.setStyleSheet(f"color: {Colors.PRIMARY}; background-color: {Colors.PRIMARY};")
        main_layout.addWidget(line1)

        # 2. 카테고리 영역
        cat_section = QWidget(self)
        cat_layout = QHBoxLayout(cat_section)
        cat_layout.setContentsMargins(0, 5, 0, 5)

        lbl_cat_header = QLabel("카테고리", cat_section)
        lbl_cat_header.setFont(QFont("Inter", 13, QFont.Bold))
        lbl_cat_header.setFixedWidth(140)
        lbl_cat_header.setAlignment(Qt.AlignCenter)
        cat_layout.addWidget(lbl_cat_header)

        self.cat_scroll_area = HorizontalScrollArea(cat_section)
        self.cat_scroll_area.setFixedHeight(95)

        cat_container = DropAreaWidget("category")
        cat_container.setStyleSheet("background-color: #E5E7EB; border-radius: 8px;")
        cat_container.item_dropped.connect(self.on_item_reordered)

        self.cat_cards_layout = QHBoxLayout(cat_container)
        self.cat_cards_layout.setContentsMargins(15, 12, 15, 12)
        self.cat_cards_layout.setAlignment(Qt.AlignLeft)
        self.cat_cards_layout.setSpacing(12)

        self.cat_scroll_area.setWidget(cat_container)
        cat_layout.addWidget(self.cat_scroll_area, 1)
        main_layout.addWidget(cat_section)

        line2 = QFrame(self)
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet(f"color: {Colors.PRIMARY}; background-color: {Colors.PRIMARY};")
        main_layout.addWidget(line2)

        # 3. 시술 영역
        svc_section = QWidget(self)
        svc_layout = QHBoxLayout(svc_section)
        svc_layout.setContentsMargins(0, 5, 0, 5)

        lbl_svc_header = QLabel("시술", svc_section)
        lbl_svc_header.setFont(QFont("Inter", 13, QFont.Bold))
        lbl_svc_header.setFixedWidth(140)
        lbl_svc_header.setAlignment(Qt.AlignCenter)
        svc_layout.addWidget(lbl_svc_header)

        svc_outer_container = QFrame(svc_section)
        svc_outer_container.setStyleSheet("background-color: #E5E7EB; border-radius: 8px;")
        svc_outer_layout = QVBoxLayout(svc_outer_container)
        svc_outer_layout.setContentsMargins(15, 15, 15, 15)
        svc_outer_layout.setSpacing(10)

        # 3.1 카테고리 탭 뱃지 영역
        self.badge_scroll_area = HorizontalScrollArea(svc_outer_container)
        self.badge_scroll_area.setFixedHeight(58)

        badge_container = DropAreaWidget("category")
        badge_container.setStyleSheet("background-color: #E5E7EB; border-radius: 8px;")
        badge_container.item_dropped.connect(self.on_item_reordered)

        self.cat_badges_layout = QHBoxLayout(badge_container)
        self.cat_badges_layout.setContentsMargins(8, 5, 8, 5)
        self.cat_badges_layout.setAlignment(Qt.AlignLeft)
        self.cat_badges_layout.setSpacing(8)

        self.badge_scroll_area.setWidget(badge_container)
        svc_outer_layout.addWidget(self.badge_scroll_area)

        # 3.2 흰색 시술 카드 영역
        self.svc_scroll_area = VerticalScrollArea(svc_outer_container)
        
        self.svc_inner_panel = DropAreaWidget("service")
        self.svc_inner_panel.setStyleSheet("background-color: #FFFFFF; border-radius: 8px;")
        self.svc_inner_panel.item_dropped.connect(self.on_item_reordered)

        self.svc_cards_layout = QGridLayout(self.svc_inner_panel)
        self.svc_cards_layout.setContentsMargins(15, 15, 15, 15)
        self.svc_cards_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.svc_cards_layout.setHorizontalSpacing(12)
        self.svc_cards_layout.setVerticalSpacing(12)

        self.svc_scroll_area.setWidget(self.svc_inner_panel)
        svc_outer_layout.addWidget(self.svc_scroll_area, 1)

        svc_layout.addWidget(svc_outer_container, 1)
        main_layout.addWidget(svc_section, 1)

        line3 = QFrame(self)
        line3.setFrameShape(QFrame.HLine)
        line3.setStyleSheet(f"color: {Colors.PRIMARY}; background-color: {Colors.PRIMARY};")
        main_layout.addWidget(line3)

        # 4. 하단 저장 버튼
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignCenter)

        self.btn_save_all = QPushButton("", self)
        self.btn_save_all.setFixedSize(320, 45)
        self.btn_save_all.setCursor(Qt.PointingHandCursor)
        self.btn_save_all.setStyleSheet(Styles.PRIMARY_BUTTON)

        btn_save_all_layout = QHBoxLayout(self.btn_save_all)
        btn_save_all_layout.setContentsMargins(10, 0, 10, 0)
        btn_save_all_layout.setAlignment(Qt.AlignCenter)

        self.lbl_btn_save_all_text = QLabel("변경 사항 모두 저장", self.btn_save_all)
        self.lbl_btn_save_all_text.setFont(QFont("Inter", 13, QFont.Bold))
        self.lbl_btn_save_all_text.setAlignment(Qt.AlignCenter)
        self.lbl_btn_save_all_text.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.lbl_btn_save_all_text.setStyleSheet("color: #FFFFFF; background: transparent; border: none;")
        btn_save_all_layout.addWidget(self.lbl_btn_save_all_text)

        self.btn_save_all.clicked.connect(self.on_save_all)

        btn_layout.addWidget(self.btn_save_all)
        main_layout.addLayout(btn_layout)

        self.render_categories()
        self.render_services()

    def set_save_button_dirty(self, is_dirty: bool):
        """변경 사항 존재 여부에 따라 저장 버튼 텍스트에 빨간색 * 표시"""
        if is_dirty:
            self.lbl_btn_save_all_text.setText(
                "변경 사항 모두 저장 <span style='color:#FF4D4F; font-weight:bold;'>*</span>"
            )
        else:
            self.lbl_btn_save_all_text.setText("변경 사항 모두 저장")

    def check_changes_modified(self):
        """현재 카테고리/시술 목록 상태가 초기 로드/저장 상태와 다른지 확인"""
        if self.original_state is None:
            self.set_save_button_dirty(False)
            return

        self.set_save_button_dirty(self._get_current_state_snapshot() != self.original_state)

    def showEvent(self, event):
        """화면이 활성화되거나 처음 렌더링될 때 정확한 너비를 계산하여 가로로 재배치"""
        super().showEvent(event)
        QTimer.singleShot(0, self.render_services)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.render_services()

    def on_item_reordered(self, target_type: str, src_idx: int, target_idx: int):
        if src_idx == target_idx or src_idx < 0 or target_idx < 0:
            return

        if target_type == "category":
            if src_idx < len(self.categories_data) and target_idx < len(self.categories_data):
                item = self.categories_data.pop(src_idx)
                self.categories_data.insert(target_idx, item)
                self.render_categories()
                self.check_changes_modified()
        elif target_type == "service":
            services = self.services_map.get(self.current_category, [])
            if src_idx < len(services) and target_idx < len(services):
                item = services.pop(src_idx)
                services.insert(target_idx, item)
                self.render_services()
                self.check_changes_modified()

    def select_category_by_name(self, cat_name: str):
        self.current_category = cat_name
        for card in self.category_widgets:
            card.is_selected = (card.name == cat_name)
            card.update_style()

        for badge in self.badge_widgets:
            badge.is_selected = (badge.name == cat_name)
            badge.update_style()

        self.render_services()

    def render_categories(self):
        while self.cat_cards_layout.count():
            item = self.cat_cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        while self.cat_badges_layout.count():
            item = self.cat_badges_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.category_widgets.clear()
        self.badge_widgets.clear()

        btn_add_cat = AddCardButton("카테고리 추가", self)
        btn_add_cat.clicked.connect(self.on_add_category)
        self.cat_cards_layout.addWidget(btn_add_cat)

        for idx, cat_info in enumerate(self.categories_data):
            cat_name = cat_info["name"]
            is_ed = cat_info.get("edited", False)
            is_del = cat_info.get("deleted", False)
            is_sys = cat_info.get("is_system", False) or (cat_name == "선결제")

            card = CategoryCard(cat_name, index=idx, is_edited=is_ed, is_deleted=is_del, is_system=is_sys, parent=self)
            card.is_selected = (cat_name == self.current_category)
            card.update_style()

            card.selected.connect(self.on_select_category)
            card.updated.connect(lambda c=cat_info, cd=card: self.sync_cat_data(c, cd))
            card.deleted_toggled.connect(lambda c=cat_info, cd=card: self.sync_cat_data(c, cd))
            
            self.cat_cards_layout.addWidget(card)
            self.category_widgets.append(card)

            badge = CategoryBadgeTab(cat_name, index=idx, is_edited=is_ed, is_deleted=is_del, is_system=is_sys, parent=self)
            badge.is_selected = (cat_name == self.current_category)
            badge.update_style()

            badge.selected.connect(self.on_select_category_by_badge)
            badge.updated.connect(lambda c=cat_info, cd=badge: self.sync_cat_data(c, cd))
            badge.deleted_toggled.connect(lambda c=cat_info, cd=badge: self.sync_cat_data(c, cd))

            self.cat_badges_layout.addWidget(badge)
            self.badge_widgets.append(badge)

    def sync_cat_data(self, cat_info, card_widget):
        cat_info["name"] = card_widget.name
        cat_info["edited"] = card_widget.is_edited
        cat_info["deleted"] = card_widget.is_deleted
        
        valid_names = [c["name"] for c in self.categories_data]
        if self.current_category not in valid_names:
            self.current_category = valid_names[0] if valid_names else None
            
        self.render_categories()
        self.render_services()
        self.check_changes_modified()

    def get_calculated_columns(self) -> int:
        viewport_w = self.svc_scroll_area.viewport().width()
        
        # 레이아웃 미계산으로 인한 초기 뷰포트 측정 오류 시 기본 5열 반환
        if viewport_w < 300:
            return 5

        card_w = 120
        spacing = 12
        margins = 30
        avail_w = viewport_w - margins

        cols = max(1, (avail_w + spacing) // (card_w + spacing))
        return cols

    def render_services(self):
        while self.svc_cards_layout.count():
            item = self.svc_cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.service_widgets.clear()

        cols = self.get_calculated_columns()

        btn_add_svc = AddCardButton("시술 추가", self)
        btn_add_svc.clicked.connect(self.on_add_service)
        self.svc_cards_layout.addWidget(btn_add_svc, 0, 0)

        if not self.current_category:
            return

        services = self.services_map.get(self.current_category, [])
        for idx, svc_data in enumerate(services):
            grid_pos = idx + 1
            row = grid_pos // cols
            col = grid_pos % cols

            card = ServiceCard(
                service_name=svc_data["name"], 
                price=svc_data["price"], 
                index=idx,
                is_edited=svc_data.get("edited", False), 
                is_deleted=svc_data.get("deleted", False), 
                parent=self
            )
            card.updated.connect(lambda s=svc_data, cd=card: self.sync_svc_data(s, cd))
            card.deleted_toggled.connect(lambda s=svc_data, cd=card: self.sync_svc_data(s, cd))

            self.svc_cards_layout.addWidget(card, row, col)
            self.service_widgets.append(card)

    def sync_svc_data(self, svc_data, card_widget):
        svc_data["name"] = card_widget.name
        svc_data["price"] = card_widget.price
        svc_data["edited"] = card_widget.is_edited
        svc_data["deleted"] = card_widget.is_deleted
        self.check_changes_modified()

    def on_select_category(self, target_card: CategoryCard):
        self.select_category_by_name(target_card.name)

    def on_select_category_by_badge(self, target_badge: CategoryBadgeTab):
        self.select_category_by_name(target_badge.name)

    def on_add_category(self):
        dlg = CustomInputDialog("카테고리 추가", "새 카테고리 명칭을 입력하세요", parent=self)
        if dlg.exec_() == QDialog.Accepted:
            cat_name = dlg.get_value()
            if cat_name == "선결제":
                CustomAlertDialog("중복 오류", "'선결제' 카테고리는 시스템 기본 항목으로 이미 존재합니다.", self).exec()
                return
            if cat_name:
                existing_names = [c["name"] for c in self.categories_data]
                if cat_name not in existing_names:
                    self.categories_data.append({"name": cat_name, "edited": True, "deleted": False})
                    self.services_map[cat_name] = []
                    self.select_category_by_name(cat_name)
                    self.render_categories()
                    self.check_changes_modified()

    def on_add_service(self):
        if not self.current_category:
            CustomAlertDialog("경고", "시술을 추가할 카테고리를 먼저 선택하거나 생성해 주세요.", self).exec()
            return

        dlg_name = CustomInputDialog("시술 추가", f"[{self.current_category}] 새 시술 명칭을 입력하세요", parent=self)
        if dlg_name.exec_() == QDialog.Accepted:
            name = dlg_name.get_value()
            if not name:
                return

            dlg_price = CustomInputDialog("시술 가격 입력", "시술 가격(원)을 입력하세요", is_price=True, default_price=1000, parent=self)
            if dlg_price.exec_() == QDialog.Accepted:
                price = dlg_price.get_value()
                new_service = {"name": name, "price": price, "edited": True, "deleted": False}
                if self.current_category not in self.services_map:
                    self.services_map[self.current_category] = []
                
                self.services_map[self.current_category].append(new_service)
                self.render_services()
                self.check_changes_modified()

    def on_save_all(self):
        """'변경 사항 모두 저장' 버튼 클릭 시 SQLite 트랜잭션 일괄 저장 실행"""
        success, message = self.db_manager.save_all_changes(self.categories_data, self.services_map)

        if success:
            CustomAlertDialog("저장 완료", message, self).exec()
            self.categories_data, self.services_map = self.db_manager.fetch_active_categories_and_services()
            if self.categories_data:
                valid_names = [c["name"] for c in self.categories_data]
                if self.current_category not in valid_names:
                    self.current_category = valid_names[0]
            else:
                self.current_category = None

            self.original_state = self._get_current_state_snapshot()
            self.set_save_button_dirty(False)

            self.render_categories()
            self.render_services()
        else:
            CustomAlertDialog("저장 실패", message, self).exec()