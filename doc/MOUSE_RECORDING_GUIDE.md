# 🖱️ Интеграция записанных движений мыши в Outlook проект

## 📁 Структура файлов

```
outlook/
├── mouse_recorder.py              # Запись движений мыши (pynput)
├── mouse_player.py                # Воспроизведение в Playwright
├── record_mouse_for_signup.py    # Скрипт для записи движений
├── forms_with_recording.py       # FormFiller с поддержкой записей
└── outlook_signup_movements.json # Ваши записанные движения (после записи)
```

## 🚀 Быстрый старт

### Шаг 1: Установка зависимостей

```bash
pip install pynput
```

### Шаг 2: Запись движений мыши

```bash
cd C:\projects
python -m outlook.record_mouse_for_signup
```

Что делает скрипт:
1. Открывает signup.live.com
2. Записывает ваши реальные движения мыши (30 сек)
3. Сохраняет в `outlook_signup_movements.json`

**Во время записи выполните:**
- Наведите на поле Email → кликните
- Введите тестовый email
- Наведите на кнопку Next → кликните
- (Опционально) повторите для других полей

### Шаг 3: Использование в коде

#### Вариант А: Использовать FormFillerWithRecording

```python
from outlook.browser import BrowserManager
from outlook.forms_with_recording import FormFillerWithRecording

async def main():
    browser = BrowserManager(proxy="...", headless=False)
    await browser.setup()
    await browser.page.goto("https://signup.live.com/")

    # ✅ С записанными движениями
    form_filler = FormFillerWithRecording(
        browser.page,
        recording_file='outlook_signup_movements.json'  # Ваша запись!
    )

    # Используйте как обычный FormFiller
    identity = {...}
    await form_filler.fill_email(identity, generate_new_identity)
    await form_filler.fill_password(identity)
    await form_filler.fill_birthdate(identity)

    await browser.close()
```

#### Вариант Б: Использовать HumanBehavior напрямую

```python
from outlook.browser import BrowserManager
from outlook.mouse_player import HumanBehavior

async def main():
    browser = BrowserManager(proxy="...", headless=False)
    await browser.setup()
    await browser.page.goto("https://signup.live.com/")

    # Создаем HumanBehavior с вашей записью
    human = HumanBehavior(
        browser.page,
        recording_file='outlook_signup_movements.json'
    )

    # Используем записанные движения
    await human.type_like_human('#email', 'test@outlook.com')
    await human.click_like_human('#iSignupAction')
    await human.scroll_like_human('down', 200)

    await browser.close()
```

## 🔧 Интеграция с существующим creator.py

### Модифицируйте OutlookCreator:

```python
# В outlook/creator.py

from .forms_with_recording import FormFillerWithRecording

class OutlookCreator:
    def __init__(self, proxy: str = None, headless: bool = False,
                 rotate_ip: bool = False,
                 mouse_recording: str = None):  # ← Новый параметр
        self.proxy = proxy or HARDCODED_PROXY
        self.headless = headless
        self.rotate_ip = rotate_ip
        self.mouse_recording = mouse_recording  # ← Сохраняем путь к записи

        # ... остальной код ...

    async def create_account(self) -> Optional[Dict]:
        # ... настройка браузера ...

        # ✅ Используем FormFillerWithRecording вместо FormFiller
        if self.mouse_recording:
            self.form_filler = FormFillerWithRecording(
                self.browser_manager.page,
                recording_file=self.mouse_recording
            )
            print(f"[CREATOR] 🎬 Используем записанные движения")
        else:
            self.form_filler = FormFillerWithRecording(
                self.browser_manager.page
            )
            print(f"[CREATOR] Используем стандартные Bezier движения")

        # ... остальной код заполнения форм ...
```

### Использование с CLI:

```python
# В outlook/main.py

async def main():
    # Добавляем аргумент для записи мыши
    mouse_recording = None
    for arg in sys.argv:
        if arg.startswith("--mouse-recording="):
            mouse_recording = arg.split("=", 1)[1]

    creator = OutlookCreator(
        proxy=proxy,
        headless=headless,
        rotate_ip=rotate_ip,
        mouse_recording=mouse_recording  # ← Передаем путь к записи
    )

    result = await creator.create_account()
```

Теперь запускайте так:

