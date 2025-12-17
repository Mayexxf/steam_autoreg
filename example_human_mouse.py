#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Пример использования записи и воспроизведения движений мыши
"""

import asyncio
import sys
import time

sys.path.insert(0, 'C:\\projects')

from outlook.browser import BrowserManager
from src.utils.mouse_recorder import MouseRecorder, MouseRecordingSession
from src.utils.mouse_player import MousePlayer, HumanBehavior


async def example_1_record_and_replay():
    """
    Пример 1: Запись движений и воспроизведение
    """
    print("="*80)
    print("ПРИМЕР 1: Запись и воспроизведение движений мыши")
    print("="*80)

    # Шаг 1: Запись движений
    print("\n[STEP 1] Запись движений мыши (10 секунд)")
    print("         Двигайте мышью, кликайте, скроллите...")

    input("\nНажмите Enter для начала записи...")

    recorder = MouseRecorder()
    recorder.start_recording()

    try:
        # Записываем 10 секунд
        for i in range(10, 0, -1):
            print(f"\rОсталось: {i} сек...", end='', flush=True)
            time.sleep(1)
        print("\r✅ Запись завершена!     ")
    except KeyboardInterrupt:
        print("\n⏹️  Запись прервана")

    recorder.stop_recording()

    # Сохраняем запись
    recording_file = "mouse_recording_example.json"
    recorder.save_to_file(recording_file)

    summary = recorder.get_summary()
    print(f"\n[SUMMARY]")
    print(f"  Движений: {summary['moves']}")
    print(f"  Кликов: {summary['clicks']}")
    print(f"  Скроллов: {summary['scrolls']}")

    # Шаг 2: Воспроизведение в браузере
    print(f"\n[STEP 2] Воспроизведение в браузере")

    browser = BrowserManager(
        proxy="MPzEefwWaIUi:tc6aWZqR@pool.proxy.market:10000",
        headless=False
    )

    try:
        await browser.setup()
        await browser.page.goto("https://www.example.com", wait_until="domcontentloaded")

        # Создаем player и воспроизводим
        player = MousePlayer(browser.page)
        await player.play_from_file(
            recording_file,
            speed_multiplier=1.0,  # Нормальная скорость
            original_screen_size=(1920, 1080)  # Укажите ваше разрешение экрана
        )

        print("\n✅ Воспроизведение завершено!")
        print("   Браузер остается открытым для проверки")

        input("\nНажмите Enter для закрытия...")

    finally:
        await browser.close()


async def example_2_human_behavior():
    """
    Пример 2: Использование HumanBehavior для форм
    """
    print("="*80)
    print("ПРИМЕР 2: Человеческое взаимодействие с формами")
    print("="*80)

    browser = BrowserManager(
        proxy="MPzEefwWaIUi:tc6aWZqR@pool.proxy.market:10000",
        headless=False
    )

    try:
        await browser.setup()

        # Переходим на страницу с формой
        await browser.page.goto("https://www.example.com", wait_until="domcontentloaded")

        # Создаем HumanBehavior
        # Можно передать файл с записью движений (опционально)
        human = HumanBehavior(browser.page)

        print("\n[DEMO] Демонстрация человеческих движений:")

        # 1. Скролл вниз
        print("  1. Скролл вниз...")
        await human.scroll_like_human('down', 300)
        await asyncio.sleep(1)

        # 2. Скролл вверх
        print("  2. Скролл вверх...")
        await human.scroll_like_human('up', 300)
        await asyncio.sleep(1)

        print("\n✅ Демонстрация завершена!")
        print("   Заметьте естественные движения мыши")

        input("\nНажмите Enter для закрытия...")

    finally:
        await browser.close()


async def example_3_outlook_signup():
    """
    Пример 3: Применение для регистрации Outlook с записанными движениями
    """
    print("="*80)
    print("ПРИМЕР 3: Регистрация Outlook с человеческими движениями")
    print("="*80)

    # Сначала запишем движения для этой формы
    print("\n[PREPARATION] Откроем форму регистрации для записи движений")
    print("              Вы должны:")
    print("              1. Навести на поле email")
    print("              2. Кликнуть")
    print("              3. Навести на кнопку Next")
    print("              4. Кликнуть")

    input("\nНажмите Enter для начала записи (будет 15 секунд)...")

    browser = BrowserManager(
        proxy="MPzEefwWaIUi:tc6aWZqR@pool.proxy.market:10000",
        headless=False
    )

    try:
        await browser.setup()
        await browser.page.goto("https://signup.live.com/", wait_until="domcontentloaded")

        print("\n🎙️  ЗАПИСЬ НАЧАЛАСЬ! (15 секунд)")
        print("   Выполните действия над формой регистрации...")

        recorder = MouseRecorder()
        recorder.start_recording()

        # Записываем 15 секунд
        for i in range(15, 0, -1):
            print(f"\rОсталось: {i} сек...", end='', flush=True)
            await asyncio.sleep(1)
        print("\r✅ Запись завершена!       ")

        recorder.stop_recording()
        recording_file = "outlook/outlook_signup_movements.json"
        recorder.save_to_file(recording_file)

        print(f"\n💾 Движения сохранены в: {recording_file}")
        print("   Теперь эти движения можно использовать для автоматизации!")

        # Демонстрация использования
        print("\n[DEMO] Воспроизведение записанных движений...")
        await asyncio.sleep(2)

        # Обновляем страницу
        await browser.page.reload(wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # Воспроизводим
        player = MousePlayer(browser.page)
        await player.play_from_file(
            recording_file,
            speed_multiplier=0.8,  # Немного медленнее для демо
            original_screen_size=(1920, 1080)
        )

        print("\n✅ Демонстрация завершена!")

        input("\nНажмите Enter для закрытия...")

    finally:
        await browser.close()


async def main():
    print("="*80)
    print("СИСТЕМА ЗАПИСИ И ВОСПРОИЗВЕДЕНИЯ ДВИЖЕНИЙ МЫШИ")
    print("="*80)

    print("\nВыберите пример:")
    print("1. Простая запись и воспроизведение")
    print("2. HumanBehavior API (скролл, клики)")
    print("3. Запись движений для Outlook регистрации")

    choice = input("\nВыбор (1/2/3): ").strip()

    if choice == '1':
        await example_1_record_and_replay()
    elif choice == '2':
        await example_2_human_behavior()
    elif choice == '3':
        await example_3_outlook_signup()
    else:
        print("Неверный выбор")


if __name__ == "__main__":
    # Проверяем наличие pynput
    try:
        import pynput
    except ImportError:
        print("="*80)
        print("⚠️  ОШИБКА: pynput не установлен!")
        print("="*80)
        print("\nУстановите командой:")
        print("  pip install pynput")
        print("\nИли:")
        print("  python -m pip install pynput")
        print("="*80)
        sys.exit(1)

    asyncio.run(main())
