import sys
import os
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from ui.login_view import LoginView
from ui.main_window import MainWindow
from core.db_manager import DBManager

# 1. Windows 작업표시줄에서 파이썬 기본 아이콘 대신 전용 아이콘으로 분리 등록
try:
    myappid = "hairmate.salon.management.system.1.0"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass


class AppController:
    """화면 전환 흐름 컨트롤러"""
    def __init__(self, app_icon: QIcon = None):
        self.app_icon = app_icon
        self.login_view = LoginView()
        self.main_window = None

        if self.app_icon and not self.app_icon.isNull():
            self.login_view.setWindowIcon(self.app_icon)

        self.login_view.login_requested.connect(self.show_main_window)

    def start(self):
        self.login_view.show()

    def show_main_window(self):
        self.login_view.close()
        self.main_window = MainWindow()
        if self.app_icon and not self.app_icon.isNull():
            self.main_window.setWindowIcon(self.app_icon)
        self.main_window.showMaximized()


def main():
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    db_mgr = DBManager()
    db_mgr.init_db()

    app = QApplication(sys.argv)

    # Windows 다크 모드 영향 방지를 위한 앱 전역 라이트 모드 고정
    try:
        app.styleHints().setColorScheme(Qt.ColorScheme.Light)
    except AttributeError:
        pass

    # 2. resources 폴더의 HM.svg 파일 로드 및 앱 전역 아이콘 지정
    project_root = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(project_root, "resources", "HM.svg")
    
    app_icon = QIcon(icon_path)
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    
    # 기본 폰트를 Inter로 설정 (시스템 미설치 시 맑은 고딕 대체)
    font = app.font()
    font.setFamily("Inter")
    app.setFont(font)

    controller = AppController(app_icon=app_icon)
    controller.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()