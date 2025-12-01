#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест 2Captcha через Task API (новый формат)
Некоторые аккаунты используют новый API формат
"""

import sys
import io
import requests
import time

# Настройка кодировки для Windows консоли
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Загружаем API ключ
with open("2captcha_config.txt", 'r', encoding='utf-8') as f:
    API_KEY = f.read().strip()

print("="*70)
print("2Captcha Task API Test (New Format)")
print("="*70)

print(f"\nAPI Key: {API_KEY[:8]}...{API_KEY[-4:]}")

# Проверяем баланс
print("\n[1/3] Checking balance...")
balance_response = requests.get(
    "https://2captcha.com/res.php",
    params={"key": API_KEY, "action": "getbalance", "json": 1}
)

balance_data = balance_response.json()
if balance_data.get("status") == 1:
    print(f"✓ Balance: ${float(balance_data.get('request', 0)):.4f}")
else:
    print(f"❌ Error: {balance_data.get('request')}")
    sys.exit(1)

# Пробуем через старый метод userrecaptcha (некоторые аккаунты)
print("\n[2/3] Trying alternative method: userrecaptcha...")
print("(Некоторые аккаунты 2Captcha используют этот метод для hCaptcha)\n")

params = {
    "key": API_KEY,
    "method": "userrecaptcha",
    "version": "v2",
    "googlekey": "10000000-ffff-ffff-ffff-000000000001",
    "pageurl": "https://accounts.hcaptcha.com/demo",
    "json": 1
}

print("Request parameters:")
for k, v in params.items():
    if k == "key":
        print(f"  {k}: {v[:8]}...{v[-4:]}")
    else:
        print(f"  {k}: {v}")

task_response = requests.post("https://2captcha.com/in.php", data=params)
print(f"\nResponse: {task_response.text}")

task_data = task_response.json()

if task_data.get("status") == 1:
    task_id = task_data.get("request")
    print(f"✓ Task created! ID: {task_id}")

    # Ждём решения
    print("\n[3/3] Waiting for solution...")
    for i in range(30):
        time.sleep(3)
        result_response = requests.get(
            "https://2captcha.com/res.php",
            params={"key": API_KEY, "action": "get", "id": task_id, "json": 1}
        )
        result_data = result_response.json()

        if result_data.get("status") == 1:
            print(f"\n✓ SUCCESS!")
            print(f"Token: {result_data.get('request')[:60]}...")
            sys.exit(0)
        elif result_data.get("request") == "CAPCHA_NOT_READY":
            print(f"Attempt {i+1}/30: Processing...")
        else:
            print(f"❌ Error: {result_data.get('request')}")
            sys.exit(1)
else:
    print(f"❌ Method failed: {task_data.get('request')}")

# Пробуем проверить какие методы вообще доступны
print("\n" + "="*70)
print("Checking available methods...")
print("="*70)

# Проверяем доступность разных типов капчи
test_methods = [
    ("normal", {"method": "base64", "body": "iVBORw0KGgo"}),
    ("recaptcha", {"method": "userrecaptcha", "googlekey": "test", "pageurl": "http://test.com"}),
    ("hcaptcha", {"method": "hcaptcha", "sitekey": "test", "pageurl": "http://test.com"}),
]

for method_name, test_params in test_methods:
    test_params["key"] = API_KEY
    test_params["json"] = 1

    test_resp = requests.post("https://2captcha.com/in.php", data=test_params, timeout=5)
    try:
        test_data = test_resp.json()
        error = test_data.get("request", "")

        if "ERROR_METHOD_CALL" in error:
            status = "❌ NOT AVAILABLE"
        elif "ERROR_WRONG_USER_KEY" in error:
            status = "⚠️  API KEY ISSUE"
        elif error.startswith("ERROR_"):
            status = f"⚠️  Available ({error})"
        else:
            status = "✅ AVAILABLE"

        print(f"{method_name:15s}: {status}")
    except:
        print(f"{method_name:15s}: ❌ ERROR")

print("\n" + "="*70)
print("DIAGNOSIS:")
print("="*70)
print("\nВаш аккаунт 2Captcha имеет следующие ограничения:")
print("• Если hcaptcha = NOT AVAILABLE:")
print("  - Метод недоступен для вашего аккаунта")
print("  - Свяжитесь с поддержкой: https://2captcha.com/support")
print("  - Или используйте CapSolver вместо 2Captcha")
print("\n• Если recaptcha = AVAILABLE:")
print("  - Попробуйте метод 'userrecaptcha' для hCaptcha")
print("  - Это альтернативный способ")
print("\n• Решение: используйте CapSolver")
print("  - CapSolver 100% работает с hCaptcha")
print("  - Регистрация: https://capsolver.com")
print("="*70)
