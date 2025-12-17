# 🖱️ Система записи и воспроизведения движений мыши

Реализация перехвата движений мыши на уровне ОС и воспроизведения в Playwright для создания **неотличимого от человека** поведения.

## 🎯 Возможности

- ✅ **Запись движений мыши** на уровне ОС (pynput)
- ✅ **Перехват кликов** и скроллинга
- ✅ **Воспроизведение** в Playwright с нормализацией координат
- ✅ **HumanBehavior API** для естественного взаимодействия с формами
- ✅ **Сохранение/загрузка** записей в JSON
- ✅ **Скорость воспроизведения** настраивается

## 📦 Установка

```bash
# Установите библиотеку для перехвата событий мыши
pip install pynput

# Или
python -m pip install pynput
```

## 🚀 Быстрый старт

### 1. Запись движений мыши

```python
from src.utils.mouse_recorder import MouseRecorder

# Создаем recorder
recorder = MouseRecorder()
recorder.start_recording()

# Двигайте мышью, кликайте, скроллите...
# Нажмите Ctrl+C для остановки

recorder.stop_recording()
recorder.save_to_file('my_movements.json')
```

### 2. Воспроизведение в браузере

```python
from outlook.browser import BrowserManager
from src.utils.mouse_player import MousePlayer

browser = BrowserManager(proxy="...", headless=False)
await browser.setup()

# Создаем player
player = MousePlayer(browser.page)

# Воспроизводим
await player.play_from_file(
    'my_movements.json',
    speed_multiplier=1.0,
    original_screen_size=(1920, 1080)  # Ваше разрешение
)
```

### 3. HumanBehavior API (рекомендуется)

```python
from src.utils.mouse_player import HumanBehavior

human = HumanBehavior(page, recording_file='my_movements.json')

# Печатать как человек
await human.type_like_human('#email', 'test@example.com')

# Кликать как человек (с движением мыши)
await human.click_like_human('#submit-button')

# Скроллить как человек
await human.scroll_like_human('down', 300)
```

## 📖 Детальное руководство

### Запись движений для конкретной формы

**Сценарий**: Записать движения для заполнения формы регистрации Outlook

```python
import asyncio
from outlook.browser import BrowserManager
from src.utils.mouse_recorder import MouseRecorder

async def record_outlook_movements():
    # Открываем браузер
    browser = BrowserManager(proxy="...", headless=False)
    await browser.setup()
    await browser.page.goto("https://signup.live.com/")

    # Начинаем запись
    recorder = MouseRecorder()
    recorder.start_recording()

    print("🎙️  ЗАПИСЬ! Выполните действия:")
    print("  1. Наведите на поле Email")
    print("  2. Кликните")
    print("  3. Введите тестовый email")
    print("  4. Наведите на кнопку Next")
    print("  5. Кликните")

    # Записываем 30 секунд
    await asyncio.sleep(30)

    recorder.stop_recording()
    recorder.save_to_file('outlook_signup.json')

    await browser.close()

asyncio.run(record_outlook_movements())
```

### Воспроизведение с автозаполнением

```python
from src.utils.mouse_player import HumanBehavior

async def signup_outlook_with_recording():
    browser = BrowserManager(proxy="...", headless=False)
    await browser.setup()
    await browser.page.goto("https://signup.live.com/")

    # Используем HumanBehavior с записанными движениями
    human = HumanBehavior(
        browser.page,
        recording_file='outlook_signup.json'
    )

    # Заполняем форму с человеческими движениями
    await human.type_like_human('#liveSwitch', 'myemail@outlook.com')
    await asyncio.sleep(1)

    await human.click_like_human('#iSignupAction')

    await browser.close()

asyncio.run(signup_outlook_with_recording())
```

## 🔧 API Reference

### MouseRecorder

#### `start_recording()`
Начинает запись движений мыши на уровне ОС.

#### `stop_recording() -> int`
Останавливает запись. Возвращает количество событий.

#### `save_to_file(filepath: str)`
Сохраняет запись в JSON файл.

#### `get_events() -> List[MouseEvent]`
Возвращает список записанных событий.

#### `get_summary() -> Dict`
Возвращает статистику: количество движений, кликов, скроллов.

### MousePlayer

#### `play_events(events, speed_multiplier=1.0, original_screen_size=None)`
Воспроизводит события мыши.

- `events`: Список MouseEvent
- `speed_multiplier`: Скорость (1.0 = нормально, 2.0 = 2x быстрее)
- `original_screen_size`: (width, height) экрана при записи

#### `play_from_file(filepath, speed_multiplier=1.0, original_screen_size=None)`
Воспроизводит из JSON файла.

#### `move_to_element_humanlike(selector, recording_file=None)`
Перемещает мышь к элементу используя человеческие движения.

### HumanBehavior

