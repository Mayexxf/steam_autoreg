# 🚨 СРОЧНЫЕ ИСПРАВЛЕНИЯ CreepJS детекций

На основе детального анализа обнаружены **КРИТИЧНЫЕ** детекции.

## 🔴 Проблема #1: `plugins (0): blocked`

**Что детектируется:**
```
plugins (0): blocked
```

**Причина:**
У вас **0 плагинов** в `navigator.plugins`, что является мгновенной детекцией бота.
Реальные браузеры Chrome/Edge всегда имеют как минимум 5 плагинов.

**Текущий код:**
В `outlook/browser.py:214` видно:
```
plugins: 5
mimeTypes: 2
```

Плагины инжектятся, но CreepJS все равно видит 0. Значит инжект не работает!

**СРОЧНОЕ ИСПРАВЛЕНИЕ:**

В `src/stealth/fingerprint_generator.py` найдите метод генерации fingerprint и добавьте:

```python
def _get_plugins_override(self):
    """
    Генерирует реалистичные plugins для Chrome/Edge
    КРИТИЧНО: должно быть минимум 5 плагинов
    """
    return """
        // Переопределяем navigator.plugins (ПРАВИЛЬНО)
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                const pluginsArray = [
                    {
                        name: 'PDF Viewer',
                        description: 'Portable Document Format',
                        filename: 'internal-pdf-viewer',
                        length: 2,
                        item: (index) => pluginsArray[0][index],
                        namedItem: (name) => pluginsArray[0][name],
                        0: { type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' },
                        1: { type: 'text/pdf', suffixes: 'pdf', description: 'Portable Document Format' }
                    },
                    {
                        name: 'Chrome PDF Viewer',
                        description: 'Portable Document Format',
                        filename: 'internal-pdf-viewer',
                        length: 2,
                        item: (index) => pluginsArray[1][index],
                        namedItem: (name) => pluginsArray[1][name],
                        0: { type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' },
                        1: { type: 'text/pdf', suffixes: 'pdf', description: 'Portable Document Format' }
                    },
                    {
                        name: 'Chromium PDF Viewer',
                        description: 'Portable Document Format',
                        filename: 'internal-pdf-viewer',
                        length: 2,
                        item: (index) => pluginsArray[2][index],
                        namedItem: (name) => pluginsArray[2][name],
                        0: { type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' },
                        1: { type: 'text/pdf', suffixes: 'pdf', description: 'Portable Document Format' }
                    },
                    {
                        name: 'Microsoft Edge PDF Viewer',
                        description: 'Portable Document Format',
                        filename: 'internal-pdf-viewer',
                        length: 2,
                        item: (index) => pluginsArray[3][index],
                        namedItem: (name) => pluginsArray[3][name],
                        0: { type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' },
                        1: { type: 'text/pdf', suffixes: 'pdf', description: 'Portable Document Format' }
                    },
                    {
                        name: 'WebKit built-in PDF',
                        description: 'Portable Document Format',
                        filename: 'internal-pdf-viewer',
                        length: 2,
                        item: (index) => pluginsArray[4][index],
                        namedItem: (name) => pluginsArray[4][name],
                        0: { type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' },
                        1: { type: 'text/pdf', suffixes: 'pdf', description: 'Portable Document Format' }
                    }
                ];

                // Делаем как массив
                const plugins = Object.create(PluginArray.prototype);
                plugins.length = pluginsArray.length;
                pluginsArray.forEach((plugin, index) => {
                    plugins[index] = plugin;
                    plugins[plugin.name] = plugin;
                });

                plugins.item = function(index) {
                    return this[index] || null;
                };
                plugins.namedItem = function(name) {
                    return this[name] || null;
                };
                plugins.refresh = function() {};

                return plugins;
            },
            configurable: true
        });

        // Переопределяем navigator.mimeTypes
        Object.defineProperty(navigator, 'mimeTypes', {
            get: () => {
                const mimeTypesArray = [
                    { type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format', enabledPlugin: navigator.plugins[0] },
                    { type: 'text/pdf', suffixes: 'pdf', description: 'Portable Document Format', enabledPlugin: navigator.plugins[0] }
                ];

                const mimeTypes = Object.create(MimeTypeArray.prototype);
                mimeTypes.length = mimeTypesArray.length;
                mimeTypesArray.forEach((mimeType, index) => {
                    mimeTypes[index] = mimeType;
                    mimeTypes[mimeType.type] = mimeType;
                });

                mimeTypes.item = function(index) {
                    return this[index] || null;
                };
                mimeTypes.namedItem = function(name) {
                    return this[name] || null;
                };

                return mimeTypes;
            },
            configurable: true
        });
    """
```

---

## 🔴 Проблема #2: `headless: blocked`, `stealth: blocked`, `chromium: blocked`

