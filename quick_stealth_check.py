#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Быстрая проверка stealth без посещения внешних сайтов
Проверяет все критичные параметры локально
"""

import asyncio
import sys
import os

sys.path.insert(0, 'C:\\projects')

from outlook.browser import BrowserManager


async def quick_check(page):
    """Быстрая проверка всех критичных параметров"""

    if sys.platform == 'win32':
        os.system('chcp 65001 > nul')
        sys.stdout.reconfigure(encoding='utf-8')

    print("\n" + "="*80)
    print("БЫСТРАЯ ПРОВЕРКА STEALTH ПАРАМЕТРОВ")
    print("="*80)

    results = await page.evaluate("""
        () => {
            const results = {
                critical: {},
                fingerprints: {},
                apis: {},
                dimensions: {},
                issues: []
            };

            // === КРИТИЧНЫЕ ПАРАМЕТРЫ ===
            results.critical.webdriver = navigator.webdriver;
            results.critical.webdriverType = typeof navigator.webdriver;

            // Проверяем automation маркеры
            const automationMarkers = [
                '__webdriver_evaluate',
                '__selenium_evaluate',
                '__webdriver_script_function',
                '__driver_evaluate',
                'webdriver',
                'domAutomation',
                'domAutomationController'
            ];

            results.critical.automationMarkers = [];
            automationMarkers.forEach(marker => {
                if (window[marker] || navigator[marker]) {
                    results.critical.automationMarkers.push(marker);
                }
            });

            // === FINGERPRINTS ===
            // WebGL
            try {
                const canvas = document.createElement('canvas');
                const gl = canvas.getContext('webgl');
                if (gl) {
                    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                    if (debugInfo) {
                        results.fingerprints.webgl = {
                            vendor: gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL),
                            renderer: gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
                        };
                    }
                }
            } catch(e) {
                results.fingerprints.webgl = { error: e.message };
            }

            // Hardware
            results.fingerprints.hardware = {
                cores: navigator.hardwareConcurrency,
                memory: navigator.deviceMemory
            };

            // Navigator
            results.fingerprints.navigator = {
                vendor: navigator.vendor,
                platform: navigator.platform,
                userAgent: navigator.userAgent,
                plugins: navigator.plugins.length,
                mimeTypes: navigator.mimeTypes.length
            };

            // === WEB APIs ===
            results.apis.storage = !!navigator.storage;
            results.apis.contacts = !!navigator.contacts;
            results.apis.connection = !!navigator.connection;
            results.apis.connectionDownlinkMax = navigator.connection ? navigator.connection.downlinkMax : null;

            // Permissions
            results.apis.notification = typeof Notification !== 'undefined' ? Notification.permission : null;

            // Speech Synthesis
            results.apis.speechSynthesis = !!window.speechSynthesis;
            results.apis.speechVoices = window.speechSynthesis ? window.speechSynthesis.getVoices().length : 0;

            // === DIMENSIONS ===
            results.dimensions = {
                outerWidth: window.outerWidth,
                outerHeight: window.outerHeight,
                innerWidth: window.innerWidth,
                innerHeight: window.innerHeight,
                screenWidth: screen.width,
                screenHeight: screen.height,
                colorDepth: screen.colorDepth
            };

            // === ПРОВЕРКА ПРОБЛЕМ ===

            // 1. WebDriver
            if (results.critical.webdriver === true) {
                results.issues.push('CRITICAL: navigator.webdriver = true (automation detected)');
            } else if (results.critical.webdriver === undefined) {
                results.issues.push('WARNING: navigator.webdriver = undefined (should be false)');
            }

            // 2. Automation markers
            if (results.critical.automationMarkers.length > 0) {
                results.issues.push(`CRITICAL: Found automation markers: ${results.critical.automationMarkers.join(', ')}`);
            }

            // 3. Headless detection
            if (results.dimensions.outerWidth === 0 || results.dimensions.outerHeight === 0) {
                results.issues.push('CRITICAL: Zero window dimensions (headless detected)');
            }

            // 4. Missing APIs
            if (!results.apis.storage) {
                results.issues.push('WARNING: navigator.storage missing');
            }
            if (!results.apis.connection) {
                results.issues.push('WARNING: navigator.connection missing');
            }
            if (results.apis.connectionDownlinkMax !== Infinity) {
                results.issues.push('WARNING: connection.downlinkMax !== Infinity');
            }

            // 5. Notification permission
            if (results.apis.notification === 'denied') {
                results.issues.push('WARNING: Notification.permission = denied (headless marker)');
            }

            // 6. Speech synthesis
            if (results.apis.speechSynthesis && results.apis.speechVoices === 0) {
                results.issues.push('WARNING: No speech synthesis voices (headless marker)');
            }

            // 7. Plugins
            if (results.fingerprints.navigator.plugins === 0) {
                results.issues.push('WARNING: No plugins (headless marker)');
            }

            // 8. Chrome object (для Chrome)
            if (navigator.userAgent.includes('Chrome') && !window.chrome) {
                results.issues.push('WARNING: window.chrome missing (Chrome should have it)');
            }

            return results;
        }
    """)

    # === ВЫВОД РЕЗУЛЬТАТОВ ===

    print("\n[1] КРИТИЧНЫЕ ПАРАМЕТРЫ")
    print("-" * 80)
    print(f"   navigator.webdriver: {results['critical']['webdriver']}")
    if results['critical']['webdriver'] == False:
        print("   ✓ OK - automation hidden")
    elif results['critical']['webdriver'] is None:
        print("   ⚠ WARNING - should be 'false', not 'undefined'")
    else:
        print("   ✗ FAIL - automation detected!")

    if results['critical']['automationMarkers']:
        print(f"   ✗ Automation markers found: {', '.join(results['critical']['automationMarkers'])}")
    else:
        print("   ✓ No automation markers")

    print("\n[2] FINGERPRINTS")
    print("-" * 80)

    # WebGL
    if 'webgl' in results['fingerprints'] and 'vendor' in results['fingerprints']['webgl']:
        webgl = results['fingerprints']['webgl']
        print(f"   WebGL Vendor: {webgl['vendor']}")
        print(f"   WebGL Renderer: {webgl['renderer'][:70]}...")

        # Проверка на реалистичность
        if 'swiftshader' in webgl['renderer'].lower():
            print("   ⚠ SwiftShader detected (software rendering)")
        elif 'google inc.' in webgl['vendor'].lower() or 'nvidia' in webgl['vendor'].lower():
            print("   ✓ Realistic GPU")

    # Hardware
    hw = results['fingerprints']['hardware']
    print(f"   Hardware Cores: {hw['cores']}")
    print(f"   Device Memory: {hw['memory']}GB")

    if hw['cores'] and hw['memory']:
        print("   ✓ Hardware info present")
    else:
        print("   ⚠ Missing hardware info")

    # Navigator
    nav = results['fingerprints']['navigator']
    print(f"   Vendor: {nav['vendor']}")
    print(f"   Platform: {nav['platform']}")
    print(f"   Plugins: {nav['plugins']}")
    print(f"   MimeTypes: {nav['mimeTypes']}")

    print("\n[3] WEB APIs")
    print("-" * 80)
    apis = results['apis']

    def print_api(name, value, expected=True):
        symbol = "✓" if (value if expected else not value) else "✗"
        print(f"   {symbol} {name}: {value}")

    print_api("navigator.storage", apis['storage'])
    print_api("navigator.contacts", apis['contacts'])
    print_api("navigator.connection", apis['connection'])

    if apis['connection']:
        is_infinity = apis['connectionDownlinkMax'] == float('inf') or str(apis['connectionDownlinkMax']) == 'Infinity'
        symbol = "✓" if is_infinity else "⚠"
        print(f"   {symbol} connection.downlinkMax: {apis['connectionDownlinkMax']}")

    print_api("Notification.permission", apis['notification'] != 'denied')
    print_api("speechSynthesis", apis['speechSynthesis'])

    if apis['speechSynthesis']:
        symbol = "✓" if apis['speechVoices'] > 0 else "⚠"
        print(f"   {symbol} speechSynthesis.voices: {apis['speechVoices']}")

    print("\n[4] WINDOW DIMENSIONS")
    print("-" * 80)
    dim = results['dimensions']

    print(f"   Outer: {dim['outerWidth']}x{dim['outerHeight']}")
    print(f"   Inner: {dim['innerWidth']}x{dim['innerHeight']}")
    print(f"   Screen: {dim['screenWidth']}x{dim['screenHeight']}")
    print(f"   Color Depth: {dim['colorDepth']}")

    if dim['outerWidth'] > 0 and dim['outerHeight'] > 0:
        print("   ✓ Dimensions OK")
    else:
        print("   ✗ HEADLESS DETECTED (zero dimensions)")

    print("\n[5] ОБНАРУЖЕННЫЕ ПРОБЛЕМЫ")
    print("-" * 80)

    if not results['issues']:
        print("   ✓ Проблем не обнаружено!")
    else:
        for issue in results['issues']:
            if 'CRITICAL' in issue:
                print(f"   ✗ {issue}")
            else:
                print(f"   ⚠ {issue}")

    print("\n" + "="*80)
    print("ИТОГОВАЯ ОЦЕНКА")
    print("="*80)

    critical_count = sum(1 for issue in results['issues'] if 'CRITICAL' in issue)
    warning_count = sum(1 for issue in results['issues'] if 'WARNING' in issue)

    if critical_count == 0 and warning_count == 0:
        print("✓ ОТЛИЧНО! Все параметры в норме, детекция маловероятна.")
    elif critical_count == 0 and warning_count <= 3:
        print("⚠ ХОРОШО! Есть мелкие предупреждения, но критичных проблем нет.")
    elif critical_count <= 1:
        print("⚠ УДОВЛЕТВОРИТЕЛЬНО! Обнаружены проблемы, требуется доработка.")
    else:
        print("✗ ПЛОХО! Множественные критичные проблемы, детекция гарантирована!")

    print(f"\nВсего проблем: {len(results['issues'])}")
    print(f"  Критичных: {critical_count}")
    print(f"  Предупреждений: {warning_count}")
    print("="*80)


async def main():
    if sys.platform == 'win32':
        os.system('chcp 65001 > nul')
        sys.stdout.reconfigure(encoding='utf-8')

    print("="*80)
    print("БЫСТРАЯ ЛОКАЛЬНАЯ ПРОВЕРКА STEALTH")
    print("="*80)
    print("\nЭта проверка выполняется локально без посещения внешних сайтов")
    print("и занимает всего несколько секунд.\n")

    browser_manager = BrowserManager(
        proxy=None,  # Без прокси для быстрой проверки
        headless=False
    )

    try:
        print("[SETUP] Настройка браузера...")
        await browser_manager.setup()
        print("   ✓ Готово!\n")

        # Переходим на пустую страницу
        await browser_manager.page.goto("about:blank")

        # Выполняем проверку
        await quick_check(browser_manager.page)

        print("\n[INFO] Браузер остается открытым для ручной проверки.")
        print("Нажмите Ctrl+C для закрытия...")

        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n[INFO] Закрытие...")
    except Exception as e:
        print(f"\n[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await browser_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
