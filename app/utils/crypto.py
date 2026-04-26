from cryptography.fernet import Fernet
from flask import current_app


class CryptoManager:
    @staticmethod
    def get_cipher():
        key = current_app.config.get("FERNET_KEY")
        if not key:
            raise ValueError("Ошибка: FERNET_KEY не установлен в .env или Config!")
        return Fernet(key.encode())

    @classmethod
    def encrypt(cls, data: str) -> str:
        if not data:
            return None
        cipher = cls.get_cipher()
        return cipher.encrypt(data.encode()).decode()

    @classmethod
    def decrypt(cls, encrypted_data: str) -> str:
        if not encrypted_data:
            return None
        cipher = cls.get_cipher()
        return cipher.decrypt(encrypted_data.encode()).decode()
