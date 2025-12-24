#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam Test Stealth Script - БЕЗ регистрации
Только запуск браузера со стелс-функционалом для тестирования на Steam
"""
from telnetlib import EC
from typing import Dict

from scipy.interpolate import CubicSpline
from selenium.webdriver import Keys
from selenium.webdriver.support.wait import WebDriverWait
from outlook.config import (
    HARDCODED_PROXY, PAGE_DELAY, FIRST_NAMES, LAST_NAMES, MONTH_NAMES,
    SIGNUP_URL
)

from outlook.creator import OutlookCreator

# ============================================================================
# 🧪 ТЕСТОВЫЙ РЕЖИМ - БЕЗ РЕГИСТРАЦИИ (STEAM)
# ============================================================================
TEST_INFO = """
[TEST MODE] БЕЗ РЕГИСТРАЦИИ (STEAM) - FIREFOX EXTENSION
================================================================================
[+] Что работает:
   - ✓ navigator.webdriver = undefined (через Firefox Web Extension)
   - ✓ Anti-detection скрипт инжектится ДО загрузки страницы (document_start)
   - ✓ Все стелс-функции (fingerprint, cookies, storage)
   - ✓ Прокси поддержка (HTTP и SOCKS5)
   - ✓ WebRTC защита, Canvas noise, Hardware spoofing
   - ✓ Человекоподобные движения мыши и печать

[-] Что отключено:
   - Заполнение формы регистрации
   - Решение капчи
   - Сохранение аккаунта

[*] Цель:
   Браузер откроется на странице Steam и остановится.
   navigator.webdriver будет undefined - проверь в консоли браузера!
   Вы можете вручную проверить стелс-функционал и закрыть браузер когда захотите.
