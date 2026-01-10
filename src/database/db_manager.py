import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="data/hairmate.db"):
        self.db_path = db_path
        # data 폴더가 없으면 생성
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        """데이터베이스 연결 객체를 반환합니다."""
        conn = sqlite3.connect(self.db_path)
        # SQLite에서 외래 키 제약 조건을 활성화합니다
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row  # 결과를 딕셔너리 형태로 받기 위해 설정
        return conn

    def init_db(self):
        """ERD 설계에 따라 테이블을 생성합니다."""
        with self.get_connection() as conn:
            # 1. 카테고리 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS category (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    display_order INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)

            # 2. 시술 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS service (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER,
                    name VARCHAR(100) NOT NULL,
                    price DECIMAL NOT NULL,
                    display_order INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (category_id) REFERENCES category(id)
                )
            """)

            # 3. 고객 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS customer (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    phone VARCHAR(100) NOT NULL,
                    point INTEGER DEFAULT 0,
                    memo TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)

            # 4. 방문 기록 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS visit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER,
                    total_amount DECIMAL NOT NULL,
                    visited_at DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customer(id)
                )
            """)

            # 5. 상세 시술 내역 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS visit_service (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_id INTEGER,
                    visit_id INTEGER,
                    price DECIMAL NOT NULL,
                    quantity INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (service_id) REFERENCES service(id),
                    FOREIGN KEY (visit_id) REFERENCES visit(id)
                )
            """)

            # 6. 결제 기록 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS payment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    visit_id INTEGER,
                    amount DECIMAL NOT NULL,
                    payment_method TEXT CHECK(payment_method IN ('CASH', 'CARD', 'POINT')),
                    paid_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (visit_id) REFERENCES visit(id)
                )
            """)
            
            conn.commit()