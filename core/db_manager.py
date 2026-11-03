import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

class DBManager:
    """SQLite 데이터베이스 연결 및 ER 다이어그램 스키마 관리를 전담하는 모듈"""
    def __init__(self):
        self.db_path = os.getenv("DB_PATH", "hairmate.db")

    def get_connection(self):
        """SQLite DB 커넥션 객체를 반환하며 외래키 제약조건을 활성화합니다."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self):
        """ER 다이어그램 스펙에 맞춘 테이블 스키마 생성 및 초기화"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. user (사용자)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                oauth_token TEXT NOT NULL,
                expire_time DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 2. settings (사용자 설정)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 3. category (카테고리)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS category (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                display_order INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER NOT NULL DEFAULT 1,
                display_order INTEGER NOT NULL DEFAULT 0
            );
            """)

            # 4. service (시술)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS service (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price INTEGER NOT NULL DEFAULT 0,
                display_order INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER NOT NULL DEFAULT 1,
                display_order INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE RESTRICT
            );
            """)

            # 5. customer (고객)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS customer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                point INTEGER NOT NULL DEFAULT 0,
                memo TEXT NOT NULL DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER NOT NULL DEFAULT 1
            );
            """)

            # 6. visit (방문 기록)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS visit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                total_amount INTEGER NOT NULL DEFAULT 0,
                visited_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customer(id) ON DELETE CASCADE
            );
            """)

            # 7. visit_service (상세 시술 내역)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS visit_service (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_id INTEGER NOT NULL,
                visit_id INTEGER NOT NULL,
                price INTEGER NOT NULL DEFAULT 0,
                quantity INTEGER NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (service_id) REFERENCES service(id) ON DELETE RESTRICT,
                FOREIGN KEY (visit_id) REFERENCES visit(id) ON DELETE CASCADE
            );
            """)

            # 8. payment (결제 기록)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visit_id INTEGER NOT NULL,
                amount INTEGER NOT NULL DEFAULT 0,
                payment_method TEXT NOT NULL, -- '카드', '현금', '포인트'
                paid_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (visit_id) REFERENCES visit(id) ON DELETE CASCADE
            );
            """)

            # 기본 설정값 예시 등록
            cursor.execute("""
            INSERT OR IGNORE INTO settings (key, value) 
            VALUES ('default_point_rate', '5');
            """)

            conn.commit()
            print(f"[DB] {self.db_path} ER 다이어그램 스펙 스키마 생성 완료.")