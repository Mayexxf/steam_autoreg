#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки SteamEnterpriseCaptchaSolver
Демонстрирует полный цикл решения капчи при регистрации Steam
"""

import sys
import argparse
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions

# Импортируем наш новый solver
from src.captcha.steam_enterprise_solver import SteamEnterpriseCaptchaSolver


def test_with_firefox(service: str, headless: bool = False):
    """Тестирование с Firefox"""
    print("=" * 80)
    print(f"Тестирование SteamEnterpriseCaptchaSolver с Firefox (service: {service})")
    print("=" * 80)

    options = FirefoxOptions()
    if headless:
        options.add_argument("--headless")

    # Базовые настройки для обхода детекции
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference('useAutomationExtension', False)

    driver = webdriver.Firefox(options=options)

    try:
        # Создаём solver
        solver = SteamEnterpriseCaptchaSolver(service=service, debug=True)

        # Открываем страницу регистрации Steam
        print("\nОткрываем https://store.steampowered.com/join/...")
        driver.get("https://store.steampowered.com/join/")

        # Запускаем полный цикл решения капчи
        success = solver.solve_and_inject(driver)

        if success:
            print("\n" + "=" * 80)
            print("УСПЕХ! Капча решена и токен инжектирован")
            print("=" * 80)
            print("\nТеперь можно заполнить форму и отправить регистрацию")

            # Даём время посмотреть на результат
            if not headless:
                input("\nНажмите Enter чтобы закрыть браузер...")

            return True
        else:
            print("\n" + "=" * 80)
            print("ПРОВАЛ: Не удалось решить капчу")
            print("=" * 80)
            driver.save_screenshot("steam_enterprise_test_fail.png")
            print("Скриншот сохранён: steam_enterprise_test_fail.png")
            return False

    except Exception as e:
        print(f"\nИСКЛЮЧЕНИЕ: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot("steam_enterprise_test_error.png")
        print("Скриншот сохранён: steam_enterprise_test_error.png")
        return False
    finally:
        driver.quit()


def test_with_chrome(service: str, headless: bool = False):
    """Тестирование с Chrome"""
    print("=" * 80)
    print(f"Тестирование SteamEnterpriseCaptchaSolver с Chrome (service: {service})")
    print("=" * 80)

    options = ChromeOptions()
    if headless:
        options.add_argument("--headless=new")

    # Базовые настройки для обхода детекции
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=options)

    # Скрываем webdriver через CDP
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    })

    try:
        # Создаём solver
        solver = SteamEnterpriseCaptchaSolver(service=service, debug=True)

        # Открываем страницу регистрации Steam
        print("\nОткрываем https://store.steampowered.com/join/...")
        driver.get("https://store.steampowered.com/join/")

        # Запускаем полный цикл решения капчи
        success = solver.solve_and_inject(driver)

        if success:
            print("\n" + "=" * 80)
            print("УСПЕХ! Капча решена и токен инжектирован")
            print("=" * 80)
            print("\nТеперь можно заполнить форму и отправить регистрацию")

            # Даём время посмотреть на результат
            if not headless:
                input("\nНажмите Enter чтобы закрыть браузер...")

            return True
        else:
            print("\n" + "=" * 80)
            print("ПРОВАЛ: Не удалось решить капчу")
            print("=" * 80)
            driver.save_screenshot("steam_enterprise_test_fail.png")
            print("Скриншот сохранён: steam_enterprise_test_fail.png")
            return False

    except Exception as e:
        print(f"\nИСКЛЮЧЕНИЕ: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot("steam_enterprise_test_error.png")
        print("Скриншот сохранён: steam_enterprise_test_error.png")
        return False
    finally:
        driver.quit()


def main():
    parser = argparse.ArgumentParser(
        description="Тестирование SteamEnterpriseCaptchaSolver",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Тест с CapSolver (по умолчанию)
  python test_steam_enterprise_solver.py

  # Тест с 2Captcha
  python test_steam_enterprise_solver.py --service 2captcha

  # Тест с AntiCaptcha в headless режиме
  python test_steam_enterprise_solver.py --service anticaptcha --headless

  # Тест с Chrome вместо Firefox
  python test_steam_enterprise_solver.py --browser chrome

Требования:
  • API ключ должен быть в файле {service}_config.txt или в переменной окружения
  • Для CapSolver: capsolver_config.txt или CAPSOLVER_API_KEY
  • Для 2Captcha: 2captcha_config.txt или TWOCAPTCHA_API_KEY
  • Для AntiCaptcha: anticaptcha_config.txt или ANTICAPTCHA_API_KEY
        """
    )

    parser.add_argument(
        "--service",
        choices=["capsolver", "2captcha", "anticaptcha"],
        default="capsolver",
        help="Сервис для решения капчи (по умолчанию: capsolver)"
    )

    parser.add_argument(
        "--browser",
        choices=["firefox", "chrome"],
        default="firefox",
        help="Браузер для тестирования (по умолчанию: firefox)"
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Запуск браузера в headless режиме"
    )

    args = parser.parse_args()

    # Запускаем тест
    if args.browser == "firefox":
        success = test_with_firefox(args.service, args.headless)
    else:
        success = test_with_chrome(args.service, args.headless)

    # Возвращаем код выхода
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
