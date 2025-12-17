# Анализ детекции Microsoft при создании аккаунта

## 🔴 Проблема
```
We can't create your account
We're having trouble creating your Microsoft account due to some unusual activity we've detected.
```

## 🔍 Возможные причины детекции

### 1. **IP/Proxy Reputation** (наиболее вероятно)
Microsoft имеет базы данных известных прокси/VPN/datacenter IP.

**Проверить:**
- Тип прокси (residential vs datacenter)
- IP reputation score
- Blacklist статус IP

**Решение:**
```python
# Проверить IP
import requests

# 1. Проверка через ipapi
response = requests.get("http://ip-api.com/json/",
    proxies={'http': 'http://user:pass@proxy:port'})
print(response.json())

# 2. Проверка IP reputation
response = requests.get(f"https://www.abuseipdb.com/check/{ip}")
```

### 2. **TLS Fingerprint**
Playwright имеет уникальный TLS fingerprint, отличный от обычного Chrome.

**Детекция:**
- ClientHello message отличается
- Cipher suites порядок
- Extensions порядок

**Решение:**
- Использовать curl-impersonate или tls-client
- Или прокси который нормализует TLS

### 3. **Behavioral Patterns**
Microsoft анализирует:
- Скорость заполнения форм (слишком быстро = бот)
- Движения мыши (отсутствие = бот)
- Время между кликами
- Скроллинг паттерны

**Решение:**
```python
import random
import asyncio

async def human_type(page, selector, text):
    """Имитация человеческого ввода"""
    await page.click(selector)
    for char in text:
        await page.keyboard.type(char)
        # Случайная задержка между символами
        await asyncio.sleep(random.uniform(0.05, 0.15))

async def human_click(page, selector):
    """Имитация человеческого клика с движением мыши"""
    element = await page.query_selector(selector)
    box = await element.bounding_box()

    # Движение к элементу
    x = box['x'] + box['width'] / 2 + random.uniform(-5, 5)
    y = box['y'] + box['height'] / 2 + random.uniform(-5, 5)

    await page.mouse.move(x, y, steps=random.randint(10, 30))
    await asyncio.sleep(random.uniform(0.1, 0.3))
    await page.mouse.click(x, y)
```

### 4. **Font Fingerprinting**
Microsoft может проверять установленные шрифты. Playwright имеет ограниченный набор шрифтов.

**Проверить:**
```javascript
// В консоли браузера
const fonts = ['Arial', 'Times New Roman', 'Courier New', 'Verdana', 'Georgia', 'Comic Sans MS', 'Trebuchet MS', 'Arial Black', 'Impact', 'Calibri'];
const available = fonts.filter(font => document.fonts.check(`12px "${font}"`));
console.log(available);
```

**Решение:**
- Установить дополнительные шрифты в Docker контейнер
- Или подменить font detection API

### 5. **WebRTC IP Leak**
Даже через прокси, WebRTC может раскрыть реальный IP.

**Проверить:**
https://browserleaks.com/webrtc

**Решение:**
Уже есть в fingerprint_generator.py, но проверим:
```python
# Убедиться что WebRTC полностью заблокирован
await page.evaluate("""
    delete RTCPeerConnection;
    delete RTCSessionDescription;
    delete RTCIceCandidate;
    delete webkitRTCPeerConnection;
""")
```

### 6. **HTTP Headers Fingerprint**
Playwright может отправлять нестандартные заголовки.

**Проверить:**
```python
# Логировать все запросы
page.on('request', lambda request: print(request.headers))
```

**Проблемные заголовки:**
- `sec-ch-ua-*` (неправильные значения)
- `user-agent` (не соответствует другим параметрам)
- `accept-language` (не соответствует timezone)

### 7. **Rate Limiting**
Слишком много попыток создания аккаунта с одного IP.

**Решение:**
- Использовать разные прокси
- Задержки между попытками (минимум 30-60 минут)
- Rotation прокси пула

