#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Быстрый тест системы записи/воспроизведения мыши
"""

import asyncio
import sys
import time

sys.path.insert(0, 'C:\\projects')

from outlook.browser import BrowserManager
from src.utils.mouse_recorder import MouseRecorder
from src.utils.mouse_player import MousePlayer, HumanBehavior


async def quick_test():
    """Быстрый тест: запись 5 сек + воспроизведение"""
    print("="*80)
    print("БЫСТРЫЙ ТЕСТ СИСТЕМЫ ДВИЖЕНИЯ МЫШИ")
    print("="*80)

    # Шаг 1: Запись
    print("\n[1/3] ЗАПИСЬ (5 секунд)")
    print("      Двигайте мышью прямо СЕЙЧАС!")

    input("\nНажмите Enter для начала...")

    recorder = MouseRecorder()
    recorder.start_recording()

    for i in range(5, 0, -1):
        print(f"\r      Осталось: {i} сек...", end='', flush=True)
        time.sleep(1)

    print("\r      ✅ Запись завершена!      ")
    recorder.stop_recording()

    summary = recorder.get_summary()
    print(f"\n      Записано:")
    print(f"      - Движений: {summary['moves']}")
    print(f"      - Кликов: {summary['clicks']}")

    if summary['moves'] == 0:
        print("\n      ⚠️  Движений не обнаружено!")
        print("      Возможно, pynput не имеет прав на перехват событий.")
        print("      Попробуйте запустить от администратора.")
        return

    # Сохраняем
    recording_file = "quick_test_recording.json"
    recorder.save_to_file(recording_file)

    # Шаг 2: Открываем браузер
    print(f"\n[2/3] ОТКРЫТИЕ БРАУЗЕРА")

    browser = BrowserManager(
        proxy="MPzEefwWaIUi:tc6aWZqR@pool.proxy.market:10000",
        headless=False
    )

    try:
        await browser.setup()
        print("      ✅ Браузер готов!")

        # Переходим на тестовую страницу
        await browser.page.goto("https://www.example.com",
                                wait_until="domcontentloaded",
                                timeout=30000)
        await asyncio.sleep(1)

        # Шаг 3: Воспроизведение
        print(f"\n[3/3] ВОСПРОИЗВЕДЕНИЕ")
        print("      Смотрите на браузер - мышь будет двигаться!")

        await asyncio.sleep(2)  # Пауза для подготовки

        player = MousePlayer(browser.page)
        await player.play_from_file(
            recording_file,
            speed_multiplier=1.0,
            original_screen_size=(1920, 1080)
        )

        print("\n" + "="*80)
        print("✅ ТЕСТ УСПЕШНО ЗАВЕРШЕН!")
        print("="*80)
        print("\nСистема работает корректно!")
        print("Вы можете использовать её для:")
        print("  - Записи движений для форм")
        print("  - Воспроизведения в автоматизации")
        print("  - Создания человекоподобного поведения")

        print("\nБраузер остается открытым.")
        input("\nНажмите Enter для закрытия...")

    finally:
        await browser.close()


if __name__ == "__main__":
    try:
        import pynput
        print("[INFO] ✅ pynput установлен")
    except ImportError:
        print("="*80)
        print("❌ ОШИБКА: pynput не установлен!")
        print("="*80)
        print("\nУстановите командой:")
        print("  pip install pynput")
        print("="*80)
        sys.exit(1)

    try:
        asyncio.run(quick_test())
    except KeyboardInterrupt:
        print("\n\n[INFO] Тест прерван пользователем")
    except Exception as e:
        print(f"\n\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
