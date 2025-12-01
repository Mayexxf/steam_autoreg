#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диагностический скрипт для выявления проблемы с AZcaptcha и Steam

Этот скрипт выполняет серию тестов для определения:
1. Работает ли AZcaptcha API в принципе
2. Поддерживает ли AZcaptcha hCaptcha
3. Может ли AZcaptcha решать капчи Steam
4. Какие параметры нужно передавать
"""

import sys
import io

# Настройка кодировки для Windows консоли
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from src.captcha.azcaptcha_solver import AZcaptchaSolver, load_azcaptcha_config


def diagnose():
    """Комплексная диагностика AZcaptcha"""
    print("="*70)
    print("AZcaptcha Diagnostic Tool")
    print("="*70)

    results = {
        "api_key_loaded": False,
        "balance_available": False,
        "balance_amount": 0.0,
        "demo_hcaptcha_works": False,
        "steam_sitekey_accepted": False,
        "error_details": []
    }

    try:
        # Тест 1: Загрузка API ключа
        print("\n[TEST 1/5] Loading API key...")
        api_key = load_azcaptcha_config()

        if not api_key:
            print("❌ FAILED: API ключ не найден")
            results["error_details"].append("API key not found in config")
            return results

        print(f"✓ PASSED: API ключ загружен ({api_key[:8]}...{api_key[-4:]})")
        results["api_key_loaded"] = True

        # Инициализация solver
        solver = AZcaptchaSolver(api_key=api_key, debug=False)

        # Тест 2: Проверка баланса
        print("\n[TEST 2/5] Checking account balance...")
        balance = solver.get_balance()

        if balance is None:
            print("❌ FAILED: Не удалось получить баланс")
            results["error_details"].append("Cannot retrieve balance (invalid API key?)")
            return results

        print(f"✓ PASSED: Баланс доступен (${balance:.4f})")
        results["balance_available"] = True
        results["balance_amount"] = balance

        if balance < 0.001:
            print("⚠️  WARNING: Недостаточно средств для тестов")
            results["error_details"].append(f"Insufficient balance: ${balance:.4f}")
            return results

        # Тест 3: Проверка работы hCaptcha на демо-сайте
        print("\n[TEST 3/5] Testing hCaptcha support (demo site)...")
        print("   Using hCaptcha official test sitekey...")
        print("   ⚠️  This will charge $0.001 from your balance")

        import time
        time.sleep(2)

        demo_sitekey = "10000000-ffff-ffff-ffff-000000000001"
        demo_url = "https://accounts.hcaptcha.com/demo"

        print(f"   Sending task to AZcaptcha...")
        token = solver.solve_hcaptcha(
            website_url=demo_url,
            website_key=demo_sitekey,
            max_attempts=15,
            poll_interval=5
        )

        if token:
            print(f"✓ PASSED: hCaptcha решена успешно!")
            print(f"   Token: {token[:40]}...")
            results["demo_hcaptcha_works"] = True
        else:
            print(f"❌ FAILED: Не удалось решить демо hCaptcha")
            results["error_details"].append("Demo hCaptcha solving failed")
            # Продолжаем тестирование

        # Тест 4: Проверка Steam sitekey
        print("\n[TEST 4/5] Testing Steam sitekey acceptance...")
        print("   Extracting actual Steam sitekey...")

        from selenium import webdriver
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import re

        options = FirefoxOptions()
        options.add_argument("--headless")

        driver = None
        steam_sitekey = None
        steam_url = None

        try:
            driver = webdriver.Firefox(options=options)
            driver.get("https://store.steampowered.com/join/")

            wait = WebDriverWait(driver, 30)
            iframe = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='hcaptcha.com']"))
            )

            iframe_src = iframe.get_attribute("src")
            match = re.search(r'sitekey=([a-f0-9-]+)', iframe_src)

            if match:
                steam_sitekey = match.group(1)
                steam_url = driver.current_url
                print(f"   ✓ Steam sitekey извлечён: {steam_sitekey}")
            else:
                print(f"   ❌ Не удалось извлечь sitekey")

            driver.quit()

        except Exception as e:
            print(f"   ❌ Ошибка при извлечении sitekey: {e}")
            if driver:
                driver.quit()

        if not steam_sitekey:
            print("   ⚠️  SKIPPED: Невозможно протестировать без sitekey")
            results["error_details"].append("Cannot extract Steam sitekey")
            return results

        # Тест 5: Попытка решить Steam капчу
        print("\n[TEST 5/5] Testing Steam captcha solving...")
        print("   ⚠️  This will charge $0.001 from your balance")
        print("   Sending task with User-Agent...")

        time.sleep(2)

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"

        token = solver.solve_hcaptcha(
            website_url=steam_url,
            website_key=steam_sitekey,
            user_agent=user_agent,
            max_attempts=15,
            poll_interval=5
        )

        if token:
            print(f"✓ PASSED: Steam капча решена!")
            print(f"   Token: {token[:40]}...")
            results["steam_sitekey_accepted"] = True
        else:
            print(f"❌ FAILED: Steam sitekey не принимается AZcaptcha")
            results["error_details"].append("Steam sitekey rejected (ERROR_INVALID_SITEKEY)")

        return results

    except KeyboardInterrupt:
        print("\n\n❌ Тест прерван пользователем")
        return results
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        results["error_details"].append(f"Critical error: {str(e)}")
        return results


def print_diagnosis_report(results):
    """Печать итогового отчёта"""
    print("\n" + "="*70)
    print("DIAGNOSIS REPORT")
    print("="*70)

    print(f"\n✓ API Key Loaded:            {'YES' if results['api_key_loaded'] else 'NO'}")
    print(f"✓ Balance Available:         {'YES' if results['balance_available'] else 'NO'}")
    if results['balance_available']:
        print(f"  Balance Amount:            ${results['balance_amount']:.4f}")
    print(f"✓ Demo hCaptcha Works:       {'YES' if results['demo_hcaptcha_works'] else 'NO'}")
    print(f"✓ Steam Sitekey Accepted:    {'YES' if results['steam_sitekey_accepted'] else 'NO'}")

    if results['error_details']:
        print(f"\n⚠️  ERRORS DETECTED:")
        for idx, error in enumerate(results['error_details'], 1):
            print(f"   {idx}. {error}")

    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)

    if results['steam_sitekey_accepted']:
        print("\n✓ AZcaptcha РАБОТАЕТ для Steam!")
        print("  Можете использовать его в production")
    elif results['demo_hcaptcha_works']:
        print("\n⚠️  AZcaptcha работает, но НЕ ПОДДЕРЖИВАЕТ Steam sitekey")
        print("\nВозможные причины:")
        print("  1. Steam блокирует решение через AZcaptcha")
        print("  2. Нужны дополнительные параметры (cookies, proxy)")
        print("  3. AZcaptcha не работает с конкретными доменами")
        print("\nРекомендации:")
        print("  - Попробуйте передать прокси того же региона что и Steam")
        print("  - Используйте альтернативные сервисы: 2Captcha, CapSolver")
        print("  - Обратитесь в поддержку AZcaptcha с вопросом о Steam")
    else:
        print("\n❌ AZcaptcha НЕ РАБОТАЕТ с hCaptcha")
        print("\nВозможные причины:")
        print("  1. Неверный API ключ")
        print("  2. AZcaptcha не поддерживает hCaptcha (только в документации)")
        print("  3. Проблемы на стороне сервиса AZcaptcha")
        print("\nРекомендации:")
        print("  - Проверьте правильность API ключа")
        print("  - Попробуйте создать новый API ключ на azcaptcha.com")
        print("  - ИСПОЛЬЗУЙТЕ АЛЬТЕРНАТИВНЫЕ СЕРВИСЫ:")
        print("    • 2Captcha (https://2captcha.com) - надёжный, проверенный")
        print("    • CapSolver (https://capsolver.com) - для сложных капчи")

    print("\n" + "="*70)


if __name__ == "__main__":
    print("\n⚠️  ВАЖНО: Этот скрипт проведёт 2 платных теста (~$0.002)")
    print("   Убедитесь что на балансе достаточно средств\n")

    input("Нажмите Enter для начала диагностики...")

    results = diagnose()
    print_diagnosis_report(results)

    if results['steam_sitekey_accepted']:
        sys.exit(0)
    else:
        sys.exit(1)
