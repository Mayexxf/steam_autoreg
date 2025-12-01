"""
Пакетная регистрация аккаунтов Steam из конфигурационного файла.
Последовательно обрабатывает аккаунты из accounts.txt с отслеживанием состояния.
"""

import time
import argparse
from steam_registration import SteamRegistration
from src.utils.account_queue import AccountQueue, AccountStatus


class SteamBatchRegistration:
    """Класс для пакетной регистрации аккаунтов Steam"""

    def __init__(self, accounts_file: str = "accounts.txt",
                 headless: bool = False,
                 manual_captcha: bool = False,
                 delay_between_accounts: int = 5):
        """
        Инициализация пакетной регистрации

        :param accounts_file: Путь к файлу с аккаунтами
        :param headless: Запускать браузер в фоновом режиме
        :param manual_captcha: Решать капчу вручную (True) или через YesCaptcha (False)
        :param delay_between_accounts: Задержка между регистрацией аккаунтов (секунды)
        """
        self.queue = AccountQueue(accounts_file=accounts_file)
        self.headless = headless
        self.manual_captcha = manual_captcha
        self.delay_between_accounts = delay_between_accounts

    def process_account(self, account) -> bool:
        """
        Обрабатывает регистрацию одного аккаунта

        :param account: AccountData объект
        :return: True если успешно, False если ошибка
        """
        print("\n" + "="*60)
        print(f"РЕГИСТРАЦИЯ АККАУНТА {self.queue.current_index + 1}/{len(self.queue.accounts)}")
        print("="*60)
        print(f"Email: {account.email}")
        print(f"Username: {account.username}")
        print(f"Попытка: {account.attempts + 1}")
        print("="*60 + "\n")

        # Отмечаем аккаунт как обрабатываемый
        self.queue.mark_in_progress(account)

        # Создаём новый экземпляр регистрации для каждого аккаунта
        registration = None
        try:
            registration = SteamRegistration(
                headless=self.headless,
                manual_captcha=self.manual_captcha
            )

            # Открываем страницу регистрации
            if not registration.open_registration_page():
                self.queue.mark_failed(account, "Не удалось открыть страницу регистрации")
                return False

            # Заполняем email
            if not registration.fill_email_address(account.email):
                self.queue.mark_failed(account, "Не удалось заполнить email")
                return False

            # Подтверждаем email
            if not registration.confirm_email(account.email):
                self.queue.mark_failed(account, "Не удалось подтвердить email")
                return False

            # Принимаем соглашение
            if not registration.accept_agreement():
                self.queue.mark_failed(account, "Не удалось принять соглашение")
                return False

            # Решаем капчу
            print("\n⚠️  Решение капчи...")
            if not registration.solve_captcha():
                self.queue.mark_captcha_failed(account, "Не удалось решить капчу")
                return False

            # Нажимаем Continue
            print("Нажатие кнопки Continue...")
            if not registration.continue_registration():
                # Проверяем, возможно Steam показала ошибку
                page_source = registration.driver.page_source.lower()

                if "неверный ответ в поле captcha" in page_source or "invalid captcha" in page_source:
                    self.queue.mark_captcha_failed(account, "Steam отклонила решение капчи")
                    return False
                elif "email" in page_source and ("already" in page_source or "уже" in page_source):
                    self.queue.mark_email_exists(account)
                    print("⚠️  Email уже зарегистрирован в Steam, пропускаем...")
                    return False
                else:
                    self.queue.mark_failed(account, "Не удалось продолжить регистрацию")
                    return False

            # Проверяем отправку email
            if registration.verify_email():
                self.queue.mark_email_sent(account)

                print("\n" + "="*60)
                print("✓ EMAIL УСПЕШНО ОТПРАВЛЕН!")
                print("="*60)
                print(f"\nEmail: {account.email}")
                print(f"Username: {account.username}")
                print(f"Password: {account.password}")
                print("\n⚠️  СЛЕДУЮЩИЕ ШАГИ:")
                print("1. Откройте почтовый ящик и подтвердите email")
                print("2. После подтверждения аккаунт будет полностью зарегистрирован")
                print("="*60 + "\n")

                # В режиме пакетной обработки не ждём подтверждения email
                # Пользователь должен подтвердить email вручную позже
                # Отмечаем как успешно завершённый (первый этап)
                self.queue.mark_completed(account)

                return True
            else:
                self.queue.mark_failed(account, "Не удалось пройти первый этап регистрации")
                return False

        except Exception as e:
            error_msg = f"Исключение при регистрации: {str(e)}"
            print(f"\n❌ ОШИБКА: {error_msg}")
            self.queue.mark_failed(account, error_msg)
            return False

        finally:
            # Закрываем браузер после обработки аккаунта
            if registration and registration.driver:
                try:
                    registration.driver.quit()
                    print("✓ Браузер закрыт")
                except Exception as e:
                    print(f"⚠️  Ошибка при закрытии браузера: {e}")

    def run(self) -> None:
        """Запускает пакетную обработку всех аккаунтов"""
        print("\n" + "="*60)
        print("ПАКЕТНАЯ РЕГИСТРАЦИЯ АККАУНТОВ STEAM")
        print("="*60)

        # Выводим начальную статистику
        self.queue.print_statistics()

        # Обрабатываем аккаунты последовательно
        while self.queue.has_more_accounts():
            account = self.queue.get_next_account()
            if account is None:
                break

            # Обрабатываем аккаунт
            success = self.process_account(account)

            # Выводим статистику после каждого аккаунта
            self.queue.print_statistics()

            # Если есть ещё аккаунты, делаем задержку
            if self.queue.has_more_accounts() and self.delay_between_accounts > 0:
                print(f"\n⏳ Задержка {self.delay_between_accounts} секунд перед следующим аккаунтом...")
                time.sleep(self.delay_between_accounts)

        # Финальная статистика
        print("\n" + "="*60)
        print("ОБРАБОТКА ЗАВЕРШЕНА")
        print("="*60)
        self.queue.print_statistics()

        stats = self.queue.get_statistics()
        if stats['email_sent'] > 0 or stats['completed'] > 0:
            print("\n⚠️  ВАЖНО:")
            print("Не забудьте подтвердить email для зарегистрированных аккаунтов!")
            print("Данные успешных регистраций сохранены в completed_accounts.txt")

        if stats['failed'] > 0 or stats['captcha_failed'] > 0:
            print("\n⚠️  Есть проваленные аккаунты!")
            print("Проверьте файл accounts_state.json для деталей")
            print("Используйте --reset-failed для повторной попытки")

    def reset_failed(self) -> None:
        """Сбрасывает статус провалившихся аккаунтов"""
        self.queue.reset_failed_accounts()
        self.queue.print_statistics()


