import sqlite3
import os
from dotenv import load_dotenv
import calendar
from datetime import datetime, timedelta

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
        """최신 9개 테이블 스키마 생성 및 개인정보/마케팅 동의 컬럼 마이그레이션 자동 수행"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. 고객 (customer)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS customer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                point INTEGER NOT NULL DEFAULT 0,
                memo TEXT DEFAULT '',
                is_consent INTEGER NOT NULL DEFAULT 0,
                consent_at DATETIME,
                is_marketing_consent INTEGER NOT NULL DEFAULT 0,
                marketing_consent_at DATETIME,
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
        """활성화된(is_active=1) 고객 목록과 개인정보 동의 상태 및 최근 방문일자 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    c.id, c.name, c.phone, c.point, c.memo, 
                    COALESCE(c.is_consent, 0), COALESCE(c.is_marketing_consent, 0),
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
                "is_consent": r[5],
                "is_marketing_consent": r[6],
                "recent_visit": r[7]
            } for r in rows]
        except Exception as e:
            print(f"[DB Error] get_all_customers: {e}")
            return []
        finally:
            conn.close()

    def get_consented_customers(self, query: str = ""):
        """개인정보 및 마케팅 동의서 출력 화면용 고객 목록 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            sql = """
                SELECT 
                    id, name, phone, memo,
                    COALESCE(is_consent, 0),
                    CASE 
                        WHEN is_consent = 1 THEN COALESCE(strftime('%Y-%m-%d', consent_at), strftime('%Y-%m-%d', created_at))
                        ELSE '-'
                    END AS consent_date,
                    COALESCE(is_marketing_consent, 0),
                    CASE 
                        WHEN is_marketing_consent = 1 THEN COALESCE(strftime('%Y-%m-%d', marketing_consent_at), strftime('%Y-%m-%d', created_at))
                        ELSE '-'
                    END AS marketing_consent_date
                FROM customer
                WHERE is_active = 1
            """
            params = []
            if query:
                sql += " AND (name LIKE ? OR phone LIKE ?)"
                q_param = f"%{query}%"
                params.extend([q_param, q_param])

            sql += " ORDER BY id DESC"
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            return [{
                "id": r[0],
                "name": r[1],
                "phone": r[2],
                "memo": r[3] or "",
                "is_consent": r[4],
                "consent_at": r[5] or "-",
                "is_marketing_consent": r[6],
                "marketing_consent_at": r[7] or "-"
            } for r in rows]
        except Exception as e:
            print(f"[DB Error] get_consented_customers: {e}")
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
            return cursor.fetchone()[0] > 0
        except Exception as e:
            print(f"[DB Error] check_phone_duplicate: {e}")
            return False
        finally:
            conn.close()

    def add_customer(self, name: str, phone: str, memo: str = "", is_consent: int = 1, is_marketing_consent: int = 0) -> tuple[bool, str]:
        """신규 고객 등록 (필수 동의 및 마케팅 동의 정보 함께 저장)"""
        if self.check_phone_duplicate(phone):
            return False, "이미 등록된 전화번호입니다."
        
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if is_consent else None
            m_now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if is_marketing_consent else None
            
            cursor.execute("""
                INSERT INTO customer (name, phone, point, memo, is_consent, consent_at, is_marketing_consent, marketing_consent_at, is_active)
                VALUES (?, ?, 0, ?, ?, ?, ?, ?, 1)
            """, (name, phone, memo, is_consent, now_str, is_marketing_consent, m_now_str))
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

    def update_customer_consent(self, customer_id: int, is_consent: int = 1, is_marketing_consent: int = 0) -> bool:
            """고객의 개인정보 수집 및 마케팅 동의 상태 DB 업데이트"""
            conn = self.get_connection()
            cursor = conn.cursor()
            try:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c_time = now_str if is_consent == 1 else None
                m_time = now_str if is_marketing_consent == 1 else None

                cursor.execute("""
                    UPDATE customer
                    SET is_consent = ?, consent_at = ?,
                        is_marketing_consent = ?, marketing_consent_at = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND is_active = 1
                """, (is_consent, c_time, is_marketing_consent, m_time, customer_id))
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                print(f"[DB Error] update_customer_consent: {e}")
                return False
            finally:
                conn.close()

    def delete_customer(self, customer_id: int) -> bool:
            """고객 삭제 처리 (개인정보보호법 준수를 위한 식별정보 익명화 및 매출 데이터 보존)"""
            try:
                customer_id = int(customer_id)
            except (TypeError, ValueError):
                return False

            conn = self.get_connection()
            cursor = conn.cursor()
            try:
                # 1. 개인식별정보(이름, 전화번호, 메모, 동의일시, 포인트) 익명화 및 파기
                # 2. UNIQUE(phone) 제약조건 충돌 방지를 위해 고객 ID 기반 고유 가상번호 부여
                cursor.execute("""
                    UPDATE customer
                    SET is_active = 0,
                        name = '(삭제된 고객)',
                        phone = '000-0000-' || printf('%04d', id),
                        memo = '',
                        point = 0,
                        is_consent = 0,
                        consent_at = NULL,
                        is_marketing_consent = 0,
                        marketing_consent_at = NULL,
                        updated_at = CURRENT_TIMESTAMP
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
        """매출 결제 완료 시 visit, visit_service, payment, point_history 등록 및 고객 정보 업데이트"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION;")

            cursor.execute("""
                INSERT INTO visit (customer_id, user_id, total_duration_minutes, original_amount, discount_amount, used_point, total_amount, visited_at)
                VALUES (?, ?, ?, ?, 0, ?, ?, ?)
            """, (customer_id, user_id, duration_minutes, total_amount, used_point, total_amount, visited_at_str))
            
            visit_id = cursor.lastrowid

            for item in cart_items:
                cursor.execute("""
                    INSERT INTO visit_service (visit_id, service_id, user_id, price, quantity)
                    VALUES (?, ?, ?, ?, ?)
                """, (visit_id, item["id"], user_id, item["price"], item["qty"]))

            for p in payments_history:
                cursor.execute("""
                    INSERT INTO payment (visit_id, amount, payment_method, paid_at)
                    VALUES (?, ?, ?, ?)
                """, (visit_id, p["amount"], p["method"], visited_at_str))

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
        """특정 고객 방문 이력 및 시술 항목별 선택 수량 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    v.id,
                    c.name AS customer_name,
                    strftime('%Y-%m-%d', v.visited_at) AS visit_date,
                    v.total_amount,
                    COALESCE(u.name, '-') AS designer_name
                FROM visit v
                JOIN customer c ON v.customer_id = c.id
                LEFT JOIN user u ON v.user_id = u.id
                WHERE v.customer_id = ?
                ORDER BY v.visited_at DESC, v.id DESC
            """, (int(customer_id),))
            rows = cursor.fetchall()

            history = []
            for v_id, c_name, v_date, total_amt, d_name in rows:
                cursor.execute("""
                    SELECT s.name, SUM(COALESCE(vs.quantity, 1)) AS cnt
                    FROM visit_service vs
                    JOIN service s ON vs.service_id = s.id
                    WHERE vs.visit_id = ?
                    GROUP BY s.id
                    ORDER BY cnt DESC, s.name ASC
                """, (v_id,))
                svc_rows = cursor.fetchall()

                if svc_rows:
                    svc_list_str = []
                    details_list = []
                    for name, cnt in svc_rows:
                        details_list.append({"name": name, "count": cnt})
                        if cnt > 1:
                            svc_list_str.append(f"{name} ({cnt}개)")
                        else:
                            svc_list_str.append(name)
                    services_str = ", ".join(svc_list_str)
                else:
                    services_str = "-"
                    details_list = []

                history.append({
                    "visit_id": v_id,
                    "customer_name": c_name,
                    "visit_date": v_date,
                    "amount": f"{total_amt:,}",
                    "services": services_str,
                    "designer": d_name,
                    "service_details": details_list
                })
            return history
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
                    COUNT(v.id) AS visit_count,
                    COALESCE(SUM(v.total_amount), 0) AS total_amt,
                    COALESCE(AVG(v.total_amount), 0) AS avg_amt,
                    COALESCE(SUM(
                        CASE 
                            WHEN v.total_duration_minutes > 0 THEN v.total_duration_minutes
                            ELSE (SELECT COALESCE(SUM(s.duration_minutes), 0) 
                                FROM visit_service vs2 
                                JOIN service s ON vs2.service_id = s.id 
                                WHERE vs2.visit_id = v.id)
                        END
                    ), 0) AS total_dur,
                    COALESCE(AVG(
                        CASE 
                            WHEN v.total_duration_minutes > 0 THEN v.total_duration_minutes
                            ELSE (SELECT COALESCE(SUM(s.duration_minutes), 0) 
                                FROM visit_service vs2 
                                JOIN service s ON vs2.service_id = s.id 
                                WHERE vs2.visit_id = v.id)
                        END
                    ), 0) AS avg_dur
                FROM visit v
                WHERE v.customer_id = ?
            """, (c_id,))
            stat = cursor.fetchone()
            
            visit_count = stat[0] if stat else 0
            total_amt = stat[1] if stat else 0
            avg_amt = int(stat[2]) if stat else 0
            total_dur = int(stat[3]) if stat else 0
            avg_dur = int(stat[4]) if stat else 0

            cursor.execute("""
                SELECT cat.id, cat.name, SUM(COALESCE(vs.quantity, 1))
                FROM visit_service vs
                JOIN visit v ON vs.visit_id = v.id
                JOIN service s ON vs.service_id = s.id
                JOIN category cat ON s.category_id = cat.id
                WHERE v.customer_id = ?
                GROUP BY cat.id
                ORDER BY SUM(COALESCE(vs.quantity, 1)) DESC, cat.id ASC
            """, (c_id,))
            pref_rows = cursor.fetchall()

            preferences = []
            for cat_id, cat_name, total_cnt in pref_rows:
                cursor.execute("""
                    SELECT s.name, SUM(COALESCE(vs.quantity, 1))
                    FROM visit_service vs
                    JOIN visit v ON vs.visit_id = v.id
                    JOIN service s ON vs.service_id = s.id
                    WHERE v.customer_id = ? AND s.category_id = ?
                    GROUP BY s.id
                    ORDER BY SUM(COALESCE(vs.quantity, 1)) DESC, s.name ASC
                """, (c_id, cat_id))
                detail_rows = cursor.fetchall()
                details = [{"service": r[0], "count": r[1]} for r in detail_rows]

                preferences.append({
                    "category": cat_name,
                    "count": total_cnt,
                    "details": details
                })

            return {
                "total_visits": visit_count,
                "total_amount": total_amt,
                "avg_amount": avg_amt,
                "total_duration": total_dur,
                "avg_duration": avg_dur,
                "preferences": preferences
            }
        except Exception as e:
            print(f"[DB Error] get_customer_stats: {e}")
            return {
                "total_visits": 0, "total_amount": 0, "avg_amount": 0,
                "total_duration": 0, "avg_duration": 0, "preferences": []
            }
        finally:
            conn.close()

    # -------------------------------------------------------------
    # Sales Cancel (결제 취소) 헬퍼
    # -------------------------------------------------------------
    def get_sales_cancel_list(self, query: str = "", date_str: str = ""):
        """결제 취소 화면용 목록 조회"""
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
                        SELECT GROUP_CONCAT(
                            CASE 
                                WHEN COALESCE(vs.quantity, 1) > 1 THEN s.name || ' (' || vs.quantity || '개)'
                                ELSE s.name 
                            END, '|||') 
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
                    svc_list = [s.strip() for s in raw_services.split('|||') if s.strip()]
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
                    "visit_date": r[7],
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
        """결제 취소 트랜잭션"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION;")

            cursor.execute("SELECT customer_id FROM visit WHERE id = ?", (visit_id,))
            row = cursor.fetchone()
            if not row:
                conn.rollback()
                return False, "존재하지 않는 결제 내역입니다."
            customer_id = row[0]

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

            net_point_change = used_point - earned_point
            cursor.execute("""
                UPDATE customer
                SET point = MAX(0, point + ?), updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND is_active = 1
            """, (net_point_change, customer_id))

            cursor.execute("DELETE FROM visit_service WHERE visit_id = ?", (visit_id,))
            cursor.execute("DELETE FROM payment WHERE visit_id = ?", (visit_id,))
            cursor.execute("DELETE FROM point_history WHERE visit_id = ?", (visit_id,))
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
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN TRANSACTION;")

            for idx, cat in enumerate(categories_data):
                cat_id = cat.get("id")
                name = cat["name"]
                
                if name == "선결제" or cat.get("is_system") == 1:
                    is_active = 1
                else:
                    is_active = 0 if cat.get("deleted", False) else 1

                display_order = idx

                if cat_id is None:
                    cursor.execute("""
                        INSERT INTO category (name, display_order, is_active, is_system)
                        VALUES (?, ?, ?, ?)
                    """, (name, display_order, is_active, 1 if name == "선결제" else 0))
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
                cat_deleted = cat.get("deleted", False) and cat_name != "선결제"

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
        """직원 삭제 처리 (과거 매출 통계 보존 + 개인 연락처 익명화)"""
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return False

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 이름은 변경하지 않고 position을 '퇴사'로 변경 (조회 시 '이름 (퇴사)'로 자동 포맷팅됨)
            cursor.execute("""
                UPDATE user 
                SET is_active = 0,
                    phone = '',
                    position = '퇴사',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND is_active = 1
            """, (user_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"[DB Error] delete_designer: {e}")
            return False
        finally:
            conn.close()

    # -------------------------------------------------------------
    # 매출 통계 분석 헬퍼 메서드
    # -------------------------------------------------------------
    def get_daily_sales_analysis(self):
        """금일 매출 분석 4종 KPI 카드, 결제 수단별 금액/비율, 전월 대비 매출 비교 및 TOP3 시술 집계"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0), COUNT(id)
                FROM visit
                WHERE strftime('%Y-%m-%d', visited_at) = strftime('%Y-%m-%d', 'now', 'localtime')
            """)
            today_row = cursor.fetchone()
            today_sales = today_row[0]
            today_visitors = today_row[1]
            today_customer_spend = int(today_sales / today_visitors) if today_visitors > 0 else 0

            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0), COUNT(id)
                FROM visit
                WHERE strftime('%Y-%m-%d', visited_at) = strftime('%Y-%m-%d', 'now', 'localtime', '-1 day')
            """)
            yesterday_row = cursor.fetchone()
            yesterday_sales = yesterday_row[0]
            yesterday_visitors = yesterday_row[1]

            cursor.execute("""
                SELECT COUNT(DISTINCT strftime('%Y-%m-%d', visited_at)),
                       COALESCE(SUM(total_amount), 0)
                FROM visit
            """)
            total_days_row = cursor.fetchone()
            active_days = total_days_row[0] or 1
            all_sales = total_days_row[1]
            avg_daily_sales = int(all_sales / active_days) if active_days > 0 else 0

            today_payments = {"카드": 0, "현금": 0, "포인트": 0}

            cursor.execute("""
                SELECT 
                    p.payment_method,
                    COALESCE(SUM(p.amount), 0)
                FROM payment p
                JOIN visit v ON p.visit_id = v.id
                WHERE strftime('%Y-%m-%d', v.visited_at) = strftime('%Y-%m-%d', 'now', 'localtime')
                GROUP BY p.payment_method
            """)
            for row in cursor.fetchall():
                pm = (row[0] or "").lower()
                amt = row[1] or 0
                if "카드" in pm or "card" in pm:
                    today_payments["카드"] += amt
                elif "현금" in pm or "cash" in pm:
                    today_payments["현금"] += amt
                elif "포인트" in pm or "선결제" in pm or "point" in pm or "적립" in pm:
                    today_payments["포인트"] += amt
                else:
                    today_payments["카드"] += amt

            cursor.execute("""
                SELECT COALESCE(SUM(used_point), 0)
                FROM visit
                WHERE strftime('%Y-%m-%d', visited_at) = strftime('%Y-%m-%d', 'now', 'localtime')
            """)
            v_used_point = cursor.fetchone()[0] or 0

            cursor.execute("""
                SELECT COALESCE(SUM(ABS(amount)), 0)
                FROM point_history ph
                JOIN visit v ON ph.visit_id = v.id
                WHERE ph.type = 'USE' AND strftime('%Y-%m-%d', v.visited_at) = strftime('%Y-%m-%d', 'now', 'localtime')
            """)
            history_used_point = cursor.fetchone()[0] or 0

            point_amt = max(today_payments["포인트"], v_used_point, history_used_point)
            today_payments["포인트"] = point_amt

            t_card = today_payments["카드"]
            t_cash = today_payments["현금"]
            t_point = today_payments["포인트"]
            t_sum = t_card + t_cash + t_point

            card_share = round((t_card / t_sum) * 100, 1) if t_sum > 0 else 0.0
            cash_share = round((t_cash / t_sum) * 100, 1) if t_sum > 0 else 0.0
            point_share = round((t_point / t_sum) * 100, 1) if t_sum > 0 else 0.0

            now = datetime.now()
            curr_year = now.year
            curr_month = now.month
            curr_day = now.day

            this_month_start = f"{curr_year:04d}-{curr_month:02d}-01"
            this_month_end = f"{curr_year:04d}-{curr_month:02d}-{curr_day:02d}"

            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0)
                FROM visit
                WHERE strftime('%Y-%m-%d', visited_at) BETWEEN ? AND ?
            """, (this_month_start, this_month_end))
            this_month_sales = cursor.fetchone()[0]

            if curr_month == 1:
                prev_year = curr_year - 1
                prev_month = 12
            else:
                prev_year = curr_year
                prev_month = curr_month - 1

            prev_month_start = f"{prev_year:04d}-{prev_month:02d}-01"
            max_days_prev = calendar.monthrange(prev_year, prev_month)[1]
            target_prev_day = min(curr_day, max_days_prev)
            prev_month_end = f"{prev_year:04d}-{prev_month:02d}-{target_prev_day:02d}"

            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0)
                FROM visit
                WHERE strftime('%Y-%m-%d', visited_at) BETWEEN ? AND ?
            """, (prev_month_start, prev_month_end))
            prev_month_sales = cursor.fetchone()[0]

            if prev_month_sales > 0:
                diff_percent = round(((this_month_sales - prev_month_sales) / prev_month_sales) * 100, 1)
            else:
                diff_percent = 100.0 if this_month_sales > 0 else 0.0

            cursor.execute("""
                SELECT 
                    s.name,
                    SUM(COALESCE(vs.quantity, 1)) AS total_qty,
                    SUM(vs.price * COALESCE(vs.quantity, 1)) AS total_price
                FROM visit_service vs
                JOIN service s ON vs.service_id = s.id
                JOIN visit v ON vs.visit_id = v.id
                WHERE strftime('%Y-%m-%d', v.visited_at) = strftime('%Y-%m-%d', 'now', 'localtime')
                GROUP BY s.id
                ORDER BY total_qty DESC, total_price DESC
                LIMIT 3
            """)
            top3_rows = cursor.fetchall()
            top3_list = [{
                "name": r[0],
                "count": r[1],
                "price": r[2]
            } for r in top3_rows]

            return {
                "today_sales": today_sales,
                "today_visitors": today_visitors,
                "today_customer_spend": today_customer_spend,
                "yesterday_sales": yesterday_sales,
                "yesterday_visitors": yesterday_visitors,
                "avg_daily_sales": avg_daily_sales,
                "today_payments": {
                    "card_amount": t_card,
                    "card_share": card_share,
                    "cash_amount": t_cash,
                    "cash_share": cash_share,
                    "point_amount": t_point,
                    "point_share": point_share,
                },
                "this_month": curr_month,
                "this_month_sales": this_month_sales,
                "prev_month": prev_month,
                "prev_month_sales": prev_month_sales,
                "diff_percent": diff_percent,
                "top3": top3_list
            }
        except Exception as e:
            print(f"[DB Error] get_daily_sales_analysis: {e}")
            return {
                "today_sales": 0, "today_visitors": 0, "today_customer_spend": 0,
                "yesterday_sales": 0, "yesterday_visitors": 0,
                "avg_daily_sales": 0,
                "today_payments": {
                    "card_amount": 0, "card_share": 0.0,
                    "cash_amount": 0, "cash_share": 0.0,
                    "point_amount": 0, "point_share": 0.0,
                },
                "this_month": 1, "this_month_sales": 0,
                "prev_month": 12, "prev_month_sales": 0,
                "diff_percent": 0.0, "top3": []
            }
        finally:
            conn.close()

    def get_period_sales_analysis(self, start_date: str, end_date: str, designer_id: str = "all"):
        """기간별 상세 매출 분석 (1일=시간대별, ~31일=일별, ~180일=주별, ~1095일=월별, 그이상=년도별)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            params = [start_date, end_date]
            is_all_designers = not designer_id or designer_id == "all"
            designer_where = ""
            if not is_all_designers:
                designer_where = " AND v.user_id = ? "
                params.append(designer_id)

            # 1. 총매출, 방문수, 총 시술시간, 사용 포인트를 단일 쿼리로 통합 집계
            cursor.execute(f"""
                SELECT 
                    COALESCE(SUM(v.total_amount), 0),
                    COUNT(DISTINCT v.id),
                    COALESCE(SUM(v.total_duration_minutes), 0),
                    COALESCE(SUM(v.used_point), 0)
                FROM visit v
                WHERE strftime('%Y-%m-%d', v.visited_at) BETWEEN ? AND ? {designer_where}
            """, params)
            sales_row = cursor.fetchone()
            total_sales = sales_row[0]
            visit_count = sales_row[1]
            total_duration = sales_row[2]
            v_used_point = sales_row[3]

            d1 = datetime.strptime(start_date, "%Y-%m-%d")
            d2 = datetime.strptime(end_date, "%Y-%m-%d")
            days_span = (d2 - d1).days + 1
            avg_daily_sales = int(total_sales / days_span) if days_span > 0 else 0

            # 2. 디자이너 기여도 계산 (전체 조회 시 중복 쿼리 생략)
            if is_all_designers:
                contribution = 100.0 if total_sales > 0 else 0.0
            else:
                cursor.execute("""
                    SELECT COALESCE(SUM(total_amount), 0)
                    FROM visit
                    WHERE strftime('%Y-%m-%d', visited_at) BETWEEN ? AND ?
                """, (start_date, end_date))
                all_store_sales = cursor.fetchone()[0]
                if all_store_sales > 0:
                    contribution = round((total_sales / all_store_sales) * 100, 1)
                else:
                    contribution = 100.0 if total_sales > 0 else 0.0

            # 3. 결제 수단별 합산
            payments = {"카드": 0, "현금": 0, "포인트": 0}
            cursor.execute(f"""
                SELECT 
                    p.payment_method,
                    COALESCE(SUM(p.amount), 0)
                FROM payment p
                JOIN visit v ON p.visit_id = v.id
                WHERE strftime('%Y-%m-%d', v.visited_at) BETWEEN ? AND ? {designer_where}
                GROUP BY p.payment_method
            """, params)

            for row in cursor.fetchall():
                pm = (row[0] or "").lower()
                amt = row[1] or 0
                if "카드" in pm or "card" in pm:
                    payments["카드"] += amt
                elif "현금" in pm or "cash" in pm:
                    payments["현금"] += amt
                elif "포인트" in pm or "선결제" in pm or "point" in pm or "적립" in pm:
                    payments["포인트"] += amt
                else:
                    payments["카드"] += amt

            if v_used_point > payments["포인트"]:
                payments["포인트"] = v_used_point

            # 4. 조회 기간에 따른 그래프 추이 집계
            trend_data = []

            if days_span == 1:
                query_params = [start_date]
                if not is_all_designers:
                    query_params.append(designer_id)

                cursor.execute(f"""
                    SELECT strftime('%H시', v.visited_at) as hr, COALESCE(SUM(v.total_amount), 0)
                    FROM visit v
                    WHERE strftime('%Y-%m-%d', v.visited_at) = ? {designer_where}
                    GROUP BY hr ORDER BY hr ASC
                """, query_params)
                for r in cursor.fetchall():
                    trend_data.append({"label": r[0], "amount": r[1]})

            elif days_span <= 31:
                cursor.execute(f"""
                    SELECT strftime('%Y-%m-%d', v.visited_at) as dt, COALESCE(SUM(v.total_amount), 0)
                    FROM visit v
                    WHERE strftime('%Y-%m-%d', v.visited_at) BETWEEN ? AND ? {designer_where}
                    GROUP BY dt ORDER BY dt ASC
                """, params)
                rows = dict(cursor.fetchall())
                curr = d1
                while curr <= d2:
                    dt_str = curr.strftime("%Y-%m-%d")
                    trend_data.append({"label": dt_str[5:], "amount": rows.get(dt_str, 0)})
                    curr += timedelta(days=1)

            elif days_span <= 180:
                cursor.execute(f"""
                    SELECT strftime('%Y-%m월-%W주', v.visited_at) as wk, COALESCE(SUM(v.total_amount), 0)
                    FROM visit v
                    WHERE strftime('%Y-%m-%d', v.visited_at) BETWEEN ? AND ? {designer_where}
                    GROUP BY wk ORDER BY wk ASC
                """, params)
                for r in cursor.fetchall():
                    trend_data.append({"label": r[0][2:], "amount": r[1]})

            elif days_span <= 1095:
                cursor.execute(f"""
                    SELECT strftime('%Y-%m월', v.visited_at) as mn, COALESCE(SUM(v.total_amount), 0)
                    FROM visit v
                    WHERE strftime('%Y-%m-%d', v.visited_at) BETWEEN ? AND ? {designer_where}
                    GROUP BY mn ORDER BY mn ASC
                """, params)
                for r in cursor.fetchall():
                    trend_data.append({"label": r[0][2:], "amount": r[1]})

            else:
                cursor.execute(f"""
                    SELECT strftime('%Y년', v.visited_at) as yr, COALESCE(SUM(v.total_amount), 0)
                    FROM visit v
                    WHERE strftime('%Y-%m-%d', v.visited_at) BETWEEN ? AND ? {designer_where}
                    GROUP BY yr ORDER BY yr ASC
                """, params)
                for r in cursor.fetchall():
                    trend_data.append({"label": r[0], "amount": r[1]})

            return {
                "total_sales": total_sales,
                "visit_count": visit_count,
                "avg_daily_sales": avg_daily_sales,
                "total_duration": total_duration,
                "contribution": contribution,
                "payments": payments,
                "days_span": days_span,
                "trend_data": trend_data
            }
        except Exception as e:
            print(f"[DB Error] get_period_sales_analysis: {e}")
            return {
                "total_sales": 0, "visit_count": 0, "avg_daily_sales": 0,
                "total_duration": 0, "contribution": 0.0,
                "payments": {"카드": 0, "현금": 0, "포인트": 0},
                "days_span": 1, "trend_data": []
            }
        finally:
            conn.close()

    def get_customers_csv_data(self):
        """고객 정보 및 동의 내역 CSV 내보내기용 데이터 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    c.id AS 고객번호,
                    c.name AS 고객명,
                    c.phone AS 전화번호,
                    c.point AS 보유포인트,
                    CASE WHEN c.is_consent = 1 THEN '동의' ELSE '미동의' END AS 필수동의여부,
                    COALESCE(strftime('%Y-%m-%d %H:%M:%S', c.consent_at), '-') AS 필수동의일시,
                    CASE WHEN c.is_marketing_consent = 1 THEN '동의' ELSE '미동의' END AS 마케팅동의여부,
                    COALESCE(strftime('%Y-%m-%d %H:%M:%S', c.marketing_consent_at), '-') AS 마케팅동의일시,
                    c.memo AS 특이사항메모,
                    strftime('%Y-%m-%d %H:%M:%S', c.created_at) AS 최초등록일시
                FROM customer c
                WHERE c.is_active = 1
                ORDER BY c.id ASC
            """)
            return cursor.fetchall()
        except Exception as e:
            print(f"[DB Error] get_customers_csv_data: {e}")
            return []
        finally:
            conn.close()

    def get_sales_csv_data(self):
        """매출 및 시술 결제 내역 CSV 내보내기용 데이터 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    v.id AS 방문번호,
                    c.name AS 고객명,
                    c.phone AS 전화번호,
                    COALESCE(u.name, '-') AS 담당디자이너,
                    v.total_amount AS 결제금액,
                    v.used_point AS 사용포인트,
                    v.total_duration_minutes AS 소요시간_분,
                    COALESCE((
                        SELECT GROUP_CONCAT(
                            CASE 
                                WHEN COALESCE(vs.quantity, 1) > 1 THEN s.name || ' (' || vs.quantity || '개)'
                                ELSE s.name 
                            END, ', ') 
                        FROM visit_service vs 
                        JOIN service s ON vs.service_id = s.id 
                        WHERE vs.visit_id = v.id
                    ), '-') AS 시술항목,
                    COALESCE((
                        SELECT GROUP_CONCAT(DISTINCT payment_method) 
                        FROM payment 
                        WHERE visit_id = v.id
                    ), '-') AS 결제수단,
                    strftime('%Y-%m-%d %H:%M:%S', v.visited_at) AS 방문결제일시
                FROM visit v
                JOIN customer c ON v.customer_id = c.id
                LEFT JOIN user u ON v.user_id = u.id
                ORDER BY v.visited_at DESC, v.id DESC
            """)
            return cursor.fetchall()
        except Exception as e:
            print(f"[DB Error] get_sales_csv_data: {e}")
            return []
        finally:
            conn.close()