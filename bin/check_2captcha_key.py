#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Быстрая проверка API ключа 2Captcha
"""

import sys
import io
import requests

# Настройка кодировки для Windows консоли
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def check_2captcha_key():
    """Проверка API ключа 2Captcha"""
    print("="*70)
    print("2Captcha API Key Checker")
    print("="*70)

    # Загружаем ключ
    try:
        with open("2captcha_config.txt", 'r', encoding='utf-8') as f:
            api_key = f.read().strip()
    except FileNotFoundError:
        print("\n❌ Файл 2captcha_config.txt не найден!")
        return False
    except Exception as e:
        print(f"\n❌ Ошибка чтения файла: {e}")
        return False

    print(f"\n[1/3] Checking API key format...")
    print(f"   Raw content: '{api_key}'")
    print(f"   Length: {len(api_key)} characters")

    # Проверяем формат
    if len(api_key) != 32:
        print(f"\n❌ НЕВЕРНЫЙ ФОРМАТ!")
        print(f"   Ключ должен быть ровно 32 символа")
        print(f"   У вас: {len(api_key)} символов")

        if ' ' in api_key:
            print(f"\n⚠️  Обнаружены ПРОБЕЛЫ в ключе!")
            print(f"   Удалите все пробелы")
            clean_key = api_key.replace(' ', '')
            print(f"   Правильный ключ: {clean_key}")

        return False

    if not all(c in '0123456789abcdef' for c in api_key.lower()):
        print(f"\n❌ НЕВЕРНЫЕ СИМВОЛЫ!")
        print(f"   Ключ должен содержать только: 0-9, a-f")
        return False

    print(f"✓ Формат ключа правильный")
    print(f"   Key: {api_key[:8]}...{api_key[-4:]}")

    # Проверяем баланс через API
    print(f"\n[2/3] Checking API key validity...")
    print(f"   Requesting balance from 2Captcha...")

    try:
        response = requests.get(
            "https://2captcha.com/res.php",
            params={
                "key": api_key,
                "action": "getbalance",
                "json": 1
            },
            timeout=10
        )

        result = response.json()

        if result.get("status") == 1:
            balance = float(result.get("request", 0))
            print(f"✓ API ключ ВАЛИДНЫЙ!")
            print(f"   Баланс: ${balance:.4f}")

            if balance < 0.01:
                print(f"\n⚠️  ВНИМАНИЕ: Недостаточно средств!")
                print(f"   Минимум для теста: $0.01")
                print(f"   Пополните баланс: https://2captcha.com/pay")
                return False

            print(f"\n[3/3] Testing simple request...")
            print(f"   Sending test task (normal captcha)...")

            # Тестовый запрос (не будет списывать деньги, только проверка)
            test_response = requests.get(
                "https://2captcha.com/in.php",
                params={
                    "key": api_key,
                    "method": "userrecaptcha",
                    "googlekey": "test",
                    "pageurl": "https://example.com",
                    "json": 1,
                    "soft_id": 0
                },
                timeout=10
            )

            test_result = test_response.json()

            # Ожидаем ошибку про неверный googlekey - это нормально
            # Главное что API принял ключ
            if test_result.get("status") == 0:
                error = test_result.get("request", "")
                if "ERROR_WRONG_USER_KEY" in error:
                    print(f"\n❌ API ключ НЕ принимается в запросах!")
                    print(f"   Возможно IP заблокирован или ключ неактивен")
                    return False
                else:
                    # Любая другая ошибка - значит ключ принят
                    print(f"✓ API ключ принимается в запросах")

            print(f"\n" + "="*70)
            print(f"✓ ВСЁ ОТЛИЧНО! API ключ работает!")
            print(f"="*70)
            print(f"\nМожно запускать: python test_2captcha_steam.py")
            return True

        elif result.get("status") == 0:
            error = result.get("request", "Unknown error")
            print(f"\n❌ API ключ НЕВАЛИДНЫЙ!")
            print(f"   Ошибка: {error}")

            if "ERROR_WRONG_USER_KEY" in error:
                print(f"\n   Возможные причины:")
                print(f"   1. Ключ неправильный (скопирован с ошибкой)")
                print(f"   2. Ключ удалён или деактивирован")
                print(f"   3. IP адрес заблокирован в настройках")
                print(f"\n   Что делать:")
                print(f"   1. Проверьте ключ на: https://2captcha.com/setting/account")
                print(f"   2. Создайте новый ключ если нужно")
                print(f"   3. Проверьте IP whitelist в настройках")

            return False

    except requests.RequestException as e:
        print(f"\n❌ Ошибка соединения с 2Captcha!")
        print(f"   {e}")
        print(f"\n   Возможные причины:")
        print(f"   1. Нет интернет соединения")
        print(f"   2. 2captcha.com недоступен")
        print(f"   3. Firewall блокирует соединение")
        return False
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = check_2captcha_key()

    if not success:
        print("\n" + "="*70)
        print("TROUBLESHOOTING")
        print("="*70)
        print("\n1. Получите НОВЫЙ API ключ:")
        print("   https://2captcha.com/setting/account")
        print("\n2. Скопируйте ключ БЕЗ пробелов")
        print("\n3. Вставьте в 2captcha_config.txt")
        print("\n4. Запустите этот скрипт снова")
        print("="*70)

    sys.exit(0 if success else 1)
