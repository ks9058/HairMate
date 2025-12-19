# main.py
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from src.ui.login_screen.login_screen_window import LoginWindow
from src.utils.colors import BACKGROUND

class HairMateApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HairMate")
        
        # 1. 흰색 배경의 '책장' 만들기
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        self.setStyleSheet(f"background-color: {BACKGROUND};")
        
        # 2. 로그인 화면 추가
        self.login_page = LoginWindow(self)
        self.stacked_widget.addWidget(self.login_page)
        
        # 3. 첫 화면으로 설정
        self.stacked_widget.setCurrentWidget(self.login_page)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    main_window = HairMateApp()
    main_window.showMaximized() # 전체화면 실행
    
    sys.exit(app.exec())