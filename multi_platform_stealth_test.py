#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Мультиплатформенный тест stealth на CreepJS, Pixelscan, BrowserLeaks и IPHey
Проверяет все fingerprint обходы на разных платформах для полной картины
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, 'C:\\projects')

from outlook.browser import BrowserManager


class MultiPlatformTest:
    """Тестирование на нескольких платформах детекции"""

    def __init__(self, browser_manager):
        self.bm = browser_manager
        self.results = {}

    async def test_iphey(self):
        """Тест на IPHey - базовая проверка IP, headers, WebRTC"""
        print("\n" + "="*80)
        print("[1/4] ТЕСТ: IPHEY (IP & HEADERS)")
        print("="*80)

        try:
            await self.bm.page.goto("https://iphey.com/", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(5)

            # Извлекаем IP и основную информацию
            info = await self.bm.page.evaluate("""
                () => {
                    const getText = (selector) => {
                        const el = document.querySelector(selector);
                        return el ? el.textContent.trim() : 'N/A';
                    };

                    return {
                        ip: getText('#ip'),
                        country: getText('#country-name'),
                        city: getText('#city'),
                        isp: getText('#isp'),
                        userAgent: navigator.userAgent
                    };
                }
            """)

            print(f"   IP: {info['ip']}")
            print(f"   Country: {info['country']}")
            print(f"   City: {info['city']}")
            print(f"   ISP: {info['isp']}")
            print(f"   User-Agent: {info['userAgent'][:80]}...")

            # Скриншот
            await self.bm.page.screenshot(path=f"C:\\projects\\test_iphey_{datetime.now().strftime('%H%M%S')}.png")
            print("   [+] Скриншот сохранен")

            self.results['iphey'] = {
                'status': 'PASS',
                'ip': info['ip'],
                'country': info['country']
            }

        except Exception as e:
            print(f"   [ERROR] Ошибка: {e}")
            self.results['iphey'] = {'status': 'FAIL', 'error': str(e)}

    async def test_browserleaks_webrtc(self):
        """Тест WebRTC утечек на BrowserLeaks"""
        print("\n" + "="*80)
        print("[2/4] ТЕСТ: BROWSERLEAKS (WebRTC Leak)")
        print("="*80)

        try:
            await self.bm.page.goto("https://browserleaks.com/webrtc", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(8)

            # Проверяем утечки IP
            leaks = await self.bm.page.evaluate("""
                () => {
                    const results = {
                        publicIP: [],
                        localIP: [],
                        leakDetected: false
                    };

                    // Ищем все IP адреса на странице
                    const text = document.body.innerText;
                    const ipPattern = /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g;
                    const ips = text.match(ipPattern) || [];

                    // Проверяем на локальные IP (утечки)
                    ips.forEach(ip => {
                        if (ip.startsWith('192.168.') || ip.startsWith('10.') || ip.startsWith('172.')) {
                            results.localIP.push(ip);
                            results.leakDetected = true;
                        } else {
                            results.publicIP.push(ip);
                        }
                    });

                    return results;
                }
            """)

            print(f"   Публичные IP: {set(leaks['publicIP'])}")
            print(f"   Локальные IP (утечки): {set(leaks['localIP'])}")

            if leaks['leakDetected']:
                print("   [!] ВНИМАНИЕ: Обнаружена утечка локального IP через WebRTC!")
                self.results['browserleaks_webrtc'] = {'status': 'LEAK', 'local_ips': leaks['localIP']}
            else:
                print("   [+] Утечек не обнаружено!")
                self.results['browserleaks_webrtc'] = {'status': 'PASS'}

            await self.bm.page.screenshot(path=f"C:\\projects\\test_browserleaks_{datetime.now().strftime('%H%M%S')}.png")
            print("   [+] Скриншот сохранен")

        except Exception as e:
            print(f"   [ERROR] Ошибка: {e}")
            self.results['browserleaks_webrtc'] = {'status': 'FAIL', 'error': str(e)}

    async def test_pixelscan(self):
        """Тест на Pixelscan - визуальный анализ fingerprint"""
        print("\n" + "="*80)
        print("[3/4] ТЕСТ: PIXELSCAN (Fingerprint Analysis)")
        print("="*80)

        try:
            await self.bm.page.goto("https://pixelscan.net/", wait_until="domcontentloaded", timeout=40000)
            print("   Ожидание завершения сканирования...")
            await asyncio.sleep(15)  # Pixelscan требует времени

            # Извлекаем Trust Score и основные параметры
            scan_results = await self.bm.page.evaluate("""
                () => {
                    const getText = (selector) => {
                        const el = document.querySelector(selector);
                        return el ? el.textContent.trim() : null;
                    };

                    return {
                        trustScore: getText('.trust-score, [class*="score"]'),
                        webdriver: getText('[data-test="webdriver"]') || document.body.textContent.includes('navigator.webdriver'),
                        headless: document.body.textContent.includes('headless'),
                        consistencyIssues: document.querySelectorAll('.warning, .error, [class*="inconsistency"]').length
                    };
                }
            """)

            print(f"   Trust Score: {scan_results['trustScore'] or 'N/A'}")
            print(f"   WebDriver обнаружен: {'Да' if scan_results['webdriver'] else 'Нет'}")
            print(f"   Headless обнаружен: {'Да' if scan_results['headless'] else 'Нет'}")
            print(f"   Проблемы консистентности: {scan_results['consistencyIssues']}")

            await self.bm.page.screenshot(path=f"C:\\projects\\test_pixelscan_{datetime.now().strftime('%H%M%S')}.png", full_page=True)
            print("   [+] Скриншот сохранен")

            status = 'PASS'
            if scan_results['webdriver'] or scan_results['headless']:
                status = 'FAIL'
            elif scan_results['consistencyIssues'] > 5:
                status = 'WARN'

            self.results['pixelscan'] = {
                'status': status,
                'trustScore': scan_results['trustScore'],
                'issues': scan_results['consistencyIssues']
            }

        except Exception as e:
            print(f"   [ERROR] Ошибка: {e}")
            self.results['pixelscan'] = {'status': 'FAIL', 'error': str(e)}

    async def test_creepjs(self):
        """Тест на CreepJS - самый продвинутый детектор"""
        print("\n" + "="*80)
        print("[4/4] ТЕСТ: CREEPJS (Advanced Detection)")
        print("="*80)

        try:
            await self.bm.page.goto("https://abrahamjuliot.github.io/creepjs/",
                                    wait_until="domcontentloaded",
                                    timeout=60000)
            print("   Ожидание завершения тестов...")

            # Ждем завершения тестов (максимум 90 секунд)
            for i in range(90):
                try:
                    progress = await self.bm.page.evaluate("""
                        () => {
                            const progressEl = document.querySelector('.ellipsis-all');
                            return progressEl ? progressEl.textContent.trim() : null;
                        }
                    """)

                    if progress and '100%' in progress:
                        print(f"   [+] Тесты завершены: {progress}")
                        break
                    elif progress and i % 10 == 0:
                        print(f"   Прогресс: {progress}")
                except:
                    pass

                await asyncio.sleep(1)

            await asyncio.sleep(3)

            # Извлекаем результаты
            results = await self.bm.page.evaluate("""
                () => {
                    const bodyText = document.body.textContent;

                    return {
                        lies: document.querySelectorAll('.lies, [style*="color: red"]').length,
                        webdriver: bodyText.includes('navigator.webdriver: true'),
                        headless: bodyText.includes('headless') && bodyText.includes('true'),
                        trustScore: bodyText.match(/([0-9]+)%/)?.[0] || 'N/A'
                    };
                }
            """)

            print(f"   Детектированные лжи: {results['lies']}")
            print(f"   WebDriver обнаружен: {'Да' if results['webdriver'] else 'Нет'}")
            print(f"   Headless обнаружен: {'Да' if results['headless'] else 'Нет'}")
            print(f"   Trust Score: {results['trustScore']}")

            await self.bm.page.screenshot(path=f"C:\\projects\\test_creepjs_{datetime.now().strftime('%H%M%S')}.png", full_page=True)
            print("   [+] Скриншот сохранен")

            status = 'PASS'
            if results['webdriver'] or results['headless']:
                status = 'FAIL'
            elif results['lies'] > 3:
                status = 'WARN'

            self.results['creepjs'] = {
                'status': status,
                'lies': results['lies'],
                'trustScore': results['trustScore']
            }

        except Exception as e:
            print(f"   [ERROR] Ошибка: {e}")
            self.results['creepjs'] = {'status': 'FAIL', 'error': str(e)}

    async def print_summary(self):
        """Печатает итоговый отчет"""
        print("\n" + "="*80)
        print("ИТОГОВЫЙ ОТЧЕТ")
        print("="*80)

        total = len(self.results)
        passed = sum(1 for r in self.results.values() if r.get('status') == 'PASS')
        warned = sum(1 for r in self.results.values() if r.get('status') == 'WARN')
        failed = sum(1 for r in self.results.values() if r.get('status') in ['FAIL', 'LEAK'])

        print(f"\nВсего тестов: {total}")
        print(f"Пройдено: {passed} [PASS]")
        print(f"Предупреждений: {warned} [WARN]")
        print(f"Провалено: {failed} [FAIL]")

        print("\nДетали:")
        for platform, result in self.results.items():
            status_symbol = {
                'PASS': '[+]',
                'WARN': '[!]',
                'FAIL': '[X]',
                'LEAK': '[!]'
            }.get(result.get('status'), '[?]')

            print(f"  {status_symbol} {platform.upper()}: {result.get('status')}")

            if 'error' in result:
                print(f"      Ошибка: {result['error'][:60]}...")

        # Общая оценка
        print("\n" + "-"*80)
        if failed == 0 and warned == 0:
            print("ОЦЕНКА: ОТЛИЧНО! Все тесты пройдены без проблем.")
        elif failed == 0 and warned <= 2:
            print("ОЦЕНКА: ХОРОШО! Есть небольшие предупреждения, но критичных проблем нет.")
        elif failed <= 1:
            print("ОЦЕНКА: УДОВЛЕТВОРИТЕЛЬНО! Есть проблемы, требуется доработка.")
        else:
            print("ОЦЕНКА: ПЛОХО! Множественные проблемы с детекцией, требуется серьезная доработка.")
        print("-"*80)


async def main():
    # Устанавливаем UTF-8 для Windows консоли
    if sys.platform == 'win32':
        os.system('chcp 65001 > nul')
        sys.stdout.reconfigure(encoding='utf-8')

    print("="*80)
    print("МУЛЬТИПЛАТФОРМЕННЫЙ ТЕСТ STEALTH")
    print("="*80)
    print("\nБудут проверены следующие платформы:")
    print("  1. IPHey - базовая проверка IP и headers")
    print("  2. BrowserLeaks - WebRTC утечки")
    print("  3. Pixelscan - визуальный анализ fingerprint")
    print("  4. CreepJS - продвинутая детекция")
    print()

    browser_manager = BrowserManager(
        proxy="MPzEefwWaIUi:tc6aWZqR@pool.proxy.market:10000",
        headless=False
    )

    try:
        print("[SETUP] Настройка браузера...")
        await browser_manager.setup()
        print("   [+] Браузер готов!\n")

        tester = MultiPlatformTest(browser_manager)

        # Запускаем все тесты последовательно
        await tester.test_iphey()
        await tester.test_browserleaks_webrtc()
        await tester.test_pixelscan()
        await tester.test_creepjs()

        # Выводим итоговый отчет
        await tester.print_summary()

        print("\n" + "="*80)
        print("ТЕСТ ЗАВЕРШЕН")
        print("="*80)
        print("\nБраузер остается открытым для ручной проверки.")
        print("Все скриншоты сохранены в C:\\projects\\")
        print("\nНажмите Ctrl+C для закрытия...")

        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n[INFO] Закрытие браузера...")
    except Exception as e:
        print(f"\n[ERROR] Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await browser_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
