"""
Модуль для управления очередью аккаунтов Steam для регистрации.
Обрабатывает загрузку, парсинг и отслеживание статуса регистрации аккаунтов.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class AccountStatus(Enum):
    """Статусы обработки аккаунта"""
    PENDING = "pending"  # Ожидает обработки
    IN_PROGRESS = "in_progress"  # В процессе регистрации
    EMAIL_SENT = "email_sent"  # Email отправлен, ожидает подтверждения
    EMAIL_VERIFIED = "email_verified"  # Email подтверждён
    COMPLETED = "completed"  # Полностью зарегистрирован
    FAILED = "failed"  # Ошибка при регистрации
    CAPTCHA_FAILED = "captcha_failed"  # Ошибка решения капчи
    EMAIL_EXISTS = "email_exists"  # Email уже используется


@dataclass
class AccountData:
    """Данные аккаунта для регистрации"""
    email: str
    username: str
    password: str
    status: AccountStatus = AccountStatus.PENDING
    error_message: Optional[str] = None
    attempts: int = 0
    last_attempt: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> dict:
        """Конвертация в словарь для сохранения"""
        data = asdict(self)
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'AccountData':
        """Создание из словаря"""
        data['status'] = AccountStatus(data.get('status', 'pending'))
        return cls(**data)


class AccountQueue:
    """Управление очередью аккаунтов для регистрации"""

    def __init__(self, accounts_file: str = "accounts.txt", state_file: str = "accounts_state.json"):
        """
        Инициализация очереди аккаунтов

        :param accounts_file: Путь к файлу с аккаунтами (формат: email:username:password)
        :param state_file: Путь к файлу для сохранения состояния обработки
        """
        self.accounts_file = accounts_file
        self.state_file = state_file
        self.accounts: List[AccountData] = []
        self.current_index: int = 0

        # Загружаем состояние или создаём новую очередь
        if os.path.exists(state_file):
            self.load_state()
        else:
            self.load_accounts()

    def load_accounts(self) -> None:
        """Загружает аккаунты из конфигурационного файла"""
        if not os.path.exists(self.accounts_file):
            raise FileNotFoundError(
                f"Файл с аккаунтами не найден: {self.accounts_file}\n"
                f"Создайте файл {self.accounts_file} по образцу {self.accounts_file}.example"
            )

        self.accounts = []
        with open(self.accounts_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Пропускаем пустые строки и комментарии
                if not line or line.startswith('#'):
                    continue

                # Парсим строку формата email:username:password
                parts = line.split(':')
                if len(parts) != 3:
                    print(f"⚠️  Предупреждение: Неверный формат в строке {line_num}: {line}")
                    print(f"   Ожидается формат: email:username:password")
                    continue

                email, username, password = [p.strip() for p in parts]

                # Валидация
                if not email or not username or not password:
                    print(f"⚠️  Предупреждение: Пустые поля в строке {line_num}")
                    continue

                if '@' not in email:
                    print(f"⚠️  Предупреждение: Некорректный email в строке {line_num}: {email}")
                    continue

                self.accounts.append(AccountData(
                    email=email,
                    username=username,
                    password=password
                ))

        if not self.accounts:
            raise ValueError(
                f"Не найдено валидных аккаунтов в файле {self.accounts_file}\n"
                f"Убедитесь, что файл содержит строки формата: email:username:password"
            )

        print(f"✓ Загружено {len(self.accounts)} аккаунтов из {self.accounts_file}")

    def save_state(self) -> None:
        """Сохраняет текущее состояние очереди в JSON файл"""
        state = {
            'current_index': self.current_index,
            'accounts': [acc.to_dict() for acc in self.accounts],
            'last_updated': datetime.now().isoformat()
        }

        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def load_state(self) -> None:
        """Загружает состояние очереди из JSON файла"""
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)

            self.current_index = state.get('current_index', 0)
            self.accounts = [
                AccountData.from_dict(acc_dict)
                for acc_dict in state.get('accounts', [])
            ]

            print(f"✓ Загружено состояние из {self.state_file}")
            print(f"  Всего аккаунтов: {len(self.accounts)}")
            print(f"  Текущий индекс: {self.current_index}")
        except Exception as e:
            print(f"⚠️  Ошибка загрузки состояния: {e}")
            print(f"   Загружаем аккаунты из {self.accounts_file}")
            self.load_accounts()

    def get_next_account(self) -> Optional[AccountData]:
        """
        Возвращает следующий аккаунт для обработки

        :return: AccountData или None если все аккаунты обработаны
        """
        # Ищем первый необработанный аккаунт начиная с current_index
        while self.current_index < len(self.accounts):
            account = self.accounts[self.current_index]

            # Пропускаем уже завершённые аккаунты
            if account.status in [AccountStatus.COMPLETED]:
                self.current_index += 1
                continue

            # Если аккаунт упал с ошибкой более 3 раз - пропускаем
            if account.status == AccountStatus.FAILED and account.attempts >= 3:
                print(f"⚠️  Пропуск аккаунта {account.email} - превышено количество попыток ({account.attempts})")
                self.current_index += 1
                continue

            return account

        return None

    def mark_in_progress(self, account: AccountData) -> None:
        """Отмечает аккаунт как находящийся в обработке"""
        account.status = AccountStatus.IN_PROGRESS
        account.attempts += 1
        account.last_attempt = datetime.now().isoformat()
        self.save_state()

    def mark_email_sent(self, account: AccountData) -> None:
        """Отмечает, что email для подтверждения отправлен"""
        account.status = AccountStatus.EMAIL_SENT
        self.save_state()

    def mark_completed(self, account: AccountData) -> None:
        """Отмечает аккаунт как успешно зарегистрированный"""
        account.status = AccountStatus.COMPLETED
        account.completed_at = datetime.now().isoformat()
        self.current_index += 1
        self.save_state()

        # Сохраняем в отдельный файл успешных регистраций
        self._save_to_completed(account)

    def mark_failed(self, account: AccountData, error_message: str) -> None:
        """Отмечает аккаунт как провалившийся с сообщением об ошибке"""
        account.status = AccountStatus.FAILED
        account.error_message = error_message
        self.save_state()

        # Если превышено количество попыток - переходим к следующему
        if account.attempts >= 3:
            self.current_index += 1
            self.save_state()

    def mark_captcha_failed(self, account: AccountData, error_message: str) -> None:
        """Отмечает, что не удалось решить капчу"""
        account.status = AccountStatus.CAPTCHA_FAILED
        account.error_message = error_message
        self.save_state()

    def mark_email_exists(self, account: AccountData) -> None:
        """Отмечает, что email уже используется"""
        account.status = AccountStatus.EMAIL_EXISTS
        account.error_message = "Email уже зарегистрирован в Steam"
        self.current_index += 1  # Переходим к следующему, повторять бесполезно
        self.save_state()

    def _save_to_completed(self, account: AccountData) -> None:
        """Сохраняет успешно зарегистрированный аккаунт в отдельный файл"""
        completed_file = "completed_accounts.txt"
        with open(completed_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Дата: {account.completed_at}\n")
            f.write(f"Email: {account.email}\n")
            f.write(f"Username: {account.username}\n")
            f.write(f"Password: {account.password}\n")
            f.write(f"Попыток: {account.attempts}\n")
            f.write(f"{'='*60}\n")

    def get_statistics(self) -> Dict[str, int]:
        """Возвращает статистику по обработке аккаунтов"""
        stats = {
            'total': len(self.accounts),
            'pending': 0,
            'in_progress': 0,
            'email_sent': 0,
            'completed': 0,
            'failed': 0,
            'captcha_failed': 0,
            'email_exists': 0
        }

        for account in self.accounts:
            if account.status == AccountStatus.PENDING:
                stats['pending'] += 1
            elif account.status == AccountStatus.IN_PROGRESS:
                stats['in_progress'] += 1
            elif account.status == AccountStatus.EMAIL_SENT:
                stats['email_sent'] += 1
            elif account.status == AccountStatus.COMPLETED:
                stats['completed'] += 1
            elif account.status == AccountStatus.FAILED:
                stats['failed'] += 1
            elif account.status == AccountStatus.CAPTCHA_FAILED:
                stats['captcha_failed'] += 1
            elif account.status == AccountStatus.EMAIL_EXISTS:
                stats['email_exists'] += 1

        return stats

    def print_statistics(self) -> None:
        """Выводит статистику в консоль"""
        stats = self.get_statistics()

        print("\n" + "="*60)
        print("СТАТИСТИКА ОБРАБОТКИ АККАУНТОВ")
        print("="*60)
        print(f"Всего аккаунтов:        {stats['total']}")
        print(f"Ожидают обработки:      {stats['pending']}")
        print(f"В процессе:             {stats['in_progress']}")
        print(f"Email отправлен:        {stats['email_sent']}")
        print(f"Успешно завершено:      {stats['completed']}")
        print(f"Ошибка регистрации:     {stats['failed']}")
        print(f"Ошибка капчи:           {stats['captcha_failed']}")
        print(f"Email уже существует:   {stats['email_exists']}")
        print("="*60)

        if stats['completed'] > 0:
            success_rate = (stats['completed'] / stats['total']) * 100
            print(f"Процент успеха: {success_rate:.1f}%")
        print()

    def has_more_accounts(self) -> bool:
        """Проверяет, есть ли ещё аккаунты для обработки"""
        return self.get_next_account() is not None

    def reset_failed_accounts(self) -> None:
        """Сбрасывает статус провалившихся аккаунтов для повторной попытки"""
        for account in self.accounts:
            if account.status in [AccountStatus.FAILED, AccountStatus.CAPTCHA_FAILED]:
                account.status = AccountStatus.PENDING
                account.error_message = None
                account.attempts = 0

        self.current_index = 0
        self.save_state()
        print("✓ Провалившиеся аккаунты сброшены для повторной обработки")
