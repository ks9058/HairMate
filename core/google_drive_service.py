import os.path
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.file']

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
                with open(self.token_file, 'w') as token:
                    token.write(self.creds.to_json())
            except Exception:
                self.creds = None

    def is_authenticated(self) -> bool:
        """인증 완료 여부 확인"""
        return self.creds is not None and self.creds.valid

    def authenticate(self) -> bool:
        """브라우저를 열어 구글 OAuth 2.0 로그인 진행"""
        try:
            if not os.path.exists(self.client_secret_file):
                raise FileNotFoundError(f"{self.client_secret_file} 파일이 필요합니다.")

            flow = InstalledAppFlow.from_client_secrets_file(self.client_secret_file, SCOPES)
            self.creds = flow.run_local_server(port=0)
            with open(self.token_file, 'w') as token:
                token.write(self.creds.to_json())
            return True
        except Exception as e:
            print(f"[Google Auth Error] {e}")
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
        """현재 월 폴더 내부의 백업 파일 목록 조회 (당일 순번 계산용)"""
        if not self.is_authenticated():
            if not self.authenticate():
                return []

        service = build('drive', 'v3', credentials=self.creds)

        try:
            target_folder_id = self._get_target_backup_folder_id()
        except Exception:
            return []

        query = f"'{target_folder_id}' in parents and name contains 'HairMate_Backup' and trashed = false"
        results = service.files().list(
            q=query,
            fields="files(id, name, size, createdTime)",
            orderBy="createdTime desc"
        ).execute()

        return results.get('files', [])

    def list_all_backups(self) -> list:
        """💡 [추가] HairMate 백업 파일 전체 목록 조회 (복원 선택용)"""
        if not self.is_authenticated():
            if not self.authenticate():
                return []

        service = build('drive', 'v3', credentials=self.creds)

        # HairMate 하위의 모든 암호화 백업 파일(.enc) 검색
        query = "name contains 'HairMate_Backup' and name contains '.enc' and trashed = false"
        results = service.files().list(
            q=query,
            fields="files(id, name, size, createdTime)",
            orderBy="createdTime desc"
        ).execute()

        return results.get('files', [])

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