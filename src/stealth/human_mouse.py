#!/usr/bin/env python3
"""
Продвинутая имитация движений человеческой мыши.

Особенности:
1. Кривая Безье для плавных траекторий
2. Микро-дрожание (human jitter)
3. Overshooting (перелет цели и коррекция)
4. Замедление у цели
5. Случайные отклонения от прямой
"""

import random
import math
import time


class HumanMouse:
    """
    Имитация человеческих движений мыши.
    """
    
    def __init__(self, page):
        """
        Args:
            page: Playwright page object
        """
        self.page = page
    
    def _bezier_curve(self, start, end, control_points, steps=20):
        """
        Генерирует точки кривой Безье для плавного движения.
        
        Args:
            start: (x, y) - начальная точка
            end: (x, y) - конечная точка
            control_points: [(x, y), ...] - контрольные точки
            steps: Количество шагов
        
        Returns:
            List of (x, y) points
        """
        points = []
        
        # Cubic Bezier (4 точки: start, control1, control2, end)
        if len(control_points) == 2:
            for i in range(steps + 1):
                t = i / steps
                
                # Кубическая кривая Безье
                x = (
                    (1-t)**3 * start[0] +
                    3*(1-t)**2*t * control_points[0][0] +
                    3*(1-t)*t**2 * control_points[1][0] +
                    t**3 * end[0]
                )
                
                y = (
                    (1-t)**3 * start[1] +
                    3*(1-t)**2*t * control_points[0][1] +
                    3*(1-t)*t**2 * control_points[1][1] +
                    t**3 * end[1]
                )
                
                points.append((x, y))
        
        return points
    
    def _add_jitter(self, x, y, jitter_amount=2.0):
        """
        Добавляет микро-дрожание (как у человеческой руки).
        
        Args:
            x, y: Исходные координаты
            jitter_amount: Амплитуда дрожания (пиксели)
        
        Returns:
            (x, y) с добавленным дрожанием
        """
        jitter_x = random.uniform(-jitter_amount, jitter_amount)
        jitter_y = random.uniform(-jitter_amount, jitter_amount)
        
        return x + jitter_x, y + jitter_y
    
    def _generate_control_points(self, start, end, curvature='medium'):
        """
        Генерирует контрольные точки для кривой Безье.
        
        Args:
            start: (x, y) - начальная точка
            end: (x, y) - конечная точка
            curvature: 'low', 'medium', 'high' - степень искривления
        
        Returns:
            [(x1, y1), (x2, y2)] - 2 контрольные точки
        """
        start_x, start_y = start
        end_x, end_y = end
        
        # Расстояние между точками
        distance = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        
        # Степень отклонения
        curvature_factor = {
            'low': 0.1,
            'medium': 0.25,
            'high': 0.5
        }.get(curvature, 0.25)
        
        deviation = distance * curvature_factor
        
        # Первая контрольная точка (1/3 пути)
        c1_x = start_x + (end_x - start_x) * 0.33
        c1_y = start_y + (end_y - start_y) * 0.33
        
        # Отклонение перпендикулярно направлению движения
        angle = math.atan2(end_y - start_y, end_x - start_x)
        perpendicular = angle + math.pi / 2
        
        c1_x += math.cos(perpendicular) * random.uniform(-deviation, deviation)
        c1_y += math.sin(perpendicular) * random.uniform(-deviation, deviation)
        
        # Вторая контрольная точка (2/3 пути)
        c2_x = start_x + (end_x - start_x) * 0.67
        c2_y = start_y + (end_y - start_y) * 0.67
        
        c2_x += math.cos(perpendicular) * random.uniform(-deviation, deviation)
        c2_y += math.sin(perpendicular) * random.uniform(-deviation, deviation)
        
        return [(c1_x, c1_y), (c2_x, c2_y)]
    
    def _get_movement_speed(self, distance):
        """
        Вычисляет скорость движения мыши в зависимости от расстояния.
        
        УСКОРЕННАЯ ВЕРСИЯ: Меньше шагов = быстрее движения
        
        Args:
            distance: Расстояние в пикселях
        
        Returns:
            Количество шагов для движения
        """
        # УСКОРЕНО: Меньше шагов для всех расстояний
        if distance < 100:
            return random.randint(5, 10)  # Было 8-15
        elif distance < 300:
            return random.randint(8, 15)   # Было 15-25
        else:
            return random.randint(12, 20)  # Было 25-40
    
    def move_to(self, target_x, target_y, duration=None):
        """
        Перемещает мышь к цели человекоподобно.
        
        Args:
            target_x, target_y: Целевые координаты
            duration: Время движения (сек), если None - вычисляется автоматически
        """
        # Получаем текущую позицию мыши (или центр экрана)
        viewport = self.page.viewport_size
        
        # Предполагаем что мышь в центре (у Playwright нет способа получить текущую позицию)
        start_x = random.randint(viewport['width'] // 4, viewport['width'] * 3 // 4)
        start_y = random.randint(viewport['height'] // 4, viewport['height'] * 3 // 4)
        
        # Вычисляем расстояние
        distance = math.sqrt((target_x - start_x)**2 + (target_y - start_y)**2)
        
        # Определяем степень искривления (длинные движения - более искривленные)
        if distance > 300:
            curvature = 'high'
        elif distance > 150:
            curvature = 'medium'
        else:
            curvature = 'low'
        
        # Генерируем контрольные точки
        control_points = self._generate_control_points(
            (start_x, start_y),
            (target_x, target_y),
            curvature
        )
        
        # Количество шагов
        steps = self._get_movement_speed(distance)
        
        # Генерируем траекторию
        path = self._bezier_curve(
            (start_x, start_y),
            (target_x, target_y),
            control_points,
            steps
        )
        
        # Двигаемся по траектории
        for i, (x, y) in enumerate(path):
            # Добавляем микро-дрожание
            jittered_x, jittered_y = self._add_jitter(x, y, jitter_amount=1.5)
            
            # Замедляемся у цели (закон Фиттса)
            if i > len(path) * 0.8:  # Последние 20%
                delay = random.uniform(0.01, 0.03)
            else:
                delay = random.uniform(0.003, 0.01)
            
            self.page.mouse.move(jittered_x, jittered_y)
            time.sleep(delay)
        
        # Финальное движение к точной цели (коррекция)
        self.page.mouse.move(target_x, target_y)
        time.sleep(random.uniform(0.05, 0.15))
    
    def move_to_element_with_overshoot(self, element):
        """
        Перемещает мышь к элементу с "перелетом" и коррекцией.
        
        Человек часто "перелетает" цель и потом корректирует.
        
        Args:
            element: Playwright locator элемента
        """
        # Получаем позицию элемента
        box = element.bounding_box()
        if not box:
            return
        
        # Центр элемента
        target_x = box['x'] + box['width'] / 2
        target_y = box['y'] + box['height'] / 2
        
        # "Перелетаем" цель на 10-30 пикселей
        overshoot_x = target_x + random.uniform(10, 30) * random.choice([-1, 1])
        overshoot_y = target_y + random.uniform(10, 30) * random.choice([-1, 1])
        
        # Двигаемся к перелетной точке
        self.move_to(overshoot_x, overshoot_y)
        
        # Пауза "осознания"
        time.sleep(random.uniform(0.05, 0.15))
        
        # Коррекция к реальной цели
        self.page.mouse.move(target_x, target_y)
        time.sleep(random.uniform(0.08, 0.2))
    
    def random_movement(self, movements=3):
        """
        Случайные движения мыши (имитация чтения страницы).
        
        Args:
            movements: Количество движений
        """
        viewport = self.page.viewport_size
        
        for _ in range(movements):
            # Случайная точка
            x = random.randint(100, viewport['width'] - 100)
            y = random.randint(100, viewport['height'] - 100)
            
            self.move_to(x, y)
            
            # Пауза (читаем)
            time.sleep(random.uniform(0.3, 1.0))

