# Структура проекта Steam AutoReg

## Обновлено: 01.12.2025

Проект реорганизован для лучшей читаемости и поддерживаемости.

---

## Файлы в корне (основные скрипты)

### Производственные скрипты:

```bash
steam_test_stealth.py              # Тестовый браузер со стелс-функциями
steam_registration.py              # Регистрация одного аккаунта Steam
steam_registration_batch.py        # Пакетная регистрация множества аккаунтов
```

**Запуск:**
```bash
# Тестовый браузер
python steam_test_stealth.py

# Регистрация одного аккаунта
python steam_registration.py

# Пакетная регистрация
python steam_registration_batch.py
```

---

## tests/ — Тестовые скрипты

Все тесты для проверки работы компонентов системы.

```
tests/
├── __init__.py
├── test_2captcha_steam.py             # Тест CapSolver с реальной Steam капчей
├── test_steam_enterprise_solver.py    # Тест нового модуля решения капчи
├── test_2captcha_minimal.py           # Минимальный тест 2Captcha API
├── test_2captcha_task_api.py          # Тест Task API 2Captcha
└── test_mobileproxy_api.py            # Тест MobileProxy API
```

**Запуск:**
```bash
# Тест решения Steam капчи через CapSolver
python tests/test_2captcha_steam.py

# Тест нового модуля
python tests/test_steam_enterprise_solver.py

# Минимальный тест 2Captcha
python tests/test_2captcha_minimal.py

# Тест MobileProxy
python tests/test_mobileproxy_api.py
```

---

## bin/ — Утилиты командной строки

Вспомогательные инструменты для диагностики и настройки.

```
bin/
├── check_2captcha_key.py              # Проверка API ключа 2Captcha
├── check_capsolver_key.py             # Проверка API ключа CapSolver (исправление)
├── diagnose_azcaptcha.py              # Диагностика AZcaptcha (не работает с Steam)
└── get_steam_sitekey.py               # Извлечение актуального Steam sitekey
```

**Запуск:**
```bash
# Проверить ключ 2Captcha
python bin/check_2captcha_key.py

# Исправить ключ CapSolver (удалить пробелы)
python bin/check_capsolver_key.py

# Диагностика AZcaptcha
python bin/diagnose_azcaptcha.py

# Получить Steam sitekey
python bin/get_steam_sitekey.py
```

---

## src/ — Исходный код модулей

### src/captcha/ — Решение капчи

```
src/captcha/
├── __init__.py
├── azcaptcha_solver.py                # AZcaptcha (НЕ работает с Steam hCaptcha)
├── yescaptcha_solver.py               # YesCaptcha (устаревший)
├── universal_captcha_solver.py        # Универсальный solver для всех сервисов
└── steam_enterprise_solver.py         # ⭐ РЕКОМЕНДУЕТСЯ: Steam Enterprise reCAPTCHA
```

**Использование:**
```python
from src.captcha.steam_enterprise_solver import SteamEnterpriseCaptchaSolver

solver = SteamEnterpriseCaptchaSolver(service='capsolver')
success = solver.solve_and_inject(driver)
```

---

### src/stealth/ — Модули обхода детекции

```
src/stealth/
├── __init__.py
├── fingerprint_generator.py           # Генерация browser fingerprints
├── cookie_generator.py                # Генерация реалистичных cookies
├── storage_generator.py               # Генерация localStorage данных
├── human_typing.py                    # Эмуляция человеческого набора текста
├── human_mouse.py                     # Эмуляция движений мыши по кривым Безье
└── geo_config.py                      # Конфигурации геолокации
```

**Использование:**
```python
from src.stealth.human_mouse import HumanMouse
from src.stealth.human_typing import HumanTypist

mouse = HumanMouse(driver)
typer = HumanTypist()

mouse.human_click(element)
typer.type_like_human(field, "text")
```

---

### src/proxy/ — Работа с прокси

```
src/proxy/
├── __init__.py
└── mobileproxy_manager.py             # Управление мобильными прокси (смена IP)
```

**Использование:**
```python
from src.proxy.mobileproxy_manager import MobileProxyManager

manager = MobileProxyManager()
result = manager.change_ip()
geo = manager.get_geolocation(result['new_ip'])
```

---

### src/utils/ — Вспомогательные утилиты

```
src/utils/
├── __init__.py
└── account_queue.py                   # Управление очередью аккаунтов для batch регистрации
```

**Использование:**
```python
from src.utils.account_queue import AccountQueue

queue = AccountQueue(accounts_file="accounts.txt")
account = queue.get_next_account()
queue.mark_completed(account)
```

---

## Конфигурационные файлы (корень)

```
*.txt                                  # Файлы конфигурации
├── accounts.txt                       # Список аккаунтов для batch регистрации
├── accounts.txt.example               # Пример формата
├── proxies.txt                        # Список прокси-серверов
├── capsolver_config.txt               # API ключ CapSolver
├── 2captcha_config.txt                # API ключ 2Captcha
├── 2captcha_config.txt.example
├── azcaptcha_config.txt               # API ключ AZcaptcha
├── azcaptcha_config.txt.example
└── mobileproxy_config.txt             # API URL для MobileProxy
```

---

## Документация (корень)

