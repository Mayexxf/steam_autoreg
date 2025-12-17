#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Детальный анализ результатов CreepJS
Извлекает все lies, warnings, блокировки и несоответствия
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, 'C:\\projects')
from outlook.browser import BrowserManager


async def extract_all_issues(page):
    """
    Извлекает ВСЕ проблемы со страницы CreepJS
    """
    print("\n" + "="*80)
    print("ДЕТАЛЬНЫЙ АНАЛИЗ ПРОБЛЕМ CREEPJS")
    print("="*80)

    issues = await page.evaluate("""
        () => {
            const results = {
                lies: [],
                blocked: [],
                mismatches: [],
                warnings: [],
                suspiciousValues: [],
                allRedSections: []
            };

            // 1. Поиск всех LIES (ложь/несоответствия)
            document.querySelectorAll('.lies, [class*="lie"]').forEach(el => {
                const text = el.textContent.trim();
                if (text && !results.lies.includes(text)) {
                    results.lies.push({
                        text: text.substring(0, 200),
                        html: el.innerHTML.substring(0, 300)
                    });
                }
            });

            // 2. Поиск BLOCKED элементов
            document.querySelectorAll('[class*="blocked"], [style*="blocked"]').forEach(el => {
                const text = el.textContent.trim();
                if (text && text.length < 200) {
                    results.blocked.push(text);
                }
            });

            // 3. Поиск текста "blocked" или "denied"
            const bodyText = document.body.innerText;
            const blockedMatches = bodyText.matchAll(/blocked|denied|failed|mismatch/gi);
            for (const match of blockedMatches) {
                const start = Math.max(0, match.index - 50);
                const end = Math.min(bodyText.length, match.index + 100);
                const context = bodyText.substring(start, end);
                if (!results.warnings.find(w => w.includes(context))) {
                    results.warnings.push(context.trim());
                }
            }

            // 4. Поиск красных/розовых секций
            document.querySelectorAll('.block-text, .block, div[class*="block"]').forEach(el => {
                const bgColor = window.getComputedStyle(el).backgroundColor;
                const color = window.getComputedStyle(el).color;

                // Проверяем красный/розовый фон или текст
                if (bgColor.includes('255, 0') || bgColor.includes('255, 192') ||
                    color.includes('255, 0') || color === 'red') {
                    const text = el.textContent.trim();
                    if (text && text.length > 10 && text.length < 500) {
                        results.allRedSections.push({
                            text: text.substring(0, 200),
                            bg: bgColor,
                            color: color
                        });
                    }
                }
            });

            // 5. Специфичные проблемы
            const checks = [
                'navigator.webdriver',
                'headless',
                'automation',
                'phantom',
                'selenium',
                'chromedriver',
                'runtime.onMessage',
                'canvas mismatch',
                'webgl mismatch',
                'audio mismatch'
            ];

            checks.forEach(check => {
                if (bodyText.toLowerCase().includes(check.toLowerCase())) {
                    // Извлекаем контекст вокруг найденного
                    const idx = bodyText.toLowerCase().indexOf(check.toLowerCase());
                    const start = Math.max(0, idx - 80);
                    const end = Math.min(bodyText.length, idx + 150);
                    results.suspiciousValues.push({
                        keyword: check,
                        context: bodyText.substring(start, end).trim()
                    });
                }
            });

            // 6. Проверяем score/trust level
            const scoreElements = document.querySelectorAll('[class*="score"], [class*="trust"], [class*="grade"]');
            scoreElements.forEach(el => {
                const text = el.textContent;
                if (text.includes('%') || text.includes('score') || text.includes('trust')) {
                    results.suspiciousValues.push({
                        keyword: 'Score/Trust',
                        context: text.trim()
                    });
                }
            });

            return results;
        }
    """)

    # Выводим результаты
    print("\n🔴 [1] LIES / НЕСООТВЕТСТВИЯ:")
    if issues['lies']:
        for i, lie in enumerate(issues['lies'][:15], 1):
            print(f"\n   #{i}:")
            print(f"   Text: {lie['text'][:150]}")
    else:
        print("   ✅ Не обнаружено")

    print("\n🚫 [2] BLOCKED / ЗАБЛОКИРОВАНО:")
    if issues['blocked']:
        for i, block in enumerate(set(issues['blocked'][:10]), 1):
            print(f"   {i}. {block}")
    else:
        print("   ✅ Не обнаружено")

    print("\n⚠️  [3] WARNINGS / ПРЕДУПРЕЖДЕНИЯ:")
    if issues['warnings']:
        unique_warnings = list(set(issues['warnings'][:20]))
        for i, warning in enumerate(unique_warnings, 1):
            print(f"   {i}. {warning[:120]}...")
    else:
        print("   ✅ Нет предупреждений")

    print("\n🔴 [4] КРАСНЫЕ/РОЗОВЫЕ СЕКЦИИ:")
    if issues['allRedSections']:
        for i, section in enumerate(issues['allRedSections'][:10], 1):
            print(f"\n   #{i} (bg: {section['bg']}, color: {section['color']}):")
            print(f"   {section['text'][:150]}...")
    else:
        print("   ✅ Не обнаружено")

    print("\n🔍 [5] ПОДОЗРИТЕЛЬНЫЕ ЗНАЧЕНИЯ:")
    if issues['suspiciousValues']:
        for i, val in enumerate(issues['suspiciousValues'][:15], 1):
            print(f"\n   {i}. Keyword: {val['keyword']}")
            print(f"      Context: {val['context'][:120]}...")
    else:
        print("   ✅ Не обнаружено")

    return issues


