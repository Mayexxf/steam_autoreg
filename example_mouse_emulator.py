#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Примеры использования эмулятора мыши (без записи)
Демонстрирует как использовать реальные движения мыши на уровне ОС
и интеграцию с Playwright
"""

import asyncio
import sys
import time

sys.path.insert(0, 'C:\\projects')

from src.utils.mouse_emulator import HumanMouseEmulator
from src.utils.playwright_mouse_emulator import PlaywrightMouseEmulator, HumanBehavior
from playwright.async_api import async_playwright


def example_os_level_mouse():
    """
    Пример 1: Управление мышью на уровне ОС (настоящая мышь)
    """
    print("="*70)
    print("ПРИМЕР 1: Управление мышью на уровне ОС")
    print("="*70)
    print("\nЭтот пример будет управлять НАСТОЯЩЕЙ мышью вашей системы")
    print("Убедитесь, что курсор мыши виден на экране\n")

    input("Нажмите Enter для начала...")

    emulator = HumanMouseEmulator()

    # 1. Узнаем текущую позицию
    print(f"\n1. Текущая позиция мыши: {emulator.get_current_position()}")

    # 2. Плавное движение к точке
    print("\n2. Плавное движение к (500, 400) с кривой Безье...")
    emulator.move_to(500, 400, duration=1.0, curve_type='bezier')
    time.sleep(0.5)

    # 3. Естественное движение с коррекцией
    print("\n3. Естественное движение к (800, 600)...")
    emulator.move_to(800, 600, duration=1.2, curve_type='natural')
    time.sleep(0.5)

    # 4. Быстрое дрожащее движение
    print("\n4. Быстрое дрожащее движение к (300, 300)...")
    emulator.move_to(300, 300, duration=0.5, curve_type='jittery')
    time.sleep(0.5)

    # 5. Клик
    print("\n5. Клик в текущей позиции...")
    emulator.click()
    time.sleep(0.5)

    # 6. Клик с движением
    print("\n6. Клик в позиции (600, 400)...")
    emulator.click(600, 400, move_duration=0.8)
    time.sleep(0.5)

    # 7. Двойной клик
    print("\n7. Двойной клик в позиции (700, 500)...")
    emulator.click(700, 500, clicks=2)
    time.sleep(0.5)

    # 8. Случайные движения (имитация просмотра)
    print("\n8. Случайные небольшие движения...")
    emulator.random_movement(radius=50, num_moves=4)
    time.sleep(0.5)

    # 9. Скролл
    print("\n9. Скролл (убедитесь, что под курсором есть прокручиваемая область)...")
    emulator.scroll(dy=-3, num_scrolls=10)
    time.sleep(1)
    emulator.scroll(dy=3, num_scrolls=10)

    print("\n✅ Пример завершен!")


async def example_playwright_integration():
    """
    Пример 2: Интеграция с Playwright (виртуальная мышь в браузере)
    """
    print("\n" + "="*70)
    print("ПРИМЕР 2: Интеграция с Playwright")
    print("="*70)
    print("\nЭтот пример управляет виртуальной мышью в браузере Playwright\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Открываем тестовую страницу
        await page.goto("https://www.example.com")
        await asyncio.sleep(1)

        # Создаем эмулятор
        emulator = PlaywrightMouseEmulator(page)

        # 1. Получаем размер viewport
        viewport = await emulator.get_viewport_size()
        print(f"\n1. Размер viewport: {viewport}")

        # 2. Плавное движение мыши
        print("\n2. Плавное движение мыши...")
        await emulator.move_to(300, 200, duration=1.0, curve_type='natural')
        await asyncio.sleep(0.5)

        # 3. Движение к другой точке
        print("\n3. Движение к центру экрана...")
        center_x = viewport[0] / 2
        center_y = viewport[1] / 2
        await emulator.move_to(center_x, center_y, duration=1.2, curve_type='bezier')
        await asyncio.sleep(0.5)

        # 4. Клик
        print("\n4. Клик...")
        await emulator.click(move_duration=0.7)
        await asyncio.sleep(0.5)

        # 5. Скролл
        print("\n5. Скролл вниз...")
        await emulator.scroll(dy=-100, num_scrolls=10)
        await asyncio.sleep(1)

        print("\n6. Скролл вверх...")
        await emulator.scroll(dy=100, num_scrolls=10)
        await asyncio.sleep(1)

        # 7. Случайные движения
        print("\n7. Случайные движения (имитация чтения)...")
        await emulator.random_movement(radius=60, num_moves=4)

        print("\n✅ Пример завершен! Закрываем браузер...")
        await asyncio.sleep(2)
        await browser.close()


async def example_form_filling():
    """
    Пример 3: Заполнение формы с человеческим поведением
    """
    print("\n" + "="*70)
    print("ПРИМЕР 3: Заполнение формы с человеческим поведением")
    print("="*70)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Открываем страницу с формой (используем Example.com для демо)
        await page.goto("https://www.example.com")
        await asyncio.sleep(2)

        # Создаем высокоуровневый класс для человеческого поведения
        human = HumanBehavior(page)

        print("\n1. Имитация чтения страницы...")
        await human.read_and_scroll(num_scrolls=3, reading_time=1.5)

        print("\n2. Случайные движения мыши...")
        await human.mouse.random_movement(radius=50, num_moves=3)

        print("\n3. Скролл вверх...")
        await human.mouse.scroll(dy=200, num_scrolls=8)

        await asyncio.sleep(1)

        print("\n✅ Демонстрация завершена! Закрываем браузер...")
        await asyncio.sleep(2)
        await browser.close()


async def example_outlook_simulation():
    """
    Пример 4: Симуляция взаимодействия с Outlook
    """
    print("\n" + "="*70)
    print("ПРИМЕР 4: Симуляция взаимодействия с Outlook")
    print("="*70)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Открываем страницу регистрации
        print("\nОткрываем страницу регистрации Outlook...")
        await page.goto("https://signup.live.com/", wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # Создаем эмулятор
        emulator = PlaywrightMouseEmulator(page)
        human = HumanBehavior(page)

        try:
            # 1. "Читаем" страницу
            print("\n1. Имитируем чтение страницы...")
            await human.mouse.random_movement(radius=80, num_moves=4)
            await asyncio.sleep(random.uniform(1.5, 2.5))

            # 2. Скроллим вниз для просмотра
            print("\n2. Скроллим для просмотра...")
            await human.mouse.scroll(dy=-50, num_scrolls=5)
            await asyncio.sleep(1)

            # 3. Скроллим обратно
            print("\n3. Возвращаемся вверх...")
            await human.mouse.scroll(dy=50, num_scrolls=5)
            await asyncio.sleep(1)

            # 4. Наводим на поле email
            print("\n4. Перемещаемся к полю ввода...")
            email_field = await page.query_selector('input[type="email"]')
            if email_field:
                box = await email_field.bounding_box()
                if box:
                    await emulator.move_to(
                        box['x'] + box['width'] / 2,
                        box['y'] + box['height'] / 2,
                        duration=1.2,
                        curve_type='natural'
                    )
                    await asyncio.sleep(0.5)

            # 5. Делаем паузу "думаем"
            print("\n5. Пауза (думаем)...")
            await asyncio.sleep(random.uniform(1.0, 2.0))

            # 6. Небольшие движения мыши
            print("\n6. Небольшие естественные движения...")
            await emulator.random_movement(radius=30, num_moves=2)

            print("\n✅ Демонстрация завершена!")

        except Exception as e:
            print(f"\n⚠️  Произошла ошибка: {e}")
            print("Возможно, структура страницы изменилась")

        print("\nЗакрываем браузер через 3 секунды...")
        await asyncio.sleep(3)
        await browser.close()


async def main():
    """Главное меню"""
    print("="*70)
    print("ЭМУЛЯТОР ЧЕЛОВЕЧЕСКИХ ДВИЖЕНИЙ МЫШИ")
    print("="*70)

    print("\nВыберите пример:")
    print("1. Управление реальной мышью (ОС)")
    print("2. Управление мышью в Playwright")
    print("3. Заполнение формы с человеческим поведением")
    print("4. Симуляция взаимодействия с Outlook")

    choice = input("\nВыбор (1-4): ").strip()

    if choice == '1':
        example_os_level_mouse()
    elif choice == '2':
        await example_playwright_integration()
    elif choice == '3':
        await example_form_filling()
    elif choice == '4':
        await example_outlook_simulation()
    else:
        print("Неверный выбор")


if __name__ == "__main__":
    # Проверяем наличие pynput
    try:
        import pynput
    except ImportError:
        print("="*70)
        print("⚠️  ОШИБКА: pynput не установлен!")
        print("="*70)
        print("\nУстановите командой:")
        print("  pip install pynput")
        sys.exit(1)

    # Проверяем наличие playwright
    try:
        import playwright
    except ImportError:
        print("="*70)
        print("⚠️  ОШИБКА: playwright не установлен!")
        print("="*70)
        print("\nУстановите командой:")
        print("  pip install playwright")
        print("  playwright install")
        sys.exit(1)

    import random
    asyncio.run(main())