#### `type_like_human(selector, text)`
Печатает текст с задержками и естественным ритмом.

#### `click_like_human(selector)`
Кликает с предварительным движением мыши к элементу.

#### `scroll_like_human(direction='down', amount=300)`
Скроллит страницу естественными движениями.

## 📊 Формат записи

JSON формат:

```json
{
  "version": "1.0",
  "total_events": 1523,
  "duration": 15.234,
  "events": [
    {
      "timestamp": 0.123,
      "x": 456,
      "y": 789,
      "event_type": "move",
      "button": null,
      "scroll_dx": 0,
      "scroll_dy": 0
    },
    {
      "timestamp": 1.456,
      "x": 500,
      "y": 300,
      "event_type": "click",
      "button": "left",
      "scroll_dx": 0,
      "scroll_dy": 0
    }
  ]
}
```

## 💡 Best Practices

### 1. Записывайте несколько вариантов

Запишите 3-5 разных вариантов заполнения формы и выбирайте случайный:

```python
import random

recordings = [
    'outlook_v1.json',
    'outlook_v2.json',
    'outlook_v3.json'
]

chosen = random.choice(recordings)
human = HumanBehavior(page, recording_file=chosen)
```

### 2. Варьируйте скорость

```python
# Случайная скорость от 0.8 до 1.2
speed = random.uniform(0.8, 1.2)
await player.play_from_file('recording.json', speed_multiplier=speed)
```

### 3. Добавляйте случайные паузы

```python
await human.type_like_human('#email', 'test@example.com')

# Случайная пауза (человек думает)
await asyncio.sleep(random.uniform(1.0, 3.0))

await human.click_like_human('#next-button')
```

### 4. Нормализуйте координаты

Всегда указывайте `original_screen_size` при воспроизведении:

```python
# При записи ваш экран был 1920x1080
await player.play_from_file(
    'recording.json',
    original_screen_size=(1920, 1080)
)
```

### 5. Комбинируйте с другими stealth техниками

```python
# 1. Stealth fingerprint
await browser.setup()  # Применяет fingerprint

# 2. Предварительные визиты
await browser.page.goto("https://www.microsoft.com/")
await human.scroll_like_human('down', 200)
await asyncio.sleep(random.uniform(2, 5))

# 3. Целевая страница с человеческими движениями
await browser.page.goto("https://signup.live.com/")
await human.type_like_human('#email', 'myemail@outlook.com')
```

## 🎬 Примеры использования

### Пример 1: Простая запись

```bash
python example_human_mouse.py
# Выберите: 1
```

### Пример 2: HumanBehavior демо

```bash
python example_human_mouse.py
# Выберите: 2
```

### Пример 3: Outlook регистрация

```bash
python example_human_mouse.py
# Выберите: 3
```

## ⚙️ Интеграция с outlook_playwright.py

Добавьте в ваш скрипт регистрации:

```python
from src.utils.mouse_player import HumanBehavior

class OutlookRegistration:
    def __init__(self):
        self.browser = BrowserManager(...)
        self.human = None

    async def setup(self):
        await self.browser.setup()
        # Инициализируем HumanBehavior с записью
        self.human = HumanBehavior(
            self.browser.page,
            recording_file='outlook_movements.json'
        )

    async def fill_email(self, email):
        # Вместо page.fill()
        await self.human.type_like_human('#liveSwitch', email)

    async def click_next(self):
        # Вместо page.click()
        await self.human.click_like_human('#iSignupAction')
```

## 🐛 Troubleshooting

### Проблема: "pynput не установлен"

```bash
pip install pynput
```

### Проблема: Координаты не совпадают

Убедитесь что указали правильный `original_screen_size`:

```python
# Узнайте ваше разрешение экрана
import tkinter as tk
root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
print(f"Screen: {screen_width}x{screen_height}")
```

### Проблема: Движения слишком быстрые/медленные

Настройте `speed_multiplier`:

```python
# Медленнее
await player.play_from_file('rec.json', speed_multiplier=0.5)

# Быстрее
await player.play_from_file('rec.json', speed_multiplier=2.0)
```

## 🔒 Безопасность

- ✅ Все движения записываются **локально**
- ✅ Никакие данные не отправляются в интернет
- ✅ Файлы записей хранятся на вашем компьютере
- ✅ Можно использовать `.gitignore` для записей

## 📝 TODO / Roadmap

- [ ] Поддержка нескольких мониторов
- [ ] Автоматическая детекция разрешения экрана
- [ ] GUI для удобной записи
- [ ] Библиотека готовых движений
- [ ] Поддержка жестов (drag & drop)

## 🤝 Contributing

Если хотите улучшить систему - добавьте новые возможности!

---

**Автор**: Claude Code Project
**Версия**: 1.0.0
**Лицензия**: MIT
