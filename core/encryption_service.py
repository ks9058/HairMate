import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

class EncryptionService:
    """SQLite DB 파일의 AES(Fernet) 암호화 및 복호화 전담 모듈"""

    def __init__(self):
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            raise ValueError(".env 파일에 ENCRYPTION_KEY가 설정되어 있지 않습니다.")
        self.cipher = Fernet(key.encode('utf-8'))

    def encrypt_db(self, db_path: str, output_enc_path: str) -> bool:
        """SQLite DB 바이너리를 읽어 Fernet AES로 암호화한 파일(.enc) 생성"""
        try:
            if not os.path.exists(db_path):
                raise FileNotFoundError(f"DB 파일을 찾을 수 없습니다: {db_path}")

            with open(db_path, "rb") as f:
                db_bytes = f.read()

            encrypted_bytes = self.cipher.encrypt(db_bytes)

            with open(output_enc_path, "wb") as f:
                f.write(encrypted_bytes)

            return True
        except Exception as e:
            print(f"[Encryption Error] {e}")
            return False

    def decrypt_db(self, enc_path: str, output_db_path: str) -> bool:
        """암호화된 백업 파일(.enc)을 복호화하여 SQLite DB 파일로 원복"""
        try:
            if not os.path.exists(enc_path):
                raise FileNotFoundError(f"백업 파일을 찾을 수 없습니다: {enc_path}")

            with open(enc_path, "rb") as f:
                encrypted_bytes = f.read()

            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)

            with open(output_db_path, "wb") as f:
                f.write(decrypted_bytes)

            return True
        except Exception as e:
            print(f"[Decryption Error] {e}")
            return False