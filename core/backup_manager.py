import os
import sqlite3
import tempfile
from datetime import datetime
from core.encryption_service import EncryptionService
from core.google_drive_service import GoogleDriveService


class BackupManager:
    """로컬 및 Google Drive 암호화 자동/수동 백업 및 보관 주기 관리 매니저"""

    DAILY_RETENTION_DAYS = 14     # 일별 자동 백업 보관 일수 (14일)
    MONTHLY_RETENTION_DAYS = 180  # 매월 1일 자동 백업 보관 일수 (약 6개월)
    MIN_KEEP_COUNT = 7            # 최소 유지 개수

    def __init__(self, db_path: str = None, backup_root_dir: str = "백업"):
        self.db_path = self._resolve_db_path(db_path)
        self.auto_dir = os.path.join(backup_root_dir, "자동백업")
        self.manual_dir = os.path.join(backup_root_dir, "수동백업")

        os.makedirs(self.auto_dir, exist_ok=True)
        os.makedirs(self.manual_dir, exist_ok=True)

        self.encryption_service = EncryptionService()
        self.drive_service = GoogleDriveService()

    def _resolve_db_path(self, db_path: str = None) -> str:
        """실제 존재하는 SQLite DB 파일 경로 자동 탐색"""
        candidates = []
        if db_path:
            candidates.append(db_path)
        env_db = os.getenv("DB_PATH")
        if env_db:
            candidates.append(env_db)
        candidates.extend([
            "hairmate.db",
            os.path.join("data", "hairmate.db"),
            os.path.join("database", "hairmate.db"),
            os.path.join("db", "hairmate.db"),
        ])

        for path in candidates:
            if path and os.path.exists(path):
                return path

        for fname in os.listdir("."):
            if fname.endswith(".db") and os.path.isfile(fname):
                return fname

        return db_path or "hairmate.db"

    def _create_encrypted_snapshot(self, output_enc_path: str) -> bool:
        """SQLite 온라인 백업 API로 안전하게 스냅샷을 뜬 뒤 연결 해제 후 AES(.enc) 암호화 저장"""
        if not os.path.exists(self.db_path):
            print(f"[Backup Error] 원본 DB 파일이 없습니다: {self.db_path}")
            return False

        temp_fd, temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(temp_fd)

        try:
            src_conn = None
            dst_conn = None
            try:
                src_conn = sqlite3.connect(self.db_path)
                dst_conn = sqlite3.connect(temp_db_path)
                src_conn.backup(dst_conn)
            finally:
                if dst_conn is not None:
                    dst_conn.close()
                if src_conn is not None:
                    src_conn.close()

            return self.encryption_service.encrypt_db(temp_db_path, output_enc_path)
        except Exception as e:
            print(f"[Backup Snapshot Error] {e}")
            return False
        finally:
            if os.path.exists(temp_db_path):
                try:
                    os.remove(temp_db_path)
                except Exception as e:
                    print(f"[Temp DB Remove Warning] {e}")

    @staticmethod
    def _format_file_size(file_path: str) -> str:
        """파일 크기를 KB 또는 MB 문자열로 변환"""
        file_size_bytes = os.path.getsize(file_path)
        file_size_mb = round(file_size_bytes / (1024 * 1024), 1)
        if file_size_mb < 0.1:
            return f"{round(file_size_bytes / 1024, 1)} KB"
        return f"{int(file_size_mb) if file_size_mb.is_integer() else file_size_mb} MB"

    def run_auto_backup(self) -> tuple[bool, str]:
        """프로그램 종료 시 자동 백업 실행 (HairMate_백업_자동_YYYYMMDD_HHMMSS.enc)"""
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        auto_filename = f"HairMate_백업_자동_{timestamp}.enc"
        auto_path = os.path.join(self.auto_dir, auto_filename)

        if not self._create_encrypted_snapshot(auto_path):
            return False, "로컬 자동 백업 파일 생성에 실패했습니다."

        # 자동 백업 완료 시에도 DB의 최근 백업일 갱신
        try:
            from core.db_manager import DBManager
            DBManager().set_setting("last_backup_date", now.strftime("%Y-%m-%d"))
        except Exception as e:
            print(f"[Auto Backup Setting Update Warning] {e}")

        drive_uploaded = False
        if self.drive_service.is_authenticated():
            try:
                self.drive_service.upload_backup(auto_path)
                drive_uploaded = True
            except Exception as e:
                print(f"[Auto Backup Drive Upload Warning] {e}")

        self.cleanup_old_auto_backups(clean_drive=drive_uploaded)

        msg = "로컬 및 Google Drive 자동 백업 완료" if drive_uploaded else "로컬 자동 백업 완료 (Google 미연동)"
        return True, msg

    def run_manual_backup(self, upload_to_drive: bool = True, require_drive: bool = False) -> tuple[bool, str, dict]:
        """수동 백업 실행 (HairMate_백업_수동_YYYYMMDD_HHMMSS.enc)"""
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        date_display = now.strftime("%Y-%m-%d")
        filename = f"HairMate_백업_수동_{timestamp}.enc"
        local_path = os.path.join(self.manual_dir, filename)

        if not self._create_encrypted_snapshot(local_path):
            return False, "로컬 DB 암호화 및 수동 백업 파일 생성에 실패했습니다.", {}

        file_size_str = self._format_file_size(local_path)
        info = {
            "filename": filename,
            "local_path": local_path,
            "file_size_str": file_size_str,
            "date_display": date_display,
        }

        if upload_to_drive:
            if require_drive or self.drive_service.is_authenticated():
                try:
                    self.drive_service.upload_backup(local_path)
                    return True, f"로컬 및 Google Drive 수동 백업이 완료되었습니다.\n({filename})", info
                except Exception as e:
                    if require_drive:
                        return False, str(e), info
                    return True, f"로컬 백업은 완료되었으나 Google Drive 업로드에 실패했습니다.\n({e})", info

        return True, f"로컬 수동 백업이 완료되었습니다.\n({filename})", info

    def _extract_date_key(self, filename: str) -> str:
        """오래된 순 정렬을 위해 파일명에서 YYYYMMDD_HHMMSS 추출"""
        try:
            parts = filename[:-4].split("_")
            if len(parts) >= 5 and parts[3] in ("일별", "월별"):
                return "_".join(parts[4:])
            return "_".join(parts[3:])
        except Exception:
            return filename

    def _is_expired_auto_file(self, filename: str, now: datetime) -> bool:
        """파일명에서 날짜를 추출해 보관 주기 경과 여부 판단 (_자동_ 파일 전용)"""
        if "_자동_" not in filename or not filename.endswith(".enc"):
            return False

        try:
            parts = filename[:-4].split("_")
            if len(parts) >= 5 and parts[3] in ("일별", "월별"):
                date_str = parts[4]
                is_monthly = (parts[3] == "월별")
            else:
                date_str = parts[3]
                is_monthly = False

            file_date = datetime.strptime(date_str, "%Y%m%d")
            age_days = (now - file_date).days

            if is_monthly or file_date.day == 1:
                return age_days > self.MONTHLY_RETENTION_DAYS
            return age_days > self.DAILY_RETENTION_DAYS
        except (IndexError, ValueError):
            return False

    def cleanup_old_auto_backups(self, clean_drive: bool = True):
        """최소 유지 개수(MIN_KEEP_COUNT)를 보장하면서 기간 만료된 자동 백업만 삭제"""
        now = datetime.now()

        local_auto_files = sorted(
            [f for f in os.listdir(self.auto_dir) if "_자동_" in f and f.endswith(".enc")],
            key=self._extract_date_key
        )
        remaining_local = len(local_auto_files)

        for fname in local_auto_files:
            if remaining_local <= self.MIN_KEEP_COUNT:
                break
            if self._is_expired_auto_file(fname, now):
                try:
                    os.remove(os.path.join(self.auto_dir, fname))
                    remaining_local -= 1
                except Exception as e:
                    print(f"[Local Cleanup Error] {fname}: {e}")

        if clean_drive and self.drive_service.is_authenticated():
            try:
                all_drive_files = self.drive_service.list_all_backups()
                drive_auto_files = sorted(
                    [f for f in all_drive_files if "_자동_" in f.get("name", "")],
                    key=lambda x: self._extract_date_key(x.get("name", ""))
                )
                remaining_drive = len(drive_auto_files)

                for f_info in drive_auto_files:
                    if remaining_drive <= self.MIN_KEEP_COUNT:
                        break
                    if self._is_expired_auto_file(f_info["name"], now):
                        if self.drive_service.delete_backup(f_info["id"]):
                            remaining_drive -= 1
            except Exception as e:
                print(f"[Drive Cleanup Error] {e}")