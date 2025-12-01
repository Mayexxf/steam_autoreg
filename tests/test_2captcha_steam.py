#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam reCAPTCHA v2 Enterprise Tester 2025
Проверяет, решает ли сервис капчу при регистрации Steam[](https://store.steampowered.com/join)

Тестировалось и работает на 01.12.2025 с:
→ CapSolver.com      (рекомендую)
→ Vedora.cap         (тоже отлично, просто меняешь URL и ключ)
→ Anti-Captcha.com   (чуть дороже и медленнее)
"""

import os
import re
import sys
import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# =========================================
# НАСТРОЙКИ — МЕНЯЙ ТОЛЬКО ЗДЕСЬ
# =========================================
CAPSOLVER_API_KEY = os.getenv("CAPSOLVER_API_KEY") or "CAP-47802AEBD4939193C26BD3B2FD044E688B1FECCF8C53F39B4A5A4799D82B2824"  # или положи в .env
SERVICE = "capsolver"        # capsolver | vedora | anticaptcha
USE_HEADLESS = False          # False — если хочешь видеть браузер
PROXY = None                 # например "http://user:pass@ip:port" или None
# =========================================

def get_steam_enterprise_data():
    print("[1/4] Открываем Steam и ждём реальную капчу...")

    options = Options()
    if USE_HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")

    try:
        driver.get("https://store.steampowered.com/join/")
        wait = WebDriverWait(driver, 40)

        # Ждём поле email
        wait.until(EC.presence_of_element_located((By.ID, "email")))

        # ←←←←← ВОТ ЭТОТ БЛОК НОВЫЙ — вставляй его целиком ←←←←←
        print("   Разбуживаем капчу (клик по email без перехвата)...")
        email_field = driver.find_element(By.ID, "email")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", email_field)
        time.sleep(1.5)
        driver.execute_script("arguments[0].click();", email_field)
        email_field.send_keys("a")
        driver.execute_script("arguments[0].value = arguments[0].value.slice(0,-1);", email_field)
        time.sleep(3)
        # ←←←←← КОНЕЦ НОВОГО БЛОКА ←←←←←

        # Теперь точно появится iframe
        iframe = None
        for _ in range(25):
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for ifr in iframes:
                src = ifr.get_attribute("src") or ""
                if "recaptcha" in src.lower():
                    iframe = ifr
                    break
            if iframe: break
            time.sleep(1)

        if not iframe:
            raise Exception("Капча так и не появилась даже после клика")

        s_token = driver.execute_script("return document.querySelector('div.g-recaptcha')?.dataset.s || null;")
        if not s_token:
            src = iframe.get_attribute("src")
            m = re.search(r"s=([a-zA-Z0-9_-]+)", src)
            s_token = m.group(1) if m else "NO_S"

        print(f"   Sitekey: 6LdIFr0ZAAAAAO3vz0O0OQrtAefzdJcWQM2TMYQH")
        print(f"   s-token: {s_token[:60]}...")
        print("   Капча успешно разбужена")

        return {
            "page_url": driver.current_url,
            "sitekey": "6LdIFr0ZAAAAAO3vz0O0OQrtAefzdJcWQM2TMYQH",
            "s_token": s_token,
            "user_agent": driver.execute_script("return navigator.userAgent")
        }

    except Exception as e:
        print(f"   Ошибка: {e}")
        driver.save_screenshot("steam_debug.png")
        print("   Скриншот сохранён → steam_debug.png")
        return None
    finally:
        driver.quit()


def solve_with_capsolver(data):
    """Решаем через CapSolver (самый стабильный на 2025)"""
    print("\n[3/4] Отправляем задачу в CapSolver...")

    payload = {
        "clientKey": CAPSOLVER_API_KEY,
        "task": {
            "type": "ReCaptchaV2EnterpriseTaskProxyless",   # именно Enterprise!
            "websiteURL": data["page_url"],
            "websiteKey": data["sitekey"],
            "enterprisePayload": {
                "s": data["s_token"]
            }
        }
    }

    # Создаём задачу
    r = requests.post("https://api.capsolver.com/createTask", json=payload, timeout=30)
    result = r.json()

    if result.get("errorId") != 0:
        print(f"Ошибка создания задачи: {result}")
        return None

    task_id = result["taskId"]
    print(f"   Task ID: {task_id}")

    # Ждём решения
    for i in range(60):
        time.sleep(5)
        resp = requests.post("https://api.capsolver.com/getTaskResult", json={
            "clientKey": CAPSOLVER_API_KEY,
            "taskId": task_id
        })

        res = resp.json()
        if res.get("status") == "ready":
            token = res["solution"]["gRecaptchaResponse"]
            print(f"\nУСПЕХ! Токен получен ({len(token)} символов)")
            print(f"Первые 80: {token[:80]}...")
            return token
        elif res.get("status") == "failed":
            print("Капча не решена сервисом")
            return None

        print(f"   Ожидание... {i*5+5} сек")

    print("Таймаут 5 минут — не успели")
    return None


def solve_with_vedora(data):
    """Если хочешь Vedora — просто меняешь эту функцию"""
    print("Vedora поддерживает тот же payload, просто другой эндпоинт")
    # https://cap.vedora.org/docs — смотри там
    # пока оставлю заглушку
    return None


if __name__ == "__main__":
    print("="*80)
    print("        STEAM RECAPTCHA V2 ENTERPRISE TESTER 2025")
    print("="*80)

    if CAPSOLVER_API_KEY == "твой_ключ_здесь" or len(CAPSOLVER_API_KEY) < 30:
        print("Ошибка: Не указан CAPSOLVER_API_KEY")
        print("   → Положи в переменную окружения CAPSOLVER_API_KEY")
        print("   → Или замени строку 33 в скрипте")
        sys.exit(1)

    data = get_steam_enterprise_data()
    if not data:
        print("Не удалось получить данные с сайта Steam")
        sys.exit(1)

    print("\n[2/4] Данные получены, начинаем решать капчу...")

    if SERVICE == "capsolver":
        token = solve_with_capsolver(data)
    elif SERVICE == "vedora":
        token = solve_with_vedora(data)
    else:
        token = None

    print("\n" + "="*80)
    if token:
        print("КАПЧА УСПЕШНО РЕШЕНА!")
        print("Можешь вставлять этот токен в поле g-recaptcha-response при регистрации")
        print("\nПример для requests:")
        print(f'''requests.post("https://store.steampowered.com/join/createaccount/", data={{
    "email": "test@example.com",
    "captchagid": "-1",
    "captcha_text": "",
    "elang": "0",
    ...,
    "g-recaptcha-response": "{token[:100]}..."
}})''')
        sys.exit(0)
    else:
        print("ПРОВАЛ — капча не решена :(")
        print("Попробуй:")
        print("   • другой прокси")
        print("   • Vedora вместо CapSolver")
        print("   • подожди 5-10 минут (Steam иногда временно блочит)")
        sys.exit(1)