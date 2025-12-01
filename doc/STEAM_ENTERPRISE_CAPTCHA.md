# Steam Enterprise reCAPTCHA Solver

Модуль для решения **reCAPTCHA v2 Enterprise** при регистрации аккаунтов Steam с поддержкой нескольких сервисов решения капчи.

## Почему был создан этот модуль?

Steam использует **reCAPTCHA v2 Enterprise** с lazy loading (ленивая загрузка), что означает:
- Капча не загружается автоматически при открытии страницы
- Iframe с капчей появляется только после взаимодействия пользователя с формой
- Требуется специальный параметр `s-token` (enterprise payload)
- Обычные методы решения капчи не работают без предварительной "активации"

**SteamEnterpriseCaptchaSolver** решает все эти проблемы автоматически.

---

## Возможности

✅ **Автоматическая "разбудка" капчи** — эмулирует взаимодействие пользователя для загрузки iframe
✅ **Извлечение s-token** — автоматически находит enterprise payload
✅ **Поддержка нескольких сервисов** — CapSolver, 2Captcha, AntiCaptcha
✅ **Подробное логирование** — отслеживание каждого шага процесса
✅ **Автоматическая инжекция токена** — вставка решения в форму
✅ **Обработка ошибок** — graceful degradation при любых проблемах

---

## Установка

### 1. Файл модуля уже создан

```
src/captcha/steam_enterprise_solver.py
```

### 2. Зависимости

```bash
pip install selenium requests
```

### 3. Настройка API ключей

Выберите один или несколько сервисов:

#### CapSolver (рекомендуется)
```bash
# Создайте файл capsolver_config.txt
echo "CAP-YOUR_API_KEY_HERE" > capsolver_config.txt

# Или установите переменную окружения
export CAPSOLVER_API_KEY="CAP-YOUR_API_KEY_HERE"
```

#### 2Captcha
```bash
# Создайте файл 2captcha_config.txt
echo "YOUR_API_KEY_HERE" > 2captcha_config.txt

# Или установите переменную окружения
export TWOCAPTCHA_API_KEY="YOUR_API_KEY_HERE"
```

#### AntiCaptcha
```bash
# Создайте файл anticaptcha_config.txt
echo "YOUR_API_KEY_HERE" > anticaptcha_config.txt

# Или установите переменную окружения
export ANTICAPTCHA_API_KEY="YOUR_API_KEY_HERE"
```

---

## Быстрый старт

### Простейший пример

```python
from selenium import webdriver
from src.captcha.steam_enterprise_solver import SteamEnterpriseCaptchaSolver

# Создаём WebDriver
driver = webdriver.Firefox()

# Создаём solver (по умолчанию CapSolver)
solver = SteamEnterpriseCaptchaSolver()

# Открываем страницу регистрации
driver.get("https://store.steampowered.com/join/")

# Решаем капчу (всё в одном методе!)
if solver.solve_and_inject(driver):
    print("Капча решена! Можно отправлять форму")
    # ... заполняем форму и отправляем
else:
    print("Не удалось решить капчу")

driver.quit()
```

### Выбор сервиса

```python
# CapSolver (рекомендуется, самый быстрый)
solver = SteamEnterpriseCaptchaSolver(service='capsolver')

# 2Captcha
solver = SteamEnterpriseCaptchaSolver(service='2captcha')

# AntiCaptcha
solver = SteamEnterpriseCaptchaSolver(service='anticaptcha')
```

### Пошаговое управление

Если нужен контроль над каждым этапом:

```python
solver = SteamEnterpriseCaptchaSolver(service='capsolver')

# Шаг 1: Разбудить капчу
if not solver.wake_up_captcha(driver):
    print("Не удалось разбудить капчу")
    exit(1)

# Шаг 2: Извлечь данные капчи
captcha_data = solver.extract_captcha_data(driver)
if not captcha_data:
    print("Не удалось извлечь данные капчи")
    exit(1)

# Шаг 3: Решить капчу
token = solver.solve_captcha(captcha_data)
if not token:
    print("Не удалось решить капчу")
    exit(1)

# Шаг 4: Инжектировать токен
if solver.inject_captcha_token(driver, token):
    print("Токен успешно инжектирован")
```

