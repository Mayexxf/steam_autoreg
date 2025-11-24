#!/usr/bin/env python3
"""
Продвинутая имитация человеческой печати.

Особенности:
1. Вариативная скорость (быстрая/медленная печать)
2. Естественные опечатки с backspace
3. Паузы для "думания"
4. Разная скорость для разных типов символов
5. Усталость (замедление к концу строки)
"""

import random
import time
import string


class HumanTypist:
    """
    Имитация человеческой печати с реалистичными паттернами.
    """
    
    # Базовые скорости печати (мс между символами)
    SPEED_PROFILES = {
        'slow': (150, 350),      # Медленная печать (старики, осторожные)
        'normal': (80, 200),     # Обычная печать (большинство людей)
        'fast': (50, 120),       # Быстрая печать (опытные)
        'expert': (30, 80),      # Очень быстрая (программисты)
    }
    
    # Соседние клавиши на QWERTY (для реалистичных опечаток)
    NEIGHBOR_KEYS = {
        'q': ['w', 'a'], 'w': ['q', 'e', 's'], 'e': ['w', 'r', 'd'],
        'r': ['e', 't', 'f'], 't': ['r', 'y', 'g'], 'y': ['t', 'u', 'h'],
        'u': ['y', 'i', 'j'], 'i': ['u', 'o', 'k'], 'o': ['i', 'p', 'l'],
        'p': ['o', 'l'],
        'a': ['q', 's', 'z'], 's': ['w', 'a', 'd', 'x'], 'd': ['e', 's', 'f', 'c'],
        'f': ['r', 'd', 'g', 'v'], 'g': ['t', 'f', 'h', 'b'], 'h': ['y', 'g', 'j', 'n'],
        'j': ['u', 'h', 'k', 'm'], 'k': ['i', 'j', 'l'], 'l': ['o', 'k', 'p'],
        'z': ['a', 'x'], 'x': ['z', 's', 'c'], 'c': ['x', 'd', 'v'],
        'v': ['c', 'f', 'b'], 'b': ['v', 'g', 'n'], 'n': ['b', 'h', 'm'],
        'm': ['n', 'j'],
    }
    
    def __init__(self, speed_profile='normal', typo_rate=0.05):
        """
        Args:
            speed_profile: 'slow', 'normal', 'fast', 'expert'
            typo_rate: Вероятность опечатки (0.0-1.0)
        """
        self.speed_profile = speed_profile
        self.typo_rate = typo_rate
        self.base_delay = self.SPEED_PROFILES[speed_profile]
        
    def _get_char_delay(self, char, position, total_length):
        """
        Вычисляет задержку для символа с учетом контекста.
        
        Args:
            char: Текущий символ
            position: Позиция в строке
            total_length: Общая длина строки
        
        Returns:
            Задержка в миллисекундах
        """
        base_min, base_max = self.base_delay
        
        # 1. Базовая задержка с вариативностью
        delay = random.uniform(base_min, base_max)
        
        # 2. Специальные символы (сложнее печатать)
        if char in string.punctuation or char in string.digits:
            delay *= random.uniform(1.2, 1.5)  # +20-50%
        
        # 3. Заглавные буквы (нажатие Shift)
        if char.isupper():
            delay *= random.uniform(1.1, 1.3)  # +10-30%
        
        # 4. Пробелы (быстрее)
        if char == ' ':
            delay *= random.uniform(0.7, 0.9)  # -10-30%
        
        # 5. Усталость к концу строки
        if position > total_length * 0.7:
            fatigue_factor = 1.0 + (position / total_length - 0.7) * 0.5
            delay *= fatigue_factor
        
        # 6. "Всплески" скорости (иногда печатаем быстрее)
        if random.random() < 0.1:  # 10% chance
            delay *= random.uniform(0.5, 0.7)  # Burst typing
        
        # 7. Паузы для "думания" (редко)
        if random.random() < 0.03:  # 3% chance
            delay += random.uniform(300, 800)  # Thinking pause
        
        return delay / 1000  # Convert to seconds
    
    def _get_typo_char(self, intended_char):
        """
        Генерирует реалистичную опечатку (соседняя клавиша).
        
        Args:
            intended_char: Символ который хотели напечатать
        
        Returns:
            Символ-опечатка
        """
        char_lower = intended_char.lower()
        
        # Проверяем есть ли соседние клавиши
        if char_lower in self.NEIGHBOR_KEYS:
            neighbors = self.NEIGHBOR_KEYS[char_lower]
            typo = random.choice(neighbors)
            
            # Сохраняем регистр
            if intended_char.isupper():
                return typo.upper()
            return typo
        else:
            # Для неизвестных символов - случайная буква
            if intended_char.isalpha():
                typo = random.choice(string.ascii_lowercase)
                return typo.upper() if intended_char.isupper() else typo
            return intended_char
    
    def _should_make_typo(self, position, total_length):
        """
        Определяет нужно ли сделать опечатку.
        
        Вероятность опечатки выше:
        - В середине слова (не в начале/конце)
        - При быстрой печати
        - В длинных словах
        """
        # Базовая вероятность
        typo_chance = self.typo_rate
        
        # Не опечатываемся в начале строки
        if position < 2:
            return False
        
        # Не опечатываемся в конце строки (визуально проверяем)
        if position > total_length - 3:
            typo_chance *= 0.3
        
        # Выше вероятность в середине длинных строк
        if 0.3 < (position / total_length) < 0.7 and total_length > 10:
            typo_chance *= 1.5
        
        return random.random() < typo_chance
    
    def type_text(self, element, text):
        """
        Печатает текст человекоподобно.
        
        Args:
            element: Playwright locator элемента ввода
            text: Текст для ввода
        """
        total_length = len(text)
        
        for i, char in enumerate(text):
            # Проверяем нужна ли опечатка
            if self._should_make_typo(i, total_length):
                # Печатаем неправильный символ
                typo_char = self._get_typo_char(char)
                
                delay = self._get_char_delay(typo_char, i, total_length)
                element.press_sequentially(typo_char, delay=int(delay * 1000))
                
                # Пауза перед осознанием опечатки
                time.sleep(random.uniform(0.1, 0.4))
                
                # Удаляем опечатку
                element.press('Backspace')
                time.sleep(random.uniform(0.05, 0.15))
            
            # Печатаем правильный символ
            delay = self._get_char_delay(char, i, total_length)
            element.press_sequentially(char, delay=int(delay * 1000))
        
        # Финальная пауза (проверка введенного)
        time.sleep(random.uniform(0.2, 0.6))
    
    def type_with_pauses(self, element, text, word_pause_chance=0.3):
        """
        Печатает текст с паузами между словами (для естественности).
        
        Args:
            element: Playwright locator элемента ввода
            text: Текст для ввода
            word_pause_chance: Вероятность паузы между словами
        """
        words = text.split(' ')
        
        for word_idx, word in enumerate(words):
            # Печатаем слово
            self.type_text(element, word)
            
            # Пауза между словами?
            if word_idx < len(words) - 1:  # Не после последнего слова
                if random.random() < word_pause_chance:
                    # "Думаем" над следующим словом
                    time.sleep(random.uniform(0.3, 1.0))
                
                # Печатаем пробел
                element.press(' ')
                time.sleep(random.uniform(0.05, 0.15))




