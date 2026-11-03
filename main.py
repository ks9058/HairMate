import sys
from PySide6.QtWidgets import QApplication
from ui.login_view import LoginView
from core.db_manager import DBManager

def main():
    # 1. DB 연결 검증
    db_mgr = DBManager()
    db_mgr.init_db()

    # 2. PySide6 애플리케이션 실행
    app = QApplication(sys.argv)
    
    font = app.font()
    font.setFamily("Malgun Gothic")
    app.setFont(font)

    window = LoginView()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()