### Передача API ключа явно

```python
solver = SteamEnterpriseCaptchaSolver(
    service='capsolver',
    api_key='CAP-YOUR_KEY_HERE'
)
```

### Отключение логирования

```python
solver = SteamEnterpriseCaptchaSolver(debug=False)
```

---

## Тестирование

Используйте готовый тестовый скрипт:

```bash
# Базовый тест (Firefox + CapSolver)
python test_steam_enterprise_solver.py

# Тест с 2Captcha
python test_steam_enterprise_solver.py --service 2captcha

# Тест с Chrome
python test_steam_enterprise_solver.py --browser chrome

# Headless режим
python test_steam_enterprise_solver.py --headless

# Все параметры вместе
python test_steam_enterprise_solver.py --service 2captcha --browser chrome --headless
```

---

## Интеграция в существующие скрипты

### Для steam_registration.py

Замените существующий метод `solve_captcha()` на:

```python
from src.captcha.steam_enterprise_solver import SteamEnterpriseCaptchaSolver

def solve_captcha(self):
    """Решаем капчу через SteamEnterpriseCaptchaSolver"""
    solver = SteamEnterpriseCaptchaSolver(
        service='capsolver',  # или '2captcha'
        debug=True
    )

    return solver.solve_and_inject(self.driver)
```

### Для steam_registration_batch.py

Аналогично — просто замените метод решения капчи:

```python
from src.captcha.steam_enterprise_solver import SteamEnterpriseCaptchaSolver

class SteamRegistrationBatch:
    def __init__(self):
        self.captcha_solver = SteamEnterpriseCaptchaSolver(service='capsolver')

    def register_account(self, email, username, password):
        # ... открытие страницы регистрации

        # Решаем капчу
        if not self.captcha_solver.solve_and_inject(self.driver):
            raise Exception("Не удалось решить капчу")

        # ... заполнение формы и отправка
```

---

## Сравнение сервисов

| Сервис | Скорость | Стоимость | Надёжность | Рекомендация |
|--------|----------|-----------|------------|--------------|
| **CapSolver** | ⚡⚡⚡ 10-15 сек | 💰 $2.5-4/1000 | ⭐⭐⭐⭐⭐ | ✅ Лучший выбор |
| **2Captcha** | ⚡⚡ 10-20 сек | 💰 $2-3/1000 | ⭐⭐⭐⭐ | ✅ Хорошая альтернатива |
| **AntiCaptcha** | ⚡ 15-25 сек | 💰 $2-3/1000 | ⭐⭐⭐⭐ | ⚠️ Чуть медленнее |

---

## Как это работает под капотом

### 1. Wake Up Captcha (Разбуживание)

```python
# Прокручиваем к полю email
driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", email_field)

# Кликаем через JavaScript (избегаем детекции Selenium)
driver.execute_script("arguments[0].click();", email_field)

# Вводим и удаляем символ (триггер для lazy loading)
email_field.send_keys("a")
driver.execute_script("arguments[0].value = arguments[0].value.slice(0,-1);", email_field)

# Ждём 3 секунды для инициализации капчи
time.sleep(3)
```

**Почему это работает:**
Steam не загружает iframe с капчей до тех пор, пока пользователь не начнёт взаимодействовать с формой. Мы эмулируем это взаимодействие.

### 2. Extract Captcha Data (Извлечение данных)

```python
# Ищем iframe с recaptcha
iframes = driver.find_elements(By.TAG_NAME, "iframe")
for iframe in iframes:
    if "recaptcha" in iframe.get_attribute("src"):
        # Нашли!
        break

# Извлекаем s-token (enterprise payload)
s_token = driver.execute_script(
    "return document.querySelector('div.g-recaptcha')?.dataset.s || null;"
)
```

**s-token** — это уникальный параметр для Enterprise версии, который нужно передать в сервис решения.

### 3. Solve Captcha (Решение)