================================================================================
"""
import sys
import io

# Настройка кодировки для Windows консоли
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print(TEST_INFO)

from seleniumwire import webdriver  # Используем selenium-wire вместо обычного selenium
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException, TimeoutException
import random
import string
import time
import requests
import os
from src.stealth.fingerprint_generator import FingerprintGenerator
from src.stealth.cookie_generator import CookieGenerator
from src.stealth.storage_generator import StorageGenerator
from src.stealth.human_typing import HumanTypist
from src.stealth.geo_config import get_geo_config, detect_country_from_geo
from src.proxy.mobileproxy_manager import MobileProxyManager

# ============================================================================
# 🔧 ЗАГЛУШКА: ПРЯМОЕ УКАЗАНИЕ HTTP ПРОКСИ
# ============================================================================
# Раскомментируйте и укажите ваш прокси напрямую здесь, чтобы не использовать
# файл proxies.txt и не вызывать API смены IP
#
# Поддерживаемые форматы:
#   - "login:pass@host:port"           (HTTP с авторизацией)
#   - "host:port"                      (HTTP без авторизации)
#   - "http://login:pass@host:port"    (явное указание HTTP)
#   - "socks5://login:pass@host:port"  (SOCKS5 прокси)
#
# Примеры:
#   HARDCODED_PROXY = "user:password@proxy.example.com:8080"
#   HARDCODED_PROXY = "185.162.128.75:9528"
#   HARDCODED_PROXY = "http://user:pass@proxy.example.com:3128"
#
HARDCODED_PROXY = "MPzEefwWaIUi:tc6aWZqR:pool.proxy.market:10000"  # Замените None на строку с вашим прокси


# ============================================================================


def refresh_proxy_ip(proxy_refresh_url=None):
    """
    Обновляет IP мобильного прокси перед запуском браузера

    Использует API mobileproxy.space для смены IP с полным логированием.

    Args:
        proxy_refresh_url: URL для обновления IP (опционально, загружается из proxy_config.txt)

    Returns:
        dict с информацией о смене IP или None при ошибке
    """
    # Если URL не передан - пытаемся загрузить из файла
    if not proxy_refresh_url:
        try:
            with open("proxy_config.txt", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "changeip" in line.lower():
                        proxy_refresh_url = line
                        break
        except FileNotFoundError:
            print("[PROXY REFRESH] proxy_config.txt not found - skipping IP refresh")
            return None
        except Exception as e:
            print(f"[PROXY REFRESH] Error reading proxy_config.txt: {e}")
            return None

    if not proxy_refresh_url:
        print("[PROXY REFRESH] No refresh URL configured - skipping")
        return None

    try:
        print(f"[PROXY REFRESH] Refreshing proxy IP...")

        # Добавляем format=json к URL если его там нет
        if "format=" not in proxy_refresh_url:
            separator = "&" if "?" in proxy_refresh_url else "?"
            proxy_refresh_url = f"{proxy_refresh_url}{separator}format=json"

        # ВАЖНО: User-Agent обязателен по документации API!
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        # Отправляем GET запрос для обновления IP
        response = requests.get(proxy_refresh_url, headers=headers, timeout=30)

        if response.status_code == 200:
            try:
                # Парсим JSON ответ
                result = response.json()

                # DEBUG: показываем что вернул API
                print(f"[PROXY REFRESH] DEBUG - API Response: {result}")

                # Проверяем разные варианты успешного ответа
                # code=200 тоже означает успех (по документации)
                if result.get('status') == 'ok' or result.get('code') == 200:
                    new_ip = result.get('new_ip', 'unknown')
                    change_time = result.get('rt', 'unknown')
                    proxy_id = result.get('proxy_id', 'unknown')

                    print(f"[PROXY REFRESH] [+] IP successfully refreshed!")
                    print(f"[PROXY REFRESH] New IP: {new_ip}")
                    print(f"[PROXY REFRESH] Change time: {change_time}s")
                    print(f"[PROXY REFRESH] Proxy ID: {proxy_id}")

                    # Даем 3 секунды на применение изменений (увеличено с 2)
                    time.sleep(3)

                    return result
                else:
                    # Ошибка в API
                    code = result.get('code', 'unknown')
                    message = result.get('message', 'No error message')
                    print(f"[PROXY REFRESH] [-] API Error: {message}")
                    print(f"[PROXY REFRESH] Error code: {code}")
                    return None

            except ValueError:
                # Ответ не JSON (старый формат)
                print(f"[PROXY REFRESH] [+] IP refreshed (non-JSON response)")
                print(f"[PROXY REFRESH] Response: {response.text[:100]}")
                time.sleep(3)
                return {'status': 'ok', 'response': response.text[:100]}
        else:
            print(f"[PROXY REFRESH] [-] Failed: HTTP {response.status_code}")
            print(f"[PROXY REFRESH] Response: {response.text[:200]}")
            return None

    except requests.exceptions.Timeout:
        print(f"[PROXY REFRESH] [-] Timeout - refresh URL not responding")
        return None
    except Exception as e:
        print(f"[PROXY REFRESH] [-] Error: {str(e)[:100]}")
        import traceback
        traceback.print_exc()
        return None


def detect_proxy_geo(new_ip):
    """
    Определяет геолокацию прокси по его IP адресу

    Args:
        new_ip: IP адрес прокси

    Returns:
        dict с geo_config или None
    """
    if not new_ip or new_ip == 'unknown':
        return None

    try:
        print(f"[GEO DETECT] Detecting geolocation for IP: {new_ip}")

        # Используем бесплатный API для определения геолокации
        # ip-api.com предоставляет 45 запросов в минуту бесплатно
        response = requests.get(
            f"http://ip-api.com/json/{new_ip}?fields=status,country,countryCode,city,timezone,currency", timeout=10)

        if response.status_code == 200:
            data = response.json()

            if data.get('status') == 'success':
                country = data.get('country', '')
                city = data.get('city', '')
                timezone = data.get('timezone', '')
                currency = data.get('currency', '')

                print(f"[GEO DETECT] [+] Location detected:")
                print(f"[GEO DETECT] Country: {country}")
                print(f"[GEO DETECT] City: {city}")
                print(f"[GEO DETECT] Timezone: {timezone}")
                print(f"[GEO DETECT] Currency: {currency}")

                # Получаем конфигурацию локали по названию страны
                geo_config = get_geo_config(country)

                # Переопределяем timezone и currency если они были получены от API
                if timezone:
                    geo_config['timezone'] = timezone
                if currency:
                    geo_config['currency'] = currency

                # Добавляем информацию о городе
                geo_config['city'] = city
                geo_config['country'] = country

                return geo_config
            else:
                print(f"[GEO DETECT] [-] API returned error status")
                return None
        else:
            print(f"[GEO DETECT] [-] HTTP {response.status_code}")
            return None

    except Exception as e:
        print(f"[GEO DETECT] [-] Error: {str(e)[:100]}")
        return None


def human_delay(min_ms=500, max_ms=1500):
    """Случайная задержка как у человека"""
    delay = random.uniform(min_ms, max_ms)
    time.sleep(delay / 1000)
    return int(delay)


class SeleniumHumanTypist:
    """Адаптер HumanTypist для Selenium"""

    def __init__(self, driver, speed_profile='normal', typo_rate=0.06, typo_correct_rate=0.9):
        self.driver = driver
        self.typist = HumanTypist(speed_profile=speed_profile, typo_rate=typo_rate)

    def type_text(self, element, text):
        """Печатает текст человекоподобно через Selenium"""
        total_length = len(text)
        for i, char in enumerate(text):
            # Проверяем опечатку (логика из HumanTypist)
            if self.typist._should_make_typo(i, total_length):
                typo_char = self.typist._get_typo_char(char)
                element.send_keys(typo_char)
                delay = self.typist._get_char_delay(typo_char, i, total_length)
                time.sleep(delay)
                time.sleep(random.uniform(0.1, 0.4))  # Пауза перед backspace
                element.send_keys(Keys.BACKSPACE)
                time.sleep(random.uniform(0.05, 0.15))

            # Правильный символ
            element.send_keys(char)
            delay = self.typist._get_char_delay(char, i, total_length)
            time.sleep(delay)


class SeleniumHumanMouse:
    """Адаптер HumanMouse для Selenium"""

    def __init__(self, driver):
        self.driver = driver
        self.actions = ActionChains(driver)

    def random_movement(self, movements=3):
        width = self.driver.execute_script("return window.innerWidth")
        height = self.driver.execute_script("return window.innerHeight")

        # Безопасные границы для движения мыши (отступ от краёв)
        margin = 50
        safe_width = max(200, width - margin * 2)
        safe_height = max(200, height - margin * 2)

        for _ in range(movements):
            # Генерируем координаты внутри безопасной зоны
            start_x = random.randint(margin, margin + safe_width)
            start_y = random.randint(margin, margin + safe_height)
            end_x = random.randint(margin, margin + safe_width)
            end_y = random.randint(margin, margin + safe_height)

            # Bézier: 4 control points for curve
            mid1_x = random.randint(min(start_x, end_x), max(start_x, end_x))
            mid1_y = random.randint(min(start_y, end_y), max(start_y, end_y))
            mid2_x = random.randint(min(start_x, end_x), max(start_x, end_x))
            mid2_y = random.randint(min(start_y, end_y), max(start_y, end_y))

            points = [(start_x, start_y), (mid1_x, mid1_y), (mid2_x, mid2_y), (end_x, end_y)]
            t = [0, 0.3, 0.7, 1]
            cs_x = CubicSpline(t, [p[0] for p in points])
            cs_y = CubicSpline(t, [p[1] for p in points])

            steps = 20
            current_x, current_y = start_x, start_y

            for i in range(steps):
                pos = i / steps
                new_x = int(cs_x(pos))
                new_y = int(cs_y(pos))

                # Вычисляем смещение относительно текущей позиции
                dx = new_x - current_x
                dy = new_y - current_y

                # Ограничиваем смещение чтобы не выйти за границы
                dx = max(-100, min(100, dx))
                dy = max(-100, min(100, dy))

                try:
                    self.actions.move_by_offset(dx, dy).perform()
                    current_x += dx
                    current_y += dy
                except Exception:
                    # Если движение невозможно - пропускаем
                    pass

                time.sleep(random.uniform(0.01, 0.05))

            self.actions.reset_actions()
            time.sleep(random.uniform(0.3, 0.8))


def human_type(driver, selector, text, speed_profile='normal', typo_rate=0.06):
    """
    Печатает текст РЕАЛИСТИЧНО как человек (версия для Selenium).

    Args:
        driver: Selenium WebDriver
        selector: CSS селектор поля ввода
        text: Текст для ввода
        speed_profile: 'slow', 'normal', 'fast', 'expert'
        typo_rate: Вероятность опечатки (0.0-1.0)
    """
    element = driver.find_element(By.CSS_SELECTOR, selector)

    # Человек сначала водит мышкой → фокус → клик
    mouse = SeleniumHumanMouse(driver)
    mouse.random_movement(movements=random.randint(2, 5))

    # 2. Плавное наведение на поле ( САМОЕ ВАЖНОЕ! )
    ActionChains(driver) \
        .move_to_element_with_offset(element, random.randint(-10, 10), random.randint(-5, 5)) \
        .pause(random.uniform(0.3, 1.1)) \
        .click() \
        .perform()

    # 3. Человек читает подсказку в поле (placeholder), думает...
    time.sleep(random.uniform(0.6, 2.1))

    # 4. Начинаем печатать — с настоящими burst'ами и опечатками
    typist = SeleniumHumanTypist(
        driver,
        speed_profile=speed_profile,
        typo_rate=typo_rate,
        typo_correct_rate=0.92
    )
    typist.type_text(element, text)

    # 5. После ввода — небольшая пауза (человек проверяет, что написал)
    time.sleep(random.uniform(0.7, 2.3))

    # 6. Иногда чуть подвигаем мышку после ввода (очень по-человечески)
    if random.random() < 0.4:
        ActionChains(driver).move_by_offset(
            random.randint(-80, 80), random.randint(-80, 80)
        ).pause(0.3).perform()


def random_mouse_movement(driver, movements=3):
    """
    Случайное движение мыши РЕАЛИСТИЧНО (версия для Selenium).

    Args:
        driver: Selenium WebDriver
        movements: Количество движений
    """
    mouse = SeleniumHumanMouse(driver)
    mouse.random_movement(movements=movements)

def stealth_checkbox_click(driver, checkbox_selector):
    """
    Максимально стелс-отметка чекбокса на Steam (или любой другой странице).
    Эмулирует реальное движение мыши + диспатч всех MouseEvent событий.
    Valve почти не ловит такой клик.

    Args:
        driver: Selenium WebDriver
        checkbox_selector: CSS селектор, например '#accept_ssa' или '#accept_ssa, [name="accept_ssa"]'
    """
    try:
        # Ищем чекбокс (с fallback селекторами)
        checkbox = driver.find_element(By.CSS_SELECTOR, checkbox_selector)

        # Если уже отмечен — выходим
        if checkbox.is_selected():
            print(f"[CHECKBOX] Уже отмечен: {checkbox_selector}")
            return True

        print(f"[CHECKBOX] Отмечаем чекбокс: {checkbox_selector}")

        # 1. Небольшое случайное движение мыши перед действием
        random_mouse_movement(driver, movements=random.randint(1, 3))
        human_delay(400, 900)  # 0.4–0.9 сек

        # 2. Плавно подводим курсор к чекбоксу с небольшим оффсетом (человек не попадает точно в центр)
        actions = ActionChains(driver)
        offset_x = random.randint(-8, 8)
        offset_y = random.randint(-8, 8)
        actions.move_to_element_with_offset(checkbox, offset_x, offset_y)
        actions.pause(random.uniform(0.2, 0.6))
        actions.perform()

        human_delay(200, 500)  # Короткая пауза перед кликом

        # 3. Диспатчим ВСЕ реальные события мыши через JS (самое важное для стелс)
        driver.execute_script("""
            const el = arguments[0];
            const events = ['mouseover', 'mousemove', 'mousedown', 'mouseup', 'click'];
            events.forEach(type => {
                const event = new MouseEvent(type, {
                    view: window,
                    bubbles: true,
                    cancelable: true,
                    buttons: 1,
                    clientX: el.getBoundingClientRect().x + el.clientWidth / 2,
                    clientY: el.getBoundingClientRect().y + el.clientHeight / 2
                });
                el.dispatchEvent(event);
            });
            // Принудительно отмечаем, если вдруг событие не сработало
            el.checked = true;
        """, checkbox)

        # Небольшая пауза после клика
        human_delay(300, 700)

        # Проверка результата
        if checkbox.is_selected():
            print(f"[CHECKBOX] ✓ Успешно отмечен: {checkbox_selector}")
            return True
        else:
            print(f"[CHECKBOX] ✗ Не отметился после JS — пробуем прямой клик (резерв)")
            checkbox.click()  # Крайний случай
            return checkbox.is_selected()

    except Exception as e:
        print(f"[CHECKBOX] Ошибка при отметке {checkbox_selector}: {str(e)[:120]}")
        return False


class SteamTestStealth:
    """Тестовый класс для проверки стелс-функционала БЕЗ регистрации на Steam"""

    def __init__(self, proxy=None, headless=False, fill_form=True):
        self.proxy = proxy
        self.headless = headless
        self.fill_form = fill_form
        self.driver = None
        self.proxy_manager = None  # MobileProxyManager instance

        # Настройки таймаутов
        self.page_timeout = 60
        self.wait_after_load = 2

        # Инициализируем MobileProxyManager если есть API ключ
        try:
            self.proxy_manager = MobileProxyManager()
            print(f"[MOBILEPROXY] Manager initialized with API key")
        except ValueError:
            print(f"[MOBILEPROXY] No API key found - will use static proxies")
            self.proxy_manager = None

        # Загружаем прокси если не указан
        if self.proxy == "DISABLED":
            self.proxy = None
            print("[INIT] Proxy disabled by user")
        elif not self.proxy:
            self.proxy = self._load_proxy()

        if self.proxy:
            proxy_display = self.proxy.split('@')[1] if '@' in self.proxy else self.proxy
            print(f"[PROXY] Loaded from proxies.txt")
            print(f"[INIT] Using proxy: {proxy_display}")
        else:
            print("[WARN] No proxy - testing without proxy")

    def _load_proxy(self):
        """Загрузка прокси из proxies.txt или HARDCODED_PROXY"""
        # Проверяем наличие заглушки HARDCODED_PROXY
        if HARDCODED_PROXY:
            print(f"[PROXY] Using HARDCODED_PROXY from code")
            # Не показываем пароль в логах
            if '@' in HARDCODED_PROXY:
                safe_display = HARDCODED_PROXY.split('@')[1]
            else:
                safe_display = HARDCODED_PROXY.split(':')[0] + ':****'
            print(f"[PROXY] Hardcoded proxy: {safe_display}")
            print(f"[PROXY] Skipping IP refresh (using static proxy)")
            return HARDCODED_PROXY

        # Загружаем из proxies.txt если заглушка не установлена
        try:
            with open("config/proxies.txt", encoding="utf-8") as f:
                proxies = [line.strip() for line in f if line.strip() and not line.startswith("#")]

            if proxies:
                # Выбираем случайный прокси
                print(f"[PROXY] Loaded from proxies.txt ({len(proxies)} available)")
                return random.choice(proxies)
        except Exception as e:
            print(f"[WARN] Could not load proxies: {e}")
        return None

    def generate_credentials(self):
        """Генерация случайных credentials"""
        username = ''.join(random.choices(string.ascii_lowercase, k=8)) + str(random.randint(100, 999))
        email = f"{username}@gmail.com"
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

        return {
            "username": username,
            "email": email,
            "password": password
        }

    def static_credentials(self):
        """Генерация случайных credentials"""
        username = ''.join(random.choices(string.ascii_lowercase, k=8)) + str(random.randint(100, 999))
        email = f"{username}@gmail.com"
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

        return {
            "username": username,
            "email": email,
            "password": password
        }

    def _parse_proxy_for_firefox(self):
        """Парсит прокси для формата Firefox"""
        if not self.proxy:
            return None

        # Определяем протокол
        if self.proxy.startswith('socks5://'):
            protocol = 'socks5'
            proxy_str = self.proxy[9:]  # Убираем префикс
        elif self.proxy.startswith('http://'):
            protocol = 'http'
            proxy_str = self.proxy[7:]
        else:
            protocol = 'http'
            proxy_str = self.proxy

        # Парсим
        if '@' in proxy_str:
            # login:pass@host:port
            auth, server = proxy_str.split('@')
            username, password = auth.split(':', 1)
            host, port = server.split(':', 1)
            return {
                'protocol': protocol,
                'host': host,
                'port': int(port),
                'username': username,
                'password': password
            }
        elif proxy_str.count(':') >= 3:
            parts = proxy_str.split(':', 3)

            # Определяем формат: host:port:login:pass ИЛИ login:pass:host:port
            if parts[1].isdigit():
                # host:port:login:pass
                return {
                    'protocol': protocol,
                    'host': parts[0],
                    'port': int(parts[1]),
                    'username': parts[2],
                    'password': parts[3]
                }
            else:
                # login:pass:host:port
                return {
                    'protocol': protocol,
                    'host': parts[2],
                    'port': int(parts[3]),
                    'username': parts[0],
                    'password': parts[1]
                }
        else:
            # host:port
            host, port = proxy_str.split(':', 1)
            return {
                'protocol': protocol,
                'host': host,
                'port': int(port),
                'username': None,
                'password': None
            }

    def test_stealth(self):
        """Минималистичный стелс-тест Steam (без регистрации, с опциональным заполнением формы)"""

        # === Прокси и гео (минимальный лог) ===
        geo_config = None
        if self.proxy and not HARDCODED_PROXY and self.proxy_manager:
            result = self.proxy_manager.change_ip_and_get_geo(wait_time=3)
            if result.get('success'):
                geo_config = result.get('geo')

        try:
            # === Fingerprint + базовые настройки ===
            fingerprint_config = FingerprintGenerator.generate()
            firefox_version = '133.0'
            user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{firefox_version}) Gecko/20100101 Firefox/{firefox_version}"
            fingerprint_script = FingerprintGenerator.get_injector_script(fingerprint_config, firefox_version)

            locale = geo_config['locale'] if geo_config else 'en-US'
            timezone_id = geo_config['timezone'] if geo_config else 'America/New_York'

            # === Firefox options ===
            options = FirefoxOptions()
            options.set_preference("general.useragent.override", user_agent)
            options.set_preference("intl.accept_languages", locale)
            options.set_preference("intl.locale.requested", locale)
            options.add_argument(f"--width={fingerprint_config['viewport']['width']}")
            options.add_argument(f"--height={fingerprint_config['viewport']['height']}")
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference("useAutomationExtension", False)
            options.set_preference("privacy.resistFingerprinting", False)
            if self.headless:
                options.add_argument("--headless")

            # === Прокси ===
            seleniumwire_options = {}
            proxy_config = self._parse_proxy_for_firefox()
            if proxy_config:
                auth = f"{proxy_config['username']}:{proxy_config['password']}@" if proxy_config.get('username') else ""
                protocol = "socks5" if proxy_config['protocol'] == 'socks5' else "http"
                proxy_url = f"{protocol}://{auth}{proxy_config['host']}:{proxy_config['port']}"
                seleniumwire_options = {
                    'proxy': {'http': proxy_url, 'https': proxy_url, 'no_proxy': 'localhost,127.0.0.1'},
                    'verify_ssl': False
                }

            # === Запуск браузера ===
            self.driver = webdriver.Firefox(options=options, seleniumwire_options=seleniumwire_options)
            self.driver.set_window_size(fingerprint_config['viewport']['width'], fingerprint_config['viewport']['height'])
            self.driver.set_page_load_timeout(self.page_timeout)
            self.driver.implicitly_wait(10)

            # === Антидетект расширение ===
            extension_path = os.path.abspath("firefox_antidetect_extension")
            if os.path.exists(extension_path):
                try:
                    self.driver.install_addon(extension_path, temporary=True)
                except:
                    pass  # Тихо, если не загрузилось

            # === Открытие страницы ===
            self.driver.get("https://login.live.com/")
            time.sleep(self.wait_after_load)

            # === Инжект fingerprint + timezone ===
            self.driver.execute_script(fingerprint_script)
            timezone_script = f"""
                const orig = Intl.DateTimeFormat;
                Intl.DateTimeFormat = function(...a) {{ if (!a[0]) a[0] = '{locale}'; return new orig(...a); }};
                Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {{
                    value: function() {{
                        let o = Object.getOwnPropertyDescriptor(orig.prototype, 'resolvedOptions').value.call(this);
                        o.timeZone = '{timezone_id}';
                        return o;
                    }}
                }});
            """
            self.driver.execute_script(timezone_script)

            # === Cookies ===
            cookies = CookieGenerator().generate_realistic_cookies(num_sites=7)
            for cookie in cookies:
                if 'steampowered' in cookie.get('domain', ''):
                    try:
                        sel_cookie = {
                            'name': cookie['name'], 'value': cookie['value'],
                            'domain': cookie.get('domain', '.steampowered.com'),
                            'path': cookie.get('path', '/'), 'secure': cookie.get('secure', True)
                        }
                        if 'expiry' in cookie:
                            sel_cookie['expiry'] = cookie['expiry']
                        self.driver.add_cookie(sel_cookie)
                    except:
                        pass

            # === LocalStorage ===
            storage_data = StorageGenerator().generate_full_storage()
            if self.driver.execute_script("return typeof(Storage) !== 'undefined'"):
                self.driver.execute_script(StorageGenerator().get_storage_script(storage_data))

            # === Проверка webdriver ===
            wd = self.driver.execute_script("return navigator.webdriver")
            status = "undefined ✓" if wd is None else f"{wd} ✗"

            print(f"\n{'=' * 60}")
            print(f"[TEST] Steam page loaded | webdriver: {status}")
            print(f"[TEST] Stealth ready — check console: navigator.webdriver")
            print(f"{'=' * 60}\n")

            # === ПРОГРЕВ БРАУЗЕРА: Посещаем нейтральную страницу ===
            print(f"\n[WARMUP] Прогрев браузера - посещаем https://www.microsoft.com...")
            try:
                self.driver.get("https://www.microsoft.com/")
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                print("[WARMUP] [+] microsoft.com успешно загружен")

                # Имитация человеческого просмотра страницы
                actions = ActionChains(self.driver)
                random_mouse_movement(self.driver, movements=random.randint(3, 6))
                human_delay(2000, 4000)

                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.4);")
                human_delay(1000, 2000)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.7);")
                human_delay(800, 1500)
                self.driver.execute_script("window.scrollTo(0, 0);")
                human_delay(1000, 2000)

                # === Поиск и клик по кнопке входа / создания аккаунта ===
                print("[WARMUP] Поиск кнопки входа или создания аккаунта...")

                signin_selectors = [
                    (By.LINK_TEXT, "Увійдіть у свій обліковий запис"),
                    (By.PARTIAL_LINK_TEXT, "Увійдіть"),
                    (By.PARTIAL_LINK_TEXT, "Sign in"),
                    (By.PARTIAL_LINK_TEXT, "Войти"),
                    (By.LINK_TEXT, "Create free account"),
                    (By.PARTIAL_LINK_TEXT, "Create"),
                    (By.PARTIAL_LINK_TEXT, "Створити"),
                    (By.CSS_SELECTOR, 'a[href*="signup"], a[href*="linkid="], a[href*="live.com"]'),
                ]

                signin_element = None
                for by, selector in signin_selectors:
                    try:
                        elements = WebDriverWait(self.driver, 8).until(
                            EC.visibility_of_all_elements_located((by, selector))
                        )
                        for el in elements:
                            if el.is_displayed() and el.is_enabled():
                                signin_element = el
                                break
                        if signin_element:
                            break
                    except:
                        continue

                if not signin_element:
                    self.driver.save_screenshot("./screens/no_signin_button.png")
                    raise Exception("Кнопка входа/создания аккаунта не найдена на microsoft.com")

                # Человеческий клик
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", signin_element)
                human_delay(1200, 2200)
                random_mouse_movement(self.driver, movements=2)
                actions.move_to_element_with_offset(signin_element, random.randint(-5, 5), random.randint(-5, 5)) \
                    .pause(random.uniform(0.3, 0.8)).click().perform()

                print("[WARMUP] [+] Клик по кнопке входа/регистрации выполнен")
                human_delay(3000, 6000)

            except Exception as e:
                print(f"[WARMUP] Ошибка во время прогрева: {e}")
                self.driver.save_screenshot("./screens/warmup_error.png")
                raise

            # === Переход к форме регистрации ===
            print(f"\n[REGISTRATION] Переходим к созданию аккаунта...")

            try:
                create_account_selectors = [
                    (By.LINK_TEXT, "Створити обліковий запис"),
                    (By.PARTIAL_LINK_TEXT, "Створити"),
                    (By.LINK_TEXT, "Create free account"),
                    (By.PARTIAL_LINK_TEXT, "Create account"),
                    (By.PARTIAL_LINK_TEXT, "Создать аккаунт"),
                    (By.CSS_SELECTOR, 'a[href*="signup.live.com"], a[href*="go.microsoft.com"]'),
                    (By.XPATH,
                     "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'next') or contains(text(), 'Далі')]"),
                ]

                create_element = None
                for by, selector in create_account_selectors:
                    try:
                        create_element = WebDriverWait(self.driver, 15).until(
                            EC.element_to_be_clickable((by, selector))
                        )
                        break
                    except:
                        continue

                if not create_element:
                    self.driver.save_screenshot("./screens/no_create_account_button.png")
                    print(f"[DEBUG] Текущий URL: {self.driver.current_url}")
                    print(f"[DEBUG] Title: {self.driver.title}")
                    raise Exception("Кнопка создания аккаунта не найдена")

                # Человеческий клик по кнопке создания
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", create_element)
                human_delay(1500, 3000)
                random_mouse_movement(self.driver, movements=random.randint(2, 4))
                actions.move_to_element_with_offset(create_element, random.randint(-8, 8), random.randint(-8, 8)) \
                    .pause(random.uniform(0.4, 1.0)).click().perform()

                print("[REGISTRATION] [+] Перешли на форму регистрации")
                human_delay(4000, 8000)  # ждём загрузку формы

            except Exception as e:
                print(f"[REGISTRATION] Ошибка перехода к форме: {e}")
                self.driver.save_screenshot("./screens/registration_error.png")
                raise

            # === Имитация поведения перед заполнением формы ===
            random_mouse_movement(self.driver, movements=random.randint(3, 5))
            human_delay(1000, 2000)
            self.driver.execute_script("window.scrollBy(0, 300);")
            human_delay(800, 1500)
            self.driver.execute_script("window.scrollBy(0, -150);")

            identity = OutlookCreator.generate_identity()
            print(f"\n[IDENTITY] Email: {identity['email']}")
            print(f"[IDENTITY] Password: {identity['password']}")
            print(f"[IDENTITY] Name: {identity['first']} {identity['last']}")
            print(f"[IDENTITY] Birth: {identity['birth_month']}/{identity['birth_day']}/{identity['birth_year']}")

            # === ШАГ 1: Ввод email ===
            print("\n[STEP 1] Ввод email...")
            if not self.form_filler.fill_email(identity,
                                               self.generate_identity):  # предполагаю, что метод адаптирован под Selenium
                print("[ERROR] Не удалось ввести email")
                return None

            human_delay(800, 1500)
            random_mouse_movement(self.driver, movements=2)

            # === ШАГ 2: Ввод пароля ===
            print("\n[STEP 2] Ввод пароля...")
            if not self.form_filler.fill_password(identity):
                print("[ERROR] Не удалось ввести пароль")
                return None

            human_delay(800, 1400)

            # === ШАГ 3: Нажатие "Далее" (Next) ===
            print("\n[STEP 3] Нажатие кнопки Далее...")
            try:
                next_btn = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "input[type='submit'], button#idSIButton9, input#iSignupAction"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
                human_delay(600, 1200)
                actions.move_to_element(next_btn).pause(random.uniform(0.3, 0.8)).click().perform()
            except Exception as e:
                print(f"[STEP 3] Ошибка нажатия Next: {e}")

            # === ШАГ 4: Дата рождения ===
            print("\n[STEP 4] Дата рождения...")
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "select#BirthMonth, select[name='BirthMonth']"))
                )
                if not self.form_filler.fill_birthdate(identity):
                    print("[ERROR] Не удалось ввести дату рождения")
                    return None
            except:
                print("[STEP 4] Поля даты рождения не найдены — пропускаем")

            human_delay(700, 1200)

            # === ШАГ 5: Имя и фамилия ===
            print("\n[STEP 5] Имя и фамилия...")
            self._handle_name_step(identity)  # предполагаю, что метод использует Selenium

            human_delay(600, 1000)
            random_mouse_movement(self.driver, movements=1)

            # === ШАГ 6: Капча ===
            print("\n[STEP 6] Проверка и решение hCaptcha...")
            human_delay(1500, 3000)
            random_mouse_movement(self.driver, movements=2)
            if not stealth_hcaptcha_checkbox_click(self.driver, timeout_attempts=4):
                print("[CAPTCHA] Не удалось решить hCaptcha")
                self.driver.save_screenshot("captcha_failed.png")

            # === ШАГ 7: Пост-регистрация ===
            print("\n[STEP 7] Обработка пост-регистрационных окон...")
            self._handle_post_registration()

            # === Проверка успеха ===
            final_url = self.driver.current_url.lower()
            if any(x in final_url for x in ['outlook', 'mail', 'office', 'live.com/dashboard']):
                print("\n" + "=" * 60)
                print("[SUCCESS] [+] Аккаунт Microsoft/Outlook успешно создан!")
                print("=" * 60)
            else:
                print(f"[WARNING] Финальный URL: {final_url} — успех не подтверждён")

            return identity

            # === Бесконечное ожидание (тестовый режим) ===
            print("[WAIT] Браузер открыт — закрывай вручную")
            try:
                while True:
                    time.sleep(1)
                    self.driver.current_url  # Проверка активности
            except:
                print("[INFO] Браузер закрыт")
            finally:
                if self.driver:
                    self.driver.quit()

        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass



if __name__ == "__main__":
    import sys

    # Парсим аргументы
    headless = "--headless" in sys.argv
    fill_form = "--fill_form" in sys.argv
    no_proxy = "--no-proxy" in sys.argv

    if "-u" not in sys.argv:
        print("[TIP] Для вывода в реальном времени запускай: python -u steam_test_stealth.py")
    # Настройка прокси
    if no_proxy:
        proxy = "DISABLED"
    else:
        proxy = None  # Автозагрузка из proxies.txt

    tester = SteamTestStealth(proxy=proxy, headless=headless)
    tester.test_stealth()
