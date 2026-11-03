import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

class DBManager:
    """SQLite 데이터베이스 연결 및 관리를 전담하는 모듈"""
    def __init__(self):
        self.db_path = os.getenv("DB_PATH", "hairmate.db")

    def get_connection(self):
        """SQLite DB 커넥션 객체를 반환합니다."""
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """초기 연결 테스트 (Issue #2에서 스키마 DDL 연동 예정)"""
        print(f"[DB] {self.db_path} 연결 확인 완료.")