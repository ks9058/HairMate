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
        """최신 9개 테이블 스키마 생성 및 필수 기본 데이터(선결제 카테고리/적립률) 자동 보장"""
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
                is_system INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """)

            cursor.execute("PRAGMA table_info(category);")
            cat_cols = [col[1] for col in cursor.fetchall()]
            if "is_system" not in cat_cols:
                cursor.execute("ALTER TABLE category ADD COLUMN is_system INTEGER NOT NULL DEFAULT 0;")

            cursor.execute("SELECT COUNT(*) FROM category WHERE name = '선결제';")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO category (name, display_order, is_active, is_system) VALUES ('선결제', 0, 1, 1);")
            else:
                cursor.execute("UPDATE category SET is_system = 1 WHERE name = '선결제';")

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

            cursor.execute("PRAGMA table_info(visit);")
            visit_cols = [col[1] for col in cursor.fetchall()]
            if "user_id" not in visit_cols:
                cursor.execute("ALTER TABLE visit ADD COLUMN user_id INTEGER;")

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

            cursor.execute("PRAGMA table_info(visit_service);")
            vs_cols = [col[1] for col in cursor.fetchall()]
            if "user_id" not in vs_cols:
                cursor.execute("ALTER TABLE visit_service ADD COLUMN user_id INTEGER;")

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

    def update_customer_point(self, customer_id: int, new_point: int) -> bool:
        """고객 포인트 업데이트"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE customer
                SET point = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND is_active = 1
            """, (int(new_point), int(customer_id)))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"[DB Error] update_customer_point: {e}")
            return False
        finally:
            conn.close()

    def update_customer_memo(self, customer_id: int, memo: str) -> bool:
        """고객 메모 단독 업데이트"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE customer
                SET memo = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND is_active = 1
            """, (str(memo), int(customer_id)))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"[DB Error] update_customer_memo: {e}")
            return False
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

    # -------------------------------------------------------------
    # 매출 데이터 저장 및 방문 통계 헬퍼
    # -------------------------------------------------------------
    def record_sale(self, customer_id: int, user_id: int, duration_minutes: int,
                    total_amount: int, used_point: int, earned_point: int,
                    visited_at_str: str, memo: str, cart_items: list, payments_history: list) -> bool:
        """매출 결제 완료 시 visit, visit_service, payment, point_history 등록 및 고객 정보(포인트, 메모) 업데이트"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION;")

            # 1. visit 테이블 저장
            cursor.execute("""
                INSERT INTO visit (customer_id, user_id, total_duration_minutes, original_amount, discount_amount, used_point, total_amount, visited_at)
                VALUES (?, ?, ?, ?, 0, ?, ?, ?)
            """, (customer_id, user_id, duration_minutes, total_amount, used_point, total_amount, visited_at_str))
            
            visit_id = cursor.lastrowid

            # 2. visit_service 상세 저장
            for item in cart_items:
                cursor.execute("""
                    INSERT INTO visit_service (visit_id, service_id, user_id, price, quantity)
                    VALUES (?, ?, ?, ?, ?)
                """, (visit_id, item["id"], user_id, item["price"], item["qty"]))

            # 3. payment 수단별 저장
            for p in payments_history:
                cursor.execute("""
                    INSERT INTO payment (visit_id, amount, payment_method, paid_at)
                    VALUES (?, ?, ?, ?)
                """, (visit_id, p["amount"], p["method"], visited_at_str))

            # 4. 포인트 사용/적립 내역 (point_history)
            if used_point > 0:
                cursor.execute("""
                    INSERT INTO point_history (customer_id, visit_id, amount, type, description)
                    VALUES (?, ?, ?, 'USE', '시술 결제 포인트 사용')
                """, (customer_id, visit_id, -used_point))

            if earned_point > 0:
                cursor.execute("""
                    INSERT INTO point_history (customer_id, visit_id, amount, type, description)
                    VALUES (?, ?, ?, 'EARN', '시술 결제 포인트 적립/충전')
                """, (customer_id, visit_id, earned_point))

            # 5. customer 포인트 및 메모 최종 업데이트
            cursor.execute("""
                UPDATE customer
                SET point = point - ? + ?, memo = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND is_active = 1
            """, (used_point, earned_point, memo, customer_id))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"[DB Error] record_sale: {e}")
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
    # Sales Cancel (결제 취소) 헬퍼
    # -------------------------------------------------------------
    def get_sales_cancel_list(self, query: str = "", date_str: str = ""):
            """결제 취소 화면용 목록 조회 (최신순 정렬, 결제 시/분 시간 포함 조회)"""
            conn = self.get_connection()
            cursor = conn.cursor()
            try:
                sql = """
                    SELECT 
                        v.id AS visit_id,
                        c.id AS customer_id,
                        c.name AS customer_name,
                        c.phone AS customer_phone,
                        COALESCE((
                            SELECT GROUP_CONCAT(s.name, '|||') 
                            FROM visit_service vs 
                            JOIN service s ON vs.service_id = s.id 
                            WHERE vs.visit_id = v.id
                        ), '-') AS services_raw,
                        COALESCE((
                            SELECT GROUP_CONCAT(DISTINCT payment_method) 
                            FROM payment 
                            WHERE visit_id = v.id
                        ), '-') AS payment_methods,
                        v.total_amount,
                        strftime('%Y-%m-%d %H:%M', v.visited_at) AS visit_date,
                        COALESCE((
                            SELECT SUM(amount) 
                            FROM point_history 
                            WHERE visit_id = v.id AND type = 'EARN'
                        ), 0) AS earned_point,
                        COALESCE((
                            SELECT SUM(ABS(amount)) 
                            FROM point_history 
                            WHERE visit_id = v.id AND type = 'USE'
                        ), 0) AS used_point,
                        v.total_duration_minutes,
                        COALESCE(u.name, '-') AS designer_name,
                        COALESCE(u.position, '') AS designer_position
                    FROM visit v
                    JOIN customer c ON v.customer_id = c.id
                    LEFT JOIN user u ON v.user_id = u.id
                    WHERE 1=1
                """
                params = []

                if query:
                    sql += " AND (c.name LIKE ? OR c.phone LIKE ?)"
                    q_param = f"%{query}%"
                    params.extend([q_param, q_param])

                if date_str:
                    sql += " AND strftime('%Y-%m-%d', v.visited_at) = ?"
                    params.append(date_str)

                sql += " ORDER BY v.visited_at DESC, v.id DESC"

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                result = []
                for r in rows:
                    raw_services = r[4]
                    if raw_services and raw_services != '-':
                        svc_list = list(dict.fromkeys([s.strip() for s in raw_services.split('|||') if s.strip()]))
                        display_services = ", ".join(svc_list)
                    else:
                        svc_list = []
                        display_services = "-"

                    dur_min = r[10] or 0
                    if dur_min >= 60:
                        h = dur_min // 60
                        m = dur_min % 60
                        dur_str = f"{h}시간" if m == 0 else f"{h}시간 {m}분"
                    else:
                        dur_str = f"{dur_min}분"

                    d_name = r[11]
                    d_pos = r[12]
                    if d_name != '-' and d_pos:
                        designer_str = f"{d_name} ({d_pos})"
                    else:
                        designer_str = d_name

                    result.append({
                        "visit_id": r[0],
                        "customer_id": r[1],
                        "customer_name": r[2],
                        "customer_phone": r[3],
                        "services": display_services,
                        "services_list": svc_list,
                        "payment_method": r[5],
                        "total_amount": r[6],
                        "visit_date": r[7], # 'YYYY-MM-DD HH:MM' 형태로 전달됨
                        "earned_point": r[8],
                        "used_point": r[9],
                        "duration_str": dur_str,
                        "designer_info": designer_str
                    })
                return result
            except Exception as e:
                print(f"[DB Error] get_sales_cancel_list: {e}")
                return []
            finally:
                conn.close()

    def cancel_sale_transaction(self, visit_id: int) -> tuple[bool, str]:
        """결제 취소 트랜잭션: 포인트 원상복구(적립 차감 & 사용 복원) 후 visit/payment/visit_service 삭제"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION;")

            # 1. 대상 visit 조회
            cursor.execute("SELECT customer_id FROM visit WHERE id = ?", (visit_id,))
            row = cursor.fetchone()
            if not row:
                conn.rollback()
                return False, "존재하지 않는 결제 내역입니다."
            customer_id = row[0]

            # 2. 해당 결제건으로 적립된 포인트 / 사용된 포인트 조회
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN type = 'EARN' THEN amount ELSE 0 END), 0) AS earned,
                    COALESCE(SUM(CASE WHEN type = 'USE' THEN ABS(amount) ELSE 0 END), 0) AS used
                FROM point_history 
                WHERE visit_id = ?
            """, (visit_id,))
            p_row = cursor.fetchone()
            earned_point = p_row[0] if p_row else 0
            used_point = p_row[1] if p_row else 0

            # 3. 고객 포인트 원상복구 (적립분 차감, 사용분 복구)
            net_point_change = used_point - earned_point
            cursor.execute("""
                UPDATE customer
                SET point = MAX(0, point + ?), updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND is_active = 1
            """, (net_point_change, customer_id))

            # 4. 연관 포인트 이력 삭제
            cursor.execute("DELETE FROM point_history WHERE visit_id = ?", (visit_id,))

            # 5. visit 삭제 (FK CASCADE로 payment, visit_service 자동 삭제)
            cursor.execute("DELETE FROM visit WHERE id = ?", (visit_id,))

            conn.commit()
            return True, "결제가 성공적으로 취소(삭제)되었습니다."
        except Exception as e:
            conn.rollback()
            print(f"[DB Error] cancel_sale_transaction: {e}")
            return False, f"결제 취소 중 오류 발생: {str(e)}"
        finally:
            conn.close()

    # -------------------------------------------------------------
    # Category & Service 헬퍼
    # -------------------------------------------------------------
    def fetch_active_categories_and_services(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, is_system FROM category WHERE is_active = 1 ORDER BY display_order ASC, id ASC")
        categories_rows = cursor.fetchall()

        categories_data = []
        services_map = {}

        for cat_id, cat_name, is_sys in categories_rows:
            categories_data.append({"id": cat_id, "name": cat_name, "is_system": is_sys, "edited": False, "deleted": False})
            
            cursor.execute("""
                SELECT id, name, price FROM service 
                WHERE category_id = ? AND is_active = 1 
                ORDER BY display_order ASC, id ASC
            """, (cat_id,))
            services_rows = cursor.fetchall()
            
            services_map[cat_name] = [
                {"id": s_id, "name": s_name, "price": s_price, "edited": False, "deleted": False}
                for s_id, s_name, s_price in services_rows
            ]

        conn.close()
        return categories_data, services_map
    
    def save_all_changes(self, categories_data, services_map):
            """카테고리 및 시술 정보 변경 사항 저장 (SQL 파라미터 바인딩 오류 수정 완료)"""
            conn = self.get_connection()
            cursor = conn.cursor()

            try:
                cursor.execute("BEGIN TRANSACTION;")

                # 1. 카테고리 저장 및 수정
                for idx, cat in enumerate(categories_data):
                    cat_id = cat.get("id")
                    name = cat["name"]
                    
                    if name == "선결제" or cat.get("is_system") == 1:
                        is_active = 1
                    else:
                        is_active = 0 if cat.get("deleted", False) else 1

                    display_order = idx

                    if cat_id is None:
                        # 물음표 4개 <-> 변수 4개
                        cursor.execute("""
                            INSERT INTO category (name, display_order, is_active, is_system)
                            VALUES (?, ?, ?, ?)
                        """, (name, display_order, is_active, 1 if name == "선결제" else 0))
                        cat["id"] = cursor.lastrowid
                    else:
                        # 물음표 4개 <-> 변수 4개
                        cursor.execute("""
                            UPDATE category
                            SET name = ?, display_order = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (name, display_order, is_active, cat_id))

                # 2. 시술 메뉴 저장 및 수정
                for cat in categories_data:
                    cat_id = cat.get("id")
                    cat_name = cat["name"]
                    services = services_map.get(cat_name, [])
                    cat_deleted = cat.get("deleted", False) and cat_name != "선결제"

                    for s_idx, svc in enumerate(services):
                        svc_id = svc.get("id")
                        svc_name = svc["name"]
                        price = svc["price"]
                        display_order = s_idx
                        
                        is_active = 0 if (svc.get("deleted", False) or cat_deleted) else 1

                        if svc_id is None:
                            # 신규 추가: 물음표 5개 <-> 변수 5개 (cat_id, svc_name, price, display_order, is_active)
                            cursor.execute("""
                                INSERT INTO service (category_id, name, price, display_order, is_active)
                                VALUES (?, ?, ?, ?, ?)
                            """, (cat_id, svc_name, price, display_order, is_active))
                            svc["id"] = cursor.lastrowid
                        else:
                            # 기존 수정: 물음표 6개 <-> 변수 6개 (cat_id, svc_name, price, display_order, is_active, svc_id)
                            cursor.execute("""
                                UPDATE service
                                SET category_id = ?, name = ?, price = ?, display_order = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (cat_id, svc_name, price, display_order, is_active, svc_id))

                conn.commit()
                return True, "변경 사항이 성공적으로 저장되었습니다."

            except Exception as e:
                conn.rollback()
                print(f"[DB Error] save_all_changes: {e}")
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