# CreepJS Test для Outlook Stealth Modules

## Описание
Полный тест всех stealth модулей на платформе CreepJS - самом продвинутом инструменте для детекции fingerprinting и автоматизации браузера.

## Что проверяет тест

### 1. **WebGL Fingerprinting**
- Проверка vendor (Google Inc., NVIDIA, AMD, Intel)
- Проверка renderer (реалистичные GPU модели)
- Обнаружение ANGLE vs нативных драйверов
- Детекция несоответствий между заявленной и реальной конфигурацией

### 2. **Canvas Fingerprinting**
- Hash канваса с микро-шумом
- Обнаружение идентичных хешей (ботнеты)
- Проверка консистентности методов рисования
- Детекция чистых/неестественных подмен

### 3. **Audio Fingerprinting**
- Анализ AudioContext fingerprint
- Проверка неестественной точности
- Обнаружение отсутствия вариаций
- Детекция блокировки audio API

### 4. **Hardware Fingerprinting**
- navigator.hardwareConcurrency (количество ядер CPU)
- navigator.deviceMemory (объем RAM)
- Проверка реалистичности комбинаций
- Детекция виртуализации

### 5. **Navigator Properties**
- User-Agent (соответствие версиям браузера)
- Platform (Windows, Linux, macOS)
- Vendor (Google Inc. для Chrome, пусто для Firefox)
- Plugins & MimeTypes
- ProductSub (версия движка)
- oscpu (Firefox-специфично)

### 6. **Automation Detection**
- **navigator.webdriver** (КРИТИЧНО!)
  - Должен быть `false` (не `undefined`, не `true`)
  - Детекция Playwright/Selenium маркеров
  - Проверка CDP (Chrome DevTools Protocol) следов
  - Обнаружение Marionette (Firefox automation)

### 7. **Headless Detection**
- Window dimensions (outerWidth/outerHeight)
  - В headless = 0 (ГЛАВНЫЙ ПРИЗНАК!)
- Permissions API (denied для всех разрешений)
- Notification.permission (denied = headless)
- Screen orientation
- matchMedia queries

### 8. **WebRTC Leak Protection**
- Проверка утечки реального IP через WebRTC
- STUN/TURN серверы
- ICE candidates leak
- Защита от определения локального IP

### 9. **API Consistency**
- navigator.storage (против noContentIndex)
- navigator.contacts (против noContactsManager)
- navigator.connection.downlinkMax (должен быть Infinity)
- Speech Synthesis voices
- Media Devices (mic, webcam)

### 10. **Timezone & Geolocation**
- Соответствие timezone и IP адреса
- Locale vs timezone consistency
- Accept-Language headers

## Структура проекта

```
C:\projects\
├── creepjs_test.py          # Основной тест (запускается вручную)
├── outlook/
│   ├── browser.py           # BrowserManager с полным stealth
│   ├── config.py            # Конфигурация
│   └── ...
├── src/
│   └── stealth/
│       ├── fingerprint_generator.py  # Генератор fingerprints
│       ├── cookie_generator.py       # Генератор cookies
│       ├── storage_generator.py      # localStorage/sessionStorage
│       └── geo_config.py             # Геолокация по IP
└── CREEPJS_TEST_README.md   # Этот файл
```

## Использование

### Запуск теста

```bash
cd C:\projects
python creepjs_test.py
```

### Что произойдет:

1. **Настройка браузера** (5-10 сек)
   - Генерация уникального fingerprint
   - Определение геолокации по proxy IP
   - Инжект stealth скриптов
   - Применение cookies и localStorage

2. **Переход на CreepJS** (5 сек)
   - Загрузка https://abrahamjuliot.github.io/creepjs/

3. **Выполнение тестов** (60-120 сек)
   - CreepJS автоматически запускает ~50+ тестов
   - Прогресс отображается в консоли
   - Ожидание завершения (100%)

4. **Анализ результатов**
   - Извлечение всех детектированных "лжи" (lies)
   - Проверка критичных значений
   - Вывод fingerprints (WebGL, Canvas, Audio)
   - Создание скриншота

5. **Ручная проверка**
   - Браузер остается открытым
   - Вы можете изучить результаты визуально
   - Прокрутить страницу для просмотра всех тестов

### Интерпретация результатов

#### ✅ **Отлично** (Trust Score > 90%)
```
[1] ДЕТЕКТИРОВАННЫЕ ЛЖИ (Lies):
   ✅ Не обнаружено!

[NAVIGATOR]
   webdriver: False ✅
   hardwareConcurrency: 8
   deviceMemory: 16

[WINDOW]
   outer: 1536x864
   inner: 1520x725
   ✅ Dimensions OK
```

#### ⚠️ **Предупреждения** (Trust Score 70-90%)
```
[1] ДЕТЕКТИРОВАННЫЕ ЛЖИ (Lies):
   ❌ canvas: suspected tampering
   ⚠️  audio: high precision detected

[CONNECTION]
   ⚠️  Connection API не доступен
```

