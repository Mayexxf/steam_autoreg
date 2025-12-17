# Эмулятор человеческих движений мыши (без записи)

Система для эмуляции естественных движений мыши без предварительной записи. Работает как на уровне ОС (реальная мышь), так и в Playwright (виртуальная мышь браузера).

## Компоненты

### 1. `src/utils/mouse_emulator.py`
**HumanMouseEmulator** - управление реальной мышью на уровне ОС через pynput

**Основные методы:**
- `move_to(x, y, duration, curve_type)` - плавное перемещение к точке
- `click(x, y, button, clicks)` - клик с естественным движением
- `scroll(dx, dy, num_scrolls)` - скролл с паузами
- `type_text(text, min_delay, max_delay, mistake_probability)` - печать как человек
- `drag_to(x, y, button, duration)` - перетаскивание
- `random_movement(radius, num_moves)` - случайные движения

**Типы кривых движения:**
- `bezier` - плавная кривая Безье (по умолчанию)
- `natural` - естественное движение с коррекцией траектории
- `jittery` - быстрое дрожащее движение

### 2. `src/utils/playwright_mouse_emulator.py`
**PlaywrightMouseEmulator** - управление виртуальной мышью в Playwright

Те же методы, что и HumanMouseEmulator, но асинхронные и работают с Playwright Page

**HumanBehavior** - высокоуровневый класс для Playwright:
- `fill_form_field(selector, text)` - заполнить поле формы
- `click_button(selector, pause_before)` - кликнуть кнопку
- `read_and_scroll(num_scrolls, reading_time)` - имитация чтения

## Установка

```bash
pip install pynput playwright
playwright install
```

## Примеры использования

### Пример 1: Реальная мышь (ОС)

```python
from src.utils.mouse_emulator import HumanMouseEmulator

# Создаем эмулятор
emulator = HumanMouseEmulator()

# Плавное движение к точке (500, 400)
emulator.move_to(500, 400, duration=1.0, curve_type='natural')

# Клик в текущей позиции
emulator.click()

# Клик с движением к точке
emulator.click(800, 600, move_duration=0.8)

# Двойной клик
emulator.click(700, 500, clicks=2)

# Скролл
emulator.scroll(dy=-3, num_scrolls=10)

# Печать текста с опечатками
emulator.type_text("Hello World!", mistake_probability=0.03)

# Случайные движения (имитация просмотра)
emulator.random_movement(radius=50, num_moves=4)
```

### Пример 2: Playwright (виртуальная мышь)

```python
import asyncio
from playwright.async_api import async_playwright
from src.utils.playwright_mouse_emulator import PlaywrightMouseEmulator

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://example.com")

        # Создаем эмулятор
        emulator = PlaywrightMouseEmulator(page)

        # Плавное движение
        await emulator.move_to(300, 200, duration=1.0, curve_type='natural')

        # Клик на элемент
        await emulator.click_element('button.submit', curve_type='bezier')

        # Заполнить поле с печатью
        await emulator.type_text(
            '#email',
            'user@example.com',
            mistake_probability=0.02
        )

        # Скролл
        await emulator.scroll(dy=-100, num_scrolls=10)

        # Случайные движения
        await emulator.random_movement(radius=60, num_moves=4)

        await browser.close()

asyncio.run(main())
```

### Пример 3: Высокоуровневое API (HumanBehavior)

```python
from src.utils.playwright_mouse_emulator import HumanBehavior

async def fill_signup_form():
    # ... открыть браузер и страницу

    human = HumanBehavior(page)

    # Имитация чтения страницы
    await human.read_and_scroll(num_scrolls=3, reading_time=2.0)

    # Заполнить поле email
    await human.fill_form_field('#email', 'user@example.com')

    # Заполнить поле пароля
    await human.fill_form_field('#password', 'MyPassword123')

    # Кликнуть кнопку с паузой перед кликом
    await human.click_button('button[type="submit"]', pause_before=1.0)
```

### Пример 4: Использование в Outlook проекте

```python
from outlook.browser import BrowserManager
from src.utils.playwright_mouse_emulator import PlaywrightMouseEmulator, HumanBehavior

async def signup_outlook():
    browser = BrowserManager(
        proxy="user:pass@proxy:10000",
        headless=False
    )

    try:
        await browser.setup()
        await browser.page.goto("https://signup.live.com/")

        # Создаем эмулятор человека
        human = HumanBehavior(browser.page)

        # Имитируем чтение страницы
        await human.read_and_scroll(num_scrolls=2)

        # Заполняем поле email
        await human.fill_form_field(
            'input[type="email"]',
            'newuser@outlook.com'
        )

        # Кликаем Next
        await human.click_button('input[type="submit"]')

    finally:
        await browser.close()
```

## Алгоритмы генерации движений

