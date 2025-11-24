// ==========================================================
// 🛡️ FIREFOX ANTI-DETECTION EXTENSION
// ==========================================================
// Инжектируется на КАЖДУЮ страницу ДО загрузки DOM (document_start)
// Скрывает navigator.webdriver и другие признаки автоматизации

(function() {
    'use strict';

    // Создаем скрипт который выполнится в контексте страницы (не extension context)
    const script = document.createElement('script');
    script.textContent = `
        (function() {
            'use strict';

            console.log('[ANTIDETECT] Extension loaded - injecting anti-detection...');

            // ============================================
            // 1. HIDE navigator.webdriver (КРИТИЧНО!)
            // ============================================
            try {
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                    configurable: true
                });
                console.log('[ANTIDETECT] ✓ navigator.webdriver hidden');
            } catch (e) {
                console.error('[ANTIDETECT] ✗ Failed to hide navigator.webdriver:', e);
            }

            // ============================================
            // 2. УДАЛЕНИЕ SELENIUM ПЕРЕМЕННЫХ
            // ============================================
            const seleniumVars = [
                '__selenium_unwrapped',
                '__webdriver_script_fn',
                '__driver_evaluate',
                '__webdriver_evaluate',
                '__selenium_evaluate',
                '__fxdriver_evaluate',
                '__driver_unwrapped',
                '__webdriver_unwrapped',
                '__fxdriver_unwrapped',
                '_Selenium_IDE_Recorder',
                '_selenium',
                'callSelenium',
                '$cdc_',
                '$wdc_'
            ];

            seleniumVars.forEach(varName => {
                if (window[varName]) {
                    delete window[varName];
                }
                if (document[varName]) {
                    delete document[varName];
                }
            });

            console.log('[ANTIDETECT] ✓ Selenium variables cleaned');

            // ============================================
            // 3. PERMISSIONS API OVERRIDE
            // ============================================
            try {
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                console.log('[ANTIDETECT] ✓ Permissions API overridden');
            } catch (e) {
                // Игнорируем если permissions API недоступен
            }

            // ============================================
            // 4. PLUGINS OVERRIDE (для реалистичности)
            // ============================================
            try {
                Object.defineProperty(navigator, 'plugins', {
                    get: () => {
                        const plugins = [
                            {
                                0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: null},
                                description: "Portable Document Format",
                                filename: "internal-pdf-viewer",
                                length: 1,
                                name: "Chrome PDF Plugin"
                            },
                            {
                                0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: null},
                                description: "Portable Document Format",
                                filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                                length: 1,
                                name: "Chrome PDF Viewer"
                            }
                        ];
                        // Делаем похожим на PluginArray
                        Object.setPrototypeOf(plugins, PluginArray.prototype);
                        return plugins;
                    },
                    configurable: true
                });
                console.log('[ANTIDETECT] ✓ Plugins overridden');
            } catch (e) {
                // Игнорируем ошибки
            }

            // ============================================
            // 5. CHROME OBJECT (для обхода некоторых детектов)
            // ============================================
            if (!window.chrome) {
                Object.defineProperty(window, 'chrome', {
                    get: () => ({
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    }),
                    configurable: true
                });
                console.log('[ANTIDETECT] ✓ Chrome object added');
            }

            // ============================================
            // 6. LANGUAGES OVERRIDE
            // ============================================
            try {
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                    configurable: true
                });
                console.log('[ANTIDETECT] ✓ Languages overridden');
            } catch (e) {
                // Игнорируем
            }

            // ============================================
            // 7. УДАЛЕНИЕ AUTOMATION EXTENSION
            // ============================================
            try {
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            } catch (e) {}

            // ============================================
            // 8. IFRAME PROTECTION (применяем и к iframe)
            // ============================================
            const originalCreateElement = document.createElement;
            document.createElement = function(...args) {
                const element = originalCreateElement.apply(this, args);
                if (element.tagName === 'IFRAME') {
                    element.addEventListener('load', function() {
                        try {
                            if (element.contentWindow) {
                                Object.defineProperty(element.contentWindow.navigator, 'webdriver', {
                                    get: () => undefined
                                });
                            }
                        } catch (e) {
                            // Cross-origin iframe - игнорируем
                        }
                    });
                }
                return element;
            };

            console.log('[ANTIDETECT] ✓ All anti-detection measures applied');
            console.log('[ANTIDETECT] navigator.webdriver =', navigator.webdriver);
        })();
    `;

    // Инжектим скрипт в начало <head> или <html>
    (document.head || document.documentElement).appendChild(script);

    // Удаляем скрипт после выполнения чтобы не оставлять следов
    script.remove();

    console.log('[ANTIDETECT EXTENSION] Content script injected');
})();