```python
# CapSolver API
payload = {
    "clientKey": api_key,
    "task": {
        "type": "ReCaptchaV2EnterpriseTaskProxyless",  # Важно: Enterprise!
        "websiteURL": page_url,
        "websiteKey": sitekey,
        "enterprisePayload": {
            "s": s_token  # Важно: передаём s-token!
        }
    }
}
```

Без `enterprisePayload` капча не решится!

### 4. Inject Token (Инжекция)

```python
# Находим или создаём поле g-recaptcha-response
script = f"""
var responseField = document.getElementById('g-recaptcha-response');
if (!responseField) {{
    responseField = document.createElement('textarea');
    responseField.id = 'g-recaptcha-response';
    responseField.name = 'g-recaptcha-response';
    document.querySelector('form').appendChild(responseField);
}}
responseField.value = '{token}';
"""
driver.execute_script(script)
```

---

## Troubleshooting (Устранение проблем)

### Капча не появляется

**Проблема:** `Iframe с капчей не найден`

**Решение:**
1. Увеличьте время ожидания в `extract_captcha_data(driver, max_wait=30)`
2. Проверьте, что страница полностью загружена
3. Проверьте работу метода `wake_up_captcha()`

### s-token не извлекается

**Проблема:** `s-token: NO_S` в логах

**Решение:**
1. Проверьте, что iframe появился в DOM
2. Инспектируйте страницу вручную и проверьте наличие `div.g-recaptcha`
3. Проверьте URL iframe — там должен быть параметр `s=...`

### Сервис возвращает ошибку

**Проблема:** `ERROR_INVALID_SITEKEY` или `ERROR_ZERO_BALANCE`

**Решение:**
1. Проверьте баланс аккаунта в сервисе
2. Убедитесь, что API ключ правильный
3. Проверьте, что используется правильный тип задачи (ReCaptchaV2Enterprise)

### Токен не принимается формой

**Проблема:** После инжекции токена форма всё равно не отправляется

**Решение:**
1. Проверьте наличие поля `g-recaptcha-response` в DOM
2. Убедитесь, что токен не пустой
3. Попробуйте добавить задержку перед отправкой формы

---

## API Reference

### Класс SteamEnterpriseCaptchaSolver

#### `__init__(service, api_key, debug)`

Создаёт экземпляр solver'а.

**Параметры:**
- `service` (str): Имя сервиса ('capsolver', '2captcha', 'anticaptcha')
- `api_key` (str, optional): API ключ (если None, берётся из окружения)
- `debug` (bool): Включить подробное логирование (по умолчанию True)

#### `wake_up_captcha(driver, wait_time=40)`

Активирует lazy-loaded капчу через эмуляцию взаимодействия.

**Возвращает:** `bool` — True если успешно

#### `extract_captcha_data(driver, max_wait=25)`

Извлекает данные капчи (sitekey, s-token, page_url).

**Возвращает:** `dict` или `None`

#### `solve_captcha(captcha_data, timeout=300)`

Решает капчу через выбранный сервис.

**Возвращает:** `str` (токен) или `None`

#### `inject_captcha_token(driver, token)`

Инжектирует токен в форму.

**Возвращает:** `bool` — True если успешно

#### `solve_and_inject(driver)`

Полный цикл: wake up → extract → solve → inject.

**Возвращает:** `bool` — True если весь процесс успешен

---

## Лицензия и использование

⚠️ **ВАЖНО:** Это исследовательский проект для изучения технологий обхода детекции.
**НЕ используйте** для нарушения условий использования сервисов или массовой регистрации.

---

## Вопросы и поддержка

При возникновении проблем:

1. Проверьте логи (используйте `debug=True`)
2. Запустите тестовый скрипт `test_steam_enterprise_solver.py`
3. Проверьте скриншоты ошибок (`steam_enterprise_test_fail.png`)
4. Проверьте баланс и API ключ вашего сервиса

---

**Последнее обновление:** 01.12.2025
**Версия модуля:** 1.0
**Протестировано с:** Steam Registration (декабрь 2025)
