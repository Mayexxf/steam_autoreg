"""
Генератор уникальных browser fingerprints
Поддерживает Chrome и Firefox с правильными fingerprint значениями
"""

import random
from typing import Dict, Any


class FingerprintGenerator:
    """Генерирует согласованные browser fingerprint профили"""

    # WebGL конфигурации для CHROME (с ANGLE и Google Inc.)
    WEBGL_CONFIGS_CHROME = [
        # NVIDIA (популярные в 2024-2025)
        {'vendor': 'Google Inc. (NVIDIA)', 'renderer': 'ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 Direct3D11 vs_5_0 ps_5_0, D3D11)'},
        {'vendor': 'Google Inc. (NVIDIA)', 'renderer': 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)'},
        {'vendor': 'Google Inc. (NVIDIA)', 'renderer': 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0, D3D11)'},
        {'vendor': 'Google Inc. (NVIDIA)', 'renderer': 'ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Direct3D11 vs_5_0 ps_5_0, D3D11)'},
        {'vendor': 'Google Inc. (NVIDIA)', 'renderer': 'ANGLE (NVIDIA, NVIDIA GeForce RTX 2060 Direct3D11 vs_5_0 ps_5_0, D3D11)'},
        {'vendor': 'Google Inc. (NVIDIA)', 'renderer': 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Ti Direct3D11 vs_5_0 ps_5_0, D3D11)'},
        # AMD (актуальные)
        {'vendor': 'Google Inc. (AMD)', 'renderer': 'ANGLE (AMD, AMD Radeon RX 7600 Direct3D11 vs_5_0 ps_5_0, D3D11)'},
        {'vendor': 'Google Inc. (AMD)', 'renderer': 'ANGLE (AMD, AMD Radeon RX 6700 XT Direct3D11 vs_5_0 ps_5_0, D3D11)'},
        {'vendor': 'Google Inc. (AMD)', 'renderer': 'ANGLE (AMD, AMD Radeon RX 6600 XT Direct3D11 vs_5_0 ps_5_0, D3D11)'},
        # Intel (актуальные)
        {'vendor': 'Google Inc. (Intel)', 'renderer': 'ANGLE (Intel, Intel(R) Arc(TM) A750 Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)'},
        {'vendor': 'Google Inc. (Intel)', 'renderer': 'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)'},
        {'vendor': 'Google Inc. (Intel)', 'renderer': 'ANGLE (Intel, Intel(R) UHD Graphics 770 Direct3D11 vs_5_0 ps_5_0, D3D11)'},
    ]

    # WebGL конфигурации для FIREFOX (нативные драйверы без ANGLE)
    # WEBGL_CONFIGS_FIREFOX = [
    #     # NVIDIA (популярные в 2024-2025) - Firefox использует нативные драйверы
    #     {'vendor': 'NVIDIA Corporation', 'renderer': 'NVIDIA GeForce RTX 4060/PCIe/SSE2'},
    #     {'vendor': 'NVIDIA Corporation', 'renderer': 'NVIDIA GeForce RTX 3060/PCIe/SSE2'},
    #     {'vendor': 'NVIDIA Corporation', 'renderer': 'NVIDIA GeForce RTX 3070/PCIe/SSE2'},
    #     {'vendor': 'NVIDIA Corporation', 'renderer': 'NVIDIA GeForce RTX 4070/PCIe/SSE2'},
    #     {'vendor': 'NVIDIA Corporation', 'renderer': 'NVIDIA GeForce RTX 2060/PCIe/SSE2'},
    #     {'vendor': 'NVIDIA Corporation', 'renderer': 'NVIDIA GeForce GTX 1660 Ti/PCIe/SSE2'},
    #     {'vendor': 'NVIDIA Corporation', 'renderer': 'NVIDIA GeForce RTX 3060 Ti/PCIe/SSE2'},
    #     # AMD (актуальные) - Firefox формат
    #     {'vendor': 'ATI Technologies Inc.', 'renderer': 'AMD Radeon RX 7600'},
    #     {'vendor': 'ATI Technologies Inc.', 'renderer': 'AMD Radeon RX 6700 XT'},
    #     {'vendor': 'ATI Technologies Inc.', 'renderer': 'AMD Radeon RX 6600 XT'},
    #     {'vendor': 'ATI Technologies Inc.', 'renderer': 'AMD Radeon RX 6600'},
    #     # Intel (актуальные) - Firefox формат
    #     {'vendor': 'Intel', 'renderer': 'Intel(R) Arc(TM) A750 Graphics'},
    #     {'vendor': 'Intel', 'renderer': 'Intel(R) Iris(R) Xe Graphics'},
    #     {'vendor': 'Intel', 'renderer': 'Intel(R) UHD Graphics 770'},
    # ]

    # Hardware конфигурации (актуальные для 2024-2025)
    HARDWARE_CONFIGS = [
        {'cores': 6, 'memory': 16},  # Средний (Intel i5 12-13 gen, Ryzen 5 5600X)
        {'cores': 8, 'memory': 16},  # Хороший (Intel i5 13-14 gen, Ryzen 5 7600X)
        {'cores': 8, 'memory': 32},  # Мощный (Intel i7 12-13 gen, Ryzen 7 5800X)
        {'cores': 12, 'memory': 32}, # Топовый (Intel i7 13-14 gen, Ryzen 7 7700X)
        {'cores': 16, 'memory': 32}, # Workstation (Intel i9 13-14 gen, Ryzen 9 7900X)
        {'cores': 16, 'memory': 64}, # High-end Workstation
    ]

    # Viewports (САМЫЕ ПОПУЛЯРНЫЕ разрешения - уменьшаем уникальность!)
    VIEWPORTS = [
        {'width': 1920, 'height': 1080},  # Full HD (23% всех пользователей!)
        {'width': 1920, 'height': 1080},  # Full HD (повторяем для увеличения вероятности)
        {'width': 1366, 'height': 768},   # Laptop (13% всех пользователей!)
        {'width': 1366, 'height': 768},   # Laptop (повторяем)
        {'width': 1536, 'height': 864},   # Windows 125% scaling
        {'width': 1440, 'height': 900},   # MacBook Pro 13"
    ]

    # Locales & Timezones
    LOCALES = [
        ('en-US', 'America/New_York'),
        ('en-US', 'America/Chicago'),
        ('en-US', 'America/Los_Angeles'),
        ('en-GB', 'Europe/London'),
        ('de-DE', 'Europe/Berlin'),
        ('nl-NL', 'Europe/Amsterdam'),
        ('pl-PL', 'Europe/Warsaw'),
    ]

    @staticmethod
    def generate(browser_type: str = 'chrome') -> Dict[str, Any]:
        """
        Генерирует согласованный fingerprint профиль

        Args:
            browser_type: 'chrome' или 'firefox'

        Returns:
            dict: Конфигурация для инжектора
        """
        # Выбираем правильные WebGL configs в зависимости от браузера
        webgl = random.choice(FingerprintGenerator.WEBGL_CONFIGS_CHROME)

        hardware = random.choice(FingerprintGenerator.HARDWARE_CONFIGS)
        viewport = random.choice(FingerprintGenerator.VIEWPORTS)
        locale, timezone = random.choice(FingerprintGenerator.LOCALES)

        # Canvas noise (случайное значение для XOR)
        canvas_noise = random.randint(1, 10)

        # Audio noise - НЕ используется! (вместо этого применяем округление в JS)
        # CreepJS детектирует неестественную точность если мы модифицируем sampleRate
        # Решение: в JS округлять итоговый audio sum до 2-4 знаков (как в реальном браузере)
        audio_noise = 0  # Не используется

        # Screen
        color_depth = random.choice([24, 30])
        pixel_ratio = random.choice([1, 1.25, 1.5, 2])

        return {
            'webgl': webgl,
            'hardware': hardware,
            'viewport': viewport,
            'locale': locale,
            'timezone': timezone,
            'canvas_noise': canvas_noise,
            'audio_noise': audio_noise,
            'screen': {
                'colorDepth': color_depth,
                'pixelRatio': pixel_ratio
            },
            'browser_type': browser_type.lower()
        }

    @staticmethod
    def get_injector_script(config: Dict[str, Any], browser_version: str = "140.0.0.0", browser_type: str = None) -> str:
        """
        Возвращает JavaScript для инжекта fingerprint

        Args:
            config: Dictionary с конфигурацией
            browser_version: Версия браузера (Chrome: "140.0.0.0", Firefox: "133.0")
            browser_type: 'chrome' или 'firefox' (если None, берется из config)

        Returns:
            str: JavaScript код
        """
        # Определяем тип браузера
        if browser_type is None:
            browser_type = config.get('browser_type', 'chrome')

        is_firefox = browser_type.lower() == 'firefox'

        # Формируем User-Agent и другие параметры в зависимости от браузера
        if is_firefox:
            fake_user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{browser_version}) Gecko/20100101 Firefox/{browser_version}"
            fake_app_version = "5.0 (Windows)"
            fake_vendor = ""  # Firefox имеет пустой vendor!
            fake_product_sub = "20100101"  # Firefox-специфично
            fake_oscpu = "Windows NT 10.0; Win64; x64"  # Firefox-специфично
        else:
            fake_user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{browser_version} Safari/537.36"
            fake_app_version = f"5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{browser_version} Safari/537.36"
            fake_vendor = "Google Inc."
            fake_product_sub = "20030107"  # Chrome-специфично
            fake_oscpu = None  # Chrome не имеет oscpu

        script = f"""
// ВАЖНО: Выполняется СРАЗУ, до загрузки DOM!
(function() {{
    'use strict';

    const BROWSER_TYPE = '{browser_type}';
    const IS_FIREFOX = BROWSER_TYPE === 'firefox';

    console.log('[FINGERPRINT] Browser type:', BROWSER_TYPE);

    // ============================================
    // РАННЯЯ ИНИЦИАЛИЗАЦИЯ WEB APIs (ДО ВСЕГО ОСТАЛЬНОГО!)
    // ============================================

    // NAVIGATOR.STORAGE API (против noContentIndex в CreepJS)
    try {{
        if (!navigator.storage) {{
            Object.defineProperty(navigator, 'storage', {{
                value: {{
                    estimate: async () => ({{
                        quota: 299982266368,  // ~280GB как в обычном Chrome
                        usage: Math.floor(Math.random() * 1000000000),  // Случайное использование
                        usageDetails: {{
                            indexedDB: Math.floor(Math.random() * 100000000),
                            caches: Math.floor(Math.random() * 50000000),
                            serviceWorkerRegistrations: 0
                        }}
                    }}),
                    getDirectory: async () => {{
                        throw new DOMException('Access denied', 'SecurityError');
                    }},
                    persist: async () => false,
                    persisted: async () => false
                }},
                configurable: true,
                enumerable: true,
                writable: false
            }});
            console.log('[FINGERPRINT] navigator.storage API added');
        }}
    }} catch(e) {{
        console.log('[FINGERPRINT] Could not add storage API:', e);
    }}

    // NAVIGATOR.CONTACTS API (против noContactsManager в CreepJS)
    try {{
        if (!navigator.contacts && !IS_FIREFOX) {{
            Object.defineProperty(navigator, 'contacts', {{
                value: {{
                    select: async (properties, options) => {{
                        throw new DOMException(
                            'contacts.select() requires user gesture',
                            'SecurityError'
                        );
                    }},
                    getProperties: async () => ['name', 'email', 'tel', 'address', 'icon']
                }},
                configurable: true,
                enumerable: true,
                writable: false
            }});
            console.log('[FINGERPRINT] navigator.contacts API added');
        }}
    }} catch(e) {{
        console.log('[FINGERPRINT] Could not add contacts API:', e);
    }}

    // NAVIGATOR.CONNECTION API + downlinkMax (против noDownlinkMax в CreepJS)
    try {{
        if (!navigator.connection && !IS_FIREFOX) {{
            const connectionData = {{
                downlink: 10,
                downlinkMax: Infinity,  // КРИТИЧНО!
                effectiveType: '4g',
                rtt: 50,
                saveData: false,
                type: 'wifi',
                onchange: null,
                addEventListener: function() {{}},
                removeEventListener: function() {{}},
                dispatchEvent: function() {{ return true; }}
            }};

            Object.defineProperty(navigator, 'connection', {{
                get: () => connectionData,
                configurable: true,
                enumerable: true
            }});

            console.log('[FINGERPRINT] navigator.connection API added (downlinkMax: Infinity)');
        }} else if (navigator.connection && navigator.connection.downlinkMax === undefined) {{
            Object.defineProperty(navigator.connection, 'downlinkMax', {{
                get: () => Infinity,
                configurable: true,
                enumerable: true
            }});
            console.log('[FINGERPRINT] downlinkMax added to existing connection');
        }}
    }} catch(e) {{
        console.log('[FINGERPRINT] Could not add connection API:', e);
    }}

    // NOTIFICATION API - FIX (против notificationIsDenied в CreepJS)
    try {{
        if (typeof Notification !== 'undefined' && Notification.permission === 'denied') {{
            // Если Notification.permission = denied, меняем на default
            Object.defineProperty(Notification, 'permission', {{
                get: () => 'default',
                configurable: true,
                enumerable: true
            }});
            console.log('[FINGERPRINT] Notification.permission changed to default');
        }}
    }} catch(e) {{
        console.log('[FINGERPRINT] Could not fix Notification.permission:', e);
    }}

    // NAVIGATOR.STANDALONE (против noTaskbar в CreepJS)
    try {{
        if (navigator.standalone === undefined && !IS_FIREFOX) {{
            // standalone - это iOS Safari специфичное свойство
            // На desktop Chrome/Windows оно должно быть false
            Object.defineProperty(navigator, 'standalone', {{
                get: () => false,
                configurable: true,
                enumerable: true
            }});
            console.log('[FINGERPRINT] navigator.standalone added (false)');
        }}
    }} catch(e) {{
        console.log('[FINGERPRINT] Could not add navigator.standalone:', e);
    }}

    // ============================================
    // 0. РАННЯЯ ПОДМЕНА (до создания canvas!)
    // ============================================
    const canvasNoise = {config['canvas_noise']};

    // Перехватываем createElement для canvas
    const originalCreateElement = document.createElement;
    document.createElement = function(tagName) {{
        const element = originalCreateElement.apply(this, arguments);

        if (tagName && tagName.toLowerCase() === 'canvas') {{
            console.log('[CANVAS] Creating canvas element with noise:', canvasNoise);

            // Подменяем getContext для этого canvas
            const originalGetContext = element.getContext;
            element.getContext = function(contextType, contextAttributes) {{
                const context = originalGetContext.apply(this, arguments);

                if (contextType === '2d' && context) {{
                    console.log('[CANVAS] 2D context created, applying minimal noise');

                    // Минимальная подмена fillText (только микро-сдвиг)
                    const originalFillText = context.fillText;
                    context.fillText = function(text, x, y, maxWidth) {{
                        const shift = (canvasNoise * 0.00001);  // Очень маленький сдвиг
                        return originalFillText.apply(this, [text, x + shift, y + shift, maxWidth]);
                    }};

                    // Подменяем strokeText
                    const originalStrokeText = context.strokeText;
                    context.strokeText = function(text, x, y, maxWidth) {{
                        const shift = (canvasNoise % 3) * 0.0001;
                        return originalStrokeText.apply(this, [text, x + shift, y + shift, maxWidth]);
                    }};

                    // Подменяем fillRect
                    const originalFillRect = context.fillRect;
                    context.fillRect = function(x, y, w, h) {{
                        const shift = (canvasNoise % 2) * 0.0001;
                        return originalFillRect.apply(this, [x + shift, y + shift, w, h]);
                    }};

                    // Подменяем getImageData (SUBTLE noise, не XOR!)
                    const originalGetImageData = context.getImageData;
                    context.getImageData = function(sx, sy, sw, sh) {{
                        const imageData = originalGetImageData.apply(this, arguments);
                        // Добавляем ОЧЕНЬ маленький, естественный шум
                        // Только к каждому 100-му пикселю, +/- 1
                        for (let i = 0; i < imageData.data.length; i += 400) {{
                            const noise = (canvasNoise % 2 === 0) ? 1 : -1;
                            imageData.data[i] = Math.max(0, Math.min(255, imageData.data[i] + noise));
                        }}
                        return imageData;
                    }};
                }}

                return context;
            }};

            // Подменяем toDataURL для этого canvas (SUBTLE noise!)
            const originalToDataURL = element.toDataURL;
            element.toDataURL = function(type) {{
                // НЕ модифицируем toDataURL - getImageData уже добавил noise
                // Двойная модификация создает детекцию!
                return originalToDataURL.apply(this, arguments);
            }};
        }}

        return element;
    }};

    // ============================================
    // 1. WEBGL FINGERPRINT (безопасное переопределение)
    // ============================================
    try {{
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) return '{config['webgl']['vendor']}';
            if (parameter === 37446) return '{config['webgl']['renderer']}';
            return getParameter.apply(this, arguments);
        }};
        console.log('[FINGERPRINT] WebGL overridden');
    }} catch(e) {{
        console.log('[FINGERPRINT] Could not override WebGL:', e);
    }}

    try {{
        if (typeof WebGL2RenderingContext !== 'undefined') {{
            const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) return '{config['webgl']['vendor']}';
                if (parameter === 37446) return '{config['webgl']['renderer']}';
                return getParameter2.apply(this, arguments);
            }};
        }}
    }} catch(e) {{
        console.log('[FINGERPRINT] Could not override WebGL2:', e);
    }}

    // ============================================
    // 2. CANVAS FINGERPRINT - уже обработан выше через createElement
    // ============================================

    // ============================================
    // 3. HARDWARE (безопасное переопределение)
    // ============================================
    try {{
        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            get: () => {config['hardware']['cores']},
            configurable: true
        }});
    }} catch(e) {{
        console.log('[FINGERPRINT] Could not override hardwareConcurrency:', e);
    }}

    try {{
        if (navigator.deviceMemory !== undefined) {{
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {config['hardware']['memory']},
                configurable: true
            }});
        }}
    }} catch(e) {{
        console.log('[FINGERPRINT] Could not override deviceMemory:', e);
    }}

    // ============================================
    // 4. SCREEN (безопасное переопределение)
    // ============================================
    try {{
        Object.defineProperty(screen, 'colorDepth', {{
            get: () => {config['screen']['colorDepth']},
            configurable: true
        }});
    }} catch(e) {{
        console.log('[FINGERPRINT] Could not override colorDepth:', e);
    }}

    try {{
        Object.defineProperty(screen, 'pixelDepth', {{
            get: () => {config['screen']['colorDepth']},
            configurable: true
        }});
    }} catch(e) {{
        console.log('[FINGERPRINT] Could not override pixelDepth:', e);
    }}

    // ============================================
    // 5. AUDIO CONTEXT - ОКРУГЛЕНИЕ (против красных цифр в CreepJS!)
    // ============================================
    // CreepJS детектирует НЕЕСТЕСТВЕННУЮ ТОЧНОСТЬ в audio fingerprint
    // Решение: округляем AnalyserNode.getFloatFrequencyData и getFloatTimeDomainData
    try {{
        if (typeof AnalyserNode !== 'undefined') {{
            // Перехватываем getFloatFrequencyData (используется для audio fingerprint)
            const originalGetFloatFrequencyData = AnalyserNode.prototype.getFloatFrequencyData;
            AnalyserNode.prototype.getFloatFrequencyData = function(array) {{
                originalGetFloatFrequencyData.apply(this, arguments);

                // Округляем значения до 2-4 знаков (как в реальном браузере)
                // Это убирает "красные цифры" в CreepJS!
                for (let i = 0; i < array.length; i++) {{
                    // Округляем до 3 знаков после запятой
                    array[i] = Math.round(array[i] * 1000) / 1000;
                }}

                return array;
            }};

            // Перехватываем getFloatTimeDomainData
            const originalGetFloatTimeDomainData = AnalyserNode.prototype.getFloatTimeDomainData;
            AnalyserNode.prototype.getFloatTimeDomainData = function(array) {{
                originalGetFloatTimeDomainData.apply(this, arguments);

                // Округляем до 3 знаков
                for (let i = 0; i < array.length; i++) {{
                    array[i] = Math.round(array[i] * 1000) / 1000;
                }}

                return array;
            }};

            console.log('[FINGERPRINT] Audio API rounded to 3 decimal places (anti-CreepJS)');
        }}
    }} catch(e) {{
        console.log('[FINGERPRINT] Could not override AnalyserNode:', e);
    }}

    // ============================================
    // 6. AUTOMATION DETECTION (КРИТИЧНО - УЛЬТРА АГРЕССИВНОЕ УДАЛЕНИЕ!)
    // ============================================

    // КРИТИЧНО: Сначала полностью удаляем webdriver из прототипа (глубокая очистка)
    try {{
        // Удаляем из прототипа Navigator
        delete Object.getPrototypeOf(navigator).webdriver;
        // Удаляем из самого navigator
        delete navigator.webdriver;
    }} catch(e) {{}}

    // КРИТИЧНО: Переопределяем navigator.webdriver с МАКСИМАЛЬНОЙ агрессией
    const overrideWebdriver = () => {{
        try {{
            // Шаг 1: Удаляем из прототипа
            delete Object.getPrototypeOf(navigator).webdriver;
            delete navigator.webdriver;

            // Шаг 2: Переопределяем с getter который ВСЕГДА возвращает false (не undefined!)
            // CreepJS проверяет navigator.webdriver === true
            // Если возвращать undefined - это ТОЖЕ детектируется как аномалия!
            // Правильное значение для НОРМАЛЬНОГО браузера = false
            Object.defineProperty(Object.getPrototypeOf(navigator), 'webdriver', {{
                get: () => false,  // ВАЖНО: false, а не undefined!
                set: () => {{}},
                configurable: true,
                enumerable: true  // ВАЖНО: enumerable=true (как в обычном браузере!)
            }});
        }} catch(e) {{}}
    }};

    // Выполняем СРАЗУ (до любой проверки)
    overrideWebdriver();

    // И переопределяем ОЧЕНЬ часто (каждые 5ms!) чтобы Playwright не успел изменить
    setInterval(overrideWebdriver, 5);

    // Также переопределяем при ВСЕХ важных событиях
    ['DOMContentLoaded', 'load', 'readystatechange', 'pageshow', 'focus'].forEach(event => {{
        document.addEventListener(event, overrideWebdriver);
    }});

    // Удаляем ВСЕ automation-related свойства
    const automationProps = [
        '__webdriver_evaluate',
        '__selenium_evaluate',
        '__webdriver_script_function',
        '__webdriver_script_func',
        '__webdriver_script_fn',
        '__fxdriver_evaluate',
        '__driver_unwrapped',
        '__webdriver_unwrapped',
        '__driver_evaluate',
        '__selenium_unwrapped',
        '__fxdriver_unwrapped',
        '_Selenium_IDE_Recorder',
        '_selenium',
        'callSelenium',
        '__webdriver_script_func',
        '__webdriver_func',
        '__driver_evaluate',
        '__webdriver_evaluate',
        '__selenium_evaluate',
        '__fxdriver_evaluate',
        '__driver_unwrapped',
        '__webdriver_unwrapped',
        '__selenium_unwrapped',
        '__fxdriver_unwrapped',
        '__webdriverFunc'
    ];

    // Удаляем из navigator
    automationProps.forEach(prop => {{
        try {{
            delete navigator[prop];
            delete Object.getPrototypeOf(navigator)[prop];
            delete window[prop];
        }} catch(e) {{}}
    }});

    // Удаляем из window
    try {{
        delete window.domAutomation;
        delete window.domAutomationController;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
    }} catch(e) {{}}

    // Удаляем Chrome DevTools Protocol маркеры (document.$cdc_*)
    try {{
        const cdcProps = Object.keys(document).filter(key => key.startsWith('$cdc_') || key.startsWith('$chrome_'));
        cdcProps.forEach(prop => {{
            try {{
                delete document[prop];
            }} catch(e) {{}}
        }});
    }} catch(e) {{}}

    // Удаляем специфичные для Firefox Marionette маркеры
    try {{
        delete window.marionette;
        delete navigator.marionette;
    }} catch(e) {{}}

    console.log('[FINGERPRINT] navigator.webdriver = false (ULTRA AGGRESSIVE continuous override)');
    console.log('[FINGERPRINT] Current value:', navigator.webdriver);
    console.log('[FINGERPRINT] Expected: false (not undefined, not true)');

    // ============================================
    // 6.5. WEBRTC LEAK PROTECTION (КРИТИЧНО!)
    // ============================================
    // Блокируем WebRTC чтобы предотвратить утечку реального IP
    try {{
        // Переопределяем RTCPeerConnection чтобы использовать только relay (TURN)
        const originalRTCPeerConnection = window.RTCPeerConnection || window.mozRTCPeerConnection || window.webkitRTCPeerConnection;

        if (originalRTCPeerConnection) {{
            window.RTCPeerConnection = function(config, constraints) {{
                // Принудительно используем только TURN серверы (relay), блокируя host/srflx
                if (config && config.iceServers) {{
                    config.iceServers = config.iceServers.filter(server => {{
                        return server.urls && server.urls.toString().includes('turn');
                    }});
                }}

                // Если нет TURN серверов - блокируем создание вообще
                if (!config || !config.iceServers || config.iceServers.length === 0) {{
                    throw new DOMException('WebRTC is disabled', 'NotSupportedError');
                }}

                return new originalRTCPeerConnection(config, constraints);
            }};

            // Копируем прототип
            window.RTCPeerConnection.prototype = originalRTCPeerConnection.prototype;

            // Для старых браузеров
            if (window.webkitRTCPeerConnection) {{
                window.webkitRTCPeerConnection = window.RTCPeerConnection;
            }}
            if (window.mozRTCPeerConnection) {{
                window.mozRTCPeerConnection = window.RTCPeerConnection;
            }}

            console.log('[FINGERPRINT] WebRTC leak protection enabled (relay-only mode)');
        }}

        // Также блокируем navigator.mediaDevices.getUserMedia для предотвращения доступа к камере/микрофону
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {{
            const originalGetUserMedia = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);

            navigator.mediaDevices.getUserMedia = function(constraints) {{
                // Всегда отклоняем запрос
                return Promise.reject(new DOMException('Permission denied', 'NotAllowedError'));
            }};

            console.log('[FINGERPRINT] getUserMedia blocked (no camera/mic access)');
        }}
    }} catch(e) {{
        console.log('[FINGERPRINT] Could not setup WebRTC protection:', e);
    }}

    // ============================================
    // 7. NAVIGATOR PROPERTIES (зависит от браузера!)
    // ============================================
    const fakeUserAgent = `{fake_user_agent}`;
    const fakeAppVersion = `{fake_app_version}`;
    const fakePlatform = 'Win32';
    const fakeVendor = `{fake_vendor}`;  // Пустая строка для Firefox!
    const fakeProductSub = '{fake_product_sub}';
    """

        # Добавляем Firefox-специфичные свойства
        if is_firefox:
            script += f"""
    // FIREFOX-СПЕЦИФИЧНЫЕ СВОЙСТВА (минимальная модификация для стабильности)

    // КРИТИЧНО: Firefox НЕ должен иметь window.chrome!
    // Наличие window.chrome в Firefox = аномалия, детектируется CreepJS
    if (window.chrome) {{
        try {{
            delete window.chrome;
            console.log('[FIREFOX] Removed window.chrome (Firefox should not have it)');
        }} catch(e) {{
            console.log('[FINGERPRINT] Could not remove window.chrome:', e);
        }}
    }}

    // Firefox не имеет userAgentData
    if (navigator.userAgentData) {{
        try {{
            delete navigator.userAgentData;
            console.log('[FIREFOX] Removed navigator.userAgentData');
        }} catch(e) {{
            console.log('[FINGERPRINT] Could not remove userAgentData:', e);
        }}
    }}

    // ============================================
    // FIREFOX-СПЕЦИФИЧНЫЕ ANTI-HEADLESS ПРОВЕРКИ
    // ============================================

    // 1. Window dimensions (КРИТИЧНО для headless детекции!)
    try {{
        // В headless режиме outerWidth/outerHeight = 0
        // Это ГЛАВНЫЙ признак headless в CreepJS!
        if (window.outerWidth === 0 || window.outerHeight === 0) {{
            console.log('[ANTI-HEADLESS] Fixing zero window dimensions (headless marker)');

            // Переопределяем с реалистичными значениями
            Object.defineProperty(window, 'outerWidth', {{
                get: () => window.innerWidth || screen.width,
                configurable: true,
                enumerable: true
            }});

            Object.defineProperty(window, 'outerHeight', {{
                get: () => (window.innerHeight || screen.height) + 100,  // +100 для toolbar/titlebar
                configurable: true,
                enumerable: true
            }});

            console.log('[ANTI-HEADLESS] Window dimensions fixed:', window.outerWidth, 'x', window.outerHeight);
        }}
    }} catch(e) {{
        console.log('[FINGERPRINT] Could not override window dimensions:', e);
    }}

    // 2. Permissions API - должен быть доступен но возвращать default/prompt
    try {{
        if (navigator.permissions && navigator.permissions.query) {{
            const originalQuery = navigator.permissions.query.bind(navigator.permissions);

            navigator.permissions.query = function(parameters) {{
                // Возвращаем realistic permissions (не denied для всего!)
                return originalQuery(parameters).then(result => {{
                    // Если permission denied - меняем на prompt (более реалистично)
                    if (result.state === 'denied' && (parameters.name === 'notifications' || parameters.name === 'geolocation')) {{
                        Object.defineProperty(result, 'state', {{
                            get: () => 'prompt',
                            configurable: true,
                            enumerable: true
                        }});
                    }}
                    return result;
                }}).catch(err => {{
                    // Если ошибка - возвращаем prompt
                    return {{ state: 'prompt', onchange: null }};
                }});
            }};

            console.log('[ANTI-HEADLESS] Permissions API fixed (prompt instead of denied)');
        }}
    }} catch(e) {{
        console.log('[FINGERPRINT] Could not override permissions:', e);
    }}

    // 3. Screen orientation - должен быть доступен
    try {{
        if (!screen.orientation) {{
            Object.defineProperty(screen, 'orientation', {{
                get: () => ({{
                    type: 'landscape-primary',
                    angle: 0,
                    onchange: null
                }}),
                configurable: true,
                enumerable: true
            }});

            console.log('[ANTI-HEADLESS] screen.orientation added');
        }}
    }} catch(e) {{
        console.log('[FINGERPRINT] Could not add screen.orientation:', e);
    }}

    // 4. Notification.permission - НЕ denied (headless признак!)
    try {{
        if (typeof Notification !== 'undefined' && Notification.permission === 'denied') {{
            console.log('[ANTI-HEADLESS] Fixing Notification.permission (denied is headless marker)');

            Object.defineProperty(Notification, 'permission', {{
                get: () => 'default',  // default = более реалистично чем denied!
                configurable: true,
                enumerable: true
            }});

            console.log('[ANTI-HEADLESS] Notification.permission = default');
        }}
    }} catch(e) {{
        console.log('[FINGERPRINT] Could not fix Notification.permission:', e);
    }}

    // 5. matchMedia - должен работать корректно
    try {{
        const originalMatchMedia = window.matchMedia;

        window.matchMedia = function(query) {{
            const result = originalMatchMedia.call(window, query);

            // В headless часто matchMedia всегда возвращает false
            // Фиксим для важных media queries
            if (query.includes('prefers-color-scheme') || query.includes('prefers-reduced-motion')) {{
                if (result.matches === false && query.includes('dark')) {{
                    Object.defineProperty(result, 'matches', {{
                        get: () => true,  // dark theme
                        configurable: true
                    }});
                }}
            }}

            return result;
        }};

        console.log('[ANTI-HEADLESS] matchMedia enhanced');
    }} catch(e) {{
        console.log('[FINGERPRINT] Could not enhance matchMedia:', e);
    }}

    // 6. Speech Synthesis - должен быть доступен (против speechSynthesisLie в CreepJS)
    try {{
        if (window.speechSynthesis && !window.speechSynthesis.getVoices().length) {{
            console.log('[ANTI-HEADLESS] Adding speech synthesis voices');

            const originalGetVoices = window.speechSynthesis.getVoices.bind(window.speechSynthesis);

            // Переопределяем getVoices чтобы возвращать реалистичные голоса
            window.speechSynthesis.getVoices = function() {{
                const voices = originalGetVoices();

                // Если нет голосов - возвращаем фейковые (как в обычном Firefox)
                if (voices.length === 0) {{
                    return [
                        {{
                            voiceURI: 'Microsoft David Desktop - English (United States)',
                            name: 'Microsoft David Desktop - English (United States)',
                            lang: 'en-US',
                            localService: true,
                            default: true
                        }},
                        {{
                            voiceURI: 'Microsoft Zira Desktop - English (United States)',
                            name: 'Microsoft Zira Desktop - English (United States)',
                            lang: 'en-US',
                            localService: true,
                            default: false
                        }}
                    ];
                }}

                return voices;
            }};

            console.log('[ANTI-HEADLESS] Speech synthesis voices added');
        }}
    }} catch(e) {{
        console.log('[FINGERPRINT] Could not add speech synthesis:', e);
    }}

    // 7. mozInnerScreenX/Y - Firefox-специфичные свойства (против inconsistency)
    try {{
        if (window.mozInnerScreenX === undefined) {{
            Object.defineProperty(window, 'mozInnerScreenX', {{
                get: () => 0,
                configurable: true,
                enumerable: true
            }});

            Object.defineProperty(window, 'mozInnerScreenY', {{
                get: () => 0,
                configurable: true,
                enumerable: true
            }});

            console.log('[ANTI-HEADLESS] mozInnerScreen properties added');
        }}
    }} catch(e) {{
        console.log('[FINGERPRINT] Could not add mozInnerScreen:', e);
    }}

    console.log('[FINGERPRINT] Firefox mode: ANTI-HEADLESS patches applied');
    """
        else:
            # Chrome-специфичные свойства
            script += f"""
    // CHROME-СПЕЦИФИЧНЫЕ СВОЙСТВА

    // КРИТИЧНО: navigator.userAgentData (User-Agent Client Hints API)
    // Это ОБЯЗАТЕЛЬНО для Chrome 90+!
    try {{
        const majorVersion = '{browser_version.split('.')[0]}';
        const fullVersion = '{browser_version}';

        const brands = [
            {{ brand: 'Microsoft Edge', version: majorVersion }},
            {{ brand: 'Chromium', version: majorVersion }},
            {{ brand: 'Not:A-Brand', version: '99' }}
        ];

        const fullVersionList = [
            {{ brand: 'Microsoft Edge', version: fullVersion }},
            {{ brand: 'Chromium', version: fullVersion }},
            {{ brand: 'Not:A-Brand', version: '99.0.0.0' }}
        ];

        Object.defineProperty(navigator, 'userAgentData', {{
            get: () => ({{
                brands: brands,
                mobile: false,
                platform: 'Windows',
                getHighEntropyValues: async (hints) => {{
                    return {{
                        architecture: 'x86',
                        bitness: '64',
                        brands: brands,
                        fullVersionList: fullVersionList,
                        mobile: false,
                        model: '',
                        platform: 'Windows',
                        platformVersion: '10.0.0',
                        uaFullVersion: fullVersion,
                        wow64: false
                    }};
                }},
                toJSON: () => ({{
                    brands: brands,
                    mobile: false,
                    platform: 'Windows'
                }})
            }}),
            configurable: true,
            enumerable: true
        }});
        console.log('[FINGERPRINT] navigator.userAgentData added with platform hints');
    }} catch(e) {{
        console.log('[FINGERPRINT] Could not add userAgentData:', e);
    }}

    // CHROME OBJECT (расширенная версия с loadTimes и csi)
    try {{
        if (!window.chrome) {{
            window.chrome = {{}};
        }}

        // chrome.runtime (обязателен!)
        if (!window.chrome.runtime) {{
            window.chrome.runtime = {{
                OnInstalledReason: {{
                    CHROME_UPDATE: "chrome_update",
                    INSTALL: "install",
                    SHARED_MODULE_UPDATE: "shared_module_update",
                    UPDATE: "update"
                }},
                OnRestartRequiredReason: {{
                    APP_UPDATE: "app_update",
                    OS_UPDATE: "os_update",
                    PERIODIC: "periodic"
                }},
                PlatformArch: {{
                    ARM: "arm",
                    ARM64: "arm64",
                    MIPS: "mips",
                    MIPS64: "mips64",
                    X86_32: "x86-32",
                    X86_64: "x86-64"
                }},
                PlatformOs: {{
                    ANDROID: "android",
                    CROS: "cros",
                    LINUX: "linux",
                    MAC: "mac",
                    OPENBSD: "openbsd",
                    WIN: "win"
                }},
                id: undefined  // Не extension
            }};
        }}

        // chrome.loadTimes (deprecated но все еще проверяется)
        if (!window.chrome.loadTimes) {{
            window.chrome.loadTimes = function() {{
                const now = Date.now() / 1000;
                return {{
                    commitLoadTime: now - Math.random() * 2,
                    connectionInfo: "h2",
                    finishDocumentLoadTime: now - Math.random(),
                    finishLoadTime: now - Math.random() * 0.5,
                    firstPaintAfterLoadTime: 0,
                    firstPaintTime: now - Math.random(),
                    navigationType: "Other",
                    npnNegotiatedProtocol: "h2",
                    requestTime: now - Math.random() * 3,
                    startLoadTime: now - Math.random() * 2.5,
                    wasAlternateProtocolAvailable: false,
                    wasFetchedViaSpdy: true,
                    wasNpnNegotiated: true
                }};
            }};
        }}

        // chrome.csi (Chrome Speed Index)
        if (!window.chrome.csi) {{
            window.chrome.csi = function() {{
                return {{
                    onloadT: Date.now(),
                    pageT: Math.random() * 1000 + 500,
                    startE: Date.now() - Math.random() * 3000,
                    tran: 15
                }};
            }};
        }}

        // chrome.app (пустой объект)
        if (!window.chrome.app) {{
            window.chrome.app = {{}};
        }}

        console.log('[FINGERPRINT] window.chrome fully configured');
    }} catch(e) {{
        console.log('[FINGERPRINT] Could not configure window.chrome:', e);
    }}
    """

        # Общие свойства navigator (безопасное переопределение с try-catch)
        script += """

    // Безопасное переопределение navigator properties для Firefox
    try {
        Object.defineProperty(navigator, 'userAgent', {
            get: () => fakeUserAgent,
            configurable: true
        });
        console.log('[FINGERPRINT] UserAgent overridden:', fakeUserAgent);
    } catch(e) {
        console.log('[FINGERPRINT] Could not override userAgent:', e);
    }

    try {
        Object.defineProperty(navigator, 'appVersion', {
            get: () => fakeAppVersion,
            configurable: true
        });
    } catch(e) {
        console.log('[FINGERPRINT] Could not override appVersion:', e);
    }

    try {
        Object.defineProperty(navigator, 'platform', {
            get: () => fakePlatform,
            configurable: true
        });
    } catch(e) {
        console.log('[FINGERPRINT] Could not override platform:', e);
    }

    try {
        Object.defineProperty(navigator, 'vendor', {
            get: () => fakeVendor,
            configurable: true
        });
        console.log('[FINGERPRINT] Vendor:', fakeVendor);
    } catch(e) {
        console.log('[FINGERPRINT] Could not override vendor:', e);
    }

    try {
        Object.defineProperty(navigator, 'productSub', {
            get: () => fakeProductSub,
            configurable: true
        });
        console.log('[FINGERPRINT] ProductSub:', fakeProductSub);
    } catch(e) {
        console.log('[FINGERPRINT] Could not override productSub:', e);
    }

    // ============================================
    // 8. PLUGINS & MIMETYPES (ПРАВИЛЬНАЯ РЕАЛИЗАЦИЯ PluginArray!)
    // ============================================
    try {
        // Создаем MimeType objects
        class FakeMimeType {
            constructor(type, description, suffixes, enabledPlugin) {
                this.type = type;
                this.description = description;
                this.suffixes = suffixes;
                this.enabledPlugin = enabledPlugin;
            }
        }

        // Создаем Plugin objects
        class FakePlugin {
            constructor(name, description, filename, mimeTypes) {
                this.name = name;
                this.description = description;
                this.filename = filename;
                this.length = mimeTypes.length;

                // Добавляем mimeTypes как индексированные properties
                mimeTypes.forEach((mt, index) => {
                    this[index] = mt;
                    this[mt.type] = mt;
                });
            }

            item(index) {
                return this[index] || null;
            }

            namedItem(name) {
                return this[name] || null;
            }
        }

        // Создаем НАСТОЯЩИЕ Plugin объекты с MimeTypes
        const pdfMimeType1 = new FakeMimeType('application/pdf', 'Portable Document Format', 'pdf', null);
        const pdfMimeType2 = new FakeMimeType('text/pdf', 'Portable Document Format', 'pdf', null);

        const pluginsData = [
            new FakePlugin('PDF Viewer', 'Portable Document Format', 'internal-pdf-viewer', [pdfMimeType1, pdfMimeType2]),
            new FakePlugin('Chrome PDF Viewer', 'Portable Document Format', 'internal-pdf-viewer', [pdfMimeType1, pdfMimeType2]),
            new FakePlugin('Chromium PDF Viewer', 'Portable Document Format', 'internal-pdf-viewer', [pdfMimeType1, pdfMimeType2]),
            new FakePlugin('Microsoft Edge PDF Viewer', 'Portable Document Format', 'internal-pdf-viewer', [pdfMimeType1, pdfMimeType2]),
            new FakePlugin('WebKit built-in PDF', 'Portable Document Format', 'internal-pdf-viewer', [pdfMimeType1, pdfMimeType2])
        ];

        // Связываем mimeTypes с их enabledPlugin
        pluginsData.forEach(plugin => {
            for (let i = 0; i < plugin.length; i++) {
                plugin[i].enabledPlugin = plugin;
            }
        });

        // Создаем PluginArray (наследуется от Array)
        const pluginArray = Object.create(PluginArray.prototype);
        pluginArray.length = pluginsData.length;

        pluginsData.forEach((plugin, index) => {
            pluginArray[index] = plugin;
            pluginArray[plugin.name] = plugin;
        });

        // Добавляем методы PluginArray
        pluginArray.item = function(index) {
            return this[index] || null;
        };

        pluginArray.namedItem = function(name) {
            return this[name] || null;
        };

        pluginArray.refresh = function() {
            // Empty refresh function
        };

        // Переопределяем navigator.plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => pluginArray,
            configurable: true,
            enumerable: true
        });

        console.log('[FINGERPRINT] Plugins injected:', pluginArray.length);
    } catch(e) {
        console.log('[FINGERPRINT] Could not override plugins:', e);
    }

    try {
        // Создаем MimeTypeArray
        const mimeTypesData = [
            { type: 'application/pdf', description: 'Portable Document Format', suffixes: 'pdf', enabledPlugin: navigator.plugins[0] },
            { type: 'text/pdf', description: 'Portable Document Format', suffixes: 'pdf', enabledPlugin: navigator.plugins[0] }
        ];

        const mimeTypeArray = Object.create(MimeTypeArray.prototype);
        mimeTypeArray.length = mimeTypesData.length;

        mimeTypesData.forEach((mt, index) => {
            mimeTypeArray[index] = mt;
            mimeTypeArray[mt.type] = mt;
        });

        mimeTypeArray.item = function(index) {
            return this[index] || null;
        };

        mimeTypeArray.namedItem = function(name) {
            return this[name] || null;
        };

        Object.defineProperty(navigator, 'mimeTypes', {
            get: () => mimeTypeArray,
            configurable: true,
            enumerable: true
        });

        console.log('[FINGERPRINT] MimeTypes injected:', mimeTypeArray.length);
    } catch(e) {
        console.log('[FINGERPRINT] Could not override mimeTypes:', e);
    }

    // ============================================
    // 9. MEDIA DEVICES (mic, webcam) - FlowebBrowser style
    // ============================================
    try {
        if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
            const originalEnumerateDevices = navigator.mediaDevices.enumerateDevices.bind(navigator.mediaDevices);

            navigator.mediaDevices.enumerateDevices = function() {
                return originalEnumerateDevices().then(devices => {
                    // Возвращаем фейковые devices (mic, webcam) как в FlowebBrowser
                    return [
                        {
                            deviceId: "default",
                            kind: "audioinput",
                            label: "",
                            groupId: "default"
                        },
                        {
                            deviceId: "communications",
                            kind: "audioinput",
                            label: "",
                            groupId: "communications"
                        },
                        {
                            deviceId: "default",
                            kind: "videoinput",
                            label: "",
                            groupId: "default"
                        }
                    ];
                });
            };

            console.log('[FINGERPRINT] Media devices spoofed (mic, webcam visible but blocked)');
        }
    } catch(e) {
        console.log('[FINGERPRINT] Could not override mediaDevices:', e);
    }


    console.log('[FINGERPRINT] Injected successfully (safe mode)');
    console.log('[FINGERPRINT] WebGL Vendor:', '""" + config['webgl']['vendor'] + """');
    console.log('[FINGERPRINT] WebGL Renderer:', '""" + config['webgl']['renderer'] + """');
    console.log('[FINGERPRINT] Hardware:', """ + str(config['hardware']['cores']) + """ + ' cores, ' + """ + str(config['hardware']['memory']) + """ + ' GB');
    console.log('[FINGERPRINT] Canvas noise:', """ + str(config['canvas_noise']) + """);
    console.log('[FINGERPRINT] Browser type:', BROWSER_TYPE);
})();
"""
        return script


if __name__ == '__main__':
    # Тест
    print("=== FINGERPRINT GENERATOR TEST ===\n")

    print("CHROME Profiles:")
    for i in range(2):
        print(f"  Profile {i+1}:")
        config = FingerprintGenerator.generate(browser_type='chrome')
        print(f"    WebGL Vendor: {config['webgl']['vendor']}")
        print(f"    WebGL Renderer: {config['webgl']['renderer'][:60]}...")
        print(f"    Hardware: {config['hardware']['cores']} cores, {config['hardware']['memory']}GB")
        print()

    print("\nFIREFOX Profiles:")
    for i in range(2):
        print(f"  Profile {i+1}:")
        config = FingerprintGenerator.generate(browser_type='firefox')
        print(f"    WebGL Vendor: {config['webgl']['vendor']}")
        print(f"    WebGL Renderer: {config['webgl']['renderer']}")
        print(f"    Hardware: {config['hardware']['cores']} cores, {config['hardware']['memory']}GB")
        print()
