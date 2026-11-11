from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QPushButton, QLabel, QStackedWidget, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
from ui.theme import Colors, Styles, get_icon, load_fonts
from ui.customer_view import CustomerView
from ui.sales_registration_view import SalesRegistrationView
from ui.sales_cancel_view import SalesCancelView
from ui.sales_analytics_view import SalesAnalyticsView
from ui.settings_google_view import SettingsGoogleView
from ui.settings_category_view import SettingsCategoryView
from ui.settings_point_view import SettingsPointView  
from ui.settings_designer_view import SettingsDesignerView
from ui.settings_backup import SettingsBackupView
from ui.settings_restore import SettingsRestoreView
from ui.settings_consent_view import SettingsConsentView  # 💡 [추가] 동의서 출력 뷰 임포트


class SidebarButton(QPushButton):
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

        # 1. 좌측 사이드바 패널
        sidebar = QFrame(self)
        sidebar.setFixedWidth(200)
        sidebar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        sidebar.setStyleSheet(f"background-color: {Colors.PRIMARY};")

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 15)
        sidebar_layout.setSpacing(4)

        kaushan_font_family = load_fonts()
        logo_container = QFrame(sidebar)
        logo_container.setFixedHeight(50)
        logo_container.setStyleSheet(f"border-bottom: 1.5px solid {Colors.WHITE}; background-color: transparent;")
        
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(15, 0, 15, 0)

        logo_label = QLabel("HairMate", logo_container)
        logo_label.setFont(QFont(kaushan_font_family, 24))
        logo_label.setStyleSheet(f"color: {Colors.WHITE}; border: none;")
        logo_layout.addWidget(logo_label)

        sidebar_layout.addWidget(logo_container)

        self.btn_customer = SidebarButton("  고객관리", "customer.svg")
        self.btn_sales_reg = SidebarButton("  결제등록", "sales_registration.svg")
        self.btn_sales_cancel = SidebarButton("  결제취소", "sales_cancel.svg")
        self.btn_sales_analysis = SidebarButton("  매출분석", "sales_statistics.svg")
        self.btn_setting = SidebarButton("  설정", "setting.svg")

        self.menu_buttons = [
            self.btn_customer, 
            self.btn_sales_reg, 
            self.btn_sales_cancel, 
            self.btn_sales_analysis, 
            self.btn_setting
        ]

        sidebar_layout.addWidget(self.btn_customer)
        sidebar_layout.addWidget(self.btn_sales_reg)
        sidebar_layout.addWidget(self.btn_sales_cancel)
        sidebar_layout.addWidget(self.btn_sales_analysis)

        self.btn_customer.clicked.connect(self.show_customer_page)
        self.btn_sales_reg.clicked.connect(self.show_sales_reg_page)
        self.btn_sales_cancel.clicked.connect(self.show_sales_cancel_page)
        self.btn_sales_analysis.clicked.connect(self.show_sales_analytics_page)

        self.sub_menu_container = QWidget(sidebar)
        sub_layout = QVBoxLayout(self.sub_menu_container)
        sub_layout.setContentsMargins(0, 0, 0, 0)
        sub_layout.setSpacing(2)

        self.btn_sub_google = SidebarButton("구글 계정 인증", is_sub=True)
        self.btn_sub_point = SidebarButton("포인트 관리", is_sub=True)
        self.btn_sub_designer = SidebarButton("디자이너 관리", is_sub=True)
        self.btn_sub_category = SidebarButton("시술 카테고리 관리", is_sub=True)
        self.btn_sub_consent = SidebarButton("동의서 출력", is_sub=True)
        self.btn_sub_backup = SidebarButton("백업", is_sub=True)
        self.btn_sub_restore = SidebarButton("복원", is_sub=True)

        self.sub_buttons = [
            self.btn_sub_google, 
            self.btn_sub_point, 
            self.btn_sub_designer, 
            self.btn_sub_category,
            self.btn_sub_consent, 
            self.btn_sub_backup, 
            self.btn_sub_restore
        ]

        for btn in self.sub_buttons:
            sub_layout.addWidget(btn)

        setting_hover_group = HoverMenuContainer(self.btn_setting, self.sub_menu_container, sidebar)
        sidebar_layout.addWidget(setting_hover_group)
        sidebar_layout.addStretch(1)

        self.btn_exit = SidebarButton("  종료", "exit.svg")
        self.btn_exit.clicked.connect(self.close)
        sidebar_layout.addWidget(self.btn_exit)

        main_layout.addWidget(sidebar, 0)

        # 2. 우측 메인 영역
        right_panel = QWidget(self)
        right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        header = QFrame(right_panel)
        header.setFixedHeight(50)
        header.setStyleSheet(f"background-color: {Colors.BACKGROUND}; border-bottom: 1.5px solid {Colors.PRIMARY};")
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 6, 20, 6)

        today_str = datetime.now().strftime("%Y년 %m월 %d일")
        lbl_date = QLabel(today_str, header)
        lbl_date.setFixedHeight(24)
        lbl_date.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 13px; font-weight: bold; background: transparent; border: none;")
        header_layout.addWidget(lbl_date)
        header_layout.addStretch()

        self.btn_top_back = QPushButton("← 뒤로가기", header)
        self.btn_top_back.setFixedSize(110, 32)
        self.btn_top_back.setCursor(Qt.PointingHandCursor)
        btn_font = QFont("Inter", 11)
        btn_font.setBold(True)
        self.btn_top_back.setFont(btn_font)
        self.btn_top_back.setStyleSheet(f"""
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
        self.btn_top_back.setVisible(False)
        header_layout.addWidget(self.btn_top_back)

        right_layout.addWidget(header)

        # 2.2 중앙 QStackedWidget 영역
        self.stack = QStackedWidget(right_panel)
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.stack.setStyleSheet(f"background-color: {Colors.BACKGROUND};")

        self.customer_page = CustomerView()
        self.stack.addWidget(self.customer_page)

        self.sales_reg_page = SalesRegistrationView()
        self.stack.addWidget(self.sales_reg_page)

        self.sales_cancel_page = SalesCancelView()
        self.stack.addWidget(self.sales_cancel_page)

        self.sales_analytics_page = SalesAnalyticsView()
        self.stack.addWidget(self.sales_analytics_page)

        self.google_setting_page = SettingsGoogleView()
        self.stack.addWidget(self.google_setting_page)

        self.point_setting_page = SettingsPointView()
        self.stack.addWidget(self.point_setting_page)

        self.designer_setting_page = SettingsDesignerView()
        self.stack.addWidget(self.designer_setting_page)

        self.category_setting_page = SettingsCategoryView()
        self.stack.addWidget(self.category_setting_page)

        self.backup_setting_page = SettingsBackupView()
        self.stack.addWidget(self.backup_setting_page)

        self.restore_setting_page = SettingsRestoreView()
        self.stack.addWidget(self.restore_setting_page)

        self.consent_setting_page = SettingsConsentView()  # 💡 [추가] 동의서 출력 뷰 인스턴스화
        self.stack.addWidget(self.consent_setting_page)

        self.btn_top_back.clicked.connect(self.handle_top_back_click)

        self.sales_reg_page.page_changed.connect(self.on_sales_reg_page_changed)
        self.customer_page.page_changed.connect(self.on_customer_page_changed)

        self.show_customer_page()

        right_layout.addWidget(self.stack)
        main_layout.addWidget(right_panel, 1)

        for btn in self.sub_buttons:
            btn.clicked.connect(lambda checked=False, target=btn: self.select_sub_button(target))

    def handle_top_back_click(self):
        current_widget = self.stack.currentWidget()
        if current_widget == self.sales_reg_page:
            self.sales_reg_page.confirm_and_clear_selection()
        elif current_widget == self.customer_page:
            self.customer_page.reset_form()

    def on_sales_reg_page_changed(self, is_in_dashboard: bool):
        if self.stack.currentWidget() == self.sales_reg_page:
            self.btn_top_back.setVisible(is_in_dashboard)

    def on_customer_page_changed(self, is_in_detail: bool):
        if self.stack.currentWidget() == self.customer_page:
            self.btn_top_back.setVisible(is_in_detail)

    def select_main_button(self, target_btn):
        for btn in self.menu_buttons:
            btn.setChecked(btn == target_btn)

    def show_customer_page(self):
        self.select_main_button(self.btn_customer)
        for btn in self.sub_buttons:
            btn.setChecked(False)
        self.customer_page.load_customer_list()
        
        is_in_detail = (self.customer_page.right_stack.currentIndex() == 1)
        self.btn_top_back.setVisible(is_in_detail)

        self.stack.setCurrentWidget(self.customer_page)

    def show_sales_reg_page(self):
        self.select_main_button(self.btn_sales_reg)
        for btn in self.sub_buttons:
            btn.setChecked(False)
        self.sales_reg_page.load_customer_list()
        self.sales_reg_page.load_menu_data()
        self.sales_reg_page.load_designers()
        
        is_in_dashboard = (self.sales_reg_page.main_stack.currentIndex() == 1)
        self.btn_top_back.setVisible(is_in_dashboard)

        self.stack.setCurrentWidget(self.sales_reg_page)

    def show_sales_cancel_page(self):
        self.btn_top_back.setVisible(False)
        self.select_main_button(self.btn_sales_cancel)
        for btn in self.sub_buttons:
            btn.setChecked(False)
        self.sales_cancel_page.load_sales_data(use_date_filter=False)
        self.stack.setCurrentWidget(self.sales_cancel_page)

    def show_sales_analytics_page(self):
        self.btn_top_back.setVisible(False)
        self.select_main_button(self.btn_sales_analysis)
        for btn in self.sub_buttons:
            btn.setChecked(False)
        
        self.sales_analytics_page.load_designers()
        if self.sales_analytics_page.stack.currentIndex() == 0:
            self.sales_analytics_page.refresh_daily_analysis()
        else:
            self.sales_analytics_page.refresh_period_analysis()

        self.stack.setCurrentWidget(self.sales_analytics_page)

    def select_sub_button(self, target_btn):
        self.btn_top_back.setVisible(False)
        for btn in self.sub_buttons:
            btn.setChecked(btn == target_btn)
        self.select_main_button(self.btn_setting)
        
        if target_btn == self.btn_sub_google:
            self.stack.setCurrentWidget(self.google_setting_page)
        elif target_btn == self.btn_sub_point:
            self.point_setting_page.load_point_rates()
            self.stack.setCurrentWidget(self.point_setting_page)
        elif target_btn == self.btn_sub_designer:
            self.designer_setting_page.load_designer_list()
            self.stack.setCurrentWidget(self.designer_setting_page)
        elif target_btn == self.btn_sub_category:
            self.stack.setCurrentWidget(self.category_setting_page)
        elif target_btn == self.btn_sub_backup:
            self.backup_setting_page.load_last_backup_date()
            self.stack.setCurrentWidget(self.backup_setting_page)
        elif target_btn == self.btn_sub_restore:
            self.restore_setting_page.load_backup_list()
            self.stack.setCurrentWidget(self.restore_setting_page)
        elif target_btn == self.btn_sub_consent:  # 💡 [추가] 동의서 출력 메뉴 연결
            self.consent_setting_page.load_customer_data()
            self.stack.setCurrentWidget(self.consent_setting_page)