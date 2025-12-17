#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Запись движений мыши для форм регистрации Outlook
Используйте этот скрипт чтобы записать ваши реальные движения мыши
"""

import asyncio
import sys
import time

from outlook.browser import BrowserManager
from outlook.mouse_recorder import MouseRecorder


async def record_signup_movements():
    """
    Записывает движения мыши при заполнении формы регистрации Outlook
    """
    print("="*80)
    print("ЗАПИСЬ ДВИЖЕНИЙ МЫШИ ДЛЯ OUTLOOK РЕГИСТРАЦИИ")
    print("="*80)

    print("\nЭтот скрипт откроет форму регистрации Outlook.")
    print("Вы должны вручную выполнить следующие действия:")
    print()
    print("  1. Навести мышь на поле Email")
    print("  2. Кликнуть в поле Email")
    print("  3. Ввести любой тестовый email")
    print("  4. Навести на кнопку 'Next'")
    print("  5. Кликнуть 'Next'")
    print("  6. (Опционально) навести на поле Password и кликнуть")
    print()
    print("Длительность записи: 30 секунд")
    print()

    input("Нажмите Enter для начала...")

    # Настраиваем браузер
    browser = BrowserManager(
        proxy="MPzEefwWaIUi:tc6aWZqR@pool.proxy.market:10000",
        headless=False
    )

    try:
        print("\n[1/3] Настройка браузера...")
        await browser.setup()
        print("      ✅ Браузер готов!")

        print("\n[2/3] Переход на страницу регистрации...")
        await browser.page.goto(
            "https://signup.live.com/",
            wait_until="domcontentloaded",
            timeout=60000
        )
        await asyncio.sleep(2)
        print("      ✅ Страница загружена!")

        print("\n[3/3] ЗАПИСЬ НАЧАЛАСЬ!")
        print("      Выполняйте действия над формой...")
        print()

        # Начинаем запись
        recorder = MouseRecorder()
        recorder.start_recording()

        # Записываем 30 секунд
        for i in range(30, 0, -1):
            print(f"\r      Осталось: {i} сек...", end='', flush=True)
            await asyncio.sleep(1)

        print("\r      ✅ Запись завершена!       ")

        # Останавливаем запись
        recorder.stop_recording()

        # Статистика
        summary = recorder.get_summary()
        print()
        print("="*80)
        print("СТАТИСТИКА ЗАПИСИ")
        print("="*80)
        print(f"  Всего событий: {summary['total_events']}")
        print(f"  Движений мыши: {summary['moves']}")
        print(f"  Кликов: {summary['clicks']}")
        print(f"  Скроллов: {summary['scrolls']}")
        print(f"  Длительность: {summary['duration']:.2f} сек")
        print()

        if summary['moves'] == 0:
            print("⚠️  ВНИМАНИЕ: Движения мыши не обнаружены!")
            print("   Возможные причины:")
            print("   1. pynput требует прав администратора")
            print("   2. Вы не двигали мышью")
            print()
            input("Нажмите Enter для закрытия...")
            return

        # Сохраняем
        filename = "outlook_signup_movements.json"
        recorder.save_to_file(filename)

        print("="*80)
        print("✅ УСПЕШНО СОХРАНЕНО!")
        print("="*80)
        print(f"  Файл: {filename}")
        print()
        print("Теперь вы можете использовать эти движения в автоматизации:")
        print()
        print("  from outlook.mouse_player import HumanBehavior")
        print()
        print("  human = HumanBehavior(page, 'outlook_signup_movements.json')")
        print("  await human.type_like_human('#email', 'test@outlook.com')")
        print("  await human.click_like_human('#next-button')")
        print()

        input("Нажмите Enter для закрытия...")

    finally:
        await browser.close()


async def main():
    # Проверяем pynput
    try:
        import pynput
    except ImportError:
        print("="*80)
        print("❌ ОШИБКА: pynput не установлен!")
        print("="*80)
        print()
        print("Установите командой:")
        print("  pip install pynput")
        print()
        print("="*80)
        return

    try:
        await record_signup_movements()
    except KeyboardInterrupt:
        print("\n\n[INFO] Прервано пользователем")
    except Exception as e:
        print(f"\n\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
