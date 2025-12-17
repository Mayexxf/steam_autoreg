#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диагностика детекции Microsoft
Проверяет все возможные причины блокировки
"""
import asyncio
import sys
import os

sys.path.insert(0, 'C:\\projects')
from outlook.browser import BrowserManager


async def check_ip_reputation(page):
    """Проверка IP reputation и типа"""
    print("\n" + "="*80)
    print("[1] IP REPUTATION CHECK")
    print("="*80)

    try:
        await page.goto("http://ip-api.com/json/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)

        ip_data = await page.evaluate("""
            () => {
                try {
                    return JSON.parse(document.body.innerText);
                } catch(e) {
                    return document.body.innerText;
                }
            }
        """)

        print(f"\n✅ IP Data:")
        if isinstance(ip_data, dict):
            print(f"   IP: {ip_data.get('query', 'N/A')}")
            print(f"   Country: {ip_data.get('country', 'N/A')}")
            print(f"   City: {ip_data.get('city', 'N/A')}")
            print(f"   ISP: {ip_data.get('isp', 'N/A')}")
            print(f"   Org: {ip_data.get('org', 'N/A')}")
            print(f"   AS: {ip_data.get('as', 'N/A')}")

            # Проверка типа IP
            isp = ip_data.get('isp', '').lower()
            org = ip_data.get('org', '').lower()

            suspicious_keywords = ['hosting', 'datacenter', 'vpn', 'proxy', 'cloud', 'virtual', 'server']
            is_suspicious = any(kw in isp or kw in org for kw in suspicious_keywords)

            if is_suspicious:
                print(f"\n   ⚠️  WARNING: IP может быть детектирован как proxy/datacenter!")
                print(f"   Рекомендация: использовать residential proxy")
            else:
                print(f"\n   ✅ IP выглядит как residential (хорошо)")
        else:
            print(f"   Data: {ip_data}")

    except Exception as e:
        print(f"   ❌ Error: {e}")


async def check_webrtc_leak(page):
    """Проверка WebRTC IP leak"""
    print("\n" + "="*80)
    print("[2] WEBRTC LEAK CHECK")
    print("="*80)

    try:
        await page.goto("https://browserleaks.com/webrtc", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(8)  # Даем время для WebRTC обнаружения

        # Проверяем наличие обнаруженных IP
        leak_data = await page.evaluate("""
            () => {
                const results = {
                    publicIPs: [],
                    localIPs: [],
                    hasLeak: false
                };

                // Ищем все IP адреса на странице
                const text = document.body.innerText;
                const ipRegex = /\\b(?:[0-9]{1,3}\\.){3}[0-9]{1,3}\\b/g;
                const ips = text.match(ipRegex) || [];

                results.publicIPs = ips.filter(ip => !ip.startsWith('192.168.') && !ip.startsWith('10.') && !ip.startsWith('172.'));
                results.localIPs = ips.filter(ip => ip.startsWith('192.168.') || ip.startsWith('10.') || ip.startsWith('172.'));
                results.hasLeak = results.publicIPs.length > 1;  // Больше 1 = утечка

                return results;
            }
        """)

        print(f"\n   Public IPs detected: {len(leak_data['publicIPs'])}")
        if leak_data['publicIPs']:
            for ip in leak_data['publicIPs']:
                print(f"      - {ip}")

        print(f"   Local IPs detected: {len(leak_data['localIPs'])}")
        if leak_data['localIPs']:
            for ip in leak_data['localIPs']:
                print(f"      - {ip}")

        if leak_data['hasLeak']:
            print(f"\n   ❌ WebRTC LEAK DETECTED! Реальный IP раскрыт!")
            print(f"   Решение: улучшить блокировку WebRTC")
        else:
            print(f"\n   ✅ No WebRTC leak detected")

    except Exception as e:
        print(f"   ❌ Error: {e}")


async def check_fonts(page):
    """Проверка доступных шрифтов"""
    print("\n" + "="*80)
    print("[3] FONT FINGERPRINT CHECK")
    print("="*80)

    try:
        fonts = await page.evaluate("""
            () => {
                const testFonts = [
                    'Arial', 'Arial Black', 'Calibri', 'Cambria', 'Comic Sans MS',
                    'Courier New', 'Georgia', 'Impact', 'Lucida Console', 'Palatino',
                    'Tahoma', 'Times New Roman', 'Trebuchet MS', 'Verdana',
                    'Consolas', 'Segoe UI', 'Microsoft Sans Serif'
                ];

                const available = [];
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');

                testFonts.forEach(font => {
                    ctx.font = `12px "${font}", monospace`;
                    const metrics1 = ctx.measureText('mmmmmmmmmmlli');

                    ctx.font = '12px monospace';
                    const metrics2 = ctx.measureText('mmmmmmmmmmlli');

                    if (metrics1.width !== metrics2.width) {
                        available.push(font);
                    }
                });

                return available;
            }
        """)

        print(f"\n   Available fonts: {len(fonts)}")
        for font in fonts:
            print(f"      - {font}")

        if len(fonts) < 10:
            print(f"\n   ⚠️  WARNING: Мало шрифтов ({len(fonts)}). Это может указывать на automation.")
            print(f"   Рекомендация: установить дополнительные шрифты в систему")
        else:
            print(f"\n   ✅ Достаточно шрифтов ({len(fonts)})")

    except Exception as e:
        print(f"   ❌ Error: {e}")


async def check_http_headers(page):
    """Проверка HTTP заголовков"""
    print("\n" + "="*80)
    print("[4] HTTP HEADERS CHECK")
    print("="*80)

    headers_captured = []

    def capture_request(request):
        if 'microsoft.com' in request.url or 'outlook' in request.url:
            headers_captured.append({
                'url': request.url[:80],
                'headers': dict(request.headers)
            })

    page.on('request', capture_request)

    try:
        await page.goto("https://www.microsoft.com/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        if headers_captured:
            print(f"\n   Captured {len(headers_captured)} requests")

            # Показываем заголовки первого запроса
            if headers_captured:
                print(f"\n   Sample request headers:")
                for key, value in headers_captured[0]['headers'].items():
                    if key.lower() in ['user-agent', 'sec-ch-ua', 'sec-ch-ua-platform', 'accept-language', 'accept']:
                        print(f"      {key}: {value[:100]}")

                # Проверяем подозрительные заголовки
                headers = headers_captured[0]['headers']
                issues = []

                if 'headless' in str(headers).lower():
                    issues.append("Заголовок содержит 'headless'")

                if 'playwright' in str(headers).lower():
                    issues.append("Заголовок содержит 'playwright'")

                if issues:
                    print(f"\n   ⚠️  Проблемы с заголовками:")
                    for issue in issues:
                        print(f"      - {issue}")
                else:
                    print(f"\n   ✅ Заголовки выглядят нормально")

    except Exception as e:
        print(f"   ❌ Error: {e}")


async def check_behavioral_timing(page):
    """Проверка behavioral timing"""
    print("\n" + "="*80)
    print("[5] BEHAVIORAL TIMING CHECK")
    print("="*80)

    try:
        timing = await page.evaluate("""
            () => {
                const timing = performance.timing;
                return {
                    navigationStart: timing.navigationStart,
                    domContentLoadedEventEnd: timing.domContentLoadedEventEnd,
                    loadEventEnd: timing.loadEventEnd,
                    domComplete: timing.domComplete
                };
            }
        """)

        load_time = timing['loadEventEnd'] - timing['navigationStart']
        print(f"\n   Page load time: {load_time}ms")

        if load_time < 100:
            print(f"   ⚠️  WARNING: Слишком быстрая загрузка! Может указывать на prefetch/cache")
        elif load_time > 10000:
            print(f"   ⚠️  WARNING: Очень медленная загрузка")
        else:
            print(f"   ✅ Нормальное время загрузки")

    except Exception as e:
        print(f"   ❌ Error: {e}")


async def check_microsoft_specific(page):
    """Проверка Microsoft-специфичных детекций"""
    print("\n" + "="*80)
    print("[6] MICROSOFT-SPECIFIC CHECKS")
    print("="*80)

    try:
        await page.goto("https://signup.live.com/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        # Проверяем наличие challenge/captcha
        has_captcha = await page.evaluate("""
            () => {
                const body = document.body.innerHTML.toLowerCase();
                return body.includes('captcha') ||
                       body.includes('verify') ||
                       body.includes('unusual activity') ||
                       body.includes('challenge');
            }
        """)

        if has_captcha:
            print(f"\n   ❌ Страница содержит CAPTCHA/Challenge")
            print(f"   Это означает что IP или fingerprint уже помечен как подозрительный")
        else:
            print(f"\n   ✅ Нет CAPTCHA/Challenge на странице регистрации")

        # Проверяем cookies
        cookies = await page.context.cookies()
        print(f"\n   Cookies count: {len(cookies)}")

        ms_cookies = [c for c in cookies if 'microsoft' in c.get('domain', '').lower() or 'live' in c.get('domain', '').lower()]
        print(f"   Microsoft cookies: {len(ms_cookies)}")

        if len(ms_cookies) < 2:
            print(f"   ⚠️  WARNING: Мало Microsoft cookies. Рекомендуется предварительно посетить microsoft.com")

    except Exception as e:
        print(f"   ❌ Error: {e}")


async def main():
    if sys.platform == 'win32':
        os.system('chcp 65001 > nul')
        sys.stdout.reconfigure(encoding='utf-8')

    print("="*80)
    print("MICROSOFT DETECTION DIAGNOSTICS")
    print("="*80)
    print("\nЭтот скрипт проверит все возможные причины детекции Microsoft")

    browser = BrowserManager(
        proxy="MPzEefwWaIUi:tc6aWZqR@pool.proxy.market:10000",
        headless=False
    )

    try:
        print("\n[SETUP] Настройка браузера...")
        await browser.setup()
        print("[SETUP] ✅ Браузер готов\n")

        # Запускаем все проверки
        await check_ip_reputation(browser.page)
        await check_webrtc_leak(browser.page)
        await check_fonts(browser.page)
        await check_http_headers(browser.page)
        await check_behavioral_timing(browser.page)
        await check_microsoft_specific(browser.page)

        print("\n" + "="*80)
        print("DIAGNOSTIC COMPLETE")
        print("="*80)
        print("\nПроверьте результаты выше и устраните обнаруженные проблемы.")
        print("\nБраузер остается открытым. Нажмите Ctrl+C для закрытия...")

        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n[INFO] Закрытие...")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
