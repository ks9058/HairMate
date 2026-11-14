import os
import time
import subprocess
import webbrowser
from datetime import datetime, timezone, timedelta
from wsgiref.simple_server import make_server, WSGIRequestHandler
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.file']
KST = timezone(timedelta(hours=9))

POPUP_WINDOW_TITLE = "HairMate 구글 인증 완료"

AUTO_CLOSE_HTML = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <title>{POPUP_WINDOW_TITLE}</title>
    <style>
        body {{
            font-family: 'Malgun Gothic', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #F8F9FA;
            color: #222222;
        }}
        .card {{
            text-align: center;
            padding: 30px 40px;
            background: #FFFFFF;
            border-radius: 12px;
            border: 1px solid #DCDCDC;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h2>로그인이 완료되었습니다.</h2>
        <p>잠시 후 창이 자동으로 닫힙니다.</p>
    </div>
    <script>
        window.close();
    </script>
</body>
</html>
"""


class _QuietWSGIHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass


class GoogleDriveService:
    """OAuth 2.0 및 Google Drive API v3 연동 서비스"""

    def __init__(self, client_secret_file="client_secret.json", token_file="token.json"):
        self.client_secret_file = client_secret_file
        self.token_file = token_file
        self.creds = None
        self._load_credentials()

    def _load_credentials(self):
        """저장된 토큰 자동 로드 및 필요시 자동 갱신"""
        if os.path.exists(self.token_file):
            try:
                self.creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            except Exception:
                self.creds = None

        if self.creds and self.creds.expired and self.creds.refresh_token:
            try:
                self.creds.refresh(Request())
                with open(self.token_file, 'w', encoding='utf-8') as token:
                    token.write(self.creds.to_json())
            except Exception:
                self.creds = None

    def is_authenticated(self) -> bool:
        """인증 완료 및 토큰 유효 여부 확인"""
        return self.creds is not None and self.creds.valid

    @staticmethod
    def _convert_utc_to_kst(utc_str: str) -> str:
        """Google Drive UTC 시간 문자열을 한국 시간(KST, UTC+9)으로 변환"""
        if not utc_str:
            return utc_str
        try:
            dt_utc = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
            dt_kst = dt_utc.astimezone(KST)
            return dt_kst.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        except Exception:
            return utc_str

    def _open_auth_popup(self, auth_url: str):
        """브라우저 앱 팝업 모드로 우선 실행"""
        browser_candidates = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        for exe_path in browser_candidates:
            if os.path.exists(exe_path):
                try:
                    subprocess.Popen([
                        exe_path,
                        f"--app={auth_url}",
                        "--window-size=520,680"
                    ])
                    return
                except Exception:
                    pass
        webbrowser.open(auth_url)

    def _close_auth_popup_window(self):
        """Windows API(WM_CLOSE)로 인증 완료 팝업 창 닫기"""
        try:
            import ctypes
            user32 = ctypes.windll.user32
            WM_CLOSE = 0x0010

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

            def enum_cb(hwnd, lparam):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    if POPUP_WINDOW_TITLE in buff.value:
                        user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
                return True

            user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
        except Exception as e:
            print(f"[Close Auth Popup Warning] {e}")

    def authenticate(self) -> bool:
        """브라우저를 열어 구글 OAuth 2.0 로그인 진행 후 창 자동 닫기"""
        try:
            if not os.path.exists(self.client_secret_file):
                raise FileNotFoundError(f"{self.client_secret_file} 파일이 필요합니다.")

            os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
            os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
            flow = InstalledAppFlow.from_client_secrets_file(self.client_secret_file, SCOPES)

            callback_data = {"url": None}

            def wsgi_app(environ, start_response):
                path = environ.get("PATH_INFO", "/")
                query = environ.get("QUERY_STRING", "")

                if path == "/favicon.ico":
                    start_response("404 Not Found", [("Content-Type", "text/plain")])
                    return [b""]

                if "code=" in query or "error=" in query:
                    port = environ.get("SERVER_PORT")
                    callback_data["url"] = f"http://localhost:{port}{path}?{query}"

                start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
                return [AUTO_CLOSE_HTML.encode("utf-8")]

            server = make_server("localhost", 0, wsgi_app, handler_class=_QuietWSGIHandler)
            server.timeout = 120
            flow.redirect_uri = f"http://localhost:{server.server_port}/"

            auth_url, _ = flow.authorization_url(
                prompt="select_account consent",
                access_type="offline"
            )
            self._open_auth_popup(auth_url)

            while callback_data["url"] is None:
                server.handle_request()

            server.server_close()

            time.sleep(0.5)
            self._close_auth_popup_window()

            if "error=" in callback_data["url"]:
                raise RuntimeError(f"OAuth 인증 거부 또는 오류: {callback_data['url']}")

            flow.fetch_token(authorization_response=callback_data["url"])
            self.creds = flow.credentials

            with open(self.token_file, 'w', encoding='utf-8') as token:
                token.write(self.creds.to_json())

            try:
                from PySide6.QtWidgets import QApplication
                win = QApplication.activeWindow() or (
                    QApplication.topLevelWidgets()[0] if QApplication.topLevelWidgets() else None
                )
                if win:
                    win.showNormal()
                    win.raise_()
                    win.activateWindow()
            except Exception:
                pass

            return True
        except Exception as e:
            print(f"[Google Auth Error] {e}")
            return False

    def get_account_info(self) -> dict:
        """연동된 구글 계정 이메일 및 사용자 정보 조회"""
        if not self.is_authenticated():
            return {"email": "미인증", "name": "알 수 없음"}

        try:
            service = build('drive', 'v3', credentials=self.creds)
            about = service.about().get(fields="user").execute()
            user = about.get('user', {})
            return {
                "email": user.get('emailAddress', '계정 정보 없음'),
                "name": user.get('displayName', '사용자')
            }
        except Exception as e:
            print(f"[Google Get Account Error] {e}")
            return {"email": "조회 실패", "name": "알 수 없음"}

    def get_last_auth_date(self) -> str:
        """token.json 생성/수정일자 반환 (최근 인증 일시)"""
        if os.path.exists(self.token_file):
            mtime = os.path.getmtime(self.token_file)
            return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        return "-"

    def disconnect(self) -> bool:
        """구글 계정 연동 해제 (token.json 삭제 및 메모리 초기화)"""
        try:
            if os.path.exists(self.token_file):
                os.remove(self.token_file)
            self.creds = None
            return True
        except Exception as e:
            print(f"[Google Disconnect Error] {e}")
            return False

    def get_or_create_folder(self, folder_name: str, parent_id: str = None) -> str:
        """지정한 이름 및 상위 폴더(parent_id) 내의 폴더 ID 조회 (없으면 자동 생성)"""
        if not self.is_authenticated():
            if not self.authenticate():
                raise PermissionError("구글 로그인 인증에 실패했습니다.")

        service = build('drive', 'v3', credentials=self.creds)

        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        if parent_id:
            query += f" and '{parent_id}' in parents"

        results = service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get('files', [])

        if folders:
            return folders[0]['id']

        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            folder_metadata['parents'] = [parent_id]

        folder = service.files().create(body=folder_metadata, fields='id').execute()
        return folder.get('id')

    def _get_target_backup_folder_id(self) -> str:
        """HairMate / YYYY년 / MM월 계층 구조 폴더 ID 반환"""
        now = datetime.now()
        year_str = now.strftime("%Y년")
        month_str = now.strftime("%m월")

        root_id = self.get_or_create_folder("HairMate")
        year_id = self.get_or_create_folder(year_str, parent_id=root_id)
        month_id = self.get_or_create_folder(month_str, parent_id=year_id)

        return month_id

    def upload_backup(self, enc_file_path: str) -> dict:
        """암호화된 백업 파일을 HairMate / YYYY년 / MM월 폴더 내에 업로드"""
        if not self.is_authenticated():
            if not self.authenticate():
                raise PermissionError("구글 로그인 인증에 실패했습니다.")

        target_folder_id = self._get_target_backup_folder_id()

        service = build('drive', 'v3', credentials=self.creds)
        file_name = os.path.basename(enc_file_path)

        file_metadata = {
            'name': file_name,
            'description': 'HairMate Encrypted Backup Data',
            'parents': [target_folder_id]
        }
        media = MediaFileUpload(enc_file_path, mimetype='application/octet-stream', resumable=True)

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, size, createdTime'
        ).execute()

        return file

    def list_backups(self) -> list:
        """현재 월 폴더 내부의 백업 파일 목록 조회 (한국 시간 변환 적용)"""
        if not self.is_authenticated():
            if not self.authenticate():
                return []

        service = build('drive', 'v3', credentials=self.creds)

        try:
            target_folder_id = self._get_target_backup_folder_id()
        except Exception:
            return []

        query = f"'{target_folder_id}' in parents and (name contains 'HairMate_백업' or name contains '헤어메이트_백업' or name contains 'HairMate_Backup') and trashed = false"
        results = service.files().list(
            q=query,
            fields="files(id, name, size, createdTime)",
            orderBy="createdTime desc"
        ).execute()

        files = results.get('files', [])
        for f in files:
            if 'createdTime' in f:
                f['createdTime'] = self._convert_utc_to_kst(f['createdTime'])
        return files

    def list_all_backups(self) -> list:
        """백업 파일 전체 목록 조회 (복원 뷰 바인딩용, 한국 시간 변환 적용)"""
        if not self.is_authenticated():
            if not self.authenticate():
                return []

        service = build('drive', 'v3', credentials=self.creds)

        query = "(name contains 'HairMate_백업' or name contains '헤어메이트_백업' or name contains 'HairMate_Backup') and name contains '.enc' and trashed = false"
        results = service.files().list(
            q=query,
            fields="files(id, name, size, createdTime)",
            orderBy="createdTime desc"
        ).execute()

        files = results.get('files', [])
        for f in files:
            if 'createdTime' in f:
                f['createdTime'] = self._convert_utc_to_kst(f['createdTime'])
        return files

    def download_backup(self, file_id: str, dest_path: str) -> bool:
        """선택한 백업 파일을 구글 드라이브에서 로컬로 다운로드"""
        if not self.is_authenticated():
            if not self.authenticate():
                return False

        service = build('drive', 'v3', credentials=self.creds)
        request = service.files().get_media(fileId=file_id)

        with open(dest_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        return True

    def delete_backup(self, file_id: str) -> bool:
        """구글 드라이브에서 지정한 백업 파일 영구 삭제"""
        if not self.is_authenticated():
            return False

        try:
            service = build('drive', 'v3', credentials=self.creds)
            service.files().delete(fileId=file_id).execute()
            return True
        except Exception as e:
            print(f"[Google Delete Backup Error] {e}")
            return False