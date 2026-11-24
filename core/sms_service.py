import hashlib
import hmac
import re
import secrets
from datetime import datetime, timezone
import requests
from PySide6.QtCore import QThread, Signal


DEFAULT_TEMPLATES = {
    "use": (
        "[{매장명}] 선결제 사용 안내\n"
        "■ 일시: {방문일시}\n"
        "■ 시술: {시술명}\n"
        "■ 사용금액: {사용금액}원\n"
        "■ 잔여금액: {잔여금액}원\n"
        "방문해 주셔서 감사합니다."
    ),
    "charge": (
        "[{매장명}] 선결제 충전 안내\n"
        "■ 일시: {방문일시}\n"
        "■ 충전금액: {충전금액}원\n"
        "■ 잔여금액: {잔여금액}원\n"
        "이용해 주셔서 감사합니다."
    ),
    "cancel_use": (
        "[{매장명}] 선결제 사용 취소 안내\n"
        "■ 취소일시: {취소일시}\n"
        "■ 원결제일: {방문일시}\n"
        "■ 복원금액: +{사용금액}원\n"
        "■ 잔여금액: {잔여금액}원\n"
        "정상적으로 취소 처리되었습니다."
    ),
    "cancel_charge": (
        "[{매장명}] 선결제 충전 취소 안내\n"
        "■ 취소일시: {취소일시}\n"
        "■ 원결제일: {방문일시}\n"
        "■ 취소금액: -{충전금액}원\n"
        "■ 잔여금액: {잔여금액}원\n"
        "정상적으로 취소 처리되었습니다."
    ),
}


def render_sms_template(template: str, context: dict) -> str:
    """템플릿 문구 변수 안전 치환"""
    result = template or ""
    for key, val in context.items():
        result = result.replace(f"{{{key}}}", str(val))
    return result


def build_prepaid_cancel_sms_payloads(db_manager, sale_data: dict) -> dict:
    """결제 취소 시 선결제 안내 문자 발송 조건 검증 및 최종 발송 페이로드 생성"""
    used_prepaid = int(sale_data.get("used_prepaid", 0) or 0)
    charged_prepaid = int(sale_data.get("charged_prepaid", 0) or 0)

    if used_prepaid <= 0 and charged_prepaid <= 0:
        return {"should_send": False}

    if db_manager.get_setting("sms_enabled", default="1") != "1":
        return {"should_send": False}

    api_key = db_manager.get_setting("sms_api_key", default="").strip()
    api_secret = db_manager.get_setting("sms_api_secret", default="").strip()
    sender_phone = db_manager.get_setting("sms_sender_phone", default="").strip()
    shop_name = db_manager.get_setting("shop_name", default="").strip() or "헤어살롱"

    customer_id = sale_data.get("customer_id")
    customer_name = sale_data.get("customer_name", "")
    customer_phone = (sale_data.get("customer_phone") or "").strip()

    if not api_key or not api_secret or not sender_phone or not customer_phone:
        return {"should_send": False}
    if customer_phone.startswith("000-0000-"):
        return {"should_send": False}

    is_active, final_prepaid = db_manager.get_customer_prepaid_status(customer_id)
    if not is_active:
        return {"should_send": False}

    cancel_time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    visit_date_str = (sale_data.get("visit_date") or "")[:16]
    service_str = sale_data.get("services") or "시술"

    context = {
        "매장명": shop_name,
        "고객명": customer_name,
        "취소일시": cancel_time_str,
        "방문일시": visit_date_str,
        "시술명": service_str,
        "사용금액": f"{used_prepaid:,}",
        "충전금액": f"{charged_prepaid:,}",
        "잔여금액": f"{final_prepaid:,}",
    }

    messages = []
    if used_prepaid > 0:
        tpl_use = (
            db_manager.get_setting("sms_tpl_cancel_use", "")
            or db_manager.get_setting("sms_template_cancel_use", "")
            or DEFAULT_TEMPLATES["cancel_use"]
        )
        messages.append({
            "type": "선결제 사용 취소",
            "text": render_sms_template(tpl_use, context),
        })

    if charged_prepaid > 0:
        tpl_charge = (
            db_manager.get_setting("sms_tpl_cancel_charge", "")
            or db_manager.get_setting("sms_template_cancel_charge", "")
            or DEFAULT_TEMPLATES["cancel_charge"]
        )
        messages.append({
            "type": "선결제 충전 취소",
            "text": render_sms_template(tpl_charge, context),
        })

    if not messages:
        return {"should_send": False}

    return {
        "should_send": True,
        "api_key": api_key,
        "api_secret": api_secret,
        "sender_phone": sender_phone,
        "to_phone": customer_phone,
        "messages": messages,
    }


def get_euckr_byte_length(text: str) -> int:
    """한글 2바이트 / 영문·숫자·공백 1바이트 기준 문자 용량 계산"""
    try:
        return len(text.encode("euc-kr", errors="replace"))
    except Exception:
        return len(text.encode("utf-8"))


def _truncate_euckr_bytes(text: str, max_bytes: int = 40) -> str:
    """EUC-KR 기준 최대 바이트(LMS 제목 한도 40byte) 이내로 한글 깨짐 없이 자르기"""
    result = []
    current_bytes = 0
    for ch in text:
        ch_bytes = len(ch.encode("euc-kr", errors="replace"))
        if current_bytes + ch_bytes > max_bytes:
            break
        result.append(ch)
        current_bytes += ch_bytes
    return "".join(result).strip()


