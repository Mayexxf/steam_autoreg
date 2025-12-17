#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Безопасное хранение OAuth токенов с шифрованием AES-256
"""

import os
import json
import base64
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("[WARN] cryptography не установлен. pip install cryptography")


class SecureTokenStorage:
    """Безопасное хранение токенов с AES-256 шифрованием"""

    def __init__(self, storage_path: str = "config/tokens",
                 master_password: str = None):
        """
        Args:
            storage_path: Директория для хранения токенов
            master_password: Мастер-пароль для шифрования
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Мастер-пароль из переменной окружения или параметра
        self.master_password = master_password or os.getenv(
            "TOKEN_MASTER_PASSWORD",
            "default_change_me_in_production"
        )

        self.cipher = None
        if CRYPTO_AVAILABLE:
            self._init_encryption()

    def _init_encryption(self):
        """Инициализирует ключ шифрования из мастер-пароля"""
        salt_file = self.storage_path / ".salt"

        if salt_file.exists():
            salt = salt_file.read_bytes()
        else:
            salt = os.urandom(16)
            salt_file.write_bytes(salt)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )

        key = base64.urlsafe_b64encode(
            kdf.derive(self.master_password.encode())
        )
        self.cipher = Fernet(key)

    def save_tokens(self, email: str, tokens: Dict[str, Any]) -> bool:
        """
        Сохраняет токены для аккаунта

        Args:
            email: Email аккаунта
            tokens: {
                'access_token': str,
                'refresh_token': str,
                'expires_in': int,
                'token_type': str,
                'scope': str,
                'id_token': str (optional)
            }
        """
        try:
            # Добавляем метаданные
            token_data = {
                **tokens,
                'email': email,
                'saved_at': datetime.utcnow().isoformat(),
                'expires_at': (
                    datetime.utcnow() +
                    timedelta(seconds=tokens.get('expires_in', 3600))
                ).isoformat()
            }

            safe_email = email.replace('@', '_at_').replace('.', '_')

            if CRYPTO_AVAILABLE and self.cipher:
                # Шифруем
                encrypted = self.cipher.encrypt(
                    json.dumps(token_data).encode()
                )
                token_file = self.storage_path / f"{safe_email}.enc"
                token_file.write_bytes(encrypted)
            else:
                # Сохраняем без шифрования (не рекомендуется!)
                token_file = self.storage_path / f"{safe_email}.json"
                with open(token_file, 'w') as f:
                    json.dump(token_data, f, indent=2)
                print("[WARN] Токены сохранены БЕЗ шифрования!")

            print(f"[STORAGE] ✓ Токены сохранены для {email}")
            return True

        except Exception as e:
            print(f"[STORAGE] ✗ Ошибка сохранения: {e}")
            return False

    def load_tokens(self, email: str) -> Optional[Dict[str, Any]]:
        """Загружает токены для аккаунта"""
        try:
            safe_email = email.replace('@', '_at_').replace('.', '_')

            # Пробуем зашифрованный файл
            token_file = self.storage_path / f"{safe_email}.enc"
            if token_file.exists() and CRYPTO_AVAILABLE and self.cipher:
                encrypted = token_file.read_bytes()
                decrypted = self.cipher.decrypt(encrypted)
                token_data = json.loads(decrypted.decode())
                print(f"[STORAGE] ✓ Токены загружены для {email}")
                return token_data

            # Пробуем незашифрованный файл
            token_file = self.storage_path / f"{safe_email}.json"
            if token_file.exists():
                with open(token_file, 'r') as f:
                    token_data = json.load(f)
                print(
                    f"[STORAGE] ✓ Токены загружены для {email} (незашифрованные)")
                return token_data

            print(f"[STORAGE] Токены не найдены для {email}")
            return None

        except Exception as e:
            print(f"[STORAGE] ✗ Ошибка загрузки: {e}")
            return None

    def is_token_expired(self, tokens: Dict[str, Any]) -> bool:
        """Проверяет истёк ли access_token"""
        if not tokens or 'expires_at' not in tokens:
            return True

        try:
            expires_at = datetime.fromisoformat(tokens['expires_at'])
            # Считаем истёкшим за 5 минут до реального истечения
            return datetime.utcnow() >= (expires_at - timedelta(minutes=5))
        except:
            return True

    def delete_tokens(self, email: str) -> bool:
        """Удаляет токены для аккаунта"""
        try:
            safe_email = email.replace('@', '_at_').replace('.', '_')

            for ext in ['.enc', '.json']:
                token_file = self.storage_path / f"{safe_email}{ext}"
                if token_file.exists():
                    token_file.unlink()

            print(f"[STORAGE] ✓ Токены удалены для {email}")
            return True

        except Exception as e:
            print(f"[STORAGE] ✗ Ошибка удаления: {e}")
            return False

    def list_accounts(self) -> list:
        """Возвращает список аккаунтов с сохранёнными токенами"""
        accounts = []

        for f in self.storage_path.glob("*_at_*"):
            if f.suffix in ['.enc', '.json']:
                email = f.stem.replace('_at_', '@').replace('_', '.')
                accounts.append(email)

        return list(set(accounts))