def main():
    """Главная функция с парсингом аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description="Пакетная регистрация аккаунтов Steam из конфигурационного файла",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  1. Базовая регистрация с автоматическим решением капчи:
     python steam_registration_batch.py

  2. Регистрация с ручным решением капчи:
     python steam_registration_batch.py --manual-captcha

  3. Регистрация в headless режиме (без GUI):
     python steam_registration_batch.py --headless

  4. Использование своего файла с аккаунтами:
     python steam_registration_batch.py --accounts my_accounts.txt

  5. Настройка задержки между аккаунтами (в секундах):
     python steam_registration_batch.py --delay 10

  6. Сброс провалившихся аккаунтов для повторной попытки:
     python steam_registration_batch.py --reset-failed

  7. Показать статистику обработки:
     python steam_registration_batch.py --stats

Формат файла accounts.txt:
  email:username:password
  testuser1@example.com:testuser1:MyPass123!
  testuser2@example.com:testuser2:AnotherPass456!
        """
    )

    parser.add_argument(
        '--accounts',
        default='accounts.txt',
        help='Путь к файлу с аккаунтами (по умолчанию: accounts.txt)'
    )

    parser.add_argument(
        '--headless',
        action='store_true',
        help='Запустить браузер в headless режиме (без GUI)'
    )

    parser.add_argument(
        '--manual-captcha',
        action='store_true',
        help='Решать капчу вручную вместо использования YesCaptcha'
    )

    parser.add_argument(
        '--delay',
        type=int,
        default=5,
        help='Задержка между регистрацией аккаунтов в секундах (по умолчанию: 5)'
    )

    parser.add_argument(
        '--reset-failed',
        action='store_true',
        help='Сбросить статус провалившихся аккаунтов для повторной попытки'
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='Показать только статистику обработки'
    )

    args = parser.parse_args()

    try:
        batch = SteamBatchRegistration(
            accounts_file=args.accounts,
            headless=args.headless,
            manual_captcha=args.manual_captcha,
            delay_between_accounts=args.delay
        )

        if args.reset_failed:
            print("Сброс провалившихся аккаунтов...")
            batch.reset_failed()
        elif args.stats:
            batch.queue.print_statistics()
        else:
            batch.run()

    except FileNotFoundError as e:
        print(f"\n❌ ОШИБКА: {e}")
        print(f"\nСоздайте файл {args.accounts} по образцу:")
        print("email:username:password")
        print("testuser1@example.com:testuser1:MyPass123!")
        print("testuser2@example.com:testuser2:AnotherPass456!")
        exit(1)

    except ValueError as e:
        print(f"\n❌ ОШИБКА: {e}")
        exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем (Ctrl+C)")
        print("Состояние обработки сохранено в accounts_state.json")
        print("Вы можете продолжить с того же места, запустив скрипт снова")
        exit(0)

    except Exception as e:
        print(f"\n❌ НЕОЖИДАННАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
