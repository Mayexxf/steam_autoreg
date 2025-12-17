#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Outlook Account Creator - Entry Point
Запуск: python -m outlook.main
"""

import sys
import asyncio

from .creator import OutlookCreator


async def main():
    """Точка входа"""
    # Парсим аргументы
    headless = "--headless" in sys.argv
    rotate_ip = "--rotate-ip" in sys.argv
    proxy = None

    for arg in sys.argv:
        if arg.startswith("--proxy="):
            proxy = arg.split("=", 1)[1]

    # Создаём и запускаем
    creator = OutlookCreator(
        proxy=proxy, headless=headless, rotate_ip=rotate_ip)
    result = await creator.create_account()

    if result:
        print("\n" + "=" * 60)
        print("Созданные учётные данные:")
        print(f"  Email: {result['email']}")
        print(f"  Password: {result['password']}")
        print("=" * 60)


def run():
    """Запуск из командной строки"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Прервано пользователем")


if __name__ == "__main__":
    run()