class TokenManager:
    """
    Менеджер токенов с автоматическим обновлением
    """

    def __init__(self,
                 client_id: str,
                 client_secret: str,
                 tenant: str = "consumers",
                 storage: SecureTokenStorage = None):
        """
        Args:
            client_id: Azure Application ID
            client_secret: Azure Client Secret
            tenant: Tenant ID
            storage: Хранилище токенов
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant = tenant
        self.storage = storage or SecureTokenStorage()

        self.token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

    def get_valid_token(self, email: str) -> Optional[str]:
        """
        Возвращает валидный access_token, обновляя при необходимости

        Args:
            email: Email аккаунта

        Returns:
            access_token или None
        """
        tokens = self.storage.load_tokens(email)

        if not tokens:
            print(f"[TOKEN] Токены не найдены для {email}")
            return None

        # Проверяем не истёк ли токен
        if not self.storage.is_token_expired(tokens):
            print(f"[TOKEN] access_token валиден для {email}")
            return tokens.get('access_token')

        # Пробуем обновить
        print(f"[TOKEN] access_token истёк, обновляем...")

        refresh_token = tokens.get('refresh_token')
        if not refresh_token:
            print(f"[TOKEN] ✗ refresh_token отсутствует")
            return None

        new_tokens = self.refresh_token(refresh_token)
        if new_tokens:
            self.storage.save_tokens(email, new_tokens)
            return new_tokens.get('access_token')

        return None

    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Обновляет токены используя refresh_token"""
        import requests

        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
        }

        try:
            response = requests.post(self.token_url, data=data, timeout=30)

            if response.status_code == 200:
                tokens = response.json()
                print("[TOKEN] ✓ Токены обновлены!")
                return tokens
            else:
                error_data = response.json()
                error = error_data.get('error', 'unknown')
                error_desc = error_data.get('error_description', 'Unknown')
                print(f"[TOKEN] ✗ Ошибка обновления: {error}")
                print(f"[TOKEN]   {error_desc}")

                # Если refresh_token невалиден - нужна повторная авторизация
                if error in ['invalid_grant', 'interaction_required']:
                    print("[TOKEN] ⚠ Требуется повторная авторизация через браузер!")

                return None

        except Exception as e:
            print(f"[TOKEN] ✗ Исключение: {e}")
            return None


# Пример использования
if __name__ == "__main__":
    # Тест хранилища
    storage = SecureTokenStorage()

    # Тестовые токены
    test_tokens = {
        'access_token': 'test_access_token_12345',
        'refresh_token': 'test_refresh_token_67890',
        'expires_in': 3600,
        'token_type': 'Bearer',
        'scope': 'Mail.Read User.Read'
    }

    # Сохраняем
    storage.save_tokens("test@outlook.com", test_tokens)

    # Загружаем
    loaded = storage.load_tokens("test@outlook.com")
    print(f"Loaded: {loaded}")

    # Проверяем истечение
    print(f"Expired: {storage.is_token_expired(loaded)}")

    # Список аккаунтов
    print(f"Accounts: {storage.list_accounts()}")
