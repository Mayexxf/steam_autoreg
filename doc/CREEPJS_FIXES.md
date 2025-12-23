# Исправления проблем CreepJS

На основе анализа результатов CreepJS обнаружены следующие проблемы и предложены исправления.

## 🔴 Критические проблемы

### 1. **LocalStorage SecurityError**

**Проблема:**
```
SecurityError: Failed to read the 'localStorage' property from 'Window': Access is denied for this document.
```

**Причина:**
В `outlook/browser.py:194-195` localStorage применяется сразу после создания страницы (about:blank), где доступ к localStorage запрещен по security policy.

**Исправление:**

Заменить в `outlook/browser.py`:

```python
# СТАРЫЙ КОД (строки 187-195):
self.page = await self.context.new_page()

if STEALTH_AVAILABLE:
    await stealth_async(self.page)
    print("[STEALTH] playwright-stealth применён [+]")

if STEALTH_MODULES_AVAILABLE:
    await self._inject_storage()
    await self.apply_storage()  # ❌ Убрать эту строку!
```

На:

```python
# НОВЫЙ КОД:
self.page = await self.context.new_page()

if STEALTH_AVAILABLE:
    await stealth_async(self.page)
    print("[STEALTH] playwright-stealth применён [+]")

if STEALTH_MODULES_AVAILABLE:
    await self._inject_storage()
    # ✅ localStorage будет применен через add_init_script автоматически
    # или вручную после перехода на реальную страницу
```

И изменить `_inject_storage()`:

```python
async def _inject_storage(self):
    """Инжектирует localStorage данные через add_init_script"""
    if not STEALTH_MODULES_AVAILABLE:
        return

    try:
        storage_gen = StorageGenerator()
        storage_data = storage_gen.generate_full_storage(self.geo_config)
        storage_script = storage_gen.get_storage_script(storage_data)

        # ✅ Используем add_init_script вместо evaluate
        # Это безопаснее и работает на всех страницах
        await self.context.add_init_script(f"""
            (() => {{
                try {{
                    // Проверяем доступность localStorage
                    if (typeof localStorage !== 'undefined') {{
                        {storage_script}
                    }}
                }} catch(e) {{
                    console.log('[Storage] Skipped due to security policy');
                }}
            }})();
        """)

        print(f"[STORAGE] [+] Injected {len(storage_data)} localStorage items via add_init_script")
    except Exception as e:
        print(f"[STORAGE] Error: {e}")
```

Теперь localStorage будет безопасно применяться на всех страницах автоматически.

---

### 2. **Canvas/WebGL Fingerprint проблемы**

**Проблема:**
CreepJS детектирует несоответствия в Canvas и WebGL fingerprints (розовые секции).

**Причина:**
Fingerprint injection может быть неконсистентным или содержать значения, которые не соответствуют реальному hardware.

**Исправление:**

В `src/stealth/fingerprint_generator.py` нужно:

1. **Улучшить WebGL vendor/renderer consistency:**

```python
def _get_webgl_config(self):
    """
    Генерирует РЕАЛИСТИЧНЫЕ WebGL параметры на основе fingerprint
    """
    # Используем реальные комбинации GPU
    gpu_configs = [
        {
            'vendor': 'Google Inc. (Intel)',
            'renderer': 'ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'max_texture_size': 16384,
            'max_vertex_texture_units': 16,
            'max_renderbuffer_size': 16384
        },
        {
            'vendor': 'Google Inc. (NVIDIA)',
            'renderer': 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Ti Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'max_texture_size': 32768,
            'max_vertex_texture_units': 16,
            'max_renderbuffer_size': 32768
        },
        {
            'vendor': 'Google Inc. (Intel)',
            'renderer': 'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'max_texture_size': 16384,
            'max_vertex_texture_units': 16,
            'max_renderbuffer_size': 16384
        }
    ]

    # Выбираем конфигурацию на основе hardware_concurrency
    # Более мощные CPU обычно идут с лучшими GPU
    if self.fingerprint.get('hardwareConcurrency', 4) >= 8:
        config = random.choice([gpu_configs[1], gpu_configs[2]])  # Лучшие GPU
    else:
        config = gpu_configs[0]  # Intel UHD

    return config
```

