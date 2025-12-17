#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест stealth модулей с реальным BrowserManager
"""

import asyncio
import sys

from outlook.utils import human_delay, human_click

sys.path.insert(0, '/')

from outlook.browser import BrowserManager


async def main():
    print("="*60)
    print("ТЕСТ STEALTH С BROWSERMANAGER")
    print("="*60)

    browser_manager = BrowserManager(
        proxy="MPzEefwWaIUi:tc6aWZqR@pool.proxy.market:10000",
        headless=False
    )

    await browser_manager.setup()

    try:
        await browser_manager.page.goto(
            "https://www.microsoft.com",
            wait_until="domcontentloaded",
            timeout=30000
        )
        print("[WARMUP] [+] Bing.com загружен")

        # Применяем storage на нейтральной странице
        await browser_manager.apply_storage()

        # Естественное поведение: задержка, движения мыши, скроллинг
        await human_delay(1500, 2500)

        # Надёжный локатор кнопки входа
        signin_locator = browser_manager.page.locator('#mectrl_main_trigger')  # по ID — самый стабильный
        # Резервные варианты
        if await signin_locator.count() == 0:
            signin_locator = browser_manager.page.get_by_role("link", name="Вхід")
        if await signin_locator.count() == 0:
            signin_locator = browser_manager.page.locator('a:has-text("Вхід")')

        await human_click(browser_manager.page, signin_locator)


    except KeyboardInterrupt:
        print(f"[WARMUP] Ошибка прогрева: {e}")
    finally:
        await browser_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