async def check_specific_detections(page):
    """
    Проверяет конкретные детекции автоматизации
    """
    print("\n" + "="*80)
    print("ПРОВЕРКА КОНКРЕТНЫХ ДЕТЕКЦИЙ")
    print("="*80)

    detections = await page.evaluate("""
        () => {
            const result = {};

            // Проверяем navigator.webdriver
            result.webdriver = {
                value: navigator.webdriver,
                detected: navigator.webdriver === true
            };

            // Проверяем Chrome runtime
            result.chromeRuntime = {
                exists: typeof chrome !== 'undefined' && typeof chrome.runtime !== 'undefined',
                value: typeof chrome !== 'undefined' ? Object.keys(chrome).join(', ') : 'N/A'
            };

            // Проверяем permissions API
            result.permissions = {
                query: typeof navigator.permissions !== 'undefined' &&
                       typeof navigator.permissions.query !== 'undefined'
            };

            // Headless детекция
            result.headless = {
                outerDimensions: `${window.outerWidth}x${window.outerHeight}`,
                innerDimensions: `${window.innerWidth}x${window.innerHeight}`,
                isZero: window.outerWidth === 0 || window.outerHeight === 0
            };

            // WebDriver детекция
            result.webdriverCheck = {
                inNavigator: 'webdriver' in navigator,
                value: navigator.webdriver,
                stringified: String(navigator.webdriver)
            };

            // Plugins
            result.plugins = {
                count: navigator.plugins.length,
                list: Array.from(navigator.plugins).map(p => p.name).join(', ')
            };

            // Canvas
            try {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                ctx.textBaseline = 'top';
                ctx.font = '14px Arial';
                ctx.fillText('Test', 2, 2);
                result.canvas = {
                    available: true,
                    dataURL: canvas.toDataURL().substring(0, 100)
                };
            } catch(e) {
                result.canvas = { available: false, error: e.message };
            }

            // WebGL
            try {
                const canvas = document.createElement('canvas');
                const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                result.webgl = {
                    available: !!gl,
                    vendor: debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : 'N/A',
                    renderer: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'N/A'
                };
            } catch(e) {
                result.webgl = { available: false, error: e.message };
            }

            return result;
        }
    """)

    print("\n[WEBDRIVER DETECTION]")
    wd = detections['webdriverCheck']
    status = "❌ DETECTED" if wd['value'] == True else "✅ HIDDEN"
    print(f"   Status: {status}")
    print(f"   In navigator: {wd['inNavigator']}")
    print(f"   Value: {wd['value']}")
    print(f"   Stringified: {wd['stringified']}")

    print("\n[HEADLESS DETECTION]")
    hl = detections['headless']
    status = "❌ DETECTED" if hl['isZero'] else "✅ NOT DETECTED"
    print(f"   Status: {status}")
    print(f"   Outer: {hl['outerDimensions']}")
    print(f"   Inner: {hl['innerDimensions']}")

    print("\n[CHROME RUNTIME]")
    cr = detections['chromeRuntime']
    print(f"   Exists: {cr['exists']}")
    print(f"   Keys: {cr['value']}")

    print("\n[PLUGINS]")
    pl = detections['plugins']
    print(f"   Count: {pl['count']}")
    print(f"   List: {pl['list'][:100]}...")

    print("\n[CANVAS]")
    cnv = detections['canvas']
    if cnv['available']:
        print(f"   ✅ Available")
        print(f"   DataURL prefix: {cnv['dataURL']}")
    else:
        print(f"   ❌ Error: {cnv.get('error', 'Unknown')}")

    print("\n[WEBGL]")
    wgl = detections['webgl']
    if wgl['available']:
        print(f"   ✅ Available")
        print(f"   Vendor: {wgl['vendor']}")
        print(f"   Renderer: {wgl['renderer'][:80]}...")
    else:
        print(f"   ❌ Error: {wgl.get('error', 'Unknown')}")

    return detections


async def main():
    if sys.platform == 'win32':
        os.system('chcp 65001 > nul')
        sys.stdout.reconfigure(encoding='utf-8')

    print("="*80)
    print("ДЕТАЛЬНЫЙ АНАЛИЗ ПРОБЛЕМ CREEPJS")
    print("="*80)

    browser_manager = BrowserManager(
        proxy="MPzEefwWaIUi:tc6aWZqR@pool.proxy.market:10000",
        headless=False
    )

    try:
        print("\n[1] Настройка браузера...")
        await browser_manager.setup()

        print("\n[2] Переход на CreepJS...")
        await browser_manager.page.goto("https://abrahamjuliot.github.io/creepjs/",
                                        wait_until="domcontentloaded",
                                        timeout=60000)

        print("\n[3] Ожидание загрузки тестов...")
        await asyncio.sleep(15)  # Даем больше времени для тестов

        # Детальная проверка
        await check_specific_detections(browser_manager.page)

        # Извлекаем все проблемы
        issues = await extract_all_issues(browser_manager.page)

        # Скриншот
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"C:\\projects\\detailed_creepjs_{timestamp}.png"
        await browser_manager.page.screenshot(path=screenshot_path, full_page=True)
        print(f"\n[SCREENSHOT] Сохранен: {screenshot_path}")

        print("\n" + "="*80)
        print("АНАЛИЗ ЗАВЕРШЕН")
        print("="*80)
        print("\nБраузер остается открытым. Ctrl+C для закрытия...")

        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n[INFO] Закрытие...")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        await browser_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
