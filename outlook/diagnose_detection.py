#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диагностический скрипт для определения факторов обнаружения
"""

import asyncio
import requests
from playwright.async_api import async_playwright

PROXY = "MPzEefwWaIUi:tc6aWZqR@pool.proxy.market:10000"


def check_proxy_type():
    """Проверяет тип прокси (datacenter vs residential)"""
    print("\n" + "="*60)
    print("ПРОВЕРКА ПРОКСИ")
    print("="*60)

    try:
        # Парсим прокси
        parts = PROXY.split('@')
        if len(parts) == 2:
            auth, server = parts
            username, password = auth.split(':')
            host, port = server.split(':')
        else:
            print("❌ Неверный формат прокси")
            return

        proxy_dict = {
            'http': f'http://{PROXY.split("@")[1]}',
            'https': f'http://{PROXY.split("@")[1]}'
        }
        auth_tuple = (username, password)

        # Проверяем IP
        print(f"\n[1] Получаем IP прокси...")
        response = requests.get(
            'http://ip-api.com/json/?fields=status,country,city,isp,proxy,hosting,mobile,query',
            proxies=proxy_dict,
            auth=auth_tuple,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            ip = data.get('query', 'unknown')
            country = data.get('country', 'unknown')
            city = data.get('city', 'unknown')
            isp = data.get('isp', 'unknown')
            is_proxy = data.get('proxy', False)
            is_hosting = data.get('hosting', False)
            is_mobile = data.get('mobile', False)

            print(f"   IP: {ip}")
            print(f"   Страна: {country}, {city}")
            print(f"   ISP: {isp}")
            print(f"   Proxy detected: {is_proxy}")
            print(f"   Hosting/Datacenter: {is_hosting}")
            print(f"   Mobile: {is_mobile}")

            # Анализ
            print(f"\n[2] Анализ:")
            if is_hosting:
                print("   [!] DATACENTER PROXY - легко детектируется!")
                print("   [i] Рекомендация: Используйте residential proxy")
            elif is_mobile:
                print("   [+] MOBILE PROXY - хорошо")
            else:
                print("   [+] RESIDENTIAL PROXY - отлично")

            if is_proxy:
                print("   [!] IP помечен как прокси в базах данных")
                print("   [i] Microsoft может использовать эти базы для блокировки")

        else:
            print(f"   [!] Ошибка: {response.status_code}")

    except Exception as e:
        print(f"   [!] Ошибка проверки: {e}")


async def check_browser_leaks():
    """Проверяет утечки браузера (WebRTC, fingerprint)"""
    print("\n" + "="*60)
    print("ПРОВЕРКА УТЕЧЕК БРАУЗЕРА")
    print("="*60)

    playwright = await async_playwright().start()

    # Парсим прокси
    parts = PROXY.split('@')
    auth, server = parts
    username, password = auth.split(':')
    host, port = server.split(':')

    proxy_config = {
        "server": f"http://{host}:{port}",
        "username": username,
        "password": password
    }

    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(proxy=proxy_config)
    page = await context.new_page()

    print("\n[1] Проверка WebRTC утечек...")

    # Проверка WebRTC
    webrtc_result = await page.evaluate("""
        async () => {
            try {
                const pc = new RTCPeerConnection({
                    iceServers: [{urls: 'stun:stun.l.google.com:19302'}]
                });

                return new Promise((resolve) => {
                    let ips = [];

                    pc.onicecandidate = (event) => {
                        if (event.candidate) {
                            const candidate = event.candidate.candidate;
                            const ipRegex = /([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3})/;
                            const match = candidate.match(ipRegex);
                            if (match && !ips.includes(match[1])) {
                                ips.push(match[1]);
                            }
                        }

                        if (event.candidate === null) {
                            resolve(ips);
                        }
                    };

                    pc.createDataChannel('');
                    pc.createOffer().then(offer => pc.setLocalDescription(offer));

                    // Таймаут на случай если не все кандидаты собраны
                    setTimeout(() => resolve(ips), 3000);
                });
            } catch (e) {
                return ['ERROR: ' + e.message];
            }
        }
    """)

    print(f"   Обнаруженные IP через WebRTC: {webrtc_result}")
    if len(webrtc_result) > 0 and not webrtc_result[0].startswith('ERROR'):
        print("   [!] WebRTC УТЕЧКА! Реальный IP раскрывается")
        print("   [i] Нужно блокировать WebRTC")
    else:
        print("   [+] WebRTC не утекает")

    print("\n[2] Проверка navigator.webdriver...")
    webdriver = await page.evaluate("() => navigator.webdriver")
    print(f"   navigator.webdriver = {webdriver}")
    if webdriver:
        print("   [!] AUTOMATION DETECTED!")
    else:
        print("   [+] OK (false или undefined)")

    print("\n[3] Проверка window.chrome...")
    has_chrome = await page.evaluate("() => typeof window.chrome !== 'undefined'")
    print(f"   window.chrome exists: {has_chrome}")
    if not has_chrome:
        print("   [!] window.chrome отсутствует (подозрительно для Chrome)")
    else:
        print("   [+] OK")

    print("\n[4] Проверка permissions...")
    permissions_state = await page.evaluate("""
        async () => {
            try {
                const result = await navigator.permissions.query({name: 'notifications'});
                return result.state;
            } catch(e) {
                return 'ERROR: ' + e.message;
            }
        }
    """)
    print(f"   Notifications permission: {permissions_state}")
    if permissions_state == 'denied':
        print("   [!] 'denied' может быть признаком headless/automation")

    print("\n[5] Проверка plugins...")
    plugins_count = await page.evaluate("() => navigator.plugins.length")
    print(f"   Количество plugins: {plugins_count}")
    if plugins_count == 0:
        print("   [!] Нет plugins - признак headless")
    else:
        print("   [+] OK")

    await browser.close()
    await playwright.stop()


async def check_http_headers():
    """Проверяет HTTP заголовки"""
    print("\n" + "="*60)
    print("ПРОВЕРКА HTTP ЗАГОЛОВКОВ")
    print("="*60)

    playwright = await async_playwright().start()

    parts = PROXY.split('@')
    auth, server = parts
    username, password = auth.split(':')
    host, port = server.split(':')

    proxy_config = {
        "server": f"http://{host}:{port}",
        "username": username,
        "password": password
    }

    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(proxy=proxy_config)
    page = await context.new_page()

    # Перехватываем заголовки
    print("\n[1] Собираем заголовки запроса к httpbin.org/headers...")

    headers_captured = []

    async def capture_headers(route, request):
        headers_captured.append(dict(request.headers))
        await route.continue_()

    await page.route("**/*", capture_headers)

    try:
        await page.goto("https://httpbin.org/headers", timeout=15000)
        await asyncio.sleep(2)

        if headers_captured:
            print("\n   Заголовки:")
            for key, value in headers_captured[0].items():
                print(f"   {key}: {value}")

            # Проверяем важные заголовки
            print("\n[2] Анализ:")

            headers = headers_captured[0]

            if 'sec-ch-ua' not in headers:
                print("   [!] Отсутствует sec-ch-ua (Client Hints)")
            else:
                print(f"   [+] sec-ch-ua: {headers['sec-ch-ua']}")

            if 'sec-ch-ua-platform' not in headers:
                print("   [!] Отсутствует sec-ch-ua-platform")
            else:
                print(f"   [+] sec-ch-ua-platform: {headers['sec-ch-ua-platform']}")

            if 'accept-language' not in headers:
                print("   [!] Отсутствует accept-language")
            else:
                print(f"   [+] accept-language: {headers['accept-language']}")

    except Exception as e:
        print(f"   [!] Ошибка: {e}")

    await browser.close()
    await playwright.stop()


async def main():
    """Главная функция диагностики"""
    print("\n" + "="*60)
    print("ДИАГНОСТИКА ФАКТОРОВ ОБНАРУЖЕНИЯ OUTLOOK")
    print("="*60)

    # 1. Проверка прокси
    check_proxy_type()

    # 2. Проверка утечек браузера
    await check_browser_leaks()

    # 3. Проверка HTTP заголовков
    await check_http_headers()

    print("\n" + "="*60)
    print("ДИАГНОСТИКА ЗАВЕРШЕНА")
    print("="*60)
    print("\n[i] Основные рекомендации будут выше")


if __name__ == "__main__":
    asyncio.run(main())