```bash
# С записанными движениями
python -m outlook.main --mouse-recording=outlook_signup_movements.json

# Без записанных движений (стандартные Bezier)
python -m outlook.main
```

## 💡 Best Practices

### 1. Запишите несколько вариантов

```bash
# Запись 1
python -m outlook.record_mouse_for_signup
# Сохранится: outlook_signup_movements.json
mv outlook_signup_movements.json outlook_signup_v1.json

# Запись 2
python -m outlook.record_mouse_for_signup
mv outlook_signup_movements.json outlook_signup_v2.json

# Запись 3
python -m outlook.record_mouse_for_signup
mv outlook_signup_movements.json outlook_signup_v3.json
```

Затем выбирайте случайный:

```python
import random

recordings = [
    'outlook_signup_v1.json',
    'outlook_signup_v2.json',
    'outlook_signup_v3.json'
]

chosen = random.choice(recordings)
form_filler = FormFillerWithRecording(page, recording_file=chosen)
```

### 2. Варьируйте скорость воспроизведения

```python
# В mouse_player.py можно добавить скорость:
await player.play_from_file(
    'outlook_signup_movements.json',
    speed_multiplier=random.uniform(0.9, 1.1)  # ±10% от скорости записи
)
```

### 3. Комбинируйте с другими stealth техниками

```python
async def create_account_stealth():
    browser = BrowserManager(proxy="...", headless=False)
    await browser.setup()  # ← Применяет fingerprint, cookies, storage

    # Предварительные визиты
    await browser.page.goto("https://www.microsoft.com/")
    await asyncio.sleep(random.uniform(2, 4))

    # Целевая страница с записанными движениями
    await browser.page.goto("https://signup.live.com/")

    human = HumanBehavior(page, 'outlook_signup_movements.json')
    await human.type_like_human('#email', 'test@outlook.com')
```

## 🔍 Troubleshooting

### Проблема: "pynput не может перехватывать события"

**Решение:**
- Windows: Запустите от администратора
- Linux: Добавьте права `sudo usermod -aG input $USER`

### Проблема: "Движения не обнаружены (0 events)"

**Решение:**
- Убедитесь что двигали мышью во время записи
- Проверьте что pynput установлен: `pip show pynput`
- Попробуйте запустить от администратора

### Проблема: "Координаты не совпадают с формой"

**Решение:**
Указывайте правильное разрешение экрана при записи:

```python
# В record_mouse_for_signup.py
# После recorder.save_to_file() добавьте:
import tkinter as tk
root = tk.Tk()
screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()
print(f"Разрешение экрана: {screen_w}x{screen_h}")
```

Затем при воспроизведении:

```python
await player.play_from_file(
    'recording.json',
    original_screen_size=(1920, 1080)  # Ваше разрешение!
)
```

## 🎯 Преимущества записанных движений

| Характеристика | Bezier кривые | Записанные движения |
|----------------|---------------|---------------------|
| Реалистичность | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Вариативность | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Простота | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Детектируемость | Низкая | Очень низкая |

**Рекомендация:**
- Для production: используйте **записанные движения**
- Для тестирования: можно использовать Bezier

## 📝 Чеклист перед использованием

- [ ] Установлен pynput
- [ ] Записаны движения мыши (30+ сек)
- [ ] Файл `outlook_signup_movements.json` существует
- [ ] FormFillerWithRecording интегрирован в creator.py
- [ ] Протестировано на тестовом аккаунте

## 🚀 Полный пример

```python
# outlook/creator.py (модифицированный)

from .forms_with_recording import FormFillerWithRecording

async def create_account(self) -> Optional[Dict]:
    # ... настройка браузера ...

    # Используем записанные движения
    self.form_filler = FormFillerWithRecording(
        self.browser_manager.page,
        recording_file='outlook_signup_movements.json'
    )

    identity = self.generate_identity()

    # Заполняем форму с записанными движениями
    if not await self.form_filler.fill_email(identity, self.generate_identity):
        return None

    if not await self.form_filler.fill_password(identity):
        return None

    if not await self.form_filler.fill_birthdate(identity):
        return None

    return {
        "email": identity["email"],
        "password": identity["password"]
    }
```

Запуск:

```bash
python -m outlook.main --mouse-recording=outlook_signup_movements.json
```

---

**Готово!** Теперь ваш проект использует реальные движения мыши на уровне ОС.
