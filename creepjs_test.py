#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Полный тест stealth модулей на CreepJS
Проверяет все fingerprint обходы, включая WebGL, Canvas, Audio, Hardware и т.д.
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, 'C:\\projects')

from outlook.browser import BrowserManager


async def wait_for_creepjs_completion(page, max_wait=120):
    """
    Ждет завершения всех тестов CreepJS
    CreepJS показывает "100%" когда все тесты завершены
    """
    print("\n[INFO] Ожидание завершения тестов CreepJS...")

    for i in range(max_wait):
        try:
            # Проверяем наличие элемента с процентом завершения
            progress = await page.evaluate("""
                () => {
                    // Ищем элемент с прогрессом
                    const progressEl = document.querySelector('.ellipsis-all');
                    if (progressEl && progressEl.textContent.includes('%')) {
                        return progressEl.textContent.trim();
                    }
                    return null;
                }
            """)

            if progress and '100%' in progress:
                print(f"[+] Тесты завершены: {progress}")
                return True
            elif progress:
                if i % 5 == 0:  # Выводим прогресс каждые 5 секунд
                    print(f"   Прогресс: {progress}")
        except Exception as e:
            pass

        await asyncio.sleep(1)

    print("[!] Тайм-аут ожидания завершения тестов")
    return False


async def analyze_creepjs_results(page):
    """
    Анализирует результаты тестов CreepJS
    Извлекает все важные данные о детекции
    """
    print("\n" + "="*80)
    print("АНАЛИЗ РЕЗУЛЬТАТОВ CREEPJS")
    print("="*80)

    try:
        results = await page.evaluate("""
            () => {
                const results = {
                    lies: [],
                    warnings: [],
                    errors: [],
                    fingerprints: {},
                    detections: []
                };

                // Собираем все блоки с результатами
                const blocks = document.querySelectorAll('.block-text, .block, .ellipsis');

                blocks.forEach(block => {
                    const text = block.textContent;

                    // Детекция лжи (красный текст)
                    if (block.classList.contains('lies') || text.includes('lied') || text.includes('mismatch')) {
                        results.lies.push(text.trim());
                    }

                    // Предупреждения
                    if (block.style.color === 'red' || text.includes('blocked') || text.includes('denied')) {
                        results.warnings.push(text.trim());
                    }
                });

                // Проверяем специфичные детекции
                const detectionChecks = {
                    webdriver: document.body.textContent.includes('navigator.webdriver'),
                    headless: document.body.textContent.includes('headless'),
                    automation: document.body.textContent.includes('automation'),
                    proxy: document.body.textContent.includes('proxy leak'),
                    webrtc: document.body.textContent.includes('WebRTC leak'),
                    canvas: document.body.textContent.includes('canvas'),
                    audio: document.body.textContent.includes('audio'),
                    webgl: document.body.textContent.includes('WebGL')
                };

                // Извлекаем значения fingerprints
                try {
                    results.fingerprints.webgl = {
                        vendor: document.body.textContent.match(/vendor: ([^\\n]+)/)?.[1] || 'N/A',
                        renderer: document.body.textContent.match(/renderer: ([^\\n]+)/)?.[1] || 'N/A'
                    };

                    results.fingerprints.canvas = document.body.textContent.match(/canvas: ([a-f0-9]+)/)?.[1] || 'N/A';
                    results.fingerprints.audio = document.body.textContent.match(/audio: ([0-9.]+)/)?.[1] || 'N/A';
                } catch (e) {
                    console.log('Error extracting fingerprints:', e);
                }

                return results;
            }
        """)

        # Выводим анализ
        print("\n[1] ДЕТЕКТИРОВАННЫЕ ЛЖИ (Lies):")
        if results['lies']:
            for lie in results['lies'][:10]:  # Первые 10
                print(f"   ❌ {lie}")
        else:
            print("   ✅ Не обнаружено!")

        print("\n[2] ПРЕДУПРЕЖДЕНИЯ:")
        if results['warnings']:
            for warning in results['warnings'][:10]:
                print(f"   ⚠️  {warning}")
        else:
            print("   ✅ Нет предупреждений!")

        print("\n[3] FINGERPRINTS:")
        if 'webgl' in results['fingerprints']:
            webgl = results['fingerprints']['webgl']
            print(f"   WebGL Vendor: {webgl['vendor']}")
            print(f"   WebGL Renderer: {webgl['renderer']}")
        if 'canvas' in results['fingerprints']:
            print(f"   Canvas Hash: {results['fingerprints']['canvas']}")
        if 'audio' in results['fingerprints']:
            print(f"   Audio Hash: {results['fingerprints']['audio']}")

    except Exception as e:
        print(f"[ERROR] Ошибка анализа: {e}")

    return results