**Что детектируется:**
```
chromium: blocked
like headless: blocked
headless: blocked
stealth: blocked
```

**Причина:**
CreepJS использует продвинутые техники детекции:
1. Проверяет `window.chrome` properties
2. Ищет следы playwright-stealth
3. Детектирует отсутствие `chrome.loadTimes()`
4. Проверяет `navigator.webdriver` через прототипы

**СРОЧНОЕ ИСПРАВЛЕНИЕ:**

Нужно **ОТКЛЮЧИТЬ** `playwright-stealth` и сделать свои обходы!

В `outlook/browser.py:189-191` **ЗАКОММЕНТИРОВАТЬ**:

```python
# ❌ ОТКЛЮЧАЕМ playwright-stealth - он ДЕТЕКТИРУЕТСЯ!
# if STEALTH_AVAILABLE:
#     await stealth_async(self.page)
#     print("[STEALTH] playwright-stealth применён [+]")
```

Вместо этого добавить в `fingerprint_generator.py`:

```python
def _get_advanced_stealth(self):
    """
    Продвинутые stealth обходы БЕЗ playwright-stealth
    """
    return """
        // 1. Chrome runtime (КРИТИЧНО для Chromium)
        if (!window.chrome) {
            window.chrome = {};
        }

        // Добавляем chrome.runtime
        window.chrome.runtime = {
            OnInstalledReason: {
                CHROME_UPDATE: "chrome_update",
                INSTALL: "install",
                SHARED_MODULE_UPDATE: "shared_module_update",
                UPDATE: "update"
            },
            OnRestartRequiredReason: {
                APP_UPDATE: "app_update",
                OS_UPDATE: "os_update",
                PERIODIC: "periodic"
            },
            PlatformArch: {
                ARM: "arm",
                ARM64: "arm64",
                MIPS: "mips",
                MIPS64: "mips64",
                X86_32: "x86-32",
                X86_64: "x86-64"
            },
            PlatformNaclArch: {
                ARM: "arm",
                MIPS: "mips",
                MIPS64: "mips64",
                X86_32: "x86-32",
                X86_64: "x86-64"
            },
            PlatformOs: {
                ANDROID: "android",
                CROS: "cros",
                LINUX: "linux",
                MAC: "mac",
                OPENBSD: "openbsd",
                WIN: "win"
            },
            RequestUpdateCheckStatus: {
                NO_UPDATE: "no_update",
                THROTTLED: "throttled",
                UPDATE_AVAILABLE: "update_available"
            },
            id: undefined  // Не extension
        };

        // 2. Chrome loadTimes (deprecated но все еще проверяется)
        window.chrome.loadTimes = function() {
            return {
                commitLoadTime: Date.now() / 1000 - Math.random() * 2,
                connectionInfo: "http/1.1",
                finishDocumentLoadTime: Date.now() / 1000 - Math.random(),
                finishLoadTime: Date.now() / 1000 - Math.random() * 0.5,
                firstPaintAfterLoadTime: 0,
                firstPaintTime: Date.now() / 1000 - Math.random(),
                navigationType: "Other",
                npnNegotiatedProtocol: "http/1.1",
                requestTime: Date.now() / 1000 - Math.random() * 3,
                startLoadTime: Date.now() / 1000 - Math.random() * 2.5,
                wasAlternateProtocolAvailable: false,
                wasFetchedViaSpdy: false,
                wasNpnNegotiated: false
            };
        };

        // 3. Chrome csi (Chrome Speed Index)
        window.chrome.csi = function() {
            return {
                onloadT: Date.now(),
                pageT: Math.random() * 1000 + 500,
                startE: Date.now() - Math.random() * 3000,
                tran: 15
            };
        };

        // 4. Permissions API (обязательно!)
        const originalQuery = navigator.permissions.query;
        navigator.permissions.query = function(parameters) {
            // Для некоторых permissions возвращаем granted
            if (parameters.name === 'notifications') {
                return Promise.resolve({ state: 'granted', onchange: null });
            }
            return originalQuery.apply(this, arguments);
        };

        // 5. Battery API (убираем - подозрительно если есть)
        if ('getBattery' in navigator) {
            delete navigator.getBattery;
        }

        // 6. Webdriver - ПОЛНОСТЬЮ убираем
        delete Object.getPrototypeOf(navigator).webdriver;
        Object.defineProperty(Object.getPrototypeOf(navigator), 'webdriver', {
            get: () => undefined,
            configurable: true
        });

        // 7. Language consistency
        Object.defineProperty(navigator, 'language', {
            get: () => '%(language)s',
            configurable: true
        });
        Object.defineProperty(navigator, 'languages', {
            get: () => %(languages)s,
            configurable: true
        });
    """
```

---

## 🔴 Проблема #3: `platform hints: blocked`

**Что детектируется:**
```
platform hints: blocked
```

