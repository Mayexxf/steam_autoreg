#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Минимальный тест 2Captcha API - прямой запрос без дополнительных библиотек
"""

import sys
import io
import requests

# Настройка кодировки для Windows консоли
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Загружаем API ключ
with open("2captcha_config.txt", 'r', encoding='utf-8') as f:
    API_KEY = f.read().strip()

print("="*70)
print("2Captcha Minimal Test - Direct API Call")
print("="*70)

print(f"\nAPI Key: {API_KEY[:8]}...{API_KEY[-4:]}")
print(f"API Key length: {len(API_KEY)}")

# Шаг 1: Проверяем баланс
print("\n[1/3] Checking balance...")
balance_response = requests.get(
    "https://2captcha.com/res.php",
    params={
        "key": API_KEY,
        "action": "getbalance",
        "json": 1
    }
)

print(f"Balance response: {balance_response.text}")
balance_data = balance_response.json()

if balance_data.get("status") == 1:
    balance = float(balance_data.get("request", 0))
    print(f"✓ Balance: ${balance:.4f}")
else:
    print(f"❌ Error: {balance_data.get('request')}")
    sys.exit(1)

# Шаг 2: Отправляем hCaptcha задачу (самый простой вариант)
print("\n[2/3] Submitting hCaptcha task...")

# Используем hCaptcha demo сайт для теста
params = {
    "key": API_KEY,
    "method": "hcaptcha",
    "sitekey": "10000000-ffff-ffff-ffff-000000000001",  # Официальный тестовый ключ
    "pageurl": "https://accounts.hcaptcha.com/demo",
    "json": 1
}

print(f"\nRequest URL: https://2captcha.com/in.php")
print(f"Parameters:")
for k, v in params.items():
    if k == "key":
        print(f"  {k}: {v[:8]}...{v[-4:]}")
    else:
        print(f"  {k}: {v}")

task_response = requests.post(
    "https://2captcha.com/in.php",
    data=params
)

print(f"\nResponse status: {task_response.status_code}")
print(f"Response body: {task_response.text}")

task_data = task_response.json()

if task_data.get("status") == 1:
    task_id = task_data.get("request")
    print(f"✓ Task created! ID: {task_id}")
else:
    error = task_data.get("request", "Unknown error")
    print(f"❌ Error: {error}")

    # Подсказки по ошибкам
    if error == "ERROR_WRONG_USER_KEY":
        print("\n💡 API ключ неверный:")
        print("   1. Проверьте ключ на https://2captcha.com/setting/account")
        print("   2. Убедитесь что нет пробелов")
        print("   3. Длина должна быть 32 символа")
    elif error == "ERROR_KEY_DOES_NOT_EXIST":
        print("\n💡 API ключ не существует:")
        print("   1. Создайте новый ключ на https://2captcha.com/setting/account")
    elif error == "ERROR_ZERO_BALANCE":
        print("\n💡 Недостаточно средств:")
        print("   1. Пополните баланс: https://2captcha.com/pay")
    elif error == "ERROR_METHOD_CALL":
        print("\n💡 Неверные параметры запроса:")
        print("   1. Проверьте что метод = 'hcaptcha'")
        print("   2. Проверьте формат sitekey")
        print("   3. Проверьте формат pageurl")

    sys.exit(1)

# Шаг 3: Получаем результат
print("\n[3/3] Waiting for solution...")
import time

for i in range(30):
    time.sleep(3)

    result_response = requests.get(
        "https://2captcha.com/res.php",
        params={
            "key": API_KEY,
            "action": "get",
            "id": task_id,
            "json": 1
        }
    )

    result_data = result_response.json()

    if result_data.get("status") == 1:
        token = result_data.get("request")
        print(f"\n✓ SUCCESS! Captcha solved!")
        print(f"Token: {token[:60]}...")
        print(f"Token length: {len(token)}")
        print("\n" + "="*70)
        print("2Captcha API works perfectly!")
        print("="*70)
        sys.exit(0)
    elif result_data.get("request") == "CAPCHA_NOT_READY":
        print(f"Attempt {i+1}/30: Processing...")
        continue
    else:
        print(f"❌ Error: {result_data.get('request')}")
        sys.exit(1)

print("❌ Timeout - captcha not solved in 90 seconds")
sys.exit(1)
