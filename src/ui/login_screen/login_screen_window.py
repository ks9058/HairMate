# src/ui/login_screen/login_screen_window.py
import os
from PySide6.QtWidgets import QMainWindow, QWidget
from PySide6.QtGui import QIcon, QFont, QFontDatabase
from PySide6.QtCore import QSize

# 변환한 UI 클래스를 가져오기
from .login_screen_ui import Ui_login
# 색상 변수 가져오기 
from src.utils.styles import LOGIN_BUTTON_STYLE, BLACK


class LoginWindow(QMainWindow, Ui_login):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager # 책장(StackedWidget) 관리를 위한 참조
        
        # 1. UI 설정
        self.setupUi(self)
        
        # 2. 커스텀 디자인 오버라이드
        self.apply_custom_styles()

        # 3. 글자색 강제 설정
        self.label.setStyleSheet(f"color: {BLACK}; background: transparent;")
        
        # 4. 버튼 클릭 이벤트 연결
        self.pushButton.clicked.connect(self.handle_login)

    def apply_custom_styles(self):
        # 전체 배경 투명 (main.py의 흰색 배경을 보기 위해)
        self.centralwidget.setStyleSheet("background: transparent;")
        
        # 색상 변수 적용 (오버라이드)
        self.pushButton.setStyleSheet(LOGIN_BUTTON_STYLE)
        
        # 아이콘 경로 설정 (main.py 위치 기준)
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        icon_path = os.path.join(base_path, "assets", "icons", "google_logo.png")
        
        if os.path.exists(icon_path):
            self.pushButton.setIcon(QIcon(icon_path))
            self.pushButton.setIconSize(QSize(24, 24))

    def handle_login(self):
        print("로그인 버튼이 눌렸습니다.")