### Кривая Безье (bezier)
- Плавная кубическая кривая с случайными контрольными точками
- Естественное перпендикулярное отклонение от прямой линии
- Микродрожание для реалистичности
- Подходит для большинства случаев

### Естественное движение (natural)
- Движение с промежуточной коррекцией траектории
- Имитирует как человек корректирует курс во время движения
- Две последовательные кривые Безье
- Подходит для длинных перемещений

### Дрожащее движение (jittery)
- Быстрое движение с повышенным дрожанием
- Имитирует волнение или спешку
- Увеличенное микродрожание на всем пути
- Подходит для имитации нервных действий

### Ease-in-out
- Все движения используют функцию плавности
- Медленное начало
- Быстрая середина
- Медленное окончание
- Случайные микрозадержки между точками

## Параметры настройки

### Движение мыши
- `duration` - длительность движения (0.3-2.0 сек рекомендуется)
- `curve_type` - тип кривой ('bezier', 'natural', 'jittery')
- `num_points` - количество промежуточных точек (автоматически)

### Клик
- `button` - кнопка мыши ('left', 'right', 'middle')
- `clicks` - количество кликов (1=одиночный, 2=двойной)
- `interval` - интервал между кликами (сек)
- Автоматическое время удержания кнопки: 0.05-0.12 сек
- Случайное микросмещение при повторных кликах: ±1-2 пикселя

### Скролл
- `dy` - направление и величина (отрицательный = вниз)
- `num_scrolls` - количество шагов
- `delay_between` - задержка между шагами (сек)
- Случайная вариация величины скролла: ±10%

### Печать текста
- `min_delay` - минимальная задержка между символами (сек)
- `max_delay` - максимальная задержка между символами (сек)
- `mistake_probability` - вероятность опечатки (0.0-1.0)
- Автоматические паузы: 5% вероятность, 0.3-0.8 сек
- Автоматическое исправление опечаток

## Запуск примеров

```bash
# Интерактивное меню с примерами
python example_mouse_emulator.py

# Тестирование реального управления мышью
python src/utils/mouse_emulator.py

# Тестирование Playwright интеграции
python src/utils/playwright_mouse_emulator.py
```

## Отличия от mouse_recorder/mouse_player

| Характеристика | Recorder/Player | Emulator |
|----------------|-----------------|----------|
| Требует записи | ✅ Да | ❌ Нет |
| Работает сразу | ❌ Нет | ✅ Да |
| Гибкость | ⚠️ Ограничена записью | ✅ Полная |
| Адаптивность | ⚠️ К размерам экрана | ✅ К любым параметрам |
| Случайность | ❌ Повторяет запись | ✅ Каждый раз разные |
| Простота | ⚠️ Нужна запись | ✅ Просто вызвать |

## Рекомендации по использованию

### Для регистрации Outlook:
```python
# Используйте 'natural' для длинных движений
await emulator.move_to(x, y, duration=1.0, curve_type='natural')

# Паузы перед важными действиями
await asyncio.sleep(random.uniform(0.5, 1.5))

# Случайные движения для имитации чтения
await emulator.random_movement(radius=40, num_moves=3)

# Вероятность опечаток 2-3%
await emulator.type_text(email, mistake_probability=0.02)
```

### Для обхода детекции:
- Варьируйте `duration` для каждого действия
- Используйте разные `curve_type` для разнообразия
- Добавляйте случайные паузы между действиями
- Используйте `random_movement()` для имитации просмотра
- Не делайте действия слишком быстро (duration < 0.3)
- Добавляйте "чтение" через `read_and_scroll()`

### Тайминги (рекомендуемые):
- Движение мыши: 0.5-1.5 сек
- Пауза перед кликом: 0.1-0.3 сек
- Пауза после клика: 0.2-0.5 сек
- Задержка при печати: 0.05-0.2 сек/символ
- Пауза для "чтения": 1-3 сек
- Скролл: 0.08-0.15 сек между шагами

## Интеграция с существующим кодом

### Замена в outlook/forms.py:
```python
# Было:
await page.click(selector)

# Стало:
from src.utils.playwright_mouse_emulator import HumanBehavior
human = HumanBehavior(page)
await human.click_button(selector)
```

### Замена в outlook/creator.py:
```python
# Было:
await page.fill(selector, value)

# Стало:
from src.utils.playwright_mouse_emulator import HumanBehavior
human = HumanBehavior(page)
await human.fill_form_field(selector, value)
```

## Производительность

- OS-level (pynput): ~0.001-0.01 сек задержка между точками
- Playwright: ~0.001-0.01 сек задержка между точками
- Генерация пути: мгновенная (< 1 мс)
- Память: минимальная (только список точек)

## Совместимость

- OS-level: Windows, macOS, Linux (через pynput)
- Playwright: все браузеры (Chromium, Firefox, WebKit)
- Python: 3.7+
