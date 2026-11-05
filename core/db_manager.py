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
        """최신 9개 테이블 스키마 생성 및 구버전 테이블 자동 마이그레이션"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 구버전 user 테이블 감지 시 마이그레이션
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
    # Customer (고객 관리) CRUD 헬퍼
    # -------------------------------------------------------------
    def get_all_customers(self):
        """활성화된(is_active=1) 고객 목록과 최근 방문일자 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    c.id, c.name, c.phone, c.point, c.memo,
                    COALESCE((
                        SELECT strftime('%Y-%m-%d', MAX(visited_at)) 
                        FROM visit 
                        WHERE customer_id = c.id
                    ), '-') AS recent_visit_date
                FROM customer c
                WHERE c.is_active = 1
                ORDER BY c.id DESC
            """)
            rows = cursor.fetchall()
            return [{
                "id": r[0],
                "name": r[1],
                "phone": r[2],
                "point": r[3],
                "memo": r[4] or "",
                "recent_visit": r[5]
            } for r in rows]
        except Exception as e:
            print(f"[DB Error] get_all_customers: {e}")
            return []
        finally:
            conn.close()

    def check_phone_duplicate(self, phone: str, exclude_id: int = None) -> bool:
        """전화번호 중복 체크"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if exclude_id is not None:
                cursor.execute("SELECT COUNT(*) FROM customer WHERE phone = ? AND id != ? AND is_active = 1", (phone, int(exclude_id)))
            else:
                cursor.execute("SELECT COUNT(*) FROM customer WHERE phone = ? AND is_active = 1", (phone,))
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            print(f"[DB Error] check_phone_duplicate: {e}")
            return False
        finally:
            conn.close()

    def add_customer(self, name: str, phone: str, memo: str = "") -> tuple[bool, str]:
        """신규 고객 등록 (전화번호 중복 검증)"""
        if self.check_phone_duplicate(phone):
            return False, "이미 등록된 전화번호입니다."
        
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO customer (name, phone, point, memo, is_active)
                VALUES (?, ?, 0, ?, 1)
            """, (name, phone, memo))
            conn.commit()
            return True, ""
        except Exception as e:
            conn.rollback()
            print(f"[DB Error] add_customer: {e}")
            return False, str(e)
        finally:
            conn.close()

    def update_customer(self, customer_id: int, name: str, phone: str, memo: str) -> tuple[bool, str]:
        """고객 정보 수정 (전화번호 중복 검증)"""
        try:
            customer_id = int(customer_id)
        except (TypeError, ValueError):
            return False, "유효하지 않은 고객 ID입니다."

        if self.check_phone_duplicate(phone, exclude_id=customer_id):
            return False, "이미 다른 고객이 사용 중인 전화번호입니다."

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE customer
                SET name = ?, phone = ?, memo = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND is_active = 1
            """, (name, phone, memo, customer_id))
            conn.commit()
            return True, ""
        except Exception as e:
            conn.rollback()
            print(f"[DB Error] update_customer: {e}")
            return False, str(e)
        finally:
            conn.close()

    def delete_customer(self, customer_id: int) -> bool:
        """고객 논리적 삭제 (is_active = 0)"""
        try:
            customer_id = int(customer_id)
        except (TypeError, ValueError):
            return False

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE customer
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (customer_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"[DB Error] delete_customer: {e}")
            return False
        finally:
            conn.close()

    def get_customer_visit_history(self, customer_id: int):
        """특정 고객 방문 이력 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    c.name AS customer_name,
                    strftime('%Y-%m-%d', v.visited_at) AS visit_date,
                    v.total_amount,
                    COALESCE(GROUP_CONCAT(DISTINCT s.name), '-') AS services,
                    COALESCE(u.name, '-') AS designer_name
                FROM visit v
                JOIN customer c ON v.customer_id = c.id
                LEFT JOIN visit_service vs ON v.id = vs.visit_id
                LEFT JOIN service s ON vs.service_id = s.id
                LEFT JOIN user u ON v.user_id = u.id
                WHERE v.customer_id = ?
                GROUP BY v.id
                ORDER BY v.visited_at DESC
            """, (int(customer_id),))
            rows = cursor.fetchall()
            return [{
                "customer_name": r[0],
                "visit_date": r[1],
                "amount": f"{r[2]:,}원",
                "services": r[3],
                "designer": r[4]
            } for r in rows]
        except Exception as e:
            print(f"[DB Error] get_customer_visit_history: {e}")
            return []
        finally:
            conn.close()

    def get_customer_stats(self, customer_id: int):
        """특정 고객 방문 통계 데이터 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            c_id = int(customer_id)
            cursor.execute("""
                SELECT 
                    COUNT(id) AS visit_count,
                    COALESCE(SUM(total_amount), 0) AS total_amt,
                    COALESCE(AVG(total_amount), 0) AS avg_amt
                FROM visit
                WHERE customer_id = ?
            """, (c_id,))
            stat = cursor.fetchone()
            
            visit_count = stat[0] if stat else 0
            total_amt = stat[1] if stat else 0
            avg_amt = int(stat[2]) if stat else 0

            cursor.execute("""
                SELECT cat.name, COUNT(vs.id)
                FROM visit_service vs
                JOIN visit v ON vs.visit_id = v.id
                JOIN service s ON vs.service_id = s.id
                JOIN category cat ON s.category_id = cat.id
                WHERE v.customer_id = ?
                GROUP BY cat.id
                ORDER BY COUNT(vs.id) DESC
            """, (c_id,))
            pref_rows = cursor.fetchall()
            preferences = [{"category": r[0], "count": r[1]} for r in pref_rows]

            return {
                "total_visits": visit_count,
                "total_amount": total_amt,
                "avg_amount": avg_amt,
                "preferences": preferences
            }
        except Exception as e:
            print(f"[DB Error] get_customer_stats: {e}")
            return {"total_visits": 0, "total_amount": 0, "avg_amount": 0, "preferences": []}
        finally:
            conn.close()

    # -------------------------------------------------------------
    # Category & Service 헬퍼
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
    # User / Designer CRUD 헬퍼
    # -------------------------------------------------------------
    def get_all_designers(self):
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