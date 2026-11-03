import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

class DBManager:
    """SQLite 데이터베이스 연결 및 ER 다이어그램 스키마 관리를 전담하는 모듈"""
    def __init__(self):
        self.db_path = os.getenv("DB_PATH", "hairmate.db")
        self.init_db()

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
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
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

    def fetch_active_categories_and_services(self):
        """앱 시작 시 is_active = 1 인 카테고리 및 시술 데이터 로드"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, name FROM category WHERE is_active = 1 ORDER BY display_order ASC")
        categories_rows = cursor.fetchall()

        categories_data = []
        services_map = {}

        for cat_id, cat_name in categories_rows:
            categories_data.append({"id": cat_id, "name": cat_name, "edited": False, "deleted": False})
            
            cursor.execute("""
                SELECT id, name, price FROM service 
                WHERE category_id = ? AND is_active = 1 
                ORDER BY display_order ASC
            """, (cat_id,))
            services_rows = cursor.fetchall()
            
            services_map[cat_name] = [
                {"id": s_id, "name": s_name, "price": s_price, "edited": False, "deleted": False}
                for s_id, s_name, s_price in services_rows
            ]

        conn.close()
        return categories_data, services_map

    def save_all_changes(self, categories_data, services_map):
        """
        카테고리 및 시술 변경사항을 SQLite 단일 트랜잭션으로 일괄 저장
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN TRANSACTION;")

            # ---------------------------------------------------------
            # [A] 카테고리 일괄 저장 및 처리 (category 테이블)
            # ---------------------------------------------------------
            for idx, cat in enumerate(categories_data):
                cat_id = cat.get("id")
                name = cat["name"]
                is_active = 0 if cat.get("deleted", False) else 1
                display_order = idx

                if cat_id is None:
                    # 신규 추가 (INSERT)
                    cursor.execute("""
                        INSERT INTO category (name, display_order, is_active)
                        VALUES (?, ?, ?)
                    """, (name, display_order, is_active))
                    cat["id"] = cursor.lastrowid
                else:
                    # 기존 항목 수정/삭제 (UPDATE)
                    cursor.execute("""
                        UPDATE category
                        SET name = ?, display_order = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (name, display_order, is_active, cat_id))

            # ---------------------------------------------------------
            # [B] 시술 항목 일괄 저장 및 처리 (service 테이블)
            # ---------------------------------------------------------
            for cat in categories_data:
                cat_id = cat.get("id")
                cat_name = cat["name"]
                services = services_map.get(cat_name, [])
                cat_deleted = cat.get("deleted", False)

                for s_idx, svc in enumerate(services):
                    svc_id = svc.get("id")
                    svc_name = svc["name"]
                    price = svc["price"]
                    display_order = s_idx
                    
                    is_active = 0 if (svc.get("deleted", False) or cat_deleted) else 1

                    if svc_id is None:
                        # 신규 추가 (INSERT)
                        cursor.execute("""
                            INSERT INTO service (category_id, name, price, display_order, is_active)
                            VALUES (?, ?, ?, ?, ?)
                        """, (cat_id, svc_name, price, display_order, is_active))
                        svc["id"] = cursor.lastrowid
                    else:
                        # 기존 항목 수정/삭제 (UPDATE)
                        cursor.execute("""
                            UPDATE service
                            SET category_id = ?, name = ?, price = ?, display_order = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (cat_id, svc_name, price, display_order, is_active, svc_id))

            conn.commit()
            return True, "변경 사항이 성공적으로 저장되었습니다."

        except Exception as e:
            conn.rollback()
            return False, f"저장 중 오류가 발생했습니다: {str(e)}"
            
        finally:
            conn.close()