async def check_specific_values(page):
    """
    Проверяет конкретные значения, которые детектирует CreepJS
    """
    print("\n" + "="*80)
    print("ПРОВЕРКА КРИТИЧНЫХ ЗНАЧЕНИЙ")
    print("="*80)

    checks = await page.evaluate("""
        () => {
            return {
                webdriver: navigator.webdriver,
                hardwareConcurrency: navigator.hardwareConcurrency,
                deviceMemory: navigator.deviceMemory,
                vendor: navigator.vendor,
                platform: navigator.platform,
                userAgent: navigator.userAgent,
                plugins: navigator.plugins.length,
                mimeTypes: navigator.mimeTypes.length,
                connection: navigator.connection ? {
                    downlinkMax: navigator.connection.downlinkMax,
                    effectiveType: navigator.connection.effectiveType
                } : null,
                permissions: {
                    notification: Notification.permission
                },
                webgl: (() => {
                    try {
                        const canvas = document.createElement('canvas');
                        const gl = canvas.getContext('webgl');
                        if (!gl) return null;
                        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                        return {
                            vendor: gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL),
                            renderer: gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
                        };
                    } catch(e) {
                        return null;
                    }
                })(),
                window: {
                    outerWidth: window.outerWidth,
                    outerHeight: window.outerHeight,
                    innerWidth: window.innerWidth,
                    innerHeight: window.innerHeight
                },
                screen: {
                    width: screen.width,
                    height: screen.height,
                    colorDepth: screen.colorDepth,
                    pixelDepth: screen.pixelDepth
                }
            };
        }
    """)

    print("\n[NAVIGATOR]")
    print(f"   webdriver: {checks['webdriver']} {'✅' if checks['webdriver'] == False else '❌'}")
    print(f"   hardwareConcurrency: {checks['hardwareConcurrency']}")
    print(f"   deviceMemory: {checks['deviceMemory']}")
    print(f"   vendor: {checks['vendor']}")
    print(f"   platform: {checks['platform']}")
    print(f"   plugins: {checks['plugins']}")
    print(f"   mimeTypes: {checks['mimeTypes']}")

    print("\n[CONNECTION]")
    if checks['connection']:
        print(f"   downlinkMax: {checks['connection']['downlinkMax']} {'✅' if checks['connection']['downlinkMax'] == float('inf') else '⚠️'}")
        print(f"   effectiveType: {checks['connection']['effectiveType']}")
    else:
        print("   ⚠️  Connection API не доступен")

    print("\n[PERMISSIONS]")
    print(f"   Notification: {checks['permissions']['notification']} {'✅' if checks['permissions']['notification'] != 'denied' else '⚠️'}")

    print("\n[WEBGL]")
    if checks['webgl']:
        print(f"   Vendor: {checks['webgl']['vendor']}")
        print(f"   Renderer: {checks['webgl']['renderer'][:70]}...")

    print("\n[WINDOW]")
    print(f"   outer: {checks['window']['outerWidth']}x{checks['window']['outerHeight']}")
    print(f"   inner: {checks['window']['innerWidth']}x{checks['window']['innerHeight']}")
    zero_dimensions = checks['window']['outerWidth'] == 0 or checks['window']['outerHeight'] == 0
    print(f"   {'❌ HEADLESS DETECTED (zero dimensions)!' if zero_dimensions else '✅ Dimensions OK'}")

    print("\n[SCREEN]")
    print(f"   Resolution: {checks['screen']['width']}x{checks['screen']['height']}")
    print(f"   Color Depth: {checks['screen']['colorDepth']} / {checks['screen']['pixelDepth']}")

    return checks


async def main():
    # Устанавливаем UTF-8 для Windows консоли
    if sys.platform == 'win32':
        os.system('chcp 65001 > nul')
        sys.stdout.reconfigure(encoding='utf-8')

    print("="*80)
    print("ПОЛНЫЙ ТЕСТ STEALTH МОДУЛЕЙ НА CREEPJS")
    print("="*80)
    print("\nЭтот тест проверит все fingerprint обходы:")
    print("  - WebGL (vendor/renderer)")
    print("  - Canvas fingerprinting")
    print("  - Audio fingerprinting")
    print("  - Hardware (cores, memory)")
    print("  - Navigator properties")
    print("  - WebRTC leak protection")
    print("  - Automation detection (webdriver)")
    print("  - Headless detection")
    print("  - И многое другое...\n")

    # Создаем BrowserManager с прокси из конфига
    browser_manager = BrowserManager(
        proxy="MPzEefwWaIUi:tc6aWZqR@pool.proxy.market:10000",
        headless=False  # ВАЖНО: False для полного теста
    )

    try:
        print("[1] Настройка браузера со всеми stealth модулями...")
        await browser_manager.setup()
        print("   ✅ Браузер настроен!")

        print("\n[2] Переход на CreepJS...")
        await browser_manager.page.goto("https://abrahamjuliot.github.io/creepjs/",
                                        wait_until="domcontentloaded",
                                        timeout=60000)
        print("   ✅ Страница загружена!")

        # Ждем немного для начала тестов
        await asyncio.sleep(3)

        print("\n[3] Ожидание завершения тестов CreepJS...")
        completed = await wait_for_creepjs_completion(browser_manager.page, max_wait=120)

        if completed:
            print("   ✅ Все тесты завершены!")
        else:
            print("   ⚠️  Продолжаем анализ (возможно тесты еще идут)...")

        # Даем время на рендеринг результатов
        await asyncio.sleep(5)

        # Проверяем конкретные значения
        await check_specific_values(browser_manager.page)

        # Анализируем результаты
        await analyze_creepjs_results(browser_manager.page)

        # Делаем скриншот
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"C:\\projects\\creepjs_result_{timestamp}.png"
        await browser_manager.page.screenshot(path=screenshot_path, full_page=True)
        print(f"\n[SCREENSHOT] Сохранен: {screenshot_path}")

        print("\n" + "="*80)
        print("ТЕСТ ЗАВЕРШЕН")
        print("="*80)
        print("\nБраузер остается открытым для ручной проверки.")
        print("Вы можете:")
        print("  1. Изучить результаты CreepJS визуально")
        print("  2. Прокрутить вниз для просмотра всех тестов")
        print("  3. Проверить конкретные значения в консоли браузера")
        print("\nНажмите Ctrl+C для закрытия...")

        # Оставляем браузер открытым
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n[INFO] Закрытие браузера...")
    except Exception as e:
        print(f"\n[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await browser_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
