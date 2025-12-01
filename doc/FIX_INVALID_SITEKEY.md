# Исправление ошибки ERROR_INVALID_SITEKEY

## Проблема

Вы получили ошибку:
```
❌ Ошибка: ERROR_INVALID_SITEKEY
   Описание: Неверный или устаревший sitekey (проверьте актуальность)
```

## Причина

hCaptcha sitekey для Steam может меняться со временем. Устаревший sitekey приводит к ошибке `ERROR_INVALID_SITEKEY`.

## Быстрое решение

### Вариант 1: Автоматическое извлечение (рекомендуется)

Тестовый скрипт `test_azcaptcha.py` теперь **автоматически** извлекает актуальный sitekey:

```bash
python test_azcaptcha.py
```

Скрипт:
1. Запустит браузер
2. Откроет страницу Steam
3. Извлечёт актуальный sitekey
4. Проверит работу AZcaptcha

### Вариант 2: Ручное извлечение

Если нужен только sitekey без теста:

```bash
# В headless режиме
python get_steam_sitekey.py

# С GUI (чтобы видеть процесс)
python get_steam_sitekey.py --no-headless
```

Вы увидите:
```
======================================================================
✓ Sitekey успешно извлечён!
======================================================================

Sitekey:  a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6
Page URL: https://store.steampowered.com/join/
Host:     hcaptcha.com
Endpoint: https://hcaptcha.com

======================================================================
Используйте этот sitekey для тестирования AZcaptcha!
======================================================================
```

### Вариант 3: Ручное извлечение через браузер

1. Откройте https://store.steampowered.com/join/ в браузере
2. Откройте DevTools (F12)
3. Перейдите на вкладку **Elements** (или **Inspector**)
4. Найдите iframe с `hcaptcha.com`:
   ```html
   <iframe src="https://hcaptcha.com/captcha/v1/...?sitekey=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX&...">
   ```
5. Скопируйте значение параметра `sitekey` из URL

## Использование в коде

После получения актуального sitekey, используйте его:

```python
from src.captcha.azcaptcha_solver import AZcaptchaSolver, load_azcaptcha_config

# Инициализация
api_key = load_azcaptcha_config()
solver = AZcaptchaSolver(api_key=api_key, debug=True)

# ВАЖНО: Используйте актуальный sitekey!
sitekey = "your-actual-sitekey-here"  # Извлечённый sitekey

# Решение капчи
token = solver.solve_hcaptcha(
    website_url="https://store.steampowered.com/join/",
    website_key=sitekey,  # Актуальный sitekey
    max_attempts=60,
    poll_interval=5
)
```

## Динамическое извлечение в production

Для production кода рекомендуется извлекать sitekey динамически:

```python
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_current_sitekey(driver):
    """Извлечь актуальный sitekey со страницы"""
    try:
        # Ждём появления iframe
        wait = WebDriverWait(driver, 30)
        iframe = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='hcaptcha.com']"))
        )

        # Извлекаем sitekey
        iframe_src = iframe.get_attribute("src")
        match = re.search(r'sitekey=([a-f0-9-]+)', iframe_src)

        if match:
            return match.group(1)
    except Exception as e:
        print(f"Ошибка извлечения sitekey: {e}")

    return None

# В вашем коде регистрации:
driver.get("https://store.steampowered.com/join/")
current_sitekey = get_current_sitekey(driver)

if current_sitekey:
    token = solver.solve_hcaptcha(
        website_url=driver.current_url,
        website_key=current_sitekey,  # Всегда актуальный!
        max_attempts=60,
        poll_interval=5
    )
```

## Проверка после исправления

После получения актуального sitekey запустите тест:

```bash
python test_azcaptcha.py
```

Ожидаемый результат:
```
✓ Задача создана. ID: XXXXXXXXXX
⏳ Ожидание решения задачи...
   Попытка 1/30: обработка...
   Попытка 2/30: обработка...
✓ Капча решена успешно через AZcaptcha!

✓ ТЕСТ УСПЕШЕН!
   Токен получен: P0_eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Дополнительная помощь

Если проблема сохраняется:

1. **Проверьте баланс**: `solver.get_balance()`
2. **Проверьте API ключ**: убедитесь что ключ правильный
3. **Проверьте URL**: должен быть точный URL страницы
4. **Попробуйте с прокси**: укажите параметр `proxy`
5. **Обратитесь в поддержку AZcaptcha**: https://azcaptcha.com/support

## Полезные ссылки

- 📖 Полная документация: [AZCAPTCHA_SETUP.md](AZCAPTCHA_SETUP.md)
- 🌐 Официальный сайт: https://azcaptcha.com
- 📚 API документация: https://azcaptcha.com/document
- 💬 Поддержка: https://azcaptcha.com/support

---

**Последнее обновление**: Декабрь 2025