2. **Добавить Canvas noise injection:**

Canvas fingerprint должен быть уникальным, но стабильным для одного "пользователя":

```python
def _inject_canvas_noise(self):
    """
    Добавляет небольшой шум в canvas для уникальности
    НО: шум должен быть детерминированным (на основе seed)
    """
    seed = hash(self.fingerprint.get('deviceId', 'default'))
    random.seed(seed)

    noise_factor = random.random() * 0.0001  # Очень маленький шум

    return f"""
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function() {{
            const context = this.getContext('2d');
            if (context) {{
                const imageData = context.getImageData(0, 0, this.width, this.height);
                // Добавляем минимальный шум
                for (let i = 0; i < imageData.data.length; i += 4) {{
                    imageData.data[i] += Math.floor(Math.random() * 2 - 1) * {noise_factor};
                }}
                context.putImageData(imageData, 0, 0);
            }}
            return originalToDataURL.apply(this, arguments);
        }};
    """
```

---

### 3. **Lies/Mismatch Detection**

**Проблема:**
CreepJS обнаруживает несоответствия (lies) между различными API.

**Причина:**
Некоторые значения не синхронизированы. Например:
- `navigator.platform` может не соответствовать `navigator.userAgent`
- Screen dimensions могут не соответствовать window dimensions
- Timezone может не соответствовать языку

**Исправление:**

В `fingerprint_generator.py` добавить проверку консистентности:

```python
def validate_consistency(self):
    """
    Проверяет и исправляет несоответствия в fingerprint
    """
    # 1. Platform должен соответствовать User-Agent
    ua = self.fingerprint.get('userAgent', '')
    if 'Windows' in ua:
        self.fingerprint['platform'] = 'Win32'
    elif 'Mac' in ua:
        self.fingerprint['platform'] = 'MacIntel'
    elif 'Linux' in ua:
        self.fingerprint['platform'] = 'Linux x86_64'

    # 2. Language должен соответствовать timezone
    tz = self.geo_config.get('timezone', 'America/New_York')
    if 'Europe' in tz:
        lang = random.choice(['en-GB', 'de-DE', 'fr-FR'])
    elif 'America/New_York' in tz:
        lang = 'en-US'
    else:
        lang = 'en-US'

    self.fingerprint['language'] = lang
    self.fingerprint['languages'] = [lang, 'en']

    # 3. Screen resolution должна соответствовать device memory
    memory = self.fingerprint.get('deviceMemory', 8)
    if memory <= 4:
        # Низкое разрешение для слабых устройств
        screen = random.choice([
            {'width': 1366, 'height': 768},
            {'width': 1280, 'height': 720}
        ])
    else:
        # Высокое разрешение для мощных устройств
        screen = random.choice([
            {'width': 1920, 'height': 1080},
            {'width': 2560, 'height': 1440}
        ])

    self.fingerprint['screen'] = screen

    # 4. HardwareConcurrency должен быть реалистичным
    cores = self.fingerprint.get('hardwareConcurrency', 8)
    # Реальные значения: 2, 4, 6, 8, 12, 16
    if cores not in [2, 4, 6, 8, 12, 16]:
        self.fingerprint['hardwareConcurrency'] = random.choice([4, 8])
```

---

### 4. **Blocked/Resistance Detection**

**Проблема:**
CreepJS показывает "blocked" в секции Resistance.

**Причина:**
Вероятно, CreepJS детектирует, что некоторые API были изменены или заблокированы.

**Исправление:**

Не блокировать API полностью, а переопределять их более аккуратно:

