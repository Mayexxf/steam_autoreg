#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Конфигурация для Outlook Account Creator
"""

# ============================================================================
# ПРОКСИ
# ============================================================================
HARDCODED_PROXY = "DEJ2ge:EP5YzGUVRujv:nproxy.site:16791"

# ============================================================================
# ЗАДЕРЖКИ (в миллисекундах)
# ============================================================================
TYPING_DELAY = (150, 350)       # Между символами (было: 40-120)
CLICK_DELAY = (200, 500)       # После клика (было: 80-200)
ACTION_DELAY = (400, 900)      # Между действиями (было: 200-500)
PAGE_DELAY = (2000, 3500)      # Загрузка страницы (было: 800-1500)

# ============================================================================
# РАЗМЕРЫ ЭКРАНА
# ============================================================================
VIEWPORT_OPTIONS = [
    {"width": 1920, "height": 1080},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
]

# ============================================================================
# НАСТРОЙКИ КАПЧИ
# ============================================================================
CAPTCHA_HOLD_TIME = (3000, 5000)  # Время удержания (мс)
CAPTCHA_MAX_ATTEMPTS = 5          # Максимум попыток

# ============================================================================
# URLs
# ============================================================================
SIGNUP_URL = "https://signup.live.com/signup"
LOGIN_URL = "https://login.live.com/"
OUTLOOK_URL = "https://outlook.live.com/mail/"

# ============================================================================
# ИМЕНА ДЛЯ ГЕНЕРАЦИИ
# ============================================================================
FIRST_NAMES = [
    "Oleksandr", "Dmytro", "Maksym", "Artem", "Vladyslav", "Mykyta", "Matviy", "Ivan", "Danylo", "Andriy",
    "Bohdan", "Kyrylo", "Mykhailo", "Roman", "Denys", "Marko", "Volodymyr", "Yaroslav", "Illia", "Oleksiy",
    "David", "Tymofiy", "Pavlo", "Yurii", "Vitaliy", "Mykola", "Bohdan", "Nazariy", "Arsen", "Maksim",
    "Yehor", "Serhiy", "Fedir", "Petro", "Taras", "Vasyl", "Anton", "Myroslav", "Danyil", "Stanislav",
    "Anastasiya", "Sofiya", "Anna", "Viktoriya", "Mariya", "Veronika", "Solomiya", "Zlata", "Yana", "Daryna",
    "Kateryna", "Olena", "Nataliya", "Yuliya", "Polina", "Alina", "Diana", "Yeva", "Marta", "Valeriya",
    "Oleksandra", "Milana", "Elizaveta", "Svitlana", "Arina", "Kamila", "Varvara", "Kristina", "Emiliya", "Vasilina",
    "Angelina", "Olha", "Nadiya", "Vira", "Liubov", "Tetyana", "Irina", "Khrystyna", "Lesya", "Zoryana",
    "Kalyna", "Roksolana", "Marharyta", "Sofia", "Anhelina", "Violeta", "Mira", "Liliya", "Eva", "Solomiya"
]

LAST_NAMES = [
    "Melnyk", "Shevchenko", "Bondarenko", "Kovalenko", "Boyko", "Tkachenko", "Kravchenko", "Kovalchuk", "Oliynyk", "Shevchuk",
    "Koval", "Rudenko", "Savchenko", "Petrenko", "Moroz", "Lysenko", "Pavlenko", "Romanenko", "Ivanenko", "Kuzmenko",
    "Symonenko", "Marchenko", "Vasylenko", "Zakharchenko", "Hryhorenko", "Litvinenko", "Kostenko", "Ponomarenko", "Sirenko", "Boiko",
    "Kucher", "Tkachuk", "Dmytrenko", "Sydorenko", "Havrylenko", "Kovalyov", "Bilous", "Shvets", "Kramarenko", "Martynenko",
    "Goncharenko", "Yurchenko", "Bilyk", "Zinchenko", "Polishchuk", "Chernenko", "Kushnir", "Pavliuk", "Hrytsenko", "Didenko"
]

MONTH_NAMES = [
    "січень",    # 1
    "лютий",
    "березень",
    "квітень",
    "травень",
    "червень",
    "липень",
    "серпень",
    "вересень",
    "жовтень",
    "листопад",
    "грудень"    # 12
]


