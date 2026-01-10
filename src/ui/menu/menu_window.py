from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QIcon
from PySide6.QtCore import QDate 
from .menu_ui import Ui_Form 
from src.utils.styles import DASHBOARD_STYLE

class MenuWindow(QWidget, Ui_Form):
    def __init__(self, manager):
        super().__init__()
        self.setupUi(self)
        self.manager = manager
        
        # 1. 스타일시트 적용
        self.setStyleSheet(DASHBOARD_STYLE)
        
        # 2. 하위 메뉴 초기 설정 (기본적으로 숨김)
        if hasattr(self, 'sub_menu_frame'):
            self.sub_menu_frame.setVisible(False)
        # 3. 오늘 날짜 표시 기능 추가 
        self.set_current_date()

        # 4. 모든 버튼과 아이콘 매핑 (하위 버튼들 추가)
        self.icons = {
            # 메인 메뉴
            self.customer_registration_btn: ("customer_info_icon.png", "customer_info_black_icon.png"),
            self.sales_registration_btn: ("sales_registration_icon.png", "sales_registration_black_icon.png"),
            self.sales_statistics_btn: ("sales_statistics_icon.png", "sales_statistics_black_icon.png"),
            self.setting_btn: ("setting_icon.png", "setting_black_icon.png"),
            self.exit_btn: ("exit_icon.png", "exit_black_icon.png"),
            
            # 설정 하위 메뉴 (이미지 파일명 확인 필수)
            self.auth_management_btn: ("auth_management_icon.png", "auth_management_black_icon.png"),
            self.point_ratio_change_btn: ("point_ratio_icon.png", "point_ratio_black_icon.png"),
            self.category_service_management_btn: ("category_management_icon.png", "category_management_black_icon.png"),
            self.backup_btn: ("backup_icon.png", "backup_black_icon.png"),
        }

        # 5. 이벤트 연결
        self.setup_button_hovers()
        self.setup_menu_logic()

    def setup_button_hovers(self):
        """아이콘 스왑 로직 (모든 버튼 공통)"""
        for btn, (normal, hover) in self.icons.items():
            btn.setIcon(QIcon(f":/assets/icons/{normal}"))
            btn.enterEvent = lambda e, b=btn, h=hover: b.setIcon(QIcon(f":/assets/icons/{h}"))
            btn.leaveEvent = lambda e, b=btn, n=normal: b.setIcon(QIcon(f":/assets/icons/{n}"))

    def setup_menu_logic(self):
        """설정 메뉴 호버 시 하위 프레임 노출 로직"""
        # 설정 버튼에 마우스 진입 시 하위 메뉴 표시
        original_setting_enter = self.setting_btn.enterEvent
        def custom_setting_enter(event):
            original_setting_enter(event) # 기존 아이콘 변경 로직 실행
            if hasattr(self, 'sub_menu_frame'):
                self.sub_menu_frame.setVisible(True) # 하위 메뉴 보이기
        
        self.setting_btn.enterEvent = custom_setting_enter

        # 사이드바 전체 영역(frame)에서 마우스가 나가면 하위 메뉴 숨기기
        original_frame_leave = self.frame.leaveEvent
        def custom_frame_leave(event):
            if hasattr(self, 'sub_menu_frame'):
                self.sub_menu_frame.setVisible(False) # 하위 메뉴 숨기기
        
        self.frame.leaveEvent = custom_frame_leave

    def set_current_date(self):
        """오늘 날짜를 가져와서 헤더 라벨에 표시합니다."""
        # QDate.currentDate()로 시스템 날짜를 가져옵니다.
        current_date = QDate.currentDate().toString("yyyy년 M월 d일") # 예: 2026년 1월 10일
        
        if hasattr(self, 'date_label'):
            self.date_label.setText(current_date)