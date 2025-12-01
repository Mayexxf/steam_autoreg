#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилита для извлечения актуального hCaptcha sitekey со страницы Steam

Этот скрипт запускает браузер, открывает страницу регистрации Steam
и извлекает актуальный sitekey для hCaptcha.
"""

import sys
import io
import re

# Настройка кодировки для Windows консоли
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_steam_sitekey(headless=True):
    """
    Извлекает актуальный hCaptcha sitekey со страницы Steam

    :param headless: Запускать браузер в headless режиме
    :return: Tuple (sitekey, page_url) или (None, None) в случае ошибки
    """
    print("="*70)
    print("Steam hCaptcha Sitekey Extractor")
    print("="*70)

    # Настройка Firefox
    options = FirefoxOptions()
    if headless:
        options.add_argument("--headless")
        print("\n[MODE] Headless mode (без GUI)")
    else:
        print("\n[MODE] Normal mode (с GUI)")

    driver = None

    try:
        print("\n[1/3] Запуск браузера...")
        driver = webdriver.Firefox(options=options)

        print("[2/3] Открытие страницы Steam Join...")
        driver.get("https://store.steampowered.com/join/")

        print("[3/3] Ожидание загрузки hCaptcha...")
        wait = WebDriverWait(driver, 30)

        # Ищем iframe с hCaptcha
        captcha_iframe = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='hcaptcha.com']"))
        )

        # Извлекаем sitekey из src iframe
        iframe_src = captcha_iframe.get_attribute("src")
        print(f"\n✓ hCaptcha iframe найден")
        print(f"  Iframe src (полный):")
        print(f"  {iframe_src}")

        # Парсим sitekey из URL
        sitekey_match = re.search(r'sitekey=([a-f0-9-]+)', iframe_src)

        if not sitekey_match:
            print("\n❌ Не удалось извлечь sitekey из iframe src!")
            driver.quit()
            return None, None

        sitekey = sitekey_match.group(1)
        page_url = driver.current_url

        print(f"\n" + "="*70)
        print(f"✓ Sitekey успешно извлечён!")
        print("="*70)
        print(f"\nSitekey:  {sitekey}")
        print(f"Page URL: {page_url}")

        # Извлекаем ВСЕ параметры из iframe URL
        try:
            # Ищем host из iframe
            host_match = re.search(r'host=([^&]+)', iframe_src)
            if host_match:
                print(f"Host:     {host_match.group(1)}")

            # Ищем endpoint
            endpoint_match = re.search(r'endpoint=([^&]+)', iframe_src)
            if endpoint_match:
                print(f"Endpoint: {endpoint_match.group(1)}")

            # Ищем rqdata (Enterprise параметр)
            rqdata_match = re.search(r'rqdata=([^&]+)', iframe_src)
            if rqdata_match:
                print(f"RQData:   {rqdata_match.group(1)}")
                print("\n⚠️  ВНИМАНИЕ: Обнаружен rqdata - это hCaptcha Enterprise!")

            # Ищем custom параметры
            custom_match = re.search(r'custom=([^&]+)', iframe_src)
            if custom_match:
                print(f"Custom:   {custom_match.group(1)}")

            # Проверяем другие параметры
            params_to_check = ['hl', 'theme', 'size', 'tab_index', 'challange', 'id']
            for param in params_to_check:
                match = re.search(rf'{param}=([^&]+)', iframe_src)
                if match:
                    print(f"{param.capitalize():9s}: {match.group(1)}")

        except Exception as e:
            print(f"Ошибка парсинга параметров: {e}")

        print("\n" + "="*70)
        print("Дополнительная информация:")
        print("="*70)

        # Проверяем div с hcaptcha
        try:
            hcaptcha_divs = driver.find_elements(By.CLASS_NAME, "h-captcha")
            if hcaptcha_divs:
                print(f"\n✓ Найдено {len(hcaptcha_divs)} элемент(ов) с классом 'h-captcha'")
                for idx, div in enumerate(hcaptcha_divs):
                    print(f"\n  Элемент #{idx + 1}:")
                    print(f"    data-sitekey:  {div.get_attribute('data-sitekey')}")
                    print(f"    data-callback: {div.get_attribute('data-callback')}")
                    print(f"    data-theme:    {div.get_attribute('data-theme')}")
                    print(f"    data-size:     {div.get_attribute('data-size')}")
        except Exception as e:
            print(f"⚠️  Ошибка при поиске h-captcha div: {e}")

        # Проверяем скрипты hCaptcha
        try:
            scripts = driver.find_elements(By.TAG_NAME, "script")
            hcaptcha_scripts = [s for s in scripts if s.get_attribute("src") and "hcaptcha" in s.get_attribute("src")]
            if hcaptcha_scripts:
                print(f"\n✓ Найдено {len(hcaptcha_scripts)} hCaptcha скрипт(ов):")
                for script in hcaptcha_scripts:
                    print(f"    {script.get_attribute('src')}")
        except Exception:
            pass

        print("\n" + "="*70)
        print("Используйте этот sitekey для тестирования AZcaptcha!")
        print("="*70)

        driver.quit()
        return sitekey, page_url

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

        if driver:
            driver.quit()

        return None, None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Извлечение hCaptcha sitekey со страницы Steam")
    parser.add_argument("--no-headless", action="store_true", help="Запустить браузер с GUI")

    args = parser.parse_args()

    sitekey, page_url = get_steam_sitekey(headless=not args.no_headless)

    if sitekey:
        sys.exit(0)
    else:
        sys.exit(1)
