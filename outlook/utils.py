#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилиты для человекоподобного поведения
- Задержки
- Движение мыши по кривой Безье
- Человекоподобный ввод текста
"""

import random
import asyncio
from typing import Tuple, List, Optional

from playwright.async_api import Page, Locator

from src.utils.mouse_emulator import HumanMouseEmulator
from .config import TYPING_DELAY, CLICK_DELAY


async def human_delay(min_ms: int = 200, max_ms: int = 500):
    """Случайная задержка как у человека"""
    delay = random.uniform(min_ms, max_ms) / 1000
    print(f"\n[Delay] Задержка {delay}")
    await asyncio.sleep(delay)


def bezier_curve(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
    """Вычисляет точку на кривой Безье"""
    return (1-t)**3 * p0 + 3*(1-t)**2 * t * p1 + 3*(1-t) * t**2 * p2 + t**3 * p3


def generate_bezier_path(start: Tuple[float, float], end: Tuple[float, float],
                         steps: int = 30) -> List[Tuple[float, float]]:
    """Генерирует путь движения мыши по кривой Безье"""
    ctrl1_x = start[0] + (end[0] - start[0]) * random.uniform(0.2, 0.4) + random.uniform(-50, 50)
    ctrl1_y = start[1] + (end[1] - start[1]) * random.uniform(0.1, 0.3) + random.uniform(-30, 30)
    ctrl2_x = start[0] + (end[0] - start[0]) * random.uniform(0.6, 0.8) + random.uniform(-50, 50)
    ctrl2_y = start[1] + (end[1] - start[1]) * random.uniform(0.7, 0.9) + random.uniform(-30, 30)

    path = []
    for i in range(steps + 1):
        t = i / steps
        t = t * t * (3 - 2 * t)  # Smoothstep

        x = bezier_curve(t, start[0], ctrl1_x, ctrl2_x, end[0])
        y = bezier_curve(t, start[1], ctrl1_y, ctrl2_y, end[1])

        # Микро-шум (тремор руки)
        x += random.uniform(-1, 1)
        y += random.uniform(-1, 1)

        path.append((x, y))

    return path


async def smooth_mouse_move(page: Page, to_x: float, to_y: float,
                            from_pos: Tuple[float, float] = None):
    """Плавное движение мыши по кривой Безье"""
    if from_pos is None:
        from_pos = await page.evaluate("""() => {
            return {x: window.__mouseX || 100, y: window.__mouseY || 100};
        }""")
        from_pos = (from_pos.get('x', 100), from_pos.get('y', 100))

    path = generate_bezier_path(from_pos, (to_x, to_y), steps=random.randint(20, 40))

    for x, y in path:
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.005, 0.015))

    await page.evaluate(f"window.__mouseX = {to_x}; window.__mouseY = {to_y};")


async def human_type(page: Page, selector: Locator, text: str, typo_rate: float = 0.05):
    """Печатает текст человекоподобно с возможными опечатками"""

    element = await selector.wait_for(state="visible", timeout=15000)
    if not element:
        raise Exception(f"Элемент не найден: {selector}")

    await human_click(page, selector)
    await human_delay(150, 350)

    for i, char in enumerate(text):
        # Случайная опечатка
        if random.random() < typo_rate and char.isalpha():
            wrong_char = random.choice('qwertyuiopasdfghjklzxcvbnm')
            await page.keyboard.type(wrong_char, delay=random.randint(30, 80))

            # Вариативность: иногда исправляем, иногда нет
            should_fix = random.random() < 0.85  # 85% исправляем, 15% оставляем

            if should_fix:
                # Иногда пауза перед исправлением (заметили ошибку)
                if random.random() < 0.3:
                    await human_delay(150, 350)
                else:
                    await human_delay(80, 200)

                # Иногда несколько backspace (как будто перестарались)
                backspace_count = 1
                if random.random() < 0.15:
                    backspace_count = random.randint(2, 3)

                for _ in range(backspace_count):
                    await page.keyboard.press('Backspace')
                    await human_delay(40, 100)

                # Если удалили лишнее - восстанавливаем
                if backspace_count > 1:
                    await human_delay(100, 200)
                    # Перепечатываем удаленные символы
                    for _ in range(backspace_count - 1):
                        if i > 0:
                            await page.keyboard.type(text[i-1], delay=random.randint(50, 120))

        # Печатаем символ
        delay = random.randint(TYPING_DELAY[0], TYPING_DELAY[1])
        await page.keyboard.type(char, delay=delay)

        # Иногда пауза (обдумывание)
        if random.random() < 0.05:  # Увеличили с 0.03 до 0.05
            await human_delay(200, 600)

    await human_delay(80, 200)


async def human_click(page: Page, locator: Locator):
    """
        Максимально человекоподобный клик в Playwright
        Проходит behavioral detection Microsoft, Google, Cloudflare, Steam
        """
    # 1. Ждём видимости и скроллим если нужно
    await locator.wait_for(state="visible", timeout=15000)
    await locator.scroll_into_view_if_needed()

    # 2. Предклик задержка (человек смотрит перед кликом)
    await human_delay(400, 1400)

    # 3. Получаем координаты элемента
    box = await locator.bounding_box()
    if not box:
        raise Exception("Не удалось получить bounding_box")

    # 4. Кликаем НЕ в центр, а в случайной точке внутри (20-80%)
    offset_x = random.uniform(box['width'] * 0.2, box['width'] * 0.8)
    offset_y = random.uniform(box['height'] * 0.2, box['height'] * 0.8)

    target_x = box['x'] + offset_x
    target_y = box['y'] + offset_y

    # 5. Плавное движение мыши к точке (с overshoot для ультра-реализма — опционально)
    # Просто:
    await human_mouse_move(page, target_x, target_y)

    # Или с лёгким overshoot (человек часто чуть промахивается):
    # overshoot_x = target_x + random.uniform(-15, 15)
    # overshoot_y = target_y + random.uniform(-15, 15)
    # await human_mouse_move(page, overshoot_x, overshoot_y)
    # await human_delay(50, 150)
    # await human_mouse_move(page, target_x, target_y)

    # 6. Задержка перед кликом
    await human_delay(80, 280)

    # 7. Клик
    await page.mouse.down()  # нажатие
    await human_delay(50, 150)
    await page.mouse.up()  # отпускание (более реалистично, чем click())

    # 8. Пост-клик задержка
    await human_delay(500, 1800)


async def human_mouse_move(page: Page, target_x: float, target_y: float):
    """Плавное реалистичное движение мыши внутри браузера"""
    steps = random.randint(18, 35)  # чем больше — тем плавнее
    await page.mouse.move(target_x, target_y, steps=steps)


async def random_mouse_movement(page: Page, movements: int = 2):
    """Случайные движения мыши"""
    viewport = page.viewport_size
    if not viewport:
        return

    for _ in range(movements):
        x = random.randint(100, viewport['width'] - 100)
        y = random.randint(100, viewport['height'] - 100)
        await smooth_mouse_move(page, x, y)
        await human_delay(80, 250)

async def generate_username(first: str, last: str) -> str:
    first = first.lower()
    last = last.lower()

    # Список возможных шаблонов
    patterns = [
        # 1. Классика: имяфамилия1234
        lambda: f"{first}{last}{random.randint(1000, 9999)}",

        # 2. Имя.фамилия1234
        lambda: f"{first}.{last}{random.randint(1000, 9999)}",

        # 3. Имя_фамилия1234
        lambda: f"{first}_{last}{random.randint(100, 999)}",

        # 5. Фамилия + имя + короткий номер
        lambda: f"{last}{first}{random.randint(10, 999)}",

        # 6. Имя + случайный короткий суффикс (без фамилии)
        lambda: f"{first}{random.choice(['_ua', '_kyiv', 'pro', 'top', 'best', 'official'])}{random.randint(10, 999)}",

        # 7. Сокращённое имя (первые 3 буквы) + фамилия + номер
        lambda: f"{first[:3]}{last}{random.randint(100, 9999)}",

        # 8. Фамилия + две цифры в начале + имя
        lambda: f"{random.randint(10, 99)}{last}{first}",

        # 9. Имя + фамилия + случайная буква + номер
        lambda: f"{first}{last}{random.choice('abcdefghijklmnopqrstuvwxyz')}{random.randint(10, 999)}",

        # 10. Полностью с разделителем и коротким годом
        lambda: f"{first}-{last[:6]}{random.randint(22, 29)}",
    ]

    # Случайно выбираем один из шаблонов
    chosen_pattern = random.choice(patterns)
    return chosen_pattern()


