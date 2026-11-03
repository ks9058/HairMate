import sys
import os
from PySide6.QtWidgets import QApplication
from ui.login_view import LoginView
from ui.main_window import MainWindow
from core.db_manager import DBManager

class AppController:
    """화면 전환 흐름 컨트롤러"""
    def __init__(self):
        self.login_view = LoginView()
        self.main_window = None
        self.login_view.login_requested.connect(self.show_main_window)

    def start(self):
        self.login_view.show()

    def show_main_window(self):
        self.login_view.close()
        self.main_window = MainWindow()
        self.main_window.showMaximized()


def main():
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    db_mgr = DBManager()
    db_mgr.init_db()

    app = QApplication(sys.argv)
    
    # 기본 폰트를 Inter로 설정 (시스템 미설치 시 맑은 고딕 대체)
    font = app.font()
    font.setFamily("Inter")
    app.setFont(font)

    controller = AppController()
    controller.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()