class SmsService:
    """솔라피(SOLAPI) REST API v4 연동 클래스"""
    BASE_URL = "https://api.solapi.com"
    ESTIMATED_UNIT_PRICE = 50  # 장문(LMS) 기준 건당 예상 단가 (원)

    def __init__(self, api_key: str, api_secret: str, sender_phone: str = ""):
        self.api_key = (api_key or "").strip()
        self.api_secret = (api_secret or "").strip()
        self.sender_phone = re.sub(r"[^0-9]", "", sender_phone or "")

    def _get_headers(self) -> dict:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        salt = secrets.token_hex(16)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            (date + salt).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return {
            "Authorization": (
                f"HMAC-SHA256 apiKey={self.api_key}, "
                f"date={date}, salt={salt}, signature={signature}"
            ),
            "Content-Type": "application/json",
        }

    def get_balance(self) -> tuple[bool, str, int]:
        """잔여 충전금(캐시 + 포인트) 조회 (LMS 기준 발송 가능 건수 계산)"""
        if not self.api_key or not self.api_secret:
            return False, "API Key와 Secret을 먼저 입력하세요.", 0

        try:
            res = requests.get(
                f"{self.BASE_URL}/cash/v1/balance",
                headers=self._get_headers(),
                timeout=5,
            )
            data = res.json()
            if res.status_code == 200:
                balance = int(data.get("balance", 0))
                point = int(data.get("point", 0))
                total = balance + point
                approx_count = total // self.ESTIMATED_UNIT_PRICE
                return True, f"{total:,}원 (LMS 기준 약 {approx_count:,}건 발송 가능)", total
            err_msg = data.get("errorMessage") or f"인증 실패 (HTTP {res.status_code})"
            return False, err_msg, 0
        except requests.Timeout:
            return False, "요청 시간 초과 (네트워크 상태를 확인하세요)", 0
        except Exception as e:
            return False, f"네트워크 오류: {e}", 0

    def send_sms(self, to_phone: str, text: str) -> tuple[bool, str]:
        """단건 문자 발송 (90byte 초과 시 첫 줄을 LMS 제목으로 자동 분리)"""
        clean_to = re.sub(r"[^0-9]", "", to_phone or "")
        if len(clean_to) < 10:
            return False, "수신자 휴대폰 번호가 올바르지 않습니다."
        if not self.api_key or not self.api_secret:
            return False, "API Key와 Secret이 설정되지 않았습니다."
        if len(self.sender_phone) < 8:
            return False, "등록된 발신번호가 올바르지 않습니다."

        clean_text = (text or "").strip()
        if not clean_text:
            return False, "발송할 문자 내용이 비어 있습니다."

        message_data = {
            "to": clean_to,
            "from": self.sender_phone,
            "text": clean_text,
        }

        # 90바이트 초과 장문(LMS)일 때 첫 줄을 제목(subject)으로 분리해 중복 및 잘림 방지
        if get_euckr_byte_length(clean_text) > 90:
            lines = clean_text.split("\n", 1)
            first_line = lines[0].strip()
            rest_body = lines[1].strip() if len(lines) > 1 else ""

            if first_line and rest_body and get_euckr_byte_length(first_line) <= 40:
                message_data["subject"] = first_line
                message_data["text"] = rest_body
            else:
                message_data["subject"] = _truncate_euckr_bytes(first_line or clean_text, 40)

        payload = {"message": message_data}
        try:
            res = requests.post(
                f"{self.BASE_URL}/messages/v4/send",
                json=payload,
                headers=self._get_headers(),
                timeout=6,
            )
            data = res.json()
            if res.status_code == 200:
                return True, "문자가 정상적으로 발송되었습니다."
            err_msg = data.get("errorMessage") or f"발송 실패 (HTTP {res.status_code})"
            return False, err_msg
        except requests.Timeout:
            return False, "문자 서버 응답 시간 초과"
        except Exception as e:
            return False, f"문자 서버 연결 실패: {e}"


class SmsBalanceWorker(QThread):
    """백그라운드 잔액 조회 워커"""
    finished_signal = Signal(bool, str, int)

    def __init__(self, api_key: str, api_secret: str, parent=None):
        super().__init__(parent)
        self.api_key = api_key
        self.api_secret = api_secret

    def run(self):
        service = SmsService(self.api_key, self.api_secret)
        ok, msg, total = service.get_balance()
        self.finished_signal.emit(ok, msg, total)


class SmsSendWorker(QThread):
    """백그라운드 단건 문자 발송 워커"""
    finished_signal = Signal(bool, str)

    def __init__(self, api_key: str, api_secret: str, sender_phone: str, to_phone: str, text: str, parent=None):
        super().__init__(parent)
        self.api_key = api_key
        self.api_secret = api_secret
        self.sender_phone = sender_phone
        self.to_phone = to_phone
        self.text = text

    def run(self):
        service = SmsService(self.api_key, self.api_secret, self.sender_phone)
        ok, msg = service.send_sms(self.to_phone, self.text)
        self.finished_signal.emit(ok, msg)