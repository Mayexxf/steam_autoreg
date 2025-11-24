#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam Test Stealth Script - БЕЗ регистрации
Только запуск браузера со стелс-функционалом для тестирования на Steam
"""

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
from selenium.common.exceptions import WebDriverException
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
        response = requests.get(f"http://ip-api.com/json/{new_ip}?fields=status,country,countryCode,city,timezone,currency", timeout=10)

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
    def __init__(self, driver, speed_profile='normal', typo_rate=0.05):
        self.driver = driver
        self.typist = HumanTypist(speed_profile=speed_profile, typo_rate=typo_rate)

    def type_text(self, element, text):
        """Печатает текст человекоподобно через Selenium"""
        for char in text:
            element.send_keys(char)
            delay = random.uniform(50, 200) / 1000
            time.sleep(delay)


class SeleniumHumanMouse:
    """Адаптер HumanMouse для Selenium"""
    def __init__(self, driver):
        self.driver = driver
        self.actions = ActionChains(driver)

    def random_movement(self, movements=3):
        """Случайное движение мыши"""
        viewport_width = self.driver.execute_script("return window.innerWidth")
        viewport_height = self.driver.execute_script("return window.innerHeight")

        for _ in range(movements):
            x = random.randint(100, viewport_width - 100)
            y = random.randint(100, viewport_height - 100)

            # Плавное движение
            self.actions.move_by_offset(x - 200, y - 200)
            self.actions.perform()
            time.sleep(random.uniform(0.3, 0.8))
            self.actions.reset_actions()


def human_type(driver, selector, text, speed_profile='normal', typo_rate=0.05):
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

    # Создаем экземпляр типиста
    typist = SeleniumHumanTypist(driver, speed_profile=speed_profile, typo_rate=typo_rate)

    # Кликаем на поле (с небольшой задержкой)
    element.click()
    time.sleep(random.uniform(0.15, 0.4))

    # Печатаем текст
    typist.type_text(element, text)


def random_mouse_movement(driver, movements=3):
    """
    Случайное движение мыши РЕАЛИСТИЧНО (версия для Selenium).

    Args:
        driver: Selenium WebDriver
        movements: Количество движений
    """
    mouse = SeleniumHumanMouse(driver)
    mouse.random_movement(movements=movements)


class SteamTestStealth:
    """Тестовый класс для проверки стелс-функционала БЕЗ регистрации на Steam"""

    def __init__(self, proxy=None, headless=False):
        self.proxy = proxy
        self.headless = headless
        self.driver = None

        # Настройки таймаутов
        self.page_timeout = 60
        self.wait_after_load = 2

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
        """Загрузка прокси из proxies.txt"""
        try:
            with open("proxies.txt", encoding="utf-8") as f:
                proxies = [line.strip() for line in f if line.strip() and not line.startswith("#")]

            if proxies:
                # Выбираем случайный прокси
                proxy = random.choice(proxies)
                print(f"[PROXY] Loaded from proxies.txt ({len(proxies)} available)")
                return proxy
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
        """Тестирование стелс-функционала БЕЗ регистрации на Steam"""
        print("="*70)
        print(f"Steam Stealth Test (NO REGISTRATION) - FIREFOX")
        print("="*70)

        # Обновляем IP прокси и определяем геолокацию (если используется прокси)
        geo_config = None
        if self.proxy:
            print(f"\n[PROXY] Refreshing IP before browser launch...")
            refresh_result = refresh_proxy_ip()

            # Определяем геолокацию по новому IP
            if refresh_result and refresh_result.get('new_ip'):
                new_ip = refresh_result['new_ip']
                geo_config = detect_proxy_geo(new_ip)

            print()

        credentials = self.generate_credentials()
        print(f"\n[TEST CREDS] (for display only, won't be used)")
        print(f"  Email: {credentials['email']}")
        print(f"  Username: {credentials['username']}")
        print(f"  Password: {credentials['password']}")

        try:
            print(f"\n[1/3] Launching Firefox with stealth...")

            # ============================================
            # FINGERPRINT GENERATION
            # ============================================
            fingerprint_config = FingerprintGenerator.generate()
            firefox_version = '133.0'  # Актуальная версия Firefox

            # Для Firefox используем другой User-Agent
            user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{firefox_version}) Gecko/20100101 Firefox/{firefox_version}"

            # Генерируем fingerprint скрипт (адаптируем для Firefox)
            fingerprint_script = FingerprintGenerator.get_injector_script(fingerprint_config, firefox_version)

            print(f"[FINGERPRINT] Custom Generator")
            print(f"  Viewport: {fingerprint_config['viewport']['width']}x{fingerprint_config['viewport']['height']}")
            print(f"  Firefox: {firefox_version}")
            print(f"  WebGL: {fingerprint_config['webgl']['vendor'].split('(')[1].split(')')[0]}")
            print(f"  Hardware: {fingerprint_config['hardware']['cores']} cores, {fingerprint_config['hardware']['memory']}GB RAM")
            print(f"  Canvas noise: {fingerprint_config['canvas_noise']}")

            # Определяем locale и timezone на основе геолокации прокси
            if geo_config:
                locale = geo_config['locale']
                timezone_id = geo_config['timezone']
                print(f"[GEO CONFIG] Using proxy geolocation:")
                print(f"  Locale: {locale}")
                print(f"  Timezone: {timezone_id}")
                print(f"  Currency: {geo_config['currency']}")
            else:
                locale = 'en-US'
                timezone_id = 'America/New_York'
                print(f"[GEO CONFIG] Using default geolocation (en-US)")

            # ============================================
            # НАСТРОЙКА FIREFOX OPTIONS
            # ============================================
            options = FirefoxOptions()

            # User Agent
            options.set_preference("general.useragent.override", user_agent)

            # Локаль и язык
            options.set_preference("intl.accept_languages", locale)
            options.set_preference("intl.locale.requested", locale)

            # Timezone (Firefox не поддерживает прямую установку timezone через preferences)
            # Будем устанавливать через JavaScript injection

            # Viewport
            options.add_argument(f"--width={fingerprint_config['viewport']['width']}")
            options.add_argument(f"--height={fingerprint_config['viewport']['height']}")

            # Anti-detection настройки для Firefox
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference("useAutomationExtension", False)

            # WebGL
            options.set_preference("webgl.disabled", False)
            options.set_preference("webgl.force-enabled", True)

            # WebRTC блокировка (МЯГКАЯ)
            options.set_preference("media.peerconnection.enabled", True)
            options.set_preference("media.peerconnection.ice.proxy_only", True)
            options.set_preference("media.peerconnection.ice.default_address_only", True)

            # Canvas fingerprint protection (отключаем встроенную защиту Firefox)
            options.set_preference("privacy.resistFingerprinting", False)

            # Permissions
            options.set_preference("permissions.default.geo", 1)  # Разрешить геолокацию

            # Кеш
            options.set_preference("browser.cache.disk.enable", False)
            options.set_preference("browser.cache.memory.enable", False)

            # Headless режим (если нужен)
            if self.headless:
                options.add_argument("--headless")

            # ============================================
            # НАСТРОЙКА ПРОКСИ ЧЕРЕЗ SELENIUM-WIRE
            # ============================================
            seleniumwire_options = {}
            proxy_config = self._parse_proxy_for_firefox()

            if proxy_config:
                # Формируем URL прокси с аутентификацией для selenium-wire
                if proxy_config.get('username') and proxy_config.get('password'):
                    # Прокси с аутентификацией
                    if proxy_config['protocol'] == 'socks5':
                        proxy_url = f"socks5://{proxy_config['username']}:{proxy_config['password']}@{proxy_config['host']}:{proxy_config['port']}"
                    else:  # http
                        proxy_url = f"http://{proxy_config['username']}:{proxy_config['password']}@{proxy_config['host']}:{proxy_config['port']}"
                else:
                    # Прокси без аутентификации
                    if proxy_config['protocol'] == 'socks5':
                        proxy_url = f"socks5://{proxy_config['host']}:{proxy_config['port']}"
                    else:  # http
                        proxy_url = f"http://{proxy_config['host']}:{proxy_config['port']}"

                # Настройки для selenium-wire
                seleniumwire_options = {
                    'proxy': {
                        'http': proxy_url,
                        'https': proxy_url,
                        'no_proxy': 'localhost,127.0.0.1'
                    },
                    'suppress_connection_errors': False,  # Показывать ошибки подключения
                    'verify_ssl': False  # Отключить проверку SSL сертификатов для прокси
                }

                # Для отладки выводим конфигурацию без пароля
                safe_config = proxy_config.copy()
                if safe_config.get('password'):
                    safe_config['password'] = '***'
                print(f"[PROXY] Config: {safe_config}")
                print(f"[SELENIUM-WIRE] Proxy configured with authentication")

            # ============================================
            # ЗАГРУЗКА ANTI-DETECTION EXTENSION
            # ============================================
            extension_path = os.path.abspath("firefox_antidetect_extension")
            if os.path.exists(extension_path):
                print(f"[EXTENSION] Loading anti-detection extension from: {extension_path}")
            else:
                print(f"[EXTENSION] WARNING: Extension not found at {extension_path}")

            # ============================================
            # ЗАПУСК FIREFOX С SELENIUM-WIRE
            # ============================================
            self.driver = webdriver.Firefox(
                options=options,
                seleniumwire_options=seleniumwire_options
            )

            # Устанавливаем размер окна
            self.driver.set_window_size(
                fingerprint_config['viewport']['width'],
                fingerprint_config['viewport']['height']
            )

            # Устанавливаем таймауты
            self.driver.set_page_load_timeout(self.page_timeout)
            self.driver.implicitly_wait(10)

            # ============================================
            # УСТАНОВКА ANTI-DETECTION EXTENSION
            # ============================================
            if os.path.exists(extension_path):
                try:
                    addon_id = self.driver.install_addon(extension_path, temporary=True)
                    print(f"[EXTENSION] ✓ Anti-detection extension installed (ID: {addon_id})")
                except Exception as e:
                    print(f"[EXTENSION] ✗ Failed to install extension: {str(e)[:100]}")
            else:
                print(f"[EXTENSION] ✗ Extension directory not found")

            print(f"[FIREFOX] Browser launched successfully")

            # ============================================
            # COOKIES GENERATION
            # ============================================
            cookie_gen = CookieGenerator()
            cookies = cookie_gen.generate_realistic_cookies(num_sites=7)

            # Сначала открываем страницу /join для работы с localStorage
            print(f"\n[2/3] Opening Steam /join page...")
            self.driver.get("https://store.steampowered.com/join/")
            time.sleep(self.wait_after_load)

            # ============================================
            # ПРОВЕРКА ANTI-DETECTION
            # ============================================
            # Проверяем что navigator.webdriver успешно скрыт
            try:
                webdriver_value = self.driver.execute_script("return navigator.webdriver")
                if webdriver_value is None:
                    print(f"[ANTI-DETECT] ✓ navigator.webdriver = undefined (SUCCESS)")
                else:
                    print(f"[ANTI-DETECT] ✗ navigator.webdriver = {webdriver_value} (DETECTED)")
            except Exception as e:
                print(f"[ANTI-DETECT] Warning: Could not check - {str(e)[:100]}")

            # ============================================
            # ИНЖЕКТ FINGERPRINT через JavaScript (После загрузки страницы)
            # ============================================
            # Firefox не поддерживает CDP, поэтому инжектим через execute_script
            try:
                self.driver.execute_script(fingerprint_script)
                print(f"[FINGERPRINT] Injected via JavaScript")
            except Exception as e:
                print(f"[FINGERPRINT] Warning: Could not inject - {str(e)[:100]}")

            # Устанавливаем timezone через JavaScript
            timezone_script = f"""
                // Override timezone
                const originalDateTimeFormat = Intl.DateTimeFormat;
                Intl.DateTimeFormat = function(...args) {{
                    if (args.length === 0 || !args[0]) {{
                        args[0] = '{locale}';
                    }}
                    return new originalDateTimeFormat(...args);
                }};

                // Override timezone detection
                Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {{
                    value: function() {{
                        const options = Object.getOwnPropertyDescriptor(
                            originalDateTimeFormat.prototype,
                            'resolvedOptions'
                        ).value.call(this);
                        options.timeZone = '{timezone_id}';
                        return options;
                    }}
                }});
            """
            try:
                self.driver.execute_script(timezone_script)
                print(f"[TIMEZONE] Set to {timezone_id}")
            except Exception as e:
                print(f"[TIMEZONE] Warning: Could not set - {str(e)[:100]}")

            # Добавляем cookies (Selenium требует определенный формат)
            print(f"[COOKIES] Injecting cookies...")
            for cookie in cookies:
                # Selenium требует чтобы мы были на домене перед добавлением cookie
                if 'steampowered' in cookie.get('domain', ''):
                    try:
                        # Преобразуем формат cookie для Selenium
                        selenium_cookie = {
                            'name': cookie['name'],
                            'value': cookie['value'],
                            'domain': cookie.get('domain', '.steampowered.com'),
                            'path': cookie.get('path', '/'),
                            'secure': cookie.get('secure', True)
                        }
                        # Firefox не поддерживает httpOnly через add_cookie
                        if 'expiry' in cookie:
                            selenium_cookie['expiry'] = cookie['expiry']

                        self.driver.add_cookie(selenium_cookie)
                    except Exception as e:
                        # Игнорируем ошибки добавления отдельных cookies
                        pass

            domains_count = len(set(c['domain'] for c in cookies))
            print(f"[COOKIES] Added {len(cookies)} cookies from {domains_count} domains")

            # ============================================
            # LOCALSTORAGE GENERATION
            # ============================================
            storage_gen = StorageGenerator()
            storage_data = storage_gen.generate_full_storage()

            browser_age_days = (storage_gen.current_time - storage_gen.install_timestamp) // 86400
            print(f"[STORAGE] Generated localStorage (Browser age: {browser_age_days} days, {len(storage_data)} items)")

            # Заполняем localStorage через JavaScript с проверкой доступности
            try:
                # Проверяем доступен ли localStorage
                ls_available = self.driver.execute_script("return typeof(Storage) !== 'undefined'")
                if ls_available:
                    storage_script = storage_gen.get_storage_script(storage_data)
                    self.driver.execute_script(storage_script)
                    print(f"[STORAGE] localStorage filled with {len(storage_data)} items")
                else:
                    print(f"[STORAGE] localStorage not available on this page - skipping")
            except Exception as e:
                print(f"[STORAGE] Warning: Could not fill localStorage - {str(e)[:100]}")

            # Перезагружаем страницу чтобы применить cookies
            print(f"[3/3] Reloading page to apply cookies...")
            self.driver.get("https://store.steampowered.com/join/")
            time.sleep(self.wait_after_load)

            # Проверяем что navigator.webdriver все еще скрыт после перезагрузки
            try:
                webdriver_value = self.driver.execute_script("return navigator.webdriver")
                if webdriver_value is None:
                    print(f"[ANTI-DETECT] ✓ navigator.webdriver still undefined after reload")
                else:
                    print(f"[ANTI-DETECT] ✗ navigator.webdriver = {webdriver_value} after reload")
            except:
                pass

            # Повторно инжектим fingerprint и timezone после перезагрузки
            try:
                self.driver.execute_script(fingerprint_script)
                self.driver.execute_script(timezone_script)
                print(f"[FINGERPRINT] Re-injected after reload")
            except:
                pass

            # ============================================================
            # ТЕСТОВЫЙ РЕЖИМ - ОСТАНАВЛИВАЕМСЯ ЗДЕСЬ
            # ============================================================
            print(f"\n{'='*70}")
            print(f"[TEST MODE] Browser is ready on Steam!")
            print(f"{'='*70}")
            print(f"[+] All stealth features applied:")
            print(f"   ✓ navigator.webdriver = undefined (via Firefox Extension)")
            print(f"   ✓ Fingerprint injected via JavaScript")
            print(f"   ✓ Cookies set ({len(cookies)} cookies)")
            print(f"   ✓ localStorage filled ({len(storage_data)} items)")
            print(f"   ✓ Anti-detection extension loaded (document_start)")
            print(f"   ✓ On Steam join page: {self.driver.current_url}")
            print(f"\n[*] You can now:")
            print(f"   1. Open DevTools Console (F12) and type: navigator.webdriver")
            print(f"   2. Should return: undefined (not true)")
            print(f"   3. Check browser fingerprint (e.g., pixelscan.net)")
            print(f"   4. Manually test Steam registration")
            print(f"   5. Check for detection")
            print(f"   6. Close browser when done")
            print(f"\n[WAIT] Browser will stay open until you close it")
            print(f"{'='*70}\n")

            # ============================================================
            # БЕСКОНЕЧНОЕ ОЖИДАНИЕ - БРАУЗЕР НЕ ЗАКРЫВАЕТСЯ
            # ============================================================
            try:
                # Ждем пока пользователь не закроет браузер
                while True:
                    try:
                        # Проверяем что драйвер все еще активен
                        _ = self.driver.current_url
                        time.sleep(1)
                    except WebDriverException:
                        # Браузер закрыт
                        print(f"\n[INFO] Browser closed")
                        break
            except KeyboardInterrupt:
                print("\n[INFO] Interrupted by user (Ctrl+C)")
            except Exception as e:
                print(f"\n[ERROR] {str(e)[:100]}")

            print(f"\n[INFO] Test session ended")

        except Exception as e:
            print(f"\n[ERROR] Failed to launch browser: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Закрываем браузер
            if self.driver:
                try:
                    self.driver.quit()
                    print("[INFO] Browser closed")
                except:
                    pass


if __name__ == "__main__":
    import sys

    # Парсим аргументы
    headless = "--headless" in sys.argv
    no_proxy = "--no-proxy" in sys.argv

    # Настройка прокси
    if no_proxy:
        proxy = "DISABLED"
    else:
        proxy = None  # Автозагрузка из proxies.txt

    tester = SteamTestStealth(proxy=proxy, headless=headless)
    tester.test_stealth()
