# main.py
import sys
import resources_rc
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from src.ui.login_screen.login_screen_window import LoginWindow
from src.ui.menu.menu_window import MenuWindow  
from src.utils.colors import BACKGROUND

class HairMateApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HairMate")
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        self.setStyleSheet(f"QMainWindow {{ background-color: {BACKGROUND}; }}")
        
        # 2. 로그인 화면 추가 (Index 0)
        self.login_page = LoginWindow(self)
        self.stacked_widget.addWidget(self.login_page)
        
        # 3. 메뉴 화면 추가 (Index 1)
        self.menu_page = MenuWindow(self)
        self.stacked_widget.addWidget(self.menu_page)
        
        self.stacked_widget.setCurrentWidget(self.login_page)

    # 4. 화면 전환용 '스위치' 함수
    def switch_to_menu(self):
        # 인덱스 1번(메뉴 화면)으로 페이지를 넘깁니다.
        self.stacked_widget.setCurrentIndex(1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = HairMateApp()
    main_window.showMaximized()
    sys.exit(app.exec())