```python
def _get_undetectable_overrides(self):
    """
    Переопределения которые НЕ детектируются
    """
    return """
        // ❌ ПЛОХО - детектируется:
        // delete navigator.webdriver;

        // ✅ ХОРОШО - не детектируется:
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
            configurable: true
        });

        // Для всех переопределений используем descriptor manipulation
        const overrideWithDescriptor = (obj, prop, value) => {
            const descriptor = Object.getOwnPropertyDescriptor(obj, prop);
            if (descriptor) {
                Object.defineProperty(obj, prop, {
                    ...descriptor,
                    value: value,
                    configurable: true
                });
            }
        };

        // Применяем к navigator properties
        overrideWithDescriptor(navigator, 'hardwareConcurrency', %(hardwareConcurrency)s);
        overrideWithDescriptor(navigator, 'deviceMemory', %(deviceMemory)s);
    """
```

---

### 5. **Тайм-аут тестов CreepJS**

**Проблема:**
Тесты не завершаются полностью (не достигают 100%).

**Причина:**
- Медленное соединение через прокси
- Некоторые тесты блокируются или зависают
- Недостаточное время ожидания

**Исправление:**

В `creepjs_test.py` увеличить timeout и улучшить детекцию:

```python
async def wait_for_creepjs_completion(page, max_wait=180):  # ✅ Увеличено до 180 сек
    """
    Ждет завершения всех тестов CreepJS
    """
    print("\n[INFO] Ожидание завершения тестов CreepJS...")

    last_progress = None
    stale_count = 0

    for i in range(max_wait):
        try:
            # Проверяем несколько индикаторов завершения
            status = await page.evaluate("""
                () => {
                    // 1. Проверяем прогресс
                    const progressEl = document.querySelector('.ellipsis-all');
                    const progress = progressEl?.textContent?.trim() || '';

                    // 2. Проверяем наличие финального score/trust
                    const trustScore = document.querySelector('[class*="trust"]')?.textContent || '';

                    // 3. Проверяем количество завершенных тестов
                    const completedTests = document.querySelectorAll('.block-text[class*="complete"]').length;

                    return {
                        progress: progress,
                        trustScore: trustScore,
                        completedTests: completedTests,
                        isComplete: progress.includes('100%') || trustScore.includes('%')
                    };
                }
            """)

            if status['isComplete']:
                print(f"[+] Тесты завершены: {status['progress']}")
                return True

            # Детекция зависания
            if status['progress'] == last_progress:
                stale_count += 1
                if stale_count > 30:  # 30 секунд без изменений
                    print(f"[!] Прогресс застрял на {status['progress']}")
                    return False
            else:
                stale_count = 0
                last_progress = status['progress']

            if i % 5 == 0 and status['progress']:
                print(f"   Прогресс: {status['progress']} | Тестов: {status['completedTests']}")

        except Exception as e:
            pass

        await asyncio.sleep(1)

    print("[!] Тайм-аут ожидания завершения тестов")
    return False
```

---

## 📋 Приоритетный план действий

1. **Высокий приоритет:**
   - ✅ Исправить LocalStorage SecurityError (может полностью сломать stealth)
   - ✅ Добавить consistency validation (убрать lies detection)

2. **Средний приоритет:**
   - ⚠️ Улучшить Canvas/WebGL fingerprinting
   - ⚠️ Исправить "blocked" detection

3. **Низкий приоритет:**
   - 🔹 Увеличить timeout для тестов CreepJS (не критично для production)

---

## ✅ Что уже работает хорошо

- ✅ `navigator.webdriver = False` - успешно скрыт
- ✅ Window dimensions - реалистичные (не headless)
- ✅ Cookies injection - работает идеально
- ✅ Fingerprint injection через add_init_script
- ✅ Proxy geo detection

---

## 🔧 Следующие шаги

1. Применить исправления для LocalStorage
2. Запустить `detailed_creepjs_analysis.py` для проверки изменений
3. Добавить consistency validation
4. Протестировать на реальных сайтах (Steam, Outlook, Discord)