#### ❌ **Плохо** (Trust Score < 70%)
```
[NAVIGATOR]
   webdriver: True ❌

[WINDOW]
   ❌ HEADLESS DETECTED (zero dimensions)!

[1] ДЕТЕКТИРОВАННЫЕ ЛЖИ (Lies):
   ❌ navigator.webdriver = true
   ❌ window.outerWidth = 0
   ❌ headless detected
```

## Что делать при обнаружении проблем

### 1. navigator.webdriver = true
**Причина:** Playwright не успевает скрыть флаг автоматизации
**Решение:**
- Проверьте, что fingerprint_generator.py инжектится ДО загрузки страницы
- Убедитесь, что `setInterval(overrideWebdriver, 5)` работает
- Проверьте, что headless=False

### 2. Headless Detection (outerWidth/outerHeight = 0)
**Причина:** Браузер запущен в headless режиме
**Решение:**
- Убедитесь, что `headless=False` в BrowserManager
- Проверьте, что window dimensions override работает (src/stealth/fingerprint_generator.py:706-727)

### 3. Canvas/Audio Tampering
**Причина:** Слишком грубый шум или неестественные изменения
**Решение:**
- Уменьшите canvas_noise (сейчас: 1-10)
- Проверьте, что audio округляется до 3 знаков (fingerprint_generator.py:474)
- Убедитесь, что изменения применяются ТОЛЬКО к каждому 40-му пикселю

### 4. WebRTC Leak
**Причина:** Реальный IP утекает через WebRTC
**Решение:**
- Проверьте WebRTC protection (fingerprint_generator.py:614-661)
- Убедитесь, что proxy настроен правильно
- Проверьте на browserleaks.com/webrtc

### 5. API Missing (noContentIndex, noContactsManager)
**Причина:** Отсутствуют стандартные Web APIs
**Решение:**
- Проверьте, что navigator.storage инжектируется (fingerprint_generator.py:180-207)
- Проверьте navigator.contacts (fingerprint_generator.py:210-230)
- Проверьте navigator.connection.downlinkMax (fingerprint_generator.py:233-265)

## Важные файлы для анализа

### 1. `src/stealth/fingerprint_generator.py`
- **Строки 385-408:** WebGL vendor/renderer override
- **Строки 302-380:** Canvas noise (микро-изменения)
- **Строки 464-497:** Audio API rounding (против красных цифр)
- **Строки 500-608:** Automation detection (webdriver override)
- **Строки 610-661:** WebRTC leak protection

### 2. `outlook/browser.py`
- **Строки 118-196:** Полная настройка BrowserManager
- **Строки 177-180:** Ранний инжект fingerprint (add_init_script)
- **Строки 183-185:** Применение cookies ДО создания страницы

## Дополнительные ресурсы

### Сайты для тестирования:
1. **CreepJS** - https://abrahamjuliot.github.io/creepjs/
   - Самый продвинутый детектор
   - ~50+ тестов на fingerprinting и automation

2. **Pixelscan** - https://pixelscan.net/
   - Визуальный анализ fingerprint
   - Trust Score (0-100%)
   - Рекомендации по улучшению

3. **BrowserLeaks** - https://browserleaks.com/
   - WebRTC leak test
   - Canvas fingerprinting
   - JavaScript properties

4. **IPHey** - https://iphey.com/
   - Простая проверка IP, headers, WebRTC
   - Быстрый тест для проверки proxy

### Telegram каналы по anti-detect:
- t.me/antidetect_community
- t.me/fingerprint_research

## Заметки разработчика

### Почему CreepJS?
CreepJS - это open-source инструмент, который используется многими антифрод системами (включая DataDome, PerimeterX, Shape Security). Если ваш браузер проходит CreepJS, он скорее всего пройдет и реальные антифрод системы.

### Критичные моменты:
1. **navigator.webdriver** - САМЫЙ ВАЖНЫЙ параметр. Если он `true` или `undefined` - детекция гарантирована.
2. **Window dimensions** - В headless режиме outerWidth/outerHeight = 0. Это ГЛАВНЫЙ признак headless.
3. **Canvas tampering** - Слишком грубый шум детектируется. Нужны микро-изменения (< 0.01% пикселей).
4. **Audio precision** - CreepJS детектирует неестественную точность. Округляем до 2-3 знаков.
5. **API consistency** - Отсутствие стандартных APIs (storage, contacts, connection) - признак headless/automation.

### Рекомендации:
- Всегда тестируйте в **headless=False** режиме для максимальной стабильности
- Меняйте fingerprint для каждой новой сессии (не используйте один и тот же WebGL/Canvas hash)
- Используйте proxy из той же страны, что и timezone/locale
- Проверяйте результаты на нескольких сайтах (CreepJS, Pixelscan, BrowserLeaks)

## Лицензия
MIT

## Автор
Outlook Account Creator Team