**Причина:**
User-Agent Client Hints API (`navigator.userAgentData`) отсутствует или заблокирован.
Это НОВОЕ API которое обязательно должно быть в современном Chrome.

**СРОЧНОЕ ИСПРАВЛЕНИЕ:**

Добавить в fingerprint:

```python
def _get_user_agent_data(self):
    """
    Добавляет navigator.userAgentData (User-Agent Client Hints)
    КРИТИЧНО для Chrome 90+
    """
    platform = self.fingerprint.get('platform', 'Windows')

    # Определяем platform на основе OS
    if 'Win' in platform:
        ua_platform = 'Windows'
        platform_version = '10.0.0'
    elif 'Mac' in platform:
        ua_platform = 'macOS'
        platform_version = '13.0.0'
    else:
        ua_platform = 'Linux'
        platform_version = '5.10.0'

    return f"""
        Object.defineProperty(navigator, 'userAgentData', {{
            get: () => ({{
                brands: [
                    {{ brand: "Microsoft Edge", version: "120" }},
                    {{ brand: "Chromium", version: "120" }},
                    {{ brand: "Not:A-Brand", version: "99" }}
                ],
                mobile: false,
                platform: "{ua_platform}",
                getHighEntropyValues: async (hints) => {{
                    return {{
                        architecture: "x86",
                        bitness: "64",
                        brands: [
                            {{ brand: "Microsoft Edge", version: "120" }},
                            {{ brand: "Chromium", version: "120" }},
                            {{ brand: "Not:A-Brand", version: "99" }}
                        ],
                        fullVersionList: [
                            {{ brand: "Microsoft Edge", version: "120.0.2210.91" }},
                            {{ brand: "Chromium", version: "120.0.6099.109" }},
                            {{ brand: "Not:A-Brand", version: "99.0.0.0" }}
                        ],
                        mobile: false,
                        model: "",
                        platform: "{ua_platform}",
                        platformVersion: "{platform_version}",
                        uaFullVersion: "120.0.2210.91",
                        wow64: false
                    }};
                }},
                toJSON: () => ({{
                    brands: [
                        {{ brand: "Microsoft Edge", version: "120" }},
                        {{ brand: "Chromium", version: "120" }},
                        {{ brand: "Not:A-Brand", version: "99" }}
                    ],
                    mobile: false,
                    platform: "{ua_platform}"
                }})
            }}),
            configurable: true
        }});
    """
```

---

## 🔴 Проблема #4: Lies/Hashes несоответствия

**Что детектируется:**
```
Lies: 0150a749, 751e5ea7, 8a9f252a, cc974c5d
```

**Причина:**
CreepJS вычисляет fingerprint hashes и находит несоответствия между:
- Canvas fingerprint
- WebGL fingerprint
- Audio fingerprint
- Fonts fingerprint

**ИСПРАВЛЕНИЕ:**

Добавить **детерминированный** noise в Canvas/Audio:

```python
def _get_canvas_noise(self):
    """
    Добавляет ДЕТЕРМИНИРОВАННЫЙ шум в canvas
    Seed на основе deviceId - всегда одинаковый для одной сессии
    """
    device_id = self.fingerprint.get('deviceId', 'default')
    seed = abs(hash(device_id)) % 10000

    return f"""
        // Детерминированный RNG на основе seed
        let canvasSeed = {seed};
        function seededRandom() {{
            const x = Math.sin(canvasSeed++) * 10000;
            return x - Math.floor(x);
        }}

        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        const originalToBlob = HTMLCanvasElement.prototype.toBlob;
        const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;

        // Добавляем минимальный шум к getImageData
        CanvasRenderingContext2D.prototype.getImageData = function() {{
            const imageData = originalGetImageData.apply(this, arguments);

            // Добавляем шум к каждому 10-му пикселю
            for (let i = 0; i < imageData.data.length; i += 40) {{
                imageData.data[i] = imageData.data[i] + (seededRandom() > 0.5 ? 1 : -1);
            }}

            return imageData;
        }};

        HTMLCanvasElement.prototype.toDataURL = function() {{
            return originalToDataURL.apply(this, arguments);
        }};

        HTMLCanvasElement.prototype.toBlob = function() {{
            return originalToBlob.apply(this, arguments);
        }};
    """
```

---

## 📋 Приоритет исправлений

1. **НЕМЕДЛЕННО**: Исправить `plugins (0): blocked` - критичная детекция
2. **СРОЧНО**: Отключить playwright-stealth и добавить свои обходы
3. **СРОЧНО**: Добавить `navigator.userAgentData` (platform hints)
4. **ВАЖНО**: Добавить детерминированный canvas noise

---

## ✅ Следующие шаги

1. Применить все исправления
2. Запустить `python detailed_creepjs_analysis.py` снова
3. Проверить что все "blocked" исчезли
4. Проверить количество плагинов > 0