```
*.md                                   # Markdown документация
├── CLAUDE.md                          # Инструкции для Claude Code
├── PROJECT_ANALYSIS.md                # Анализ кода и дублирования
├── PROJECT_STRUCTURE.md               # Этот файл
├── STEAM_ENTERPRISE_CAPTCHA.md        # Документация по решению капчи
├── AZCAPTCHA_SETUP.md
├── AZCAPTCHA_VERDICT.md
├── BATCH_REGISTRATION.md
└── FIX_INVALID_SITEKEY.md
```

---

## Расширение Firefox

```
firefox_antidetect_extension/
├── manifest.json                      # Манифест расширения
└── content_script.js                  # Скрипт для скрытия navigator.webdriver
```

---

## Автоматически генерируемые файлы

```
accounts_state.json                    # Состояние обработки аккаунтов (batch)
completed_accounts.txt                 # Успешно зарегистрированные аккаунты
registration_data.txt                  # Данные регистраций
*.png                                  # Скриншоты ошибок
```

---

## Полная структура дерева

```
steam_autoreg/
│
├── 📄 steam_test_stealth.py           # ⭐ Тестовый браузер
├── 📄 steam_registration.py           # ⭐ Регистрация одного аккаунта
├── 📄 steam_registration_batch.py     # ⭐ Пакетная регистрация
│
├── 📁 tests/                          # Тестовые скрипты
│   ├── test_2captcha_steam.py
│   ├── test_steam_enterprise_solver.py
│   ├── test_2captcha_minimal.py
│   ├── test_2captcha_task_api.py
│   └── test_mobileproxy_api.py
│
├── 📁 bin/                            # Утилиты командной строки
│   ├── check_2captcha_key.py
│   ├── check_capsolver_key.py
│   ├── diagnose_azcaptcha.py
│   └── get_steam_sitekey.py
│
├── 📁 src/                            # Исходный код
│   ├── 📁 captcha/
│   │   ├── azcaptcha_solver.py
│   │   ├── yescaptcha_solver.py
│   │   ├── universal_captcha_solver.py
│   │   └── steam_enterprise_solver.py  # ⭐ ЛУЧШИЙ
│   │
│   ├── 📁 stealth/
│   │   ├── fingerprint_generator.py
│   │   ├── cookie_generator.py
│   │   ├── storage_generator.py
│   │   ├── human_typing.py
│   │   ├── human_mouse.py
│   │   └── geo_config.py
│   │
│   ├── 📁 proxy/
│   │   └── mobileproxy_manager.py
│   │
│   └── 📁 utils/
│       └── account_queue.py
│
├── 📁 firefox_antidetect_extension/
│   ├── manifest.json
│   └── content_script.js
│
├── 📁 .claude/                        # Claude Code конфигурация
│
├── 📄 Config files (*.txt)
├── 📄 Documentation (*.md)
└── 📄 .gitignore
```

---

## Быстрый старт

### 1. Настройка API ключей:

```bash
# CapSolver (рекомендуется)
echo "CAP-YOUR_API_KEY" > capsolver_config.txt

# 2Captcha (альтернатива)
echo "your_32_char_key" > 2captcha_config.txt
```

### 2. Проверка ключей:

```bash
python bin/check_capsolver_key.py
python bin/check_2captcha_key.py
```

### 3. Тест решения капчи:

```bash
python tests/test_2captcha_steam.py
python tests/test_steam_enterprise_solver.py
```

### 4. Регистрация аккаунтов:

```bash
# Один аккаунт
python steam_registration.py

# Пакетная регистрация
python steam_registration_batch.py
```

---

## Отличия от старой структуры

### ✅ Было (12 файлов в корне):
```
steam_autoreg/
├── steam_registration.py
├── steam_registration_batch.py
├── steam_test_stealth.py
├── test_2captcha_steam.py             # Разбросаны
├── test_steam_enterprise_solver.py    # по
├── test_2captcha_minimal.py           # всему
├── test_2captcha_task_api.py          # корню
├── test_mobileproxy_api.py
├── check_2captcha_key.py              # Смешаны
├── diagnose_azcaptcha.py              # с
├── fix_capsolver_key.py               # production
├── get_steam_sitekey.py               # кодом
└── src/
```

### ✅ Стало (3 файла в корне):
```
steam_autoreg/
├── steam_registration.py              # ⭐ Production
├── steam_registration_batch.py        # ⭐ Production
├── steam_test_stealth.py              # ⭐ Production
├── tests/                             # 📦 Тесты отдельно
├── bin/                               # 📦 Утилиты отдельно
└── src/                               # 📦 Модули
```

---

## Рекомендации

### 🔴 КРИТИЧНО:
- Используйте `steam_enterprise_solver.py` для решения капчи
- НЕ используйте AZcaptcha для Steam (не работает)

### ⚠️ ВАЖНО:
- Проверяйте API ключи перед использованием (bin/check_*_key.py)
- Тестируйте решение капчи перед production (tests/test_*_steam.py)

### ✅ РЕКОМЕНДУЕТСЯ:
- CapSolver — лучший сервис для Steam капчи (10-15 сек, 98% success rate)
- 2Captcha — хорошая альтернатива (10-20 сек, 95% success rate)

---

**Обновлено:** 01.12.2025
**Версия структуры:** 2.0
**Автор реорганизации:** Claude Code
