#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright Mouse Emulator - эмуляция человеческих движений в Playwright
Использует логику генерации путей из mouse_emulator для Playwright
"""

import asyncio
import random
from typing import Tuple, Optional, List
from playwright.async_api import Page

from src.utils.mouse_emulator import HumanMouseEmulator, Point


class PlaywrightMouseEmulator:
    """
    Эмулятор человеческих движений мыши для Playwright
    Использует те же алгоритмы генерации путей, что и HumanMouseEmulator
    """

    def __init__(self, page: Page):
        """
        Args:
            page: Playwright Page объект
        """
        self.page = page
        self.viewport_size = None
        # Создаем экземпляр базового эмулятора для использования его алгоритмов
        self._path_generator = HumanMouseEmulator()

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

    async def get_current_position(self) -> Tuple[float, float]:
        """Получает текущую позицию мыши в браузере"""
        pos = await self.page.evaluate("""
            () => {
                return { x: window.mouseX || 0, y: window.mouseY || 0 };
            }
        """)
        return pos.get('x', 0), pos.get('y', 0)

    async def move_to(
        self,
        x: float,
        y: float,
        duration: float = 0.5,
        curve_type: str = 'bezier'
    ):
        """
        Плавно перемещает мышь к указанной точке с человеческим движением

        Args:
            x: Целевая координата X
            y: Целевая координата Y
            duration: Длительность движения в секундах
            curve_type: Тип кривой ('bezier', 'natural', 'jittery')
        """
        start_x, start_y = await self.get_current_position()

        # Генерируем путь используя алгоритмы из HumanMouseEmulator
        if curve_type == 'bezier':
            points = self._path_generator._generate_bezier_path(start_x, start_y, x, y)
        elif curve_type == 'natural':
            points = self._path_generator._generate_natural_path(start_x, start_y, x, y)
        elif curve_type == 'jittery':
            points = self._path_generator._generate_jittery_path(start_x, start_y, x, y)
        else:
            points = self._path_generator._generate_bezier_path(start_x, start_y, x, y)

        # Вычисляем задержку между точками
        total_points = len(points)
        base_delay = duration / total_points

        # Перемещаемся по точкам
        for i, point in enumerate(points):
            progress = i / total_points
            speed_factor = self._path_generator._ease_in_out_quad(progress)
            delay = base_delay * (2 - speed_factor)

            jitter = random.uniform(-delay * 0.1, delay * 0.1)
            actual_delay = max(0.001, delay + jitter)

            await self.page.mouse.move(point.x, point.y)
            await asyncio.sleep(actual_delay)

    async def click(
        self,
        x: Optional[float] = None,
        y: Optional[float] = None,
        button: str = 'left',
        clicks: int = 1,
        interval: float = 0.1,
        move_duration: float = 0.5,
        curve_type: str = 'bezier'
    ):
        """
        Кликает с естественным движением

        Args:
            x, y: Координаты для клика (если None - кликает на текущей позиции)
            button: Кнопка мыши ('left', 'right', 'middle')
            clicks: Количество кликов
            interval: Интервал между кликами
            move_duration: Длительность движения к точке
            curve_type: Тип кривой движения
        """
        # Перемещаемся к точке клика
        if x is not None and y is not None:
            await self.move_to(x, y, duration=move_duration, curve_type=curve_type)
            await asyncio.sleep(random.uniform(0.05, 0.15))

        # Выполняем клики
        for i in range(clicks):
            if i > 0:
                # Небольшое смещение при повторных кликах
                current_x, current_y = await self.get_current_position()
                offset_x = random.uniform(-1, 1)
                offset_y = random.uniform(-1, 1)
                await self.page.mouse.move(current_x + offset_x, current_y + offset_y)

            # Клик с задержкой удержания
            await self.page.mouse.down(button=button)
            await asyncio.sleep(random.uniform(0.05, 0.12))
            await self.page.mouse.up(button=button)

            if i < clicks - 1:
                await asyncio.sleep(interval)

    async def click_element(
        self,
        selector: str,
        button: str = 'left',
        clicks: int = 1,
        move_duration: float = 0.5,
        curve_type: str = 'bezier',
        offset_x: float = 0,
        offset_y: float = 0
    ):
        """
        Кликает на элемент с естественным движением

        Args:
            selector: CSS селектор элемента
            button: Кнопка мыши
            clicks: Количество кликов
            move_duration: Длительность движения
            curve_type: Тип кривой
            offset_x, offset_y: Смещение от центра элемента
        """
        element = await self.page.query_selector(selector)
        if not element:
            raise ValueError(f"Элемент не найден: {selector}")

        box = await element.bounding_box()
        if not box:
            raise ValueError(f"Не удалось получить координаты элемента: {selector}")

        # Вычисляем координаты с небольшим случайным смещением
        target_x = box['x'] + box['width'] / 2 + offset_x + random.uniform(-5, 5)
        target_y = box['y'] + box['height'] / 2 + offset_y + random.uniform(-5, 5)

        await self.click(
            target_x, target_y,
            button=button,
            clicks=clicks,
            move_duration=move_duration,
            curve_type=curve_type
        )

    async def scroll(
        self,
        dx: float = 0,
        dy: float = -100,
        num_scrolls: int = 5,
        delay_between: float = 0.08
    ):
        """
        Скроллит с естественными паузами

        Args:
            dx: Горизонтальный скролл
            dy: Вертикальный скролл
            num_scrolls: Количество шагов
            delay_between: Задержка между шагами
        """
        for i in range(num_scrolls):
            scroll_amount = dy + random.uniform(-dy * 0.1, dy * 0.1)
            await self.page.mouse.wheel(dx, scroll_amount)

            delay = delay_between + random.uniform(-0.02, 0.02)
            await asyncio.sleep(max(0.01, delay))

    async def type_text(
        self,
        selector: str,
        text: str,
        min_delay: float = 0.05,
        max_delay: float = 0.2,
        mistake_probability: float = 0.02,
        move_to_field: bool = True,
        clear_first: bool = False
    ):
        """
        Печатает текст в поле как человек

        Args:
            selector: CSS селектор поля ввода
            text: Текст для ввода
            min_delay: Минимальная задержка между символами
            max_delay: Максимальная задержка между символами
            mistake_probability: Вероятность опечатки
            move_to_field: Перемещать ли мышь к полю перед печатью
            clear_first: Очистить поле перед вводом
        """
        # Перемещаемся к полю и кликаем
        if move_to_field:
            await self.click_element(selector)
        else:
            await self.page.click(selector)

        await asyncio.sleep(random.uniform(0.2, 0.5))

        # Очищаем поле если нужно
        if clear_first:
            await self.page.fill(selector, '')

        # Печатаем текст с опечатками
        for i, char in enumerate(text):
            # Иногда делаем опечатку
            if random.random() < mistake_probability and i < len(text) - 1:
                # Печатаем неправильный символ
                wrong_char = chr(ord(char) + random.choice([-1, 1]))
                await self.page.keyboard.type(wrong_char)
                await asyncio.sleep(random.uniform(0.1, 0.3))
                # Исправляем
                await self.page.keyboard.press('Backspace')
                await asyncio.sleep(random.uniform(0.05, 0.1))

            # Печатаем правильный символ
            await self.page.keyboard.type(char)

            # Случайная задержка
            delay = random.uniform(min_delay, max_delay)

            # Иногда делаем паузу
            if random.random() < 0.05:
                delay += random.uniform(0.3, 0.8)

            await asyncio.sleep(delay)

    async def random_movement(
        self,
        radius: int = 50,
        num_moves: int = 3,
        delay_between: float = 0.5
    ):
        """
        Делает случайные небольшие движения (имитация просмотра)

        Args:
            radius: Радиус движения
            num_moves: Количество движений
            delay_between: Задержка между движениями
        """
        current_x, current_y = await self.get_current_position()

        for _ in range(num_moves):
            offset_x = random.uniform(-radius, radius)
            offset_y = random.uniform(-radius, radius)

            target_x = current_x + offset_x
            target_y = current_y + offset_y

            await self.move_to(
                target_x, target_y,
                duration=random.uniform(0.3, 0.7),
                curve_type='natural'
            )

            await asyncio.sleep(random.uniform(
                delay_between * 0.5,
                delay_between * 1.5
            ))

    async def hover_element(
        self,
        selector: str,
        duration: float = 0.5,
        pause_after: float = 0.3
    ):
        """
        Наводит мышь на элемент с естественным движением

        Args:
            selector: CSS селектор
            duration: Длительность движения
            pause_after: Пауза после наведения
        """
        element = await self.page.query_selector(selector)
        if not element:
            raise ValueError(f"Элемент не найден: {selector}")

        box = await element.bounding_box()
        target_x = box['x'] + box['width'] / 2 + random.uniform(-5, 5)
        target_y = box['y'] + box['height'] / 2 + random.uniform(-5, 5)

        await self.move_to(target_x, target_y, duration=duration)
        await asyncio.sleep(pause_after)


class HumanBehavior:
    """
    Высокоуровневый класс для эмуляции человеческого поведения в Playwright
    """

    def __init__(self, page: Page):
        """
        Args:
            page: Playwright Page
        """
        self.page = page
        self.mouse = PlaywrightMouseEmulator(page)

    async def fill_form_field(
        self,
        selector: str,
        text: str,
        curve_type: str = 'natural'
    ):
        """
        Заполняет поле формы как человек

        Args:
            selector: CSS селектор поля
            text: Текст для ввода
            curve_type: Тип кривой движения мыши
        """
        # Перемещаемся к полю
        await self.mouse.hover_element(selector, duration=0.7)

        # Небольшая пауза перед кликом
        await asyncio.sleep(random.uniform(0.1, 0.3))

        # Кликаем
        await self.mouse.click_element(selector, curve_type=curve_type)

        # Печатаем
        await self.mouse.type_text(
            selector, text,
            move_to_field=False,
            mistake_probability=0.03
        )

    async def click_button(
        self,
        selector: str,
        curve_type: str = 'bezier',
        pause_before: float = 0.5
    ):
        """
        Кликает на кнопку как человек

        Args:
            selector: CSS селектор кнопки
            curve_type: Тип кривой
            pause_before: Пауза перед кликом
        """
        # Пауза (думаем)
        await asyncio.sleep(pause_before)

        # Наводим на кнопку
        await self.mouse.hover_element(selector, duration=0.6)

        # Небольшая пауза перед кликом
        await asyncio.sleep(random.uniform(0.15, 0.35))

        # Кликаем
        await self.mouse.click_element(selector, curve_type=curve_type)

    async def read_and_scroll(
        self,
        num_scrolls: int = 5,
        reading_time: float = 2.0
    ):
        """
        Имитирует чтение страницы со скроллингом

        Args:
            num_scrolls: Количество скроллов
            reading_time: Время "чтения" между скроллами
        """
        for i in range(num_scrolls):
            # "Читаем"
            await asyncio.sleep(random.uniform(
                reading_time * 0.7,
                reading_time * 1.3
            ))

            # Случайные движения глаз
            await self.mouse.random_movement(radius=40, num_moves=2)

            # Скроллим
            await self.mouse.scroll(
                dy=-random.randint(80, 150),
                num_scrolls=random.randint(3, 6)
            )


# Пример использования
async def example_usage():
    """Пример использования эмулятора"""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto("https://www.example.com")

        # Создаем эмулятор
        emulator = PlaywrightMouseEmulator(page)

        # Пример 1: Простое движение
        print("Движение мыши...")
        await emulator.move_to(300, 300, duration=1.0, curve_type='natural')

        await asyncio.sleep(1)

        # Пример 2: Клик
        print("Клик...")
        await emulator.click(500, 400, move_duration=0.7)

        await asyncio.sleep(1)

        # Пример 3: Скролл
        print("Скролл...")
        await emulator.scroll(dy=-100, num_scrolls=10)

        await asyncio.sleep(2)

        # Пример 4: Случайные движения
        print("Случайные движения...")
        await emulator.random_movement(radius=60, num_moves=5)

        print("\nГотово! Закрываем через 3 секунды...")
        await asyncio.sleep(3)
        await browser.close()


if __name__ == '__main__':
    asyncio.run(example_usage())
