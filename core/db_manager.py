import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()


class DBManager:
    """SQLite 데이터베이스 연결, 최신 ERD 스키마 관리 및 CRUD 전담 모듈"""

    def __init__(self):
        self.db_path = os.getenv("DB_PATH", "hairmate.db")
        self.init_db()

    def get_connection(self):
        """SQLite DB 커넥션 객체를 반환하며 외래키 제약조건을 활성화합니다."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self):
        """최신 9개 테이블 스키마 생성 및 구버전 user 테이블 감지 시 마이그레이션"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 구버전 user 테이블 감지 (name 컬럼이 없으면 구버전 테이블 삭제 후 재설계)
            cursor.execute("PRAGMA table_info(user);")
            user_cols_info = cursor.fetchall()
            if user_cols_info:
                col_names = [col[1] for col in user_cols_info]
                if "name" not in col_names:
                    cursor.execute("DROP TABLE IF EXISTS user;")

            # 1. 고객 (customer)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS customer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                point INTEGER NOT NULL DEFAULT 0,
                memo TEXT DEFAULT '',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 2. 사용자/직원/디자이너 (user)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                position TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 3. 카테고리 (category)
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

            # 4. 시술 (service)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS service (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price INTEGER NOT NULL DEFAULT 0,
                duration_minutes INTEGER DEFAULT 30,
                display_order INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE RESTRICT
            );
            """)

            # 5. 방문 및 결제 건 (visit)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS visit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                user_id INTEGER,
                total_duration_minutes INTEGER DEFAULT 0,
                original_amount INTEGER NOT NULL DEFAULT 0,
                discount_amount INTEGER NOT NULL DEFAULT 0,
                used_point INTEGER NOT NULL DEFAULT 0,
                total_amount INTEGER NOT NULL DEFAULT 0,
                visited_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customer(id) ON DELETE RESTRICT,
                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL
            );
            """)

            # 6. 상세 시술 내역 (visit_service)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS visit_service (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visit_id INTEGER NOT NULL,
                service_id INTEGER NOT NULL,
                user_id INTEGER,
                price INTEGER NOT NULL DEFAULT 0,
                quantity INTEGER NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (visit_id) REFERENCES visit(id) ON DELETE CASCADE,
                FOREIGN KEY (service_id) REFERENCES service(id) ON DELETE RESTRICT,
                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL
            );
            """)

            # 7. 결제 수단별 기록 (payment)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visit_id INTEGER NOT NULL,
                amount INTEGER NOT NULL DEFAULT 0,
                payment_method TEXT NOT NULL,
                paid_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (visit_id) REFERENCES visit(id) ON DELETE CASCADE
            );
            """)

            # 8. 포인트 이력 (point_history)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS point_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                visit_id INTEGER,
                amount INTEGER NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customer(id) ON DELETE RESTRICT,
                FOREIGN KEY (visit_id) REFERENCES visit(id) ON DELETE SET NULL
            );
            """)

            # 9. 설정 (settings)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """)

            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('point_rate_general', '10');")
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('point_rate_prepaid', '20');")

            conn.commit()

    # -------------------------------------------------------------
    # 카테고리 & 시술 관리 헬퍼
    # -------------------------------------------------------------
    def fetch_active_categories_and_services(self):
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
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN TRANSACTION;")

            for idx, cat in enumerate(categories_data):
                cat_id = cat.get("id")
                name = cat["name"]
                is_active = 0 if cat.get("deleted", False) else 1
                display_order = idx

                if cat_id is None:
                    cursor.execute("""
                        INSERT INTO category (name, display_order, is_active)
                        VALUES (?, ?, ?)
                    """, (name, display_order, is_active))
                    cat["id"] = cursor.lastrowid
                else:
                    cursor.execute("""
                        UPDATE category
                        SET name = ?, display_order = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (name, display_order, is_active, cat_id))

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
                        cursor.execute("""
                            INSERT INTO service (category_id, name, price, display_order, is_active)
                            VALUES (?, ?, ?, ?, ?)
                        """, (cat_id, svc_name, price, display_order, is_active))
                        svc["id"] = cursor.lastrowid
                    else:
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

    # -------------------------------------------------------------
    # Settings 헬퍼
    # -------------------------------------------------------------
    def get_setting(self, key: str, default: str = "") -> str:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default
        except Exception as e:
            print(f"[DB Error] get_setting: {e}")
            return default
        finally:
            conn.close()

    def set_setting(self, key: str, value: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
            """, (key, str(value)))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"[DB Error] set_setting: {e}")
            return False
        finally:
            conn.close()

    # -------------------------------------------------------------
    # User / Designer (디자이너/직원) CRUD 헬퍼
    # -------------------------------------------------------------
    def get_all_designers(self):
        """활성화된(is_active=1) 디자이너/직원 목록 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, name, phone, position 
                FROM user 
                WHERE is_active = 1 
                ORDER BY id ASC
            """)
            rows = cursor.fetchall()
            return [{"id": r[0], "name": r[1], "phone": r[2] or "", "position": r[3] or ""} for r in rows]
        except Exception as e:
            print(f"[DB Error] get_all_designers: {e}")
            return []
        finally:
            conn.close()

    def add_designer(self, name: str, phone: str, position: str) -> tuple[bool, str]:
        """신규 디자이너 등록 (성공 여부, 에러 메시지 반환)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO user (name, phone, position, is_active)
                VALUES (?, ?, ?, 1)
            """, (name, phone, position))
            conn.commit()
            return True, ""
        except Exception as e:
            conn.rollback()
            print(f"[DB Error] add_designer: {e}")
            return False, str(e)
        finally:
            conn.close()

    def update_designer(self, user_id: int, name: str, phone: str, position: str) -> tuple[bool, str]:
        """디자이너 정보 수정 (성공 여부, 에러 메시지 반환)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE user 
                SET name = ?, phone = ?, position = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND is_active = 1
            """, (name, phone, position, user_id))
            conn.commit()
            return True, ""
        except Exception as e:
            conn.rollback()
            print(f"[DB Error] update_designer: {e}")
            return False, str(e)
        finally:
            conn.close()

    def delete_designer(self, user_id: int) -> bool:
        """디자이너 논리적 삭제 (is_active = 0)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE user 
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (user_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"[DB Error] delete_designer: {e}")
            return False
        finally:
            conn.close()