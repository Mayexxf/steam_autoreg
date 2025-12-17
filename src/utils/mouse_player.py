#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mouse Player - воспроизводит записанные движения мыши в Playwright
"""

import asyncio
import json
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from playwright.async_api import Page

from .mouse_recorder import MouseEvent, load_recording


class MousePlayer:
    """
    Воспроизводит записанные движения мыши в браузере Playwright
    """

    def __init__(self, page: Page):
        """
        Args:
            page: Playwright Page объект
        """
        self.page = page
        self.viewport_size = None

    async def get_viewport_size(self) -> Tuple[int, int]:
        """Получает размер viewport браузера"""
        if not self.viewport_size:
            self.viewport_size = await self.page.evaluate("""
                () => {
                    return {
                        width: window.innerWidth,
                        height: window.innerHeight
                    };
                }
            """)
        return self.viewport_size['width'], self.viewport_size['height']

    def normalize_coordinates(
        self,
        x: int,
        y: int,
        original_screen: Tuple[int, int],
        target_viewport: Tuple[int, int]
    ) -> Tuple[float, float]:
        """
        Нормализует координаты с экрана на viewport браузера

        Args:
            x, y: Координаты на экране
            original_screen: Размер экрана при записи (width, height)
            target_viewport: Размер viewport браузера (width, height)

        Returns:
            Tuple[float, float]: Нормализованные координаты
        """
        # Пропорционально масштабируем координаты
        scale_x = target_viewport[0] / original_screen[0]
        scale_y = target_viewport[1] / original_screen[1]

        new_x = x * scale_x
        new_y = y * scale_y

        # Ограничиваем координаты viewport'ом
        new_x = max(0, min(new_x, target_viewport[0] - 1))
        new_y = max(0, min(new_y, target_viewport[1] - 1))

        return new_x, new_y

    async def play_events(
        self,
        events: List[MouseEvent],
        speed_multiplier: float = 1.0,
        original_screen_size: Optional[Tuple[int, int]] = None
    ):
        """
        Воспроизводит события мыши

        Args:
            events: Список событий для воспроизведения
            speed_multiplier: Множитель скорости (1.0 = нормально, 2.0 = 2x быстрее)
            original_screen_size: Размер экрана при записи (для нормализации координат)
        """
        if not events:
            print("[MOUSE PLAYER] Нет событий для воспроизведения")
            return

        # Получаем размер viewport
        viewport = await self.get_viewport_size()

        # Если не указан размер экрана - используем максимальные координаты из записи
        if not original_screen_size:
            max_x = max(e.x for e in events)
            max_y = max(e.y for e in events)
            original_screen_size = (max_x, max_y)

        print(f"[MOUSE PLAYER] 🎬 Начало воспроизведения")
        print(f"[MOUSE PLAYER] События: {len(events)}")
        print(f"[MOUSE PLAYER] Скорость: {speed_multiplier}x")
        print(f"[MOUSE PLAYER] Нормализация: {original_screen_size} -> {viewport}")

        last_timestamp = 0
        moves_count = 0
        clicks_count = 0
        scrolls_count = 0

        for i, event in enumerate(events):
            # Вычисляем задержку между событиями
            delay = (event.timestamp - last_timestamp) / speed_multiplier
            if delay > 0:
                await asyncio.sleep(delay)

            # Нормализуем координаты
            x, y = self.normalize_coordinates(
                event.x, event.y,
                original_screen_size,
                viewport
            )

            try:
                if event.event_type == 'move':
                    await self.page.mouse.move(x, y)
                    moves_count += 1

                elif event.event_type == 'click':
                    # Сначала двигаем к точке клика
                    await self.page.mouse.move(x, y)

                    # Определяем кнопку
                    button = event.button or 'left'
                    await self.page.mouse.click(x, y, button=button)
                    clicks_count += 1

                    if i % 10 == 0:  # Логируем каждый 10-й клик
                        print(f"[MOUSE PLAYER] Клик #{clicks_count} в ({x:.0f}, {y:.0f})")

                elif event.event_type == 'scroll':
                    # Playwright использует delta в пикселях
                    await self.page.mouse.wheel(
                        event.scroll_dx * 10,
                        event.scroll_dy * 10
                    )
                    scrolls_count += 1

            except Exception as e:
                print(f"[MOUSE PLAYER] Ошибка при событии {i}: {e}")

            last_timestamp = event.timestamp

        print(f"\n[MOUSE PLAYER] ✅ Воспроизведение завершено!")
        print(f"[MOUSE PLAYER] Движений: {moves_count}")
        print(f"[MOUSE PLAYER] Кликов: {clicks_count}")
        print(f"[MOUSE PLAYER] Скроллов: {scrolls_count}")

    async def play_from_file(
        self,
        filepath: str,
        speed_multiplier: float = 1.0,
        original_screen_size: Optional[Tuple[int, int]] = None
    ):
        """
        Воспроизводит движения из файла

        Args:
            filepath: Путь к файлу с записью
            speed_multiplier: Множитель скорости
            original_screen_size: Размер экрана при записи
        """
        events = load_recording(filepath)
        await self.play_events(events, speed_multiplier, original_screen_size)

    async def move_to_element_humanlike(
        self,
        selector: str,
        recording_file: Optional[str] = None
    ):
        """
        Перемещает мышь к элементу используя человеческие движения

        Args:
            selector: CSS селектор элемента
            recording_file: Путь к файлу с записью движений (опционально)
        """
        # Получаем позицию элемента
        element = await self.page.query_selector(selector)
        if not element:
            raise ValueError(f"Элемент не найден: {selector}")

        box = await element.bounding_box()
        target_x = box['x'] + box['width'] / 2
        target_y = box['y'] + box['height'] / 2

        # Получаем текущую позицию мыши
        current_pos = await self.page.evaluate("""
            () => {
                return { x: window.mouseX || 0, y: window.mouseY || 0 };
            }
        """)

        start_x = current_pos['x']
        start_y = current_pos['y']

        # Если есть запись - используем её паттерн движения
        if recording_file and Path(recording_file).exists():
            events = load_recording(recording_file)
            # Берем только движения
            move_events = [e for e in events if e.event_type == 'move']

            if move_events:
                # Масштабируем движения к нашему пути
                for event in move_events[:30]:  # Максимум 30 точек
                    # Интерполируем между start и target
                    progress = event.timestamp / move_events[-1].timestamp
                    x = start_x + (target_x - start_x) * progress
                    y = start_y + (target_y - start_y) * progress
                    await self.page.mouse.move(x, y)
                    await asyncio.sleep(0.01)
                return

        # Если нет записи - используем bezier кривую
        await self._move_bezier(start_x, start_y, target_x, target_y)

    async def _move_bezier(
        self,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        steps: int = 30
    ):
        """
        Перемещение по кривой Безье (имитация человеческого движения)
        """
        import random

        # Создаем контрольные точки для кривой Безье
        ctrl1_x = start_x + (end_x - start_x) * 0.3 + random.uniform(-50, 50)
        ctrl1_y = start_y + (end_y - start_y) * 0.3 + random.uniform(-50, 50)
        ctrl2_x = start_x + (end_x - start_x) * 0.7 + random.uniform(-50, 50)
        ctrl2_y = start_y + (end_y - start_y) * 0.7 + random.uniform(-50, 50)

        for i in range(steps + 1):
            t = i / steps

            # Кубическая кривая Безье
            x = (
                (1-t)**3 * start_x +
                3 * (1-t)**2 * t * ctrl1_x +
                3 * (1-t) * t**2 * ctrl2_x +
                t**3 * end_x
            )
            y = (
                (1-t)**3 * start_y +
                3 * (1-t)**2 * t * ctrl1_y +
                3 * (1-t) * t**2 * ctrl2_y +
                t**3 * end_y
            )

            await self.page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.005, 0.015))


class HumanBehavior:
    """
    Высокоуровневый класс для человеческого поведения в браузере
    """

    def __init__(self, page: Page, recording_file: Optional[str] = None):
        """
        Args:
            page: Playwright Page
            recording_file: Путь к файлу с записью движений мыши
        """
        self.page = page
        self.player = MousePlayer(page)
        self.recording_file = recording_file

    async def type_like_human(self, selector: str, text: str):
        """
        Печатает текст как человек (с задержками и опечатками)

        Args:
            selector: CSS селектор поля ввода
            text: Текст для ввода
        """
        import random

        # Перемещаемся к полю
        if self.recording_file:
            await self.player.move_to_element_humanlike(selector, self.recording_file)
        else:
            element = await self.page.query_selector(selector)
            box = await element.bounding_box()
            await self.player._move_bezier(
                0, 0,
                box['x'] + box['width']/2,
                box['y'] + box['height']/2
            )

        # Кликаем
        await self.page.click(selector)
        await asyncio.sleep(random.uniform(0.2, 0.5))

        # Печатаем с задержками
        for char in text:
            await self.page.keyboard.type(char)
            # Случайная задержка между символами (50-200ms)
            await asyncio.sleep(random.uniform(0.05, 0.2))

            # Иногда делаем паузу (5% вероятность)
            if random.random() < 0.05:
                await asyncio.sleep(random.uniform(0.3, 0.8))

    async def click_like_human(self, selector: str):
        """
        Кликает как человек (с движением мыши)

        Args:
            selector: CSS селектор элемента
        """
        import random

        # Перемещаемся к элементу
        if self.recording_file:
            await self.player.move_to_element_humanlike(selector, self.recording_file)
        else:
            element = await self.page.query_selector(selector)
            box = await element.bounding_box()
            await self.player._move_bezier(
                0, 0,
                box['x'] + box['width']/2,
                box['y'] + box['height']/2
            )

        # Небольшая пауза перед кликом
        await asyncio.sleep(random.uniform(0.1, 0.3))

        # Кликаем
        await self.page.click(selector)

    async def scroll_like_human(self, direction: str = 'down', amount: int = 300):
        """
        Скроллит как человек

        Args:
            direction: 'up' или 'down'
            amount: Количество пикселей для скролла
        """
        import random

        scroll_delta = amount if direction == 'down' else -amount

        # Разбиваем скролл на несколько частей
        parts = random.randint(3, 6)
        for _ in range(parts):
            delta = scroll_delta / parts
            await self.page.mouse.wheel(0, delta)
            await asyncio.sleep(random.uniform(0.05, 0.15))
