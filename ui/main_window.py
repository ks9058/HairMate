from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QPushButton, QLabel, QStackedWidget, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
from ui.theme import Colors, Styles, get_icon, load_fonts
from ui.settings_google_view import SettingsGoogleView
from ui.settings_category_view import SettingsCategoryView
from ui.settings_point_view import SettingsPointView  
from ui.settings_designer_view import SettingsDesignerView


class SidebarButton(QPushButton):
    """호버/선택 시 우측 라운드 흰색 바탕 및 검은색 SVG 아이콘으로 전환되는 커스텀 버튼"""
    def __init__(self, text, icon_name=None, is_sub=False, parent=None):
        super().__init__(text, parent)
        self.icon_name = icon_name
        self.black_icon_name = icon_name.replace(".svg", "_black.svg") if icon_name else None
        self.is_sub = is_sub

        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(Styles.SIDEBAR_SUB_BUTTON if is_sub else Styles.SIDEBAR_BUTTON)

        if self.icon_name:
            self.setIcon(get_icon(self.icon_name))
            icon_size = 16 if is_sub else 22
            self.setIconSize(QSize(icon_size, icon_size))

    def enterEvent(self, event):
        if self.black_icon_name:
            self.setIcon(get_icon(self.black_icon_name))
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.isChecked() and self.icon_name:
            self.setIcon(get_icon(self.icon_name))
        super().leaveEvent(event)

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        if self.black_icon_name:
            if checked:
                self.setIcon(get_icon(self.black_icon_name))
            elif self.icon_name:
                self.setIcon(get_icon(self.icon_name))


class HoverMenuContainer(QWidget):
    """설정 버튼과 서브메뉴를 감싸 호버 시 서브메뉴가 동적으로 노출되는 컨테이너"""
    def __init__(self, main_btn, sub_container, parent=None):
        super().__init__(parent)
        self.main_btn = main_btn
        self.sub_container = sub_container

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self.main_btn)
        layout.addWidget(self.sub_container)

        self.sub_container.setVisible(False)

    def enterEvent(self, event):
        self.sub_container.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.sub_container.setVisible(False)
        super().leaveEvent(event)


