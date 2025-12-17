#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Быстрый тест с принудительным выводом"""
import sys
import asyncio
sys.path.insert(0, 'C:\\projects')

from outlook.browser import BrowserManager

async def main():
    print("НАЧАЛО ТЕСТА", flush=True)

    browser_manager = BrowserManager(
        proxy="MPzEefwWaIUi:tc6aWZqR@pool.proxy.market:10000",
        headless=False
    )

    try:
        print("[1] Настройка браузера...", flush=True)
        await browser_manager.setup()
        print("[2] Браузер готов", flush=True)

        print("[3] Переход на signup.live.com...", flush=True)
        await browser_manager.page.goto("https://signup.live.com/signup", timeout=60000)
        print("[4] Страница загружена", flush=True)

        # Проверяем URL и заголовок
        url = browser_manager.page.url
        title = await browser_manager.page.title()
        print(f"[5] URL: {url}", flush=True)
        print(f"[6] Title: {title}", flush=True)

        # Получаем текст страницы
        body_text = await browser_manager.page.inner_text('body')
        print(f"[7] Текст (первые 500 символов):", flush=True)
        print(body_text[:500], flush=True)

        # Проверяем на блокировку
        if 'suspicious' in body_text.lower() or 'unusual' in body_text.lower():
            print("[!] ОБНАРУЖЕНА БЛОКИРОВКА!", flush=True)

        # Делаем скриншот
        screenshot_path = "C:\\projects\\signup_screenshot.png"
        await browser_manager.page.screenshot(path=screenshot_path, full_page=True)
        print(f"[8] Скриншот сохранен: {screenshot_path}", flush=True)

        # Проверяем navigator.webdriver
        webdriver = await browser_manager.page.evaluate("() => navigator.webdriver")
        print(f"[9] navigator.webdriver = {webdriver}", flush=True)

        # Ждем 10 секунд чтобы можно было посмотреть
        print("[10] Жду 10 секунд...", flush=True)
        await asyncio.sleep(10)

        print("[11] ТЕСТ ЗАВЕРШЕН", flush=True)

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        import traceback
        traceback.print_exc()
    finally:
        await browser_manager.close()
        print("[12] Браузер закрыт", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