### 8. **Canvas/WebGL Fingerprint Database**
Microsoft может иметь базу известных automation fingerprints.

**Проверить:**
```python
# Запустить несколько раз и проверить что fingerprint меняется
for i in range(5):
    fp = FingerprintGenerator.generate('chrome')
    print(f"Canvas noise: {fp['canvas_noise']}")
    print(f"WebGL: {fp['webgl']['renderer']}")
```

**Решение:**
- Убедиться что каждая сессия имеет уникальный fingerprint
- Но fingerprint должен быть стабильным в рамках одной сессии

### 9. **Permissions API**
Проверка разрешений (notifications, geolocation, etc)

**Решение:**
```python
# В fingerprint_generator.py уже есть, но проверим:
await context.grant_permissions(['notifications', 'geolocation'])
```

### 10. **localStorage/Cookies Consistency**
Microsoft может проверять:
- Наличие определенных cookies от предыдущих посещений
- localStorage данные
- IndexedDB

**Решение:**
- Добавить Microsoft-специфичные cookies/storage ПЕРЕД регистрацией

---

## 🔧 Рекомендуемые действия (по приоритету)

### Высокий приоритет:

1. **Проверить IP reputation**
   ```bash
   curl -x proxy:port http://ip-api.com/json/
   ```

   Если тип = "hosting" или "proxy" - использовать residential прокси

2. **Добавить human-like behavior**
   - Случайные задержки
   - Движения мыши
   - Естественная скорость ввода

3. **Проверить WebRTC leak**
   Зайти на https://browserleaks.com/webrtc через прокси

### Средний приоритет:

4. **Добавить предварительные визиты**
   Перед регистрацией:
   - Посетить microsoft.com
   - Посетить outlook.com
   - Подождать 5-10 секунд
   - Поскроллить страницу
   - Только потом переходить к регистрации

5. **Проверить TLS fingerprint**
   https://tls.browserleaks.com/json

6. **Ротация прокси**
   Использовать разные IP для каждой попытки

### Низкий приоритет:

7. **Font fingerprinting**
8. **HTTP headers audit**
9. **Cookies/Storage pre-population**

---

## 🧪 Диагностический скрипт

Создайте этот скрипт для детальной диагностики:

```python
#!/usr/bin/env python3
"""
Диагностика детекции Microsoft
"""
import asyncio
from outlook.browser import BrowserManager

async def diagnose():
    browser = BrowserManager(
        proxy="your_proxy",
        headless=False
    )

    await browser.setup()
    page = browser.page

    # 1. Проверка IP
    await page.goto("https://ip-api.com/json/")
    ip_info = await page.evaluate("() => document.body.innerText")
    print(f"[IP INFO] {ip_info}")

    # 2. Проверка WebRTC
    await page.goto("https://browserleaks.com/webrtc")
    await asyncio.sleep(5)
    print("[WEBRTC] Проверьте визуально на утечку IP")

    # 3. Проверка TLS
    await page.goto("https://tls.browserleaks.com/json")
    tls_info = await page.evaluate("() => document.body.innerText")
    print(f"[TLS] {tls_info[:200]}...")

    # 4. Проверка fonts
    await page.goto("https://www.browserleaks.com/fonts")
    await asyncio.sleep(3)
    print("[FONTS] Проверьте количество шрифтов визуально")

    # 5. Проверка HTTP headers
    await page.goto("https://www.whatismybrowser.com/detect/what-http-headers-is-my-browser-sending")
    await asyncio.sleep(3)
    print("[HEADERS] Проверьте заголовки визуально")

    input("Нажмите Enter для закрытия...")
    await browser.close()

if __name__ == "__main__":
    asyncio.run(diagnose())
```

---

## 📊 Следующие шаги

1. Запустить диагностический скрипт
2. Проверить IP reputation
3. Добавить human-like behavior в outlook_playwright.py
4. Попробовать другой residential прокси
5. Добавить предварительные визиты на Microsoft сайты