class MainWindow(QMainWindow):
    """HairMate 메인 대시보드 윈도우"""
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("HairMate - 미용실 관리 시스템")
        self.setMinimumSize(960, 600)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # -------------------------------------------------------------
        # 1. 좌측 사이드바 패널
        # -------------------------------------------------------------
        sidebar = QFrame(self)
        sidebar.setFixedWidth(200)
        sidebar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        sidebar.setStyleSheet(f"background-color: {Colors.PRIMARY};")

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 15)
        sidebar_layout.setSpacing(4)

        # 1.1 로고 헤더
        kaushan_font_family = load_fonts()
        
        logo_container = QFrame(sidebar)
        logo_container.setFixedHeight(50)
        logo_container.setStyleSheet(f"border-bottom: 1.5px solid {Colors.WHITE}; background-color: transparent;")
        
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(15, 0, 15, 0)

        logo_label = QLabel("HairMate", logo_container)
        logo_font = QFont(kaushan_font_family, 24)
        logo_label.setFont(logo_font)
        logo_label.setStyleSheet(f"color: {Colors.WHITE}; border: none;")
        logo_layout.addWidget(logo_label)

        sidebar_layout.addWidget(logo_container)

        # 1.2 메인 사이드바 버튼 목록
        self.btn_customer = SidebarButton("  고객관리", "customer.svg")
        self.btn_sales_reg = SidebarButton("  매출등록", "sales_registration.svg")
        self.btn_sales_analysis = SidebarButton("  매출분석", "sales_statistics.svg")
        self.btn_setting = SidebarButton("  설정", "setting.svg")

        self.menu_buttons = [self.btn_customer, self.btn_sales_reg, self.btn_sales_analysis, self.btn_setting]

        sidebar_layout.addWidget(self.btn_customer)
        sidebar_layout.addWidget(self.btn_sales_reg)
        sidebar_layout.addWidget(self.btn_sales_analysis)

        # 1.3 설정 하위 서브메뉴 Container (디자이너 관리 버튼 추가 반영)
        self.sub_menu_container = QWidget(sidebar)
        sub_layout = QVBoxLayout(self.sub_menu_container)
        sub_layout.setContentsMargins(0, 0, 0, 0)
        sub_layout.setSpacing(2)

        self.btn_sub_google = SidebarButton("구글 계정 인증", is_sub=True)
        self.btn_sub_point = SidebarButton("포인트 관리", is_sub=True)
        self.btn_sub_designer = SidebarButton("디자이너 관리", is_sub=True)  # 디자이너 관리 버튼 추가
        self.btn_sub_category = SidebarButton("시술 카테고리 관리", is_sub=True)
        self.btn_sub_backup = SidebarButton("백업", is_sub=True)
        self.btn_sub_restore = SidebarButton("복원", is_sub=True)

        self.sub_buttons = [
            self.btn_sub_google, 
            self.btn_sub_point, 
            self.btn_sub_designer, 
            self.btn_sub_category, 
            self.btn_sub_backup, 
            self.btn_sub_restore
        ]

        for btn in self.sub_buttons:
            sub_layout.addWidget(btn)

        setting_hover_group = HoverMenuContainer(self.btn_setting, self.sub_menu_container, sidebar)
        sidebar_layout.addWidget(setting_hover_group)

        sidebar_layout.addStretch(1)

        # 1.4 종료 버튼
        self.btn_exit = SidebarButton("  종료", "exit.svg")
        self.btn_exit.clicked.connect(self.close)
        sidebar_layout.addWidget(self.btn_exit)

        main_layout.addWidget(sidebar, 0)

        # -------------------------------------------------------------
        # 2. 우측 메인 영역
        # -------------------------------------------------------------
        right_panel = QWidget(self)
        right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 2.1 상단 날짜 헤더
        header = QFrame(right_panel)
        header.setFixedHeight(50)
        header.setStyleSheet(f"background-color: {Colors.BACKGROUND}; border-bottom: 1.5px solid {Colors.PRIMARY};")
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 6, 20, 10)

        today_str = datetime.now().strftime("%Y년 %m월 %d일")
        lbl_date = QLabel(today_str, header)
        lbl_date.setFixedHeight(24)
        lbl_date.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 13px; font-weight: bold; background: transparent; border: none;")
        header_layout.addWidget(lbl_date)
        header_layout.addStretch()

        right_layout.addWidget(header)

        # 2.2 중앙 Stacked Widget 영역 및 페이지 등록
        self.stack = QStackedWidget(right_panel)
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.stack.setStyleSheet(f"background-color: {Colors.BACKGROUND};")

        # 0 index: 초기 기본 빈 페이지
        self.empty_page = QWidget()
        self.stack.addWidget(self.empty_page)

        # 1 index: 구글 계정 인증 화면
        self.google_setting_page = SettingsGoogleView()
        self.stack.addWidget(self.google_setting_page)

        # 2 index: 포인트 관리 화면
        self.point_setting_page = SettingsPointView()
        self.stack.addWidget(self.point_setting_page)

        # 3 index: 디자이너 관리 화면
        self.designer_setting_page = SettingsDesignerView()
        self.stack.addWidget(self.designer_setting_page)

        # 4 index: 시술 카테고리 관리 화면
        self.category_setting_page = SettingsCategoryView()
        self.stack.addWidget(self.category_setting_page)

        # 초기 시작 화면 설정
        self.stack.setCurrentWidget(self.empty_page)

        right_layout.addWidget(self.stack)
        main_layout.addWidget(right_panel, 1)

        # 모든 서브메뉴 버튼 클릭 이벤트 일괄 바인딩 (클로저 바인딩 처리)
        for btn in self.sub_buttons:
            btn.clicked.connect(lambda checked=False, target=btn: self.select_sub_button(target))

    def select_main_button(self, target_btn):
        """메인 메뉴 선택 상태 갱신"""
        for btn in self.menu_buttons:
            btn.setChecked(btn == target_btn)

    def select_sub_button(self, target_btn):
        """서브 메뉴 선택 상태 갱신 및 대응되는 설정 화면 전환"""
        for btn in self.sub_buttons:
            btn.setChecked(btn == target_btn)
        self.select_main_button(self.btn_setting)
        
        if target_btn == self.btn_sub_google:
            self.stack.setCurrentWidget(self.google_setting_page)
        elif target_btn == self.btn_sub_point:
            self.point_setting_page.load_point_rates()  # 화면 전환 시 최신 DB 설정값 재로드
            self.stack.setCurrentWidget(self.point_setting_page)
        elif target_btn == self.btn_sub_designer:
            self.designer_setting_page.load_designer_list()  # 최신 직원 목록 재로드
            self.stack.setCurrentWidget(self.designer_setting_page)
        elif target_btn == self.btn_sub_category:
            self.stack.setCurrentWidget(self.category_setting_page)