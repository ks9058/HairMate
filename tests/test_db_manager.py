import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

# 프로젝트 루트 경로 추가 (직접 실행 및 unittest 모듈 실행 모두 지원)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.db_manager import DBManager


class TestDBManager(unittest.TestCase):
    """DBManager 핵심 기능 단위 테스트 (정상값 + 경계값)"""

    def setUp(self):
        """각 테스트마다 독립된 임시 SQLite DB 생성"""
        self._prev_db_path = os.environ.get("DB_PATH")
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db_path = tmp.name
        tmp.close()

        os.environ["DB_PATH"] = self.temp_db_path
        self.db = DBManager()

    def tearDown(self):
        """테스트 종료 후 임시 DB 파일 및 환경변수 정리"""
        if self._prev_db_path is None:
            os.environ.pop("DB_PATH", None)
        else:
            os.environ["DB_PATH"] = self._prev_db_path

        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except OSError:
                pass

    # =========================================================================
    # 1. DB 초기화 및 설정(Settings) 테스트
    # =========================================================================
    def test_init_db_schema_and_defaults(self):
        """[정상/경계] 10개 테이블 생성, 기본 설정값 및 init_db 중복 호출 멱등성 검증"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {row[0] for row in cursor.fetchall()}

        expected_tables = {
            "customer", "user", "category", "service",
            "visit", "visit_service", "payment",
            "point_history", "prepaid_history", "settings"
        }
        self.assertTrue(expected_tables.issubset(tables))

        # 기본 포인트 적립률 확인
        self.assertEqual(self.db.get_setting("point_rate_general"), "10")
        self.assertEqual(self.db.get_setting("point_rate_prepaid"), "20")

        # 존재하지 않는 키 조회 시 default 반환 (경계값)
        self.assertEqual(self.db.get_setting("unknown_key", default="기본값"), "기본값")

        # 설정 저장 및 덮어쓰기(UPSERT)
        self.assertTrue(self.db.set_setting("last_backup_date", "2026-11-14"))
        self.assertEqual(self.db.get_setting("last_backup_date"), "2026-11-14")
        self.assertTrue(self.db.set_setting("last_backup_date", "2026-11-15"))
        self.assertEqual(self.db.get_setting("last_backup_date"), "2026-11-15")

        # init_db() 재호출 시 '선결제' 카테고리가 중복 생성되지 않는지 확인
        self.db.init_db()
        cats, _ = self.db.fetch_active_categories_and_services()
        prepaid_cats = [c for c in cats if c["name"] == "선결제"]
        self.assertEqual(len(prepaid_cats), 1)
        self.assertEqual(prepaid_cats[0]["is_system"], 1)

    # =========================================================================
    # 2. 고객(Customer) CRUD 및 개인정보 익명화 테스트
    # =========================================================================
    def test_customer_crud_and_boundary_cases(self):
        """[정상/경계] 고객 등록, 중복 전화번호 차단, 수정, 동의 변경, 삭제 익명화 및 재등록"""
        # 정상 등록
        ok, msg = self.db.add_customer("김지민", "010-1234-5678", "두피 민감", is_consent=1, is_marketing_consent=1)
        self.assertTrue(ok)
        self.assertEqual(msg, "")

        # 경계값: 동일 전화번호 중복 등록 차단
        ok_dup, msg_dup = self.db.add_customer("박서준", "010-1234-5678")
        self.assertFalse(ok_dup)
        self.assertIn("이미 등록된", msg_dup)

        # 두 번째 고객 등록
        ok2, _ = self.db.add_customer("이수진", "010-9876-5432", "", is_consent=1, is_marketing_consent=0)
        self.assertTrue(ok2)

        customers = self.db.get_all_customers()
        self.assertEqual(len(customers), 2)
        c1 = next(c for c in customers if c["name"] == "김지민")
        c2 = next(c for c in customers if c["name"] == "이수진")
        self.assertEqual(c1["prepaid_balance"], 0)

        # 경계값: 본인 전화번호 유지하며 메모/이름만 수정 시 허용
        ok_upd1, _ = self.db.update_customer(c1["id"], "김지민(수정)", "010-1234-5678", "염색 선호")
        self.assertTrue(ok_upd1)

        # 경계값: 타인 전화번호로 수정 시 차단
        ok_upd2, msg_upd2 = self.db.update_customer(c1["id"], "김지민(수정)", "010-9876-5432", "염색 선호")
        self.assertFalse(ok_upd2)
        self.assertIn("이미 다른 고객", msg_upd2)

        # 경계값: 유효하지 않은 고객 ID 입력 방어
        ok_invalid, _ = self.db.update_customer("invalid_id", "테스트", "010-0000-1111", "")
        self.assertFalse(ok_invalid)
        self.assertFalse(self.db.delete_customer("invalid_id"))

        # 동의 상태 업데이트 및 검색 조회
        self.assertTrue(self.db.update_customer_consent(c2["id"], is_consent=1, is_marketing_consent=1))
        consented = self.db.get_consented_customers(query="이수진")
        self.assertEqual(len(consented), 1)
        self.assertEqual(consented[0]["is_marketing_consent"], 1)

        # 고객 삭제 시 개인식별정보 익명화 및 활성 목록 제외 검증
        self.assertTrue(self.db.delete_customer(c1["id"]))
        active_customers = self.db.get_all_customers()
        self.assertEqual(len(active_customers), 1)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name, phone, memo, point, prepaid_balance, is_active FROM customer WHERE id = ?",
                (c1["id"],)
            )
            row = cursor.fetchone()
            self.assertEqual(row[0], "(삭제된 고객)")
            self.assertEqual(row[1], f"000-0000-{c1['id']:04d}")
            self.assertEqual(row[2], "")
            self.assertEqual(row[3], 0)
            self.assertEqual(row[4], 0)
            self.assertEqual(row[5], 0)

        # 경계값: 삭제된 고객과 동일한 전화번호로 신규 고객 재등록 허용 확인
        ok_re, _ = self.db.add_customer("신규김지민", "010-1234-5678")
        self.assertTrue(ok_re)

    # =========================================================================
    # 3. 카테고리 및 시술 메뉴 관리 테스트
    # =========================================================================
    def test_categories_and_services_save_and_system_protection(self):
        """[정상/경계] 카테고리/시술 추가·삭제 저장 및 시스템 카테고리('선결제') 삭제 방어"""
        cats, svcs = self.db.fetch_active_categories_and_services()

        # 신규 카테고리 '커트' 및 시술 추가
        cats.append({"id": None, "name": "커트", "is_system": 0, "edited": False, "deleted": False})
        svcs["커트"] = [
            {"id": None, "name": "여성 커트", "price": 25000, "edited": False, "deleted": False},
            {"id": None, "name": "남성 커트", "price": 20000, "edited": False, "deleted": False},
        ]

        # 경계값: 시스템 카테고리 '선결제'에 deleted=True 설정 시도
        for c in cats:
            if c["name"] == "선결제":
                c["deleted"] = True

        ok, _ = self.db.save_all_changes(cats, svcs)
        self.assertTrue(ok)

        loaded_cats, loaded_svcs = self.db.fetch_active_categories_and_services()
        cat_names = [c["name"] for c in loaded_cats]
        self.assertIn("선결제", cat_names)  # 삭제 방어 확인
        self.assertIn("커트", cat_names)
        self.assertEqual(len(loaded_svcs["커트"]), 2)

        # 일반 카테고리 삭제 시 하위 시술까지 비활성화 확인
        for c in loaded_cats:
            if c["name"] == "커트":
                c["deleted"] = True
        ok_del, _ = self.db.save_all_changes(loaded_cats, loaded_svcs)
        self.assertTrue(ok_del)

        after_cats, after_svcs = self.db.fetch_active_categories_and_services()
        self.assertNotIn("커트", [c["name"] for c in after_cats])
        self.assertNotIn("커트", after_svcs)

    # =========================================================================
    # 4. 디자이너(User) 관리 테스트
    # =========================================================================
    def test_designer_crud_and_soft_delete(self):
        """[정상/경계] 디자이너 등록·수정·퇴사(소프트 삭제) 처리 검증"""
        ok, _ = self.db.add_designer("정원장", "010-1111-2222", "원장")
        self.assertTrue(ok)

        designers = self.db.get_all_designers()
        self.assertEqual(len(designers), 1)
        d_id = designers[0]["id"]

        self.assertTrue(self.db.update_designer(d_id, "정대표", "010-1111-3333", "대표원장")[0])
        updated = self.db.get_all_designers()[0]
        self.assertEqual(updated["name"], "정대표")

        # 퇴사 처리: 활성 목록에서는 제외되지만 DB 내 이름 보존 및 연락처 파기
        self.assertTrue(self.db.delete_designer(d_id))
        self.assertEqual(len(self.db.get_all_designers()), 0)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, phone, position, is_active FROM user WHERE id = ?", (d_id,))
            row = cursor.fetchone()
            self.assertEqual(row, ("정대표", "", "퇴사", 0))

        self.assertFalse(self.db.delete_designer("not_an_int"))

    # =========================================================================
    # 5. 매출 결제 등록, 툴팁 목록, 선결제/포인트 적립·차감 및 결제 취소 테스트
    # =========================================================================
    def _prepare_sale_fixtures(self):
        """결제/통계 테스트용 고객, 디자이너, 시술 2종 사전 생성"""
        self.db.add_customer("홍길동", "010-5555-6666", "초기메모")
        customer = self.db.get_all_customers()[0]

        self.db.add_designer("한디자이너", "010-7777-8888", "실장")
        designer = self.db.get_all_designers()[0]

        cats, svcs = self.db.fetch_active_categories_and_services()
        cats.append({"id": None, "name": "펌", "is_system": 0, "edited": False, "deleted": False})
        svcs["펌"] = [
            {"id": None, "name": "셋팅펌", "price": 100000, "edited": False, "deleted": False},
            {"id": None, "name": "클리닉", "price": 50000, "edited": False, "deleted": False},
        ]
        self.db.save_all_changes(cats, svcs)
        _, saved_svcs = self.db.fetch_active_categories_and_services()
        return customer, designer, saved_svcs["펌"]

    def test_record_sale_and_cancel_transaction_with_point_guard(self):
        """[정상/경계] 복합 결제 등록, 툴팁 목록(시술·결제수단 금액), 결제 취소 및 포인트 음수 방지 검증"""
        customer, designer, services = self._prepare_sale_fixtures()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1차 결제: 150,000원 결제 -> 15,000P 적립
        cart_1 = [
            {"id": services[0]["id"], "price": 100000, "qty": 1},
            {"id": services[1]["id"], "price": 50000, "qty": 1},
        ]
        payments_1 = [
            {"amount": 100000, "method": "카드"},
            {"amount": 50000, "method": "현금"},
        ]
        ok_sale1 = self.db.record_sale(
            customer_id=customer["id"],
            user_id=designer["id"],
            duration_minutes=120,
            total_amount=150000,
            used_point=0,
            earned_point=15000,
            visited_at_str=now_str,
            memo="1차 시술 완료",
            cart_items=cart_1,
            payments_history=payments_1
        )
        self.assertTrue(ok_sale1)

        c_after1 = self.db.get_all_customers()[0]
        self.assertEqual(c_after1["point"], 15000)
        self.assertEqual(c_after1["memo"], "1차 시술 완료")

        # 방문 이력 및 통계 확인
        history = self.db.get_customer_visit_history(customer["id"])
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["amount"], "150,000")

        stats = self.db.get_customer_stats(customer["id"])
        self.assertEqual(stats["total_visits"], 1)
        self.assertEqual(stats["total_amount"], 150000)
        self.assertEqual(stats["total_duration"], 120)
        self.assertEqual(stats["preferences"][0]["category"], "펌")

        # 2차 결제: 기존 적립금 15,000P 전액 사용 (현재 보유 포인트 0P 상태)
        ok_sale2 = self.db.record_sale(
            customer_id=customer["id"],
            user_id=designer["id"],
            duration_minutes=60,
            total_amount=50000,
            used_point=15000,
            earned_point=0,
            visited_at_str=now_str,
            memo="포인트 전액 사용",
            cart_items=[{"id": services[1]["id"], "price": 50000, "qty": 1}],
            payments_history=[{"amount": 35000, "method": "카드"}, {"amount": 15000, "method": "포인트"}]
        )
        self.assertTrue(ok_sale2)
        self.assertEqual(self.db.get_all_customers()[0]["point"], 0)

        cancel_list = self.db.get_sales_cancel_list(query="홍길동")
        self.assertEqual(len(cancel_list), 2)

        # ORDER BY visited_at DESC, v.id DESC 이므로 index 0이 2차 결제, index 1이 1차 결제
        sale_2 = cancel_list[0]
        sale_1 = cancel_list[1]

        # 툴팁용 시술 목록 및 결제수단별 금액 포맷 검증
        self.assertEqual(sale_1["services_list"], ["셋팅펌", "클리닉"])
        self.assertEqual(sale_1["payment_methods_list"], ["카드 : 100,000원", "현금 : 50,000원"])
        self.assertEqual(sale_2["payment_methods_list"], ["카드 : 35,000원", "포인트 : 15,000P"])

        # 경계값 테스트: 이미 15,000P를 다 써서 잔액이 0P인 상태에서 15,000P가 적립됐던 1차 결제를 먼저 취소
        # 잔액이 음수(-15000)가 되지 않고 MAX(0, ...)에 의해 0으로 방어되어야 함
        ok_c1, _ = self.db.cancel_sale_transaction(sale_1["visit_id"])
        self.assertTrue(ok_c1)
        self.assertEqual(self.db.get_all_customers()[0]["point"], 0)

        # 이어서 15,000P를 사용했던 2차 결제 취소 시 사용 포인트 15,000P 원복 확인
        ok_c2, _ = self.db.cancel_sale_transaction(sale_2["visit_id"])
        self.assertTrue(ok_c2)
        self.assertEqual(self.db.get_all_customers()[0]["point"], 15000)

        # 경계값: 존재하지 않는 visit_id 취소 요청 방어
        ok_none, msg_none = self.db.cancel_sale_transaction(999999)
        self.assertFalse(ok_none)
        self.assertIn("존재하지 않는", msg_none)

    def test_prepaid_charge_use_tooltip_and_cancel_restoration(self):
        """[정상/경계] 선결제 충전·사용, 수량 표기 툴팁, 결제 취소 시 선결제 잔액 원복 검증"""
        customer, designer, services = self._prepare_sale_fixtures()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. 선결제 100,000원 충전
        ok_charge = self.db.record_sale(
            customer_id=customer["id"],
            user_id=designer["id"],
            duration_minutes=0,
            total_amount=100000,
            used_point=0,
            earned_point=0,
            visited_at_str=now_str,
            memo="선결제 충전",
            cart_items=[],
            payments_history=[{"amount": 100000, "method": "카드"}],
            used_prepaid=0,
            charged_prepaid=100000
        )
        self.assertTrue(ok_charge)
        self.assertEqual(self.db.get_all_customers()[0]["prepaid_balance"], 100000)

        # 2. 선결제 30,000원 + 카드 70,000원 복합 결제 (클리닉 2개)
        ok_use = self.db.record_sale(
            customer_id=customer["id"],
            user_id=designer["id"],
            duration_minutes=60,
            total_amount=100000,
            used_point=0,
            earned_point=0,
            visited_at_str=now_str,
            memo="선결제 일부 사용",
            cart_items=[{"id": services[1]["id"], "price": 50000, "qty": 2}],
            payments_history=[
                {"amount": 30000, "method": "선결제"},
                {"amount": 70000, "method": "카드"}
            ],
            used_prepaid=30000,
            charged_prepaid=0
        )
        self.assertTrue(ok_use)
        self.assertEqual(self.db.get_all_customers()[0]["prepaid_balance"], 70000)

        cancel_list = self.db.get_sales_cancel_list(query="홍길동")
        use_sale = cancel_list[0]
        charge_sale = cancel_list[1]

        # 수량 표기("클리닉 (2개)") 및 선결제 금액 툴팁 포맷 확인
        self.assertEqual(use_sale["services_list"], ["클리닉 (2개)"])
        self.assertEqual(use_sale["payment_methods_list"], ["선결제 : 30,000원", "카드 : 70,000원"])

        # 선결제 사용 건 취소 시 차감된 30,000원 원복 확인 (70,000 -> 100,000)
        ok_cancel_use, _ = self.db.cancel_sale_transaction(use_sale["visit_id"])
        self.assertTrue(ok_cancel_use)
        self.assertEqual(self.db.get_all_customers()[0]["prepaid_balance"], 100000)

        # 선결제 충전 건 취소 시 충전된 100,000원 회수 확인 (100,000 -> 0)
        ok_cancel_charge, _ = self.db.cancel_sale_transaction(charge_sale["visit_id"])
        self.assertTrue(ok_cancel_charge)
        self.assertEqual(self.db.get_all_customers()[0]["prepaid_balance"], 0)

    def test_record_sale_rollback_on_invalid_customer(self):
        """[경계] 존재하지 않는 고객 ID로 결제 시 트랜잭션 롤백 보장 검증"""
        _, designer, services = self._prepare_sale_fixtures()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        ok = self.db.record_sale(
            customer_id=999999,
            user_id=designer["id"],
            duration_minutes=30,
            total_amount=50000,
            used_point=0,
            earned_point=5000,
            visited_at_str=now_str,
            memo="",
            cart_items=[{"id": services[1]["id"], "price": 50000, "qty": 1}],
            payments_history=[{"amount": 50000, "method": "카드"}]
        )
        self.assertFalse(ok)
        self.assertEqual(len(self.db.get_sales_cancel_list()), 0)

    # =========================================================================
    # 6. 매출 통계 분석 및 CSV 조회 테스트
    # =========================================================================
    def test_sales_analytics_empty_and_populated(self):
        """[정상/경계] 빈 DB 매출 분석(ZeroDivision 방어) 및 기간별·디자이너별 집계·CSV 조회 검증"""
        # 경계값: 매출이 0건인 초기 DB 상태
        empty_daily = self.db.get_daily_sales_analysis()
        self.assertEqual(empty_daily["today_sales"], 0)
        self.assertEqual(empty_daily["today_customer_spend"], 0)
        self.assertEqual(empty_daily["today_payments"]["card_share"], 0.0)
        self.assertEqual(empty_daily["today_payments"]["prepaid_share"], 0.0)

        today_str = datetime.now().strftime("%Y-%m-%d")
        empty_period = self.db.get_period_sales_analysis(today_str, today_str, designer_id="all")
        self.assertEqual(empty_period["total_sales"], 0)
        self.assertEqual(empty_period["contribution"], 0.0)

        # 데이터 1건 등록 후 정상 집계 확인
        customer, designer, services = self._prepare_sale_fixtures()
        now_dt_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.record_sale(
            customer_id=customer["id"],
            user_id=designer["id"],
            duration_minutes=90,
            total_amount=100000,
            used_point=0,
            earned_point=10000,
            visited_at_str=now_dt_str,
            memo="통계테스트",
            cart_items=[{"id": services[0]["id"], "price": 100000, "qty": 1}],
            payments_history=[{"amount": 100000, "method": "카드"}]
        )

        daily = self.db.get_daily_sales_analysis()
        self.assertEqual(daily["today_sales"], 100000)
        self.assertEqual(daily["today_visitors"], 1)
        self.assertEqual(daily["today_customer_spend"], 100000)
        self.assertEqual(daily["today_payments"]["card_share"], 100.0)
        self.assertEqual(daily["top3"][0]["name"], "셋팅펌")

        # 기간별 조회 (1일 시간대별 / 7일 일별)
        p_1day = self.db.get_period_sales_analysis(today_str, today_str, designer_id=str(designer["id"]))
        self.assertEqual(p_1day["total_sales"], 100000)
        self.assertEqual(p_1day["contribution"], 100.0)

        week_ago_str = (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d")
        p_7days = self.db.get_period_sales_analysis(week_ago_str, today_str, designer_id="all")
        self.assertEqual(len(p_7days["trend_data"]), 7)

        # CSV 내보내기 데이터 조회 확인
        cust_csv = self.db.get_customers_csv_data()
        sales_csv = self.db.get_sales_csv_data()
        self.assertEqual(len(cust_csv), 1)
        self.assertEqual(len(sales_csv), 1)
        self.assertEqual(sales_csv[0][1], "홍길동")


if __name__ == "__main__":
    unittest.main(verbosity=2)