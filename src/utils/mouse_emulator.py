#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mouse Emulator - эмуляция человеческих движений мыши на уровне ОС
Использует pynput для реального перемещения мыши без предварительной записи
"""

import time
import random
import math
from typing import Tuple, Optional, List
from dataclasses import dataclass

from playwright.async_api import Page


@dataclass
class Point:
    """Точка с координатами"""
    x: float
    y: float


class HumanMouseEmulator:
    """
    Эмулятор человеческих движений мыши на уровне ОС
    Генерирует естественные движения без предварительной записи
    """

    def __init__(self):
        """Инициализация эмулятора"""
        try:
            from pynput.mouse import Controller, Button
            from pynput.keyboard import Controller as KeyboardController
        except ImportError:
            raise ImportError(
                "pynput не установлен. Установите: pip install pynput"
            )

        self.mouse = Controller()
        self.keyboard = KeyboardController()
        self.Button = Button

    def get_current_position(self) -> Tuple[int, int]:
        """Получает текущую позицию мыши"""
        pos = self.mouse.position
        return pos[0], pos[1]

    async def get_random_point_in_element(page: Page, selector: str, padding: float = 0.2) -> Optional[
        Tuple[float, float]]:
        """
        Возвращает случайную точку внутри элемента (не центр)
        padding — отступ от краёв (0.2 = 20% от краёв)
        """
        element = await page.query_selector(selector)
        if not element:
            return None

        box = await element.bounding_box()
        if not box:
            return None

        left = box['x'] + box['width'] * padding
        right = box['x'] + box['width'] * (1 - padding)
        top = box['y'] + box['height'] * padding
        bottom = box['y'] + box['height'] * (1 - padding)

        x = random.uniform(left, right)
        y = random.uniform(top, bottom)

        return x, y

    def move_to(
        self,
        x: int,
        y: int,
        duration: float = 0.5,
        curve_type: str = 'bezier'
    ):
        """
        Плавно перемещает мышь к указанной точке с человеческим движением

        Args:
            x: Целевая координата X
            y: Целевая координата Y
            duration: Длительность движения в секундах (0.3-2.0 рекомендуется)
            curve_type: Тип кривой ('bezier', 'natural', 'jittery')
        """
        start_x, start_y = self.get_current_position()

        # Генерируем путь в зависимости от типа кривой
        if curve_type == 'bezier':
            points = self._generate_bezier_path(start_x, start_y, x, y)
        elif curve_type == 'natural':
            points = self._generate_natural_path(start_x, start_y, x, y)
        elif curve_type == 'jittery':
            points = self._generate_jittery_path(start_x, start_y, x, y)
        else:
            points = self._generate_bezier_path(start_x, start_y, x, y)

        # Вычисляем задержку между точками
        total_points = len(points)
        base_delay = duration / total_points

        # Перемещаемся по точкам с вариациями скорости
        for i, point in enumerate(points):
            # Добавляем вариацию скорости (быстрее в середине, медленнее в начале/конце)
            progress = i / total_points
            speed_factor = self._ease_in_out_quad(progress)
            delay = base_delay * (2 - speed_factor)  # Инвертируем для замедления на концах

            # Добавляем случайную микрозадержку для реалистичности
            jitter = random.uniform(-delay * 0.1, delay * 0.1)
            actual_delay = max(0.001, delay + jitter)

            self.mouse.position = (int(point.x), int(point.y))
            time.sleep(actual_delay)

    def _generate_bezier_path(
        self,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        num_points: int = 50
    ) -> List[Point]:
        """
        Генерирует путь по кубической кривой Безье

        Args:
            start_x, start_y: Начальная точка
            end_x, end_y: Конечная точка
            num_points: Количество промежуточных точек

        Returns:
            Список точек пути
        """
        points = []

        # Создаем случайные контрольные точки для естественного изгиба
        distance = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)

        # Контрольные точки со случайным отклонением
        ctrl1_offset = random.uniform(0.2, 0.4)
        ctrl2_offset = random.uniform(0.6, 0.8)

        # Случайное отклонение перпендикулярно направлению движения
        perpendicular_offset = distance * random.uniform(-0.2, 0.2)

        ctrl1_x = start_x + (end_x - start_x) * ctrl1_offset
        ctrl1_y = start_y + (end_y - start_y) * ctrl1_offset + perpendicular_offset

        ctrl2_x = start_x + (end_x - start_x) * ctrl2_offset
        ctrl2_y = start_y + (end_y - start_y) * ctrl2_offset - perpendicular_offset * 0.5

        # Генерируем точки по кривой Безье
        for i in range(num_points + 1):
            t = i / num_points

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

            # Добавляем микродрожание для реалистичности
            if 0 < i < num_points:  # Не трясем начало и конец
                x += random.uniform(-1, 1)
                y += random.uniform(-1, 1)

            points.append(Point(x, y))

        return points

    def _generate_natural_path(
        self,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        num_points: int = 60
    ) -> List[Point]:
        """
        Генерирует более естественный путь с несколькими изгибами
        Имитирует коррекцию траектории как у человека
        """
        points = []

        # Создаем промежуточную точку для коррекции траектории
        mid_x = (start_x + end_x) / 2 + random.uniform(-30, 30)
        mid_y = (start_y + end_y) / 2 + random.uniform(-30, 30)

        # Первая половина пути
        first_half = self._generate_bezier_path(
            start_x, start_y, mid_x, mid_y, num_points // 2
        )

        # Вторая половина с коррекцией
        second_half = self._generate_bezier_path(
            mid_x, mid_y, end_x, end_y, num_points // 2
        )

        points.extend(first_half)
        points.extend(second_half)

        return points

    def _generate_jittery_path(
        self,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        num_points: int = 70
    ) -> List[Point]:
        """
        Генерирует путь с дрожанием (как при быстром движении или волнении)
        """
        # Базовый путь Безье
        base_points = self._generate_bezier_path(
            start_x, start_y, end_x, end_y, num_points
        )

        # Добавляем больше дрожания
        jittery_points = []
        for point in base_points:
            jitter_x = random.uniform(-2, 2)
            jitter_y = random.uniform(-2, 2)
            jittery_points.append(Point(point.x + jitter_x, point.y + jitter_y))

        return jittery_points

    def _ease_in_out_quad(self, t: float) -> float:
        """
        Функция плавности (ease-in-out)
        Медленное начало, быстрая середина, медленный конец
        """
        if t < 0.5:
            return 2 * t * t
        else:
            return 1 - (-2 * t + 2) ** 2 / 2

    async def click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = 'left',
        clicks: int = 1,
        interval: float = 0.1,
        move_duration: float = 0.5
    ):
        """
        Кликает мышью с естественным движением

        Args:
            x, y: Координаты для клика (если None - кликает на текущей позиции)
            button: Кнопка мыши ('left', 'right', 'middle')
            clicks: Количество кликов (1 = одиночный, 2 = двойной)
            interval: Интервал между кликами при множественном клике
            move_duration: Длительность движения к точке клика
        """
        # Перемещаемся к точке клика
        if x is not None and y is not None:
            self.move_to(x, y, duration=move_duration)
            # Небольшая пауза перед кликом
            time.sleep(random.uniform(0.05, 0.15))

        # Определяем кнопку
        button_map = {
            'left': self.Button.left,
            'right': self.Button.right,
            'middle': self.Button.middle
        }
        mouse_button = button_map.get(button, self.Button.left)

        # Выполняем клики
        for i in range(clicks):
            # Небольшое случайное смещение при каждом клике (1-2 пикселя)
            if i > 0:
                current_x, current_y = self.get_current_position()
                offset_x = random.uniform(-1, 1)
                offset_y = random.uniform(-1, 1)
                self.mouse.position = (current_x + offset_x, current_y + offset_y)

            # Клик с реалистичными задержками
            self.mouse.press(mouse_button)
            time.sleep(random.uniform(0.05, 0.12))  # Время удержания кнопки
            self.mouse.release(mouse_button)

            if i < clicks - 1:
                time.sleep(interval)

    def scroll(
        self,
        dx: int = 0,
        dy: int = -3,
        num_scrolls: int = 5,
        delay_between: float = 0.08
    ):
        """
        Скроллит с естественными паузами

        Args:
            dx: Горизонтальный скролл (обычно 0)
            dy: Вертикальный скролл (положительный = вниз, отрицательный = вверх)
            num_scrolls: Количество шагов скролла
            delay_between: Задержка между шагами скролла
        """
        for i in range(num_scrolls):
            # Добавляем вариацию в величину скролла
            scroll_amount = dy + random.uniform(-0.5, 0.5)
            self.mouse.scroll(dx, scroll_amount)

            # Вариация задержки
            delay = delay_between + random.uniform(-0.02, 0.02)
            time.sleep(max(0.01, delay))

    def drag_to(
        self,
        x: int,
        y: int,
        button: str = 'left',
        duration: float = 0.7
    ):
        """
        Перетаскивает мышь (drag) к указанной точке

        Args:
            x, y: Целевые координаты
            button: Кнопка для удержания
            duration: Длительность перетаскивания
        """
        # Зажимаем кнопку
        button_map = {
            'left': self.Button.left,
            'right': self.Button.right,
            'middle': self.Button.middle
        }
        mouse_button = button_map.get(button, self.Button.left)

        self.mouse.press(mouse_button)
        time.sleep(random.uniform(0.05, 0.1))

        # Перемещаемся с зажатой кнопкой
        self.move_to(x, y, duration=duration)

        # Отпускаем кнопку
        time.sleep(random.uniform(0.05, 0.1))
        self.mouse.release(mouse_button)

    def type_text(
        self,
        text: str,
        min_delay: float = 0.05,
        max_delay: float = 0.2,
        mistake_probability: float = 0.02
    ):
        """
        Печатает текст как человек с задержками и опечатками

        Args:
            text: Текст для ввода
            min_delay: Минимальная задержка между символами
            max_delay: Максимальная задержка между символами
            mistake_probability: Вероятность опечатки (0.0-1.0)
        """
        for i, char in enumerate(text):
            # Иногда делаем опечатку
            if random.random() < mistake_probability and i < len(text) - 1:
                # Печатаем случайный соседний символ
                wrong_char = chr(ord(char) + random.choice([-1, 1]))
                self.keyboard.type(wrong_char)
                time.sleep(random.uniform(0.1, 0.3))
                # Исправляем (backspace + правильный символ)
                self.keyboard.press('\b')
                time.sleep(random.uniform(0.05, 0.1))

            # Печатаем правильный символ
            self.keyboard.type(char)

            # Случайная задержка
            delay = random.uniform(min_delay, max_delay)

            # Иногда делаем паузу (как будто думаем)
            if random.random() < 0.05:
                delay += random.uniform(0.3, 0.8)

            time.sleep(delay)

    def random_movement(
        self,
        radius: int = 50,
        num_moves: int = 3,
        delay_between: float = 0.5
    ):
        """
        Делает случайные небольшие движения мышью (имитация чтения/просмотра)

        Args:
            radius: Радиус случайного движения в пикселях
            num_moves: Количество движений
            delay_between: Задержка между движениями
        """
        current_x, current_y = self.get_current_position()

        for _ in range(num_moves):
            # Случайное смещение
            offset_x = random.uniform(-radius, radius)
            offset_y = random.uniform(-radius, radius)

            target_x = current_x + offset_x
            target_y = current_y + offset_y

            # Двигаемся
            self.move_to(
                int(target_x),
                int(target_y),
                duration=random.uniform(0.3, 0.7)
            )

            # Пауза
            time.sleep(random.uniform(delay_between * 0.5, delay_between * 1.5))


class MouseEmulatorExample:
    """Примеры использования эмулятора мыши"""

    @staticmethod
    def example_basic_movement():
        """Пример базового движения"""
        print("=== Пример 1: Базовое движение ===")
        emulator = HumanMouseEmulator()

        print("Текущая позиция:", emulator.get_current_position())
        print("Перемещение к (500, 500)...")

        emulator.move_to(500, 500, duration=1.0)
        print("Новая позиция:", emulator.get_current_position())

    @staticmethod
    def example_click():
        """Пример клика"""
        print("\n=== Пример 2: Клик с движением ===")
        emulator = HumanMouseEmulator()

        print("Клик в позиции (800, 400)...")
        emulator.click(800, 400)

        print("Двойной клик в позиции (900, 500)...")
        time.sleep(1)
        emulator.click(900, 500, clicks=2)

    @staticmethod
    def example_scroll():
        """Пример скролла"""
        print("\n=== Пример 3: Скролл ===")
        emulator = HumanMouseEmulator()

        print("Скролл вниз...")
        emulator.scroll(dy=-3, num_scrolls=10)

        time.sleep(1)
        print("Скролл вверх...")
        emulator.scroll(dy=3, num_scrolls=10)

    @staticmethod
    def example_typing():
        """Пример печати"""
        print("\n=== Пример 4: Печать текста ===")
        print("Откройте текстовый редактор и установите курсор!")
        input("Нажмите Enter когда готовы...")

        emulator = HumanMouseEmulator()
        text = "Hello, this is a test of human-like typing!"

        print(f"Печатаем: {text}")
        emulator.type_text(text, mistake_probability=0.05)
        print("Готово!")

    @staticmethod
    def example_natural_behavior():
        """Пример естественного поведения"""
        print("\n=== Пример 5: Естественное поведение ===")
        emulator = HumanMouseEmulator()

        print("1. Перемещение к элементу...")
        emulator.move_to(600, 300, duration=0.8, curve_type='natural')

        time.sleep(0.5)
        print("2. Небольшие случайные движения (просмотр)...")
        emulator.random_movement(radius=30, num_moves=3)

        time.sleep(0.5)
        print("3. Клик...")
        emulator.click()

        time.sleep(0.5)
        print("4. Скролл для чтения...")
        emulator.scroll(dy=-2, num_scrolls=15, delay_between=0.1)


if __name__ == '__main__':
    import sys

    print("="*70)
    print("HUMAN MOUSE EMULATOR - Эмуляция человеческих движений мыши")
    print("="*70)

    print("\nВыберите пример:")
    print("1. Базовое движение")
    print("2. Клик")
    print("3. Скролл")
    print("4. Печать текста")
    print("5. Естественное поведение (комбинация)")
    print("6. Все примеры по очереди")

    choice = input("\nВыбор (1-6): ").strip()

    examples = MouseEmulatorExample()

    if choice == '1':
        examples.example_basic_movement()
    elif choice == '2':
        examples.example_click()
    elif choice == '3':
        examples.example_scroll()
    elif choice == '4':
        examples.example_typing()
    elif choice == '5':
        examples.example_natural_behavior()
    elif choice == '6':
        print("\nВыполнение всех примеров...\n")
        examples.example_basic_movement()
        time.sleep(2)
        examples.example_click()
        time.sleep(2)
        examples.example_scroll()
        time.sleep(2)
        examples.example_natural_behavior()
        print("\n\nВсе примеры выполнены!")
    else:
        print("Неверный выбор")
        sys.exit(1)

    print("\n[DONE] Демонстрация завершена!")
