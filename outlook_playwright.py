#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Outlook Account Creator - Playwright + Stealth версия
Полностью автоматическое создание аккаунта с обходом PerimeterX
Интегрированы stealth-модули из steam_test_stealth.py
"""
import sys
import os
import time
import random
import string
import asyncio
import math
import requests
from typing import Optional, Dict, Any, List, Tuple

# Playwright
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from playwright.async_api import TimeoutError as PlaywrightTimeout

# Stealth
try:
    from playwright_stealth import stealth_async
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    print("[WARN] playwright-stealth не установлен. Установите: pip install playwright-stealth")

# PyAutoGUI для реальных системных кликов (обход детекции)
try:
    import pyautogui
    pyautogui.FAILSAFE = False  # Отключаем защиту от автоклика
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("[WARN] pyautogui не установлен. Установите: pip install pyautogui")

# ============================================================================
# STEALTH МОДУЛИ (из steam_test_stealth.py)
# ============================================================================
try:
    from src.stealth.fingerprint_generator import FingerprintGenerator
    from src.stealth.cookie_generator import CookieGenerator
    from src.stealth.storage_generator import StorageGenerator
    from src.stealth.human_typing import HumanTypist
    from src.stealth.geo_config import get_geo_config, enrich_geo_config
    STEALTH_MODULES_AVAILABLE = True
    print("[STEALTH] ✓ Stealth modules loaded (fingerprint, cookies, storage, human_typing)")
except ImportError as e:
    STEALTH_MODULES_AVAILABLE = False
    print(f"[WARN] Stealth modules not available: {e}")

# ============================================================================
# MOBILE PROXY MANAGER (ротация IP)
# ============================================================================
try:
    from src.proxy.mobileproxy_manager import MobileProxyManager
    MOBILEPROXY_AVAILABLE = True
except ImportError:
    MOBILEPROXY_AVAILABLE = False
    print("[WARN] MobileProxyManager not available")

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================
HARDCODED_PROXY = "MPzEefwWaIUi:tc6aWZqR:pool.proxy.market:10000"

# Задержки (в миллисекундах)
TYPING_DELAY = (150, 350)       # Между символами
CLICK_DELAY = (80, 200)        # После клика
ACTION_DELAY = (200, 500)      # Между действиями
PAGE_DELAY = (800, 1500)       # Загрузка страницы

# Размеры экрана
VIEWPORT_OPTIONS = [
    {"width": 1920, "height": 1080},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
]

# Настройки капчи
CAPTCHA_HOLD_TIME = (3000, 5000)  # Время удержания (мс)
CAPTCHA_MAX_ATTEMPTS = 5          # Максимум попыток


async def human_delay(min_ms: int = 200, max_ms: int = 500):
    """Случайная задержка как у человека"""
    delay = random.uniform(min_ms, max_ms) / 1000
    await asyncio.sleep(delay)


def bezier_curve(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
    """Вычисляет точку на кривой Безье"""
    return (1-t)**3 * p0 + 3*(1-t)**2 * t * p1 + 3*(1-t) * t**2 * p2 + t**3 * p3


def generate_bezier_path(start: Tuple[float, float], end: Tuple[float, float],
                         steps: int = 30) -> List[Tuple[float, float]]:
    """Генерирует путь движения мыши по кривой Безье"""
    # Контрольные точки с рандомизацией
    ctrl1_x = start[0] + (end[0] - start[0]) * \
        random.uniform(0.2, 0.4) + random.uniform(-50, 50)
    ctrl1_y = start[1] + (end[1] - start[1]) * \
        random.uniform(0.1, 0.3) + random.uniform(-30, 30)
    ctrl2_x = start[0] + (end[0] - start[0]) * \
        random.uniform(0.6, 0.8) + random.uniform(-50, 50)
    ctrl2_y = start[1] + (end[1] - start[1]) * \
        random.uniform(0.7, 0.9) + random.uniform(-30, 30)

    path = []
    for i in range(steps + 1):
        t = i / steps
        # Добавляем небольшое ускорение/замедление
        t = t * t * (3 - 2 * t)  # Smoothstep

        x = bezier_curve(t, start[0], ctrl1_x, ctrl2_x, end[0])
        y = bezier_curve(t, start[1], ctrl1_y, ctrl2_y, end[1])

        # Добавляем микро-шум (тремор руки)
        x += random.uniform(-1, 1)
        y += random.uniform(-1, 1)

        path.append((x, y))

    return path


async def smooth_mouse_move(page: Page, to_x: float, to_y: float, from_pos: Tuple[float, float] = None):
    """Плавное движение мыши по кривой Безье"""
    if from_pos is None:
        # Получаем текущую позицию через evaluate
        from_pos = await page.evaluate("""() => {
            return {x: window.__mouseX || 100, y: window.__mouseY || 100};
        }""")
        from_pos = (from_pos.get('x', 100), from_pos.get('y', 100))

    path = generate_bezier_path(
        from_pos, (to_x, to_y), steps=random.randint(20, 40))

    for x, y in path:
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.005, 0.015))

    # Сохраняем позицию
    await page.evaluate(f"window.__mouseX = {to_x}; window.__mouseY = {to_y};")


async def human_type(page: Page, selector: str, text: str, typo_rate: float = 0.02):
    """Печатает текст человекоподобно с возможными опечатками"""
    element = await page.wait_for_selector(selector, timeout=15000)
    if not element:
        raise Exception(f"Элемент не найден: {selector}")

    await element.click()
    await human_delay(150, 350)

    for i, char in enumerate(text):
        # Случайная опечатка
        if random.random() < typo_rate and char.isalpha():
            wrong_char = random.choice('qwertyuiopasdfghjklzxcvbnm')
            await page.keyboard.type(wrong_char, delay=random.randint(30, 80))
            await human_delay(80, 200)
            await page.keyboard.press('Backspace')
            await human_delay(40, 100)

        # Печатаем символ
        delay = random.randint(TYPING_DELAY[0], TYPING_DELAY[1])
        await page.keyboard.type(char, delay=delay)

        # Иногда пауза
        if random.random() < 0.03:
            await human_delay(150, 400)

    await human_delay(80, 200)


async def human_click(page: Page, selector: str, timeout: int = 10000):
    """Человекоподобный клик с движением мыши по Безье"""
    element = await page.wait_for_selector(selector, timeout=timeout)
    if not element:
        raise Exception(f"Элемент не найден: {selector}")

    box = await element.bounding_box()
    if box:
        # Случайная точка внутри элемента
        x = box['x'] + random.uniform(box['width'] * 0.25, box['width'] * 0.75)
        y = box['y'] + random.uniform(box['height']
                                      * 0.25, box['height'] * 0.75)

        # Плавное движение
        await smooth_mouse_move(page, x, y)
        await human_delay(30, 100)

        # Клик
        await page.mouse.click(x, y)
    else:
        await element.click()

    await human_delay(CLICK_DELAY[0], CLICK_DELAY[1])


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


class OutlookPlaywrightCreator:
    """Создание Outlook аккаунта через Playwright + Stealth"""

    MONTH_NAMES = ["", "January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]

    def __init__(self, proxy: str = None, headless: bool = False, rotate_ip: bool = False):
        self.proxy = proxy or HARDCODED_PROXY
        self.headless = headless
        self.rotate_ip = rotate_ip  # Ротировать IP перед каждой регистрацией
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.proxy_manager = None
        self.geo_config = None  # Будет заполнено при ротации IP или в _setup_browser

        # Инициализируем MobileProxyManager если доступен
        if MOBILEPROXY_AVAILABLE and self.rotate_ip:
            try:
                self.proxy_manager = MobileProxyManager()
                print("[PROXY] ✓ MobileProxyManager initialized")
            except Exception as e:
                print(f"[PROXY] MobileProxyManager failed: {e}")
                self.proxy_manager = None

    async def _rotate_ip(self) -> bool:
        """Ротирует IP мобильного прокси перед регистрацией"""
        if not self.proxy_manager:
            print("[PROXY] IP rotation not available (no proxy manager)")
            return False

        print("\n" + "=" * 60)
        print("[PROXY] РОТАЦИЯ IP ПЕРЕД РЕГИСТРАЦИЕЙ")
        print("=" * 60)

        # Запускаем sync метод в executor
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.proxy_manager.change_ip_and_get_geo(wait_time=5)
        )

        if result.get('success'):
            new_ip = result.get('new_ip', 'unknown')
            geo = result.get('geo', {})

            print(f"[PROXY] ✓ Новый IP: {new_ip}")
            if geo.get('country'):
                print(
                    f"[PROXY] ✓ Страна: {geo['country']}, {geo.get('city', '')}")

            # Сохраняем geo_config для использования в браузере
            if geo.get('success'):
                self.geo_config = geo

            return True
        else:
            print(
                f"[PROXY] ✗ Ротация не удалась: {result.get('message', 'unknown error')}")
            return False

    def _parse_proxy(self) -> Optional[Dict[str, Any]]:
        """Парсит строку прокси"""
        if not self.proxy:
            return None

        proxy_str = self.proxy

        # Формат: user:pass@host:port или user:pass:host:port
        if '@' in proxy_str:
            auth, server = proxy_str.split('@', 1)
            username, password = auth.split(':', 1)
            host, port = server.split(':', 1)
        elif proxy_str.count(':') >= 3:
            parts = proxy_str.split(':')
            if parts[1].isdigit():
                host, port, username, password = parts[0], parts[1], parts[2], parts[3]
            else:
                username, password, host, port = parts[0], parts[1], parts[2], parts[3]
        else:
            return None

        return {
            "server": f"http://{host}:{port}",
            "username": username,
            "password": password
        }

    @staticmethod
    def _generate_identity() -> Dict[str, Any]:
        """Генерирует случайную личность"""
        first_names = ["Liam", "Noah", "Oliver", "Ethan", "Mason", "Logan", "Lucas", "Henry", "James", "Benjamin",
                       "Emma", "Olivia", "Ava", "Sophia", "Isabella", "Mia", "Charlotte", "Amelia", "Harper", "Evelyn"]
        last_names = ["Smith", "Johnson", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor", "Anderson", "Thomas",
                      "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson", "Clark", "Lewis"]

        first = random.choice(first_names)
        last = random.choice(last_names)
        suffix = random.randint(1000, 9999)
        username = f"{first.lower()}{last.lower()}{suffix}"

        password_chars = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(random.choices(password_chars, k=16))

        year = random.randint(1985, 2000)
        month = random.randint(1, 12)
        day = random.randint(1, 28)

        return {
            "first": first,
            "last": last,
            "username": username,
            "password": password,
            "birth_year": year,
            "birth_month": month,
            "birth_day": day,
            "email": f"{username}@outlook.com"
        }

    async def _detect_proxy_geo(self) -> Optional[Dict]:
        """Определяет геолокацию по IP прокси"""
        if not self.proxy:
            return None

        try:
            # Парсим прокси для запроса
            proxy_config = self._parse_proxy()
            if not proxy_config:
                return None

            # Используем ip-api.com для определения геолокации
            # Делаем запрос через прокси
            proxies = {
                'http': proxy_config['server'].replace('http://', ''),
                'https': proxy_config['server'].replace('http://', '')
            }

            # Простой запрос без прокси (определяем IP)
            response = requests.get(
                "http://ip-api.com/json/?fields=status,country,countryCode,city,timezone,query",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    country = data.get('country', 'United States')
                    geo_config = get_geo_config(country)
                    geo_config = enrich_geo_config(geo_config)

                    # Добавляем информацию из API
                    geo_config['detected_ip'] = data.get('query', 'unknown')
                    geo_config['city'] = data.get('city', '')

                    if data.get('timezone'):
                        geo_config['timezone'] = data['timezone']

                    print(
                        f"[GEO] Detected: {country}, {geo_config.get('city', '')}")
                    print(
                        f"[GEO] Timezone: {geo_config['timezone']}, Locale: {geo_config['locale']}")
                    return geo_config
        except Exception as e:
            print(f"[GEO] Detection failed: {e}")

        # Fallback to default US config
        return enrich_geo_config(get_geo_config('United States')) if STEALTH_MODULES_AVAILABLE else None

    async def _setup_browser(self):
        """Настраивает браузер с полным stealth (FingerprintGenerator + Cookies + Storage)"""
        self.playwright = await async_playwright().start()

        # === ОПРЕДЕЛЕНИЕ ГЕОЛОКАЦИИ ===
        # Используем geo_config от ротации IP если уже есть, иначе определяем
        if not hasattr(self, 'geo_config') or not self.geo_config:
            self.geo_config = await self._detect_proxy_geo() if STEALTH_MODULES_AVAILABLE else None

        # === ГЕНЕРАЦИЯ FINGERPRINT ===
        if STEALTH_MODULES_AVAILABLE:
            self.fingerprint_config = FingerprintGenerator.generate(
                browser_type='chrome')
            viewport = self.fingerprint_config['viewport']
            chrome_version = "131.0.0.0"  # Актуальная версия

            # Генерируем fingerprint script
            self.fingerprint_script = FingerprintGenerator.get_injector_script(
                self.fingerprint_config,
                browser_version=chrome_version,
                browser_type='chrome'
            )

            print(f"[FINGERPRINT] Generated:")
            print(
                f"  WebGL: {self.fingerprint_config['webgl']['vendor'][:30]}...")
            print(
                f"  Hardware: {self.fingerprint_config['hardware']['cores']} cores, {self.fingerprint_config['hardware']['memory']}GB")
            print(f"  Canvas noise: {self.fingerprint_config['canvas_noise']}")
        else:
            viewport = random.choice(VIEWPORT_OPTIONS)
            chrome_version = "131.0.0.0"
            self.fingerprint_config = None
            self.fingerprint_script = None

        # Прокси
        proxy_config = self._parse_proxy()

        print(f"[BROWSER] Запуск Chromium (Playwright + Full Stealth)...")
        print(f"[BROWSER] Viewport: {viewport['width']}x{viewport['height']}")
        if proxy_config:
            print(f"[BROWSER] Proxy: {proxy_config['server']}")

        # Аргументы для Chromium (stealth)
        chromium_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--ignore-certificate-errors',
            f'--window-size={viewport["width"]},{viewport["height"]}',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
        ]

        # Используем Chromium (лучше stealth поддержка)
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=chromium_args,
        )

        # User-Agent для Chrome
        user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36"

        # Locale и timezone из geo_config
        locale = self.geo_config['locale'] if self.geo_config else 'en-US'
        timezone_id = self.geo_config['timezone'] if self.geo_config else 'America/New_York'

        # Создаём контекст с настройками
        context_options = {
            "viewport": viewport,
            "locale": locale,
            "timezone_id": timezone_id,
            "user_agent": user_agent,
            "ignore_https_errors": True,
            "java_script_enabled": True,
            "bypass_csp": True,
            "color_scheme": random.choice(['light', 'dark']),
        }

        if proxy_config:
            context_options["proxy"] = proxy_config

        self.context = await self.browser.new_context(**context_options)

        # === ИНЖЕКТ FINGERPRINT SCRIPT (КРИТИЧНО - ДО загрузки страниц!) ===
        if self.fingerprint_script:
            await self.context.add_init_script(self.fingerprint_script)
            print("[FINGERPRINT] ✓ Injected via add_init_script")

        self.page = await self.context.new_page()

        # Применяем playwright-stealth если доступен
        if STEALTH_AVAILABLE:
            await stealth_async(self.page)
            print("[STEALTH] playwright-stealth применён ✓")

        # === ДОБАВЛЯЕМ COOKIES (после создания страницы) ===
        if STEALTH_MODULES_AVAILABLE:
            await self._inject_cookies()
            await self._inject_storage()

        # Проверяем webdriver
        webdriver_check = await self.page.evaluate("() => navigator.webdriver")
        print(f"[STEALTH] navigator.webdriver = {webdriver_check}")

        # Проверяем WebGL
        webgl_vendor = await self.page.evaluate("() => { try { const gl = document.createElement('canvas').getContext('webgl'); return gl.getParameter(37445); } catch(e) { return 'error'; } }")
        print(f"[STEALTH] WebGL vendor = {webgl_vendor[:40]}...")

    async def _inject_cookies(self):
        """Инжектирует реалистичные cookies"""
        if not STEALTH_MODULES_AVAILABLE:
            return

        try:
            cookie_gen = CookieGenerator()

            # Генерируем cookies от популярных сайтов
            all_cookies = cookie_gen.generate_realistic_cookies(num_sites=5)

            # Добавляем Microsoft-специфичные cookies
            ms_cookies = cookie_gen._generate_microsoft_cookies()
            all_cookies.extend(ms_cookies)

            # Фильтруем cookies для outlook.com домена
            # Playwright требует сначала перейти на домен
            # Поэтому сохраняем для добавления после первого перехода
            self.pending_cookies = all_cookies

            print(
                f"[COOKIES] Prepared {len(all_cookies)} cookies from popular sites")
        except Exception as e:
            print(f"[COOKIES] Error: {e}")

    async def _inject_storage(self):
        """Инжектирует localStorage данные"""
        if not STEALTH_MODULES_AVAILABLE:
            return

        try:
            storage_gen = StorageGenerator()
            storage_data = storage_gen.generate_full_storage(self.geo_config)
            storage_script = storage_gen.get_storage_script(storage_data)

            # Сохраняем для выполнения после загрузки страницы
            self.pending_storage_script = storage_script

            print(f"[STORAGE] Prepared {len(storage_data)} localStorage items")
        except Exception as e:
            print(f"[STORAGE] Error: {e}")

    async def _apply_cookies_and_storage(self):
        """Применяет cookies и localStorage после загрузки страницы"""
        # Добавляем cookies для текущего домена
        if hasattr(self, 'pending_cookies') and self.pending_cookies:
            try:
                for cookie in self.pending_cookies:
                    domain = cookie.get('domain', '')
                    # Пропускаем cookies для других доменов
                    if 'microsoft' in domain or 'live' in domain or 'outlook' in domain:
                        try:
                            # Playwright требует url или domain
                            cookie_data = {
                                'name': cookie['name'],
                                'value': cookie['value'],
                                'domain': domain,
                                'path': cookie.get('path', '/'),
                            }
                            if 'expires' in cookie:
                                cookie_data['expires'] = cookie['expires']
                            await self.context.add_cookies([cookie_data])
                        except Exception:
                            pass  # Игнорируем ошибки отдельных cookies
                print(f"[COOKIES] ✓ Applied Microsoft cookies")
            except Exception as e:
                print(f"[COOKIES] Error applying: {e}")

        # Выполняем localStorage скрипт
        if hasattr(self, 'pending_storage_script') and self.pending_storage_script:
            try:
                await self.page.evaluate(self.pending_storage_script)
                print(f"[STORAGE] ✓ Applied localStorage data")
            except Exception as e:
                print(f"[STORAGE] Error applying: {e}")

    async def _get_captcha_frame(self) -> Optional[Any]:
        """Находит iframe с капчей и возвращает его frame (включая вложенные)"""

        async def find_nested_frames(parent_frame, depth=0):
            """Рекурсивно ищет вложенные frame"""
            frames_found = []
            try:
                iframes = await parent_frame.query_selector_all('iframe')
                for iframe in iframes:
                    try:
                        style = await iframe.get_attribute('style') or ''
                        if 'display: none' in style.lower() or 'display:none' in style.lower():
                            continue
                        box = await iframe.bounding_box()
                        if not box or box['width'] < 50 or box['height'] < 20:
                            continue
                        child_frame = await iframe.content_frame()
                        if child_frame:
                            frames_found.append(child_frame)
                            # Рекурсивно ищем глубже
                            deeper = await find_nested_frames(child_frame, depth + 1)
                            frames_found.extend(deeper)
                    except:
                        continue
            except:
                pass
            return frames_found

        # Ищем iframe капчи на главной странице
        iframes = await self.page.query_selector_all('iframe')

        for iframe in iframes:
            try:
                title = await iframe.get_attribute('title') or ''
                src = await iframe.get_attribute('src') or ''
                style = await iframe.get_attribute('style') or ''

                if ('human' in title.lower() or 'verification' in title.lower() or
                        'hsprotect' in src.lower() or 'captcha' in src.lower()):

                    if 'display: none' not in style.lower() and 'display:none' not in style.lower():
                        box = await iframe.bounding_box()
                        if box and box['width'] > 50 and box['height'] > 20:
                            if not hasattr(self, '_iframe_logged'):
                                print(
                                    f"[CAPTCHA] Найден внешний iframe: title='{title}', size={box['width']}x{box['height']}")
                                self._iframe_logged = True

                            frame = await iframe.content_frame()
                            if frame:
                                # Ищем вложенные iframe
                                nested = await find_nested_frames(frame)
                                if nested:
                                    print(
                                        f"[CAPTCHA] Найдено {len(nested)} вложенных iframe")
                                    # Возвращаем самый глубокий
                                    return nested[-1]
                                return frame
            except:
                continue

        return None

    async def _find_captcha_button(self, frame=None) -> Optional[Any]:
        """Ищет кнопку Press & Hold капчи в заданном frame или на главной странице"""

        # Определяем где искать
        target = frame if frame else self.page
        context_name = "iframe" if frame else "main page"

        # Отладка: смотрим что внутри iframe (только один раз)
        if frame and not hasattr(self, '_debug_logged'):
            self._debug_logged = True
            try:
                debug_info = await frame.evaluate("""() => {
                    const body = document.body;
                    if (!body) return {error: 'no body'};
                    
                    const allButtons = document.querySelectorAll('[role="button"], button, [tabindex]');
                    const btns = [];
                    for (let b of allButtons) {
                        btns.push({
                            tag: b.tagName,
                            id: b.id || '',
                            role: b.getAttribute('role') || '',
                            aria: b.getAttribute('aria-label') || '',
                            text: (b.innerText || '').substring(0, 50),
                            w: b.offsetWidth,
                            h: b.offsetHeight
                        });
                    }
                    return {
                        url: location.href,
                        bodyText: (body.innerText || '').substring(0, 200),
                        buttons: btns
                    };
                }""")
                print(f"[DEBUG] iframe содержимое: {debug_info}")
            except Exception as e:
                print(f"[DEBUG] Ошибка чтения iframe: {e}")

        # Селекторы для кнопки "hold" (Microsoft PerimeterX)
        selectors = [
            # Основные по aria-label (& может быть экранирован)
            '[aria-label*="Press"][aria-label*="Hold"]',
            '[aria-label*="Hold Human"]',
            '[aria-label*="hold" i][role="button"]',
            '[aria-label*="Hold" i]',
            # Кнопка с текстом "hold"
            'div[role="button"]:has-text("hold")',
            '[role="button"]:has-text("hold")',
            # По ID паттерну (динамические ID)
            'div[role="button"][tabindex="0"]',
            # Контейнер
            '#px-captcha [role="button"]',
        ]

        for sel in selectors:
            try:
                elements = await target.query_selector_all(sel)
                for el in elements:
                    try:
                        visible = await el.is_visible()
                        if not visible:
                            continue

                        box = await el.bounding_box()
                        if not box or box['width'] < 50 or box['height'] < 20:
                            continue

                        text = ''
                        try:
                            text = await el.inner_text() or ''
                        except:
                            pass
                        aria = await el.get_attribute('aria-label') or ''

                        # Ищем кнопку с "hold" но не "completed"
                        text_lower = text.lower() if text else ''
                        aria_lower = aria.lower() if aria else ''

                        if 'completed' in aria_lower or 'completed' in text_lower:
                            continue

                        if 'hold' in text_lower or 'hold' in aria_lower or \
                           ('button' in aria_lower and box['width'] > 100):
                            print(
                                f"[CAPTCHA] Найдена кнопка в {context_name}: text='{text[:30]}', aria='{aria[:50]}'")
                            return el
                    except Exception as e:
                        continue
            except Exception as e:
                continue

        # JavaScript fallback для frame
        if frame:
            try:
                btn = await frame.evaluate_handle("""() => {
                    // Ищем div[role="button"] с aria-label содержащим "Hold"
                    const buttons = document.querySelectorAll('[role="button"]');
                    for (let btn of buttons) {
                        const aria = (btn.getAttribute('aria-label') || '').toLowerCase();
                        const text = (btn.innerText || '').toLowerCase();
                        
                        if ((aria.includes('hold') || text.includes('hold')) &&
                            !aria.includes('completed') && !text.includes('completed') &&
                            btn.offsetWidth > 50) {
                            return btn;
                        }
                    }
                    return null;
                }""")

                if btn:
                    el = btn.as_element()
                    if el:
                        print(f"[CAPTCHA] Найдена кнопка через JS fallback")
                        return el
            except:
                pass

        return None

    async def _get_captcha_click_coordinates(self, frame=None) -> Optional[tuple]:
        """Получает координаты для клика по капче (ВСЕГДА в координатах viewport)"""

        # ВАЖНО: page.mouse работает в координатах viewport главной страницы
        # Поэтому получаем координаты iframe элемента с главной страницы

        try:
            iframes = await self.page.query_selector_all('iframe')
            for iframe in iframes:
                title = await iframe.get_attribute('title') or ''
                src = await iframe.get_attribute('src') or ''
                style = await iframe.get_attribute('style') or ''

                # Пропускаем скрытые
                if 'display: none' in style.lower() or 'display:none' in style.lower():
                    continue

                if 'verification' in title.lower() or 'human' in title.lower() or 'hsprotect' in src.lower():
                    box = await iframe.bounding_box()
                    if box and box['width'] > 50 and box['height'] > 30:
                        # Кликаем ПРАВЕЕ центра (там кнопка "hold", слева - "Accessible challenge")
                        # Accessible challenge слева ~25%, hold справа ~75%
                        x = box['x'] + box['width'] * 0.75  # Правая часть
                        y = box['y'] + box['height'] * \
                            0.5  # Центр по вертикали
                        print(
                            f"[CAPTCHA] Координаты из iframe (viewport): x={x:.0f}, y={y:.0f}")
                        print(
                            f"[CAPTCHA] iframe box: x={box['x']:.0f}, y={box['y']:.0f}, w={box['width']:.0f}, h={box['height']:.0f}")
                        return (x, y, box)
        except Exception as e:
            print(f"[CAPTCHA] Ошибка получения координат iframe: {e}")

        # Fallback: ищем #px-captcha на главной странице
        try:
            px = await self.page.query_selector('#px-captcha')
            if px:
                box = await px.bounding_box()
                if box and box['width'] > 50:
                    # Кликаем правее (кнопка hold справа)
                    x = box['x'] + box['width'] * 0.75
                    y = box['y'] + box['height'] * 0.5
                    print(
                        f"[CAPTCHA] Координаты из #px-captcha: x={x:.0f}, y={y:.0f}")
                    return (x, y, box)
        except:
            pass

        return None

    async def _hold_by_coordinates(self, x: float, y: float, frame=None) -> bool:
        """Нажимает и удерживает по координатам используя РЕАЛЬНЫЕ системные клики"""

        # Используем pyautogui для реальных кликов (обход детекции)
        if PYAUTOGUI_AVAILABLE:
            return await self._hold_with_pyautogui(x, y, frame)
        else:
            return await self._hold_with_playwright(x, y, frame)

    async def _hold_with_pyautogui(self, x: float, y: float, frame=None) -> bool:
        """Реальные системные клики через pyautogui"""
        try:
            # Получаем позицию окна браузера через CDP
            try:
                window_info = await self.page.evaluate("""() => {
                    return {
                        screenX: window.screenX,
                        screenY: window.screenY,
                        outerWidth: window.outerWidth,
                        outerHeight: window.outerHeight,
                        innerWidth: window.innerWidth,
                        innerHeight: window.innerHeight
                    };
                }""")

                # Вычисляем смещение от края окна до viewport
                chrome_offset_x = (
                    window_info['outerWidth'] - window_info['innerWidth']) // 2
                chrome_offset_y = window_info['outerHeight'] - \
                    window_info['innerHeight'] - chrome_offset_x

                # Конвертируем viewport координаты в экранные
                screen_x = int(window_info['screenX'] + chrome_offset_x + x)
                screen_y = int(window_info['screenY'] + chrome_offset_y + y)

                print(
                    f"[CAPTCHA] Окно браузера: screenX={window_info['screenX']}, screenY={window_info['screenY']}")
                print(
                    f"[CAPTCHA] Экранные координаты: ({screen_x}, {screen_y})")
            except Exception as e:
                print(f"[CAPTCHA] Не удалось получить позицию окна: {e}")
                # Fallback - используем viewport координаты как есть
                screen_x = int(x)
                screen_y = int(y)

            # Плавно двигаем мышь к позиции
            print(
                f"[CAPTCHA] ▶ PyAutoGUI: двигаем мышь к ({screen_x}, {screen_y})...")
            pyautogui.moveTo(screen_x, screen_y, duration=0.3)
            await asyncio.sleep(0.2)

            # Нажимаем и держим
            print("[CAPTCHA] ▶ PyAutoGUI: нажимаем и удерживаем...")
            pyautogui.mouseDown()

            # Определяем контекст для мониторинга
            eval_context = frame if frame else self.page

            # Удерживаем до 15 секунд (но отпускаем раньше при успехе)
            max_hold_time = 15000
            start_time = time.time()
            success = False
            last_log = 0

            while (time.time() - start_time) * 1000 < max_hold_time:
                await asyncio.sleep(0.03)  # Проверяем чаще
                elapsed_ms = int((time.time() - start_time) * 1000)

                # Микро-движения (реальные!)
                dx = random.uniform(-2, 2)
                dy = random.uniform(-2, 2)
                pyautogui.moveTo(screen_x + dx, screen_y + dy, duration=0.01)

                # Проверяем прогресс каждые 100мс (быстрее!)
                if elapsed_ms - last_log >= 100:
                    last_log = elapsed_ms

                    try:
                        # Проверяем состояние капчи
                        status = await self.page.evaluate("""() => {
                            const body = document.body;
                            const text = body ? body.innerText.toLowerCase() : '';
                            
                            // 1. Исчезла надпись "press" - СРАЗУ отпускаем!
                            if (!text.includes('press')) {
                                return {status: 'press_gone', reason: 'no press text'};
                            }
                            
                            // 2. Появились три точки (loading) - отпускаем!
                            // Ищем через iframe
                            const iframes = document.querySelectorAll('iframe');
                            for (let iframe of iframes) {
                                try {
                                    const doc = iframe.contentDocument;
                                    if (doc) {
                                        // Проверяем fetching-volume (три точки)
                                        const dots = doc.querySelector('.fetching-volume');
                                        if (dots && (dots.classList.contains('draw') || 
                                            getComputedStyle(dots).display !== 'none')) {
                                            return {status: 'dots_visible', reason: 'three dots appeared'};
                                        }
                                        
                                        // Проверяем aria-label кнопки
                                        const btns = doc.querySelectorAll('[role="button"]');
                                        for (let btn of btns) {
                                            const aria = (btn.getAttribute('aria-label') || '').toLowerCase();
                                            if (aria.includes('completed') || aria.includes('please wait')) {
                                                return {status: 'completed', reason: aria};
                                            }
                                        }
                                        
                                        // Проверяем checkmark
                                        const check = doc.querySelector('#checkmark');
                                        if (check && check.classList.contains('draw')) {
                                            return {status: 'checkmark', reason: 'checkmark visible'};
                                        }
                                    }
                                } catch(e) {}
                            }
                            
                            // 3. Капча исчезла
                            const px = document.querySelector('#px-captcha');
                            if (px && px.offsetHeight < 20) {
                                return {status: 'captcha_gone', reason: 'captcha hidden'};
                            }
                            
                            // 4. Текст изменился на wait/completed
                            if (text.includes('please wait') || text.includes('completed')) {
                                return {status: 'wait_text', reason: 'please wait text'};
                            }
                            
                            return {status: 'holding'};
                        }""")
                    except:
                        status = {'status': 'holding'}

                    st = status.get('status', 'holding')
                    reason = status.get('reason', '')

                    if st != 'holding':
                        print(f"[CAPTCHA] ✓ Отпускаем! {st}: {reason}")
                        success = True
                        break

                    # Логируем каждые 500мс
                    if elapsed_ms % 500 < 100:
                        print(f"[CAPTCHA] Удерживаем... {elapsed_ms}мс")

            # Отпускаем
            pyautogui.mouseUp()
            print("[CAPTCHA] ■ Кнопка отпущена (PyAutoGUI)")

            await asyncio.sleep(2)
            return success

        except Exception as e:
            print(f"[CAPTCHA] Ошибка PyAutoGUI: {e}")
            import traceback
            traceback.print_exc()
            try:
                pyautogui.mouseUp()
            except:
                pass
            return False

    async def _hold_with_playwright(self, x: float, y: float, frame=None) -> bool:
        """Fallback: клики через Playwright (менее надёжно)"""
        try:
            print(f"[CAPTCHA] ▶ Playwright: клик по ({x:.0f}, {y:.0f})...")

            await smooth_mouse_move(self.page, x, y)
            await human_delay(100, 200)

            await self.page.mouse.down()
            print("[CAPTCHA] ▶ Playwright: кнопка нажата...")

            eval_context = frame if frame else self.page
            max_hold_time = 15000
            start_time = time.time()
            success = False
            last_log = 0

            while (time.time() - start_time) * 1000 < max_hold_time:
                await asyncio.sleep(0.05)
                elapsed_ms = int((time.time() - start_time) * 1000)

                dx = random.uniform(-1.5, 1.5)
                dy = random.uniform(-1.5, 1.5)
                await self.page.mouse.move(x + dx, y + dy)

                if elapsed_ms - last_log >= 500:
                    last_log = elapsed_ms
                    print(f"[CAPTCHA] Удерживаем... {elapsed_ms}мс")

            await self.page.mouse.up()
            print("[CAPTCHA] ■ Кнопка отпущена")

            await asyncio.sleep(2)
            return success

        except Exception as e:
            print(f"[CAPTCHA] Ошибка Playwright: {e}")
            try:
                await self.page.mouse.up()
            except:
                pass
            return False

    async def _dispatch_pointer_events(self, x: float, y: float, event_type: str):
        """Диспатчит нативные PointerEvent через JavaScript"""
        await self.page.evaluate(f"""(coords) => {{
            const el = document.elementFromPoint(coords.x, coords.y);
            if (!el) return;
            
            const eventInit = {{
                bubbles: true,
                cancelable: true,
                view: window,
                clientX: coords.x,
                clientY: coords.y,
                screenX: coords.x + window.screenX,
                screenY: coords.y + window.screenY,
                pointerId: 1,
                pointerType: 'mouse',
                isPrimary: true,
                button: 0,
                buttons: '{event_type}' === 'pointerdown' ? 1 : 0,
                pressure: '{event_type}' === 'pointerdown' ? 0.5 : 0,
                width: 1,
                height: 1,
                tiltX: 0,
                tiltY: 0,
                twist: 0
            }};
            
            const event = new PointerEvent('{event_type}', eventInit);
            el.dispatchEvent(event);
            
            // Также диспатчим MouseEvent для совместимости
            const mouseEvent = new MouseEvent('{event_type}'.replace('pointer', 'mouse'), {{
                bubbles: true,
                cancelable: true,
                view: window,
                clientX: coords.x,
                clientY: coords.y,
                button: 0,
                buttons: '{event_type}' === 'pointerdown' ? 1 : 0
            }});
            el.dispatchEvent(mouseEvent);
        }}""", {"x": x, "y": y})

    async def _solve_captcha(self) -> bool:
        """Автоматически решает Press & Hold капчу с повторными попытками"""
        print("[CAPTCHA] === Начало решения капчи ===")

        max_retries = 10  # Максимум попыток
        self.captcha_frame = None  # Сохраняем frame для использования в других методах

        for retry in range(max_retries):
            print(f"\n[CAPTCHA] Попытка {retry + 1}/{max_retries}")

            # Сначала ищем iframe с капчей
            button = None
            frame = None

            for attempt in range(10):
                # Пробуем найти iframe
                frame = await self._get_captcha_frame()

                if frame:
                    if attempt == 0:  # Логируем только первый раз
                        print(f"[CAPTCHA] Ищем кнопку в iframe...")
                    button = await self._find_captcha_button(frame)
                    self.captcha_frame = frame
                else:
                    if attempt == 0:
                        print(
                            f"[CAPTCHA] Iframe не найден, ищем на главной странице...")
                    button = await self._find_captcha_button(None)

                if button:
                    break

                if attempt == 4:  # На 5-й попытке сообщаем
                    print(f"[CAPTCHA] Кнопка пока не найдена, продолжаем искать...")

                await asyncio.sleep(0.5)

            if not button:
                print("[CAPTCHA] Кнопка не найдена, пробуем клик по координатам...")

                # Пробуем клик по координатам как fallback
                coords = await self._get_captcha_click_coordinates(frame)
                if coords:
                    x, y, box = coords
                    success = await self._hold_by_coordinates(x, y, frame)
                    if success:
                        print("[CAPTCHA] ✓ Капча пройдена через координаты!")
                        return True

                # Проверяем не прошла ли капча
                is_done = await self._check_captcha_success()
                if is_done:
                    print("[CAPTCHA] ✓ Капча уже пройдена!")
                    return True
                await asyncio.sleep(2)
                continue

            # Пробуем нажать и удержать (передаём frame для проверки прогресса)
            success = await self._hold_captcha_button(button, frame)

            if success:
                print("[CAPTCHA] ✓ Капча пройдена!")
                return True

            # Ждём перед следующей попыткой
            print(f"[CAPTCHA] Ожидание перед повтором...")
            await asyncio.sleep(2)

            # Проверяем не появилась ли ошибка
            error = await self._check_captcha_error()
            if error:
                print(f"[CAPTCHA] ⚠ Ошибка: {error}")

        print("[CAPTCHA] ✗ Не удалось пройти капчу после всех попыток")
        return False

    async def _check_captcha_success(self) -> bool:
        """Проверяет прошла ли капча успешно"""
        try:
            # Проверяем на главной странице
            result = await self.page.evaluate("""() => {
                const body = document.body.innerText.toLowerCase();
                // Проверяем исчезновение капчи или появление успеха
                if (body.includes('welcome') || body.includes('account created')) return true;
                
                // Проверяем #px-captcha
                const px = document.querySelector('#px-captcha');
                if (!px || px.offsetHeight < 20) return true;
                
                // Проверяем текст на странице
                if (!body.includes('hold') && !body.includes('prove you')) return true;
                
                return false;
            }""")

            if result:
                return True

            # Проверяем в iframe
            if hasattr(self, 'captcha_frame') and self.captcha_frame:
                try:
                    frame_result = await self.captcha_frame.evaluate("""() => {
                        const body = document.body;
                        if (!body) return false;
                        
                        const text = body.innerText.toLowerCase();
                        
                        // Успех
                        if (text.includes('completed') || text.includes('please wait') || 
                            text.includes('verified')) {
                            return true;
                        }
                        
                        // Проверяем aria-label
                        const btns = document.querySelectorAll('[role="button"]');
                        for (let btn of btns) {
                            const aria = (btn.getAttribute('aria-label') || '').toLowerCase();
                            if (aria.includes('completed')) return true;
                        }
                        
                        // Checkmark
                        const check = document.querySelector('#checkmark');
                        if (check && check.classList.contains('draw')) return true;
                        
                        return false;
                    }""")
                    if frame_result:
                        return True
                except:
                    pass

            return result
        except:
            return False

    async def _check_captcha_error(self) -> Optional[str]:
        """Проверяет наличие ошибки капчи"""
        try:
            error = await self.page.evaluate("""() => {
                const body = document.body.innerText.toLowerCase();
                if (body.includes('try again')) return 'Try again';
                if (body.includes('error')) return 'Error detected';
                if (body.includes('failed')) return 'Failed';
                return null;
            }""")
            return error
        except:
            return None

    async def _check_block_error(self) -> Optional[str]:
        """Проверяет блокировку от Microsoft (unusual activity)"""
        try:
            error = await self.page.evaluate("""() => {
                const body = document.body.innerText.toLowerCase();
                
                // Блокировка - "We can't create your account"
                if (body.includes("can't create your account") || 
                    body.includes("cannot create your account") ||
                    body.includes("we can't create")) {
                    return 'BLOCKED: Account creation blocked';
                }
                
                // Unusual activity
                if (body.includes('unusual activity') || 
                    body.includes('suspicious activity')) {
                    return 'BLOCKED: Unusual activity detected';
                }
                
                // Temporary block
                if (body.includes('too many requests') ||
                    body.includes('try again later')) {
                    return 'RATE_LIMIT: Too many requests';
                }
                
                // Phone required
                if (body.includes('verify your phone') ||
                    body.includes('add a phone number')) {
                    return 'PHONE_REQUIRED: Phone verification needed';
                }
                
                // Generic block
                if (body.includes('something went wrong') && 
                    body.includes('trouble')) {
                    return 'BLOCKED: Generic block';
                }
                
                return null;
            }""")
            return error
        except:
            return None

    async def _hold_captcha_button(self, button, frame=None) -> bool:
        """Нажимает и удерживает кнопку капчи"""
        try:
            # Определяем контекст для evaluate (iframe или main page)
            eval_context = frame if frame else self.page

            text = ''
            aria = ''
            try:
                text = await button.inner_text() or ''
                aria = await button.get_attribute('aria-label') or ''
            except:
                pass
            print(f"[CAPTCHA] Кнопка: '{text[:20]}' aria='{aria[:40]}'")

            # Получаем координаты
            box = await button.bounding_box()
            if not box:
                print("[CAPTCHA] Не удалось получить координаты")
                return False

            center_x = box['x'] + box['width'] / 2 + random.uniform(-3, 3)
            center_y = box['y'] + box['height'] / 2 + random.uniform(-3, 3)
            print(
                f"[CAPTCHA] Координаты: ({center_x:.0f}, {center_y:.0f}), размер: {box['width']:.0f}x{box['height']:.0f}")

            # Плавно двигаем мышь к кнопке
            await smooth_mouse_move(self.page, center_x, center_y)
            await human_delay(100, 200)

            # Нажимаем и ДЕРЖИМ
            await self.page.mouse.down()
            print("[CAPTCHA] ▶ Кнопка нажата, удерживаем...")

            # Удерживаем до 15 секунд (пока прогресс не заполнится)
            max_hold_time = 15000  # 15 секунд максимум
            start_time = time.time()
            success = False
            last_log = 0

            while (time.time() - start_time) * 1000 < max_hold_time:
                await asyncio.sleep(0.05)

                elapsed_ms = int((time.time() - start_time) * 1000)

                # Микро-движения мышью
                dx = random.uniform(-1.5, 1.5)
                dy = random.uniform(-1.5, 1.5)
                await self.page.mouse.move(center_x + dx, center_y + dy)

                # Проверяем прогресс и успех каждые 500мс
                if elapsed_ms - last_log >= 500:
                    last_log = elapsed_ms

                    # Проверяем статус в контексте iframe/page
                    try:
                        status = await eval_context.evaluate("""() => {
                            const body = document.body;
                            const text = body ? body.innerText.toLowerCase() : '';
                            
                            // Проверяем checkmark / галочку
                            const checkEl = document.querySelector('#checkmark');
                            if (checkEl && checkEl.classList.contains('draw')) {
                                return {status: 'checkmark'};
                            }
                            
                            // Проверяем "please wait" или "completed"
                            if (text.includes('please wait') || text.includes('completed') || 
                                text.includes('verified') || text.includes('success')) {
                                return {status: 'text_success'};
                            }
                            
                            // Проверяем aria-label кнопки
                            const btns = document.querySelectorAll('[role="button"]');
                            for (let btn of btns) {
                                const aria = (btn.getAttribute('aria-label') || '').toLowerCase();
                                if (aria.includes('completed') || aria.includes('please wait')) {
                                    return {status: 'aria_success', aria: aria};
                                }
                            }
                            
                            // Ищем прогресс-бар (div со стилем width)
                            const progressEls = document.querySelectorAll('div[style*="width"]');
                            let maxWidth = 0;
                            for (let el of progressEls) {
                                const styleWidth = el.style.width;
                                if (styleWidth && styleWidth.includes('px')) {
                                    const w = parseInt(styleWidth) || 0;
                                    if (w > maxWidth) maxWidth = w;
                                }
                            }
                            
                            return {status: 'holding', progress: maxWidth};
                        }""")
                    except Exception as e:
                        status = {'status': 'holding', 'progress': 0}

                    if status:
                        st = status.get('status', '')
                        if st in ['checkmark', 'text_success', 'aria_success']:
                            extra = status.get('aria', '')
                            print(f"[CAPTCHA] ✓ Успех: {st} {extra}")
                            success = True
                            break

                        progress = status.get('progress', 0)
                        if progress > 0:
                            print(
                                f"[CAPTCHA] Прогресс: {progress}px ({elapsed_ms}мс)")
                        else:
                            print(f"[CAPTCHA] Удерживаем... {elapsed_ms}мс")

            # Отпускаем кнопку
            await self.page.mouse.up()
            print("[CAPTCHA] ■ Кнопка отпущена")

            # Ждём результат
            await asyncio.sleep(2)

            # Финальная проверка
            final = await self._check_captcha_success()
            if final or success:
                return True

            return False

        except Exception as e:
            print(f"[CAPTCHA] Ошибка: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def _check_and_solve_captcha(self) -> bool:
        """Проверяет наличие капчи и пытается решить"""
        print("[CAPTCHA] Проверяем наличие капчи...")

        # Ждём и проверяем капчу несколько раз
        for check in range(10):  # Проверяем 10 раз по 1 сек
            captcha_present = False
            captcha_reason = ""

            # Способ 1: #px-captcha
            try:
                px_captcha = await self.page.query_selector('#px-captcha')
                if px_captcha and await px_captcha.is_visible():
                    box = await px_captcha.bounding_box()
                    if box and box['height'] > 30:
                        captcha_present = True
                        captcha_reason = "#px-captcha"
            except:
                pass

            # Способ 2: iframe
            if not captcha_present:
                try:
                    iframes = await self.page.query_selector_all('iframe[src*="hsprotect"], iframe[title*="Human"]')
                    for iframe in iframes:
                        if await iframe.is_visible():
                            box = await iframe.bounding_box()
                            if box and box['width'] > 50:
                                captcha_present = True
                                captcha_reason = "iframe"
                                break
                except:
                    pass

            # Способ 3: текст на странице
            if not captcha_present:
                try:
                    body_text = await self.page.inner_text('body')
                    body_lower = body_text.lower()
                    if 'press and hold' in body_lower or "prove you're human" in body_lower or \
                       'hold' in body_lower and 'human' in body_lower:
                        captcha_present = True
                        captcha_reason = "text"
                except:
                    pass

            # Способ 4: ищем кнопку hold
            if not captcha_present:
                try:
                    hold_btn = await self.page.query_selector('[aria-label*="hold" i], button:has-text("hold"), [role="button"]:has-text("hold")')
                    if hold_btn and await hold_btn.is_visible():
                        captcha_present = True
                        captcha_reason = "hold button"
                except:
                    pass

            if captcha_present:
                print(
                    f"[CAPTCHA] ✓ Обнаружена капча ({captcha_reason}), решаем...")
                return await self._solve_captcha()

            # Проверяем не прошли ли мы уже дальше (успех без капчи)
            try:
                url = self.page.url.lower()
                if 'outlook' in url or 'office' in url or 'welcome' in url or 'inbox' in url:
                    print("[CAPTCHA] Уже на следующей странице, капча не нужна")
                    return True
            except:
                pass

            if check < 9:
                await asyncio.sleep(1)

        print("[CAPTCHA] Капча не обнаружена после 10 проверок")
        return True  # Возможно капчи нет

    async def _fill_email(self, identity: Dict) -> bool:
        """Заполняет email с проверкой занятости"""
        max_attempts = 5

        for attempt in range(1, max_attempts + 1):
            try:
                # Ждём поле email
                email_selector = 'input[name="MemberName"], input#MemberName, input[type="email"]'
                await self.page.wait_for_selector(email_selector, timeout=15000)

                # Очищаем если повтор
                if attempt > 1:
                    await self.page.fill(email_selector, '')
                    await human_delay(200, 400)

                # Вводим email
                await human_type(self.page, email_selector, identity["email"], typo_rate=0.02)
                await human_delay(300, 600)

                # Нажимаем Next
                next_btn = 'button#iSignupAction, button[type="submit"]'
                await human_click(self.page, next_btn)

                # Ждём ответа
                await human_delay(1500, 2500)

                # Проверяем появление поля пароля (успех)
                try:
                    password_field = await self.page.wait_for_selector(
                        'input[type="password"]', timeout=3000
                    )
                    if password_field and await password_field.is_visible():
                        print(f"[EMAIL] ✓ Принят: {identity['email']}")
                        return True
                except:
                    pass

                # Проверяем ошибку
                error_selectors = [
                    '#MemberNameError', 'div[id*="MemberNameError"]',
                    '.alert-error', '[role="alert"]'
                ]

                for sel in error_selectors:
                    try:
                        error_el = await self.page.query_selector(sel)
                        if error_el and await error_el.is_visible():
                            error_text = await error_el.inner_text()
                            if error_text:
                                print(f"[EMAIL] Ошибка: {error_text[:60]}")

                                # Если занят - генерируем новый
                                if any(kw in error_text.lower() for kw in ['taken', 'already', 'exist']):
                                    identity.update(self._generate_identity())
                                    print(
                                        f"[EMAIL] Новый: {identity['email']}")
                                break
                    except:
                        continue

            except Exception as e:
                print(f"[EMAIL] Ошибка попытки {attempt}: {e}")

        return False

    async def _fill_password(self, identity: Dict) -> bool:
        """Заполняет пароль"""
        try:
            await self.page.wait_for_selector('input[type="password"]', timeout=15000)
            await human_type(self.page, 'input[type="password"]', identity["password"], typo_rate=0.01)
            await human_delay(300, 600)

            await human_click(self.page, 'button#iSignupAction, button[type="submit"]')
            print("[PASSWORD] ✓ Введён")
            return True
        except Exception as e:
            print(f"[PASSWORD] Ошибка: {e}")
            return False

    async def _fill_birthdate(self, identity: Dict) -> bool:
        """Заполняет дату рождения (поддержка разных версий формы)"""
        month = identity["birth_month"]
        day = identity["birth_day"]
        year = identity["birth_year"]
        month_name = self.MONTH_NAMES[month] if 1 <= month <= 12 else "January"

        print(f"[BIRTH] Заполняем: {month_name} {day}, {year}")

        try:
            # Ждём появления любых элементов даты
            await self.page.wait_for_selector(
                'select#BirthMonth, select[name="BirthMonth"], button#BirthMonthDropdown, #DateOfBirthMonth',
                timeout=15000
            )

            await human_delay(300, 500)

            # === СТРАНА (если есть) ===
            country_selectors = [
                'select#Country',
                'select[name="Country"]',
                'select#CountryRegion',
                'select[aria-label*="Country"]',
            ]
            for sel in country_selectors:
                try:
                    country_el = await self.page.query_selector(sel)
                    if country_el and await country_el.is_visible():
                        # Выбираем США для консистентности
                        await self.page.select_option(sel, value='US')
                        print("[BIRTH] Страна: US")
                        await human_delay(200, 400)
                        break
                except:
                    try:
                        await self.page.select_option(sel, label='United States')
                        print("[BIRTH] Страна: United States")
                        await human_delay(200, 400)
                        break
                    except:
                        continue

            # === МЕСЯЦ ===
            month_selected = False

            # Fluent UI: #BirthMonthDropdown с label перекрывающим клик
            month_dropdown_selectors = [
                '#BirthMonthDropdown',  # Fluent UI
                'button#BirthMonthDropdown',
                '#BirthMonth',
                '[name="BirthMonth"]',
                'select#BirthMonth',
            ]

            for sel in month_dropdown_selectors:
                try:
                    dropdown = await self.page.query_selector(sel)
                    if not dropdown or not await dropdown.is_visible():
                        continue

                    tag_name = await dropdown.evaluate("el => el.tagName.toLowerCase()")
                    print(f"[BIRTH] Месяц dropdown: {sel} (tag: {tag_name})")

                    # Если это <select> - используем select_option
                    if tag_name == 'select':
                        try:
                            await self.page.select_option(sel, value=str(month))
                            print(f"[BIRTH] Месяц (select): {month}")
                            month_selected = True
                            break
                        except:
                            continue

                    # JavaScript клик - обходит перекрывающий label
                    await dropdown.evaluate("el => el.click()")
                    print(f"[BIRTH] JS клик на месяц")
                    await human_delay(400, 700)

                    # Ищем опцию с нужным месяцем
                    option_found = False

                    # Ждём появления listbox
                    await human_delay(300, 500)

                    # Ищем все опции
                    options = await self.page.query_selector_all('[role="option"]')
                    print(f"[BIRTH] Найдено опций месяца: {len(options)}")

                    for opt in options:
                        try:
                            text = (await opt.inner_text()).strip()
                            if text == month_name or month_name.lower() in text.lower():
                                # JS клик на опцию
                                await opt.evaluate("el => el.click()")
                                print(f"[BIRTH] Месяц: {text}")
                                month_selected = True
                                option_found = True
                                break
                        except:
                            continue

                    if option_found:
                        break

                    # Fallback по индексу (month - 1 т.к. может быть placeholder)
                    if len(options) >= month:
                        try:
                            await options[month - 1].evaluate("el => el.click()")
                            print(f"[BIRTH] Месяц по индексу: {month}")
                            month_selected = True
                            break
                        except:
                            pass

                    # Закрываем dropdown
                    await self.page.keyboard.press('Escape')
                    await human_delay(200, 300)

                except Exception as e:
                    print(f"[BIRTH] Ошибка месяц: {e}")
                    continue

            await human_delay(200, 400)

            # === ДЕНЬ ===
            day_selected = False

            day_dropdown_selectors = [
                '#BirthDayDropdown',  # Fluent UI
                'button#BirthDayDropdown',
                '#BirthDay',
                '[name="BirthDay"]',
                'select#BirthDay',
            ]

            for sel in day_dropdown_selectors:
                try:
                    dropdown = await self.page.query_selector(sel)
                    if not dropdown or not await dropdown.is_visible():
                        continue

                    tag_name = await dropdown.evaluate("el => el.tagName.toLowerCase()")
                    print(f"[BIRTH] День dropdown: {sel} (tag: {tag_name})")

                    if tag_name == 'select':
                        await self.page.select_option(sel, value=str(day))
                        print(f"[BIRTH] День (select): {day}")
                        day_selected = True
                        break

                    # JavaScript клик - обходит перекрывающий label
                    await dropdown.evaluate("el => el.click()")
                    print(f"[BIRTH] JS клик на день")
                    await human_delay(400, 700)

                    # Ищем опцию дня
                    await human_delay(300, 500)
                    options = await self.page.query_selector_all('[role="option"]')
                    print(f"[BIRTH] Найдено опций дня: {len(options)}")

                    for opt in options:
                        try:
                            text = (await opt.inner_text()).strip()
                            if text == str(day):
                                await opt.evaluate("el => el.click()")
                                print(f"[BIRTH] День: {day}")
                                day_selected = True
                                break
                        except:
                            continue

                    if day_selected:
                        break

                    # Fallback по индексу
                    if len(options) >= day:
                        try:
                            await options[day - 1].evaluate("el => el.click()")
                            print(f"[BIRTH] День по индексу: {day}")
                            day_selected = True
                            break
                        except:
                            pass

                    await self.page.keyboard.press('Escape')
                except:
                    continue

            await human_delay(200, 400)

            # === ГОД ===
            year_entered = False
            year_selectors = [
                'input#BirthYear',
                'input[name="BirthYear"]',
                'input#DateOfBirthYear',
                'input[aria-label*="Year"]',
                'input[aria-label*="year"]',
                'input[placeholder*="Year"]',
            ]
            for sel in year_selectors:
                try:
                    year_input = await self.page.query_selector(sel)
                    if year_input and await year_input.is_visible():
                        await year_input.click()
                        await human_delay(100, 200)
                        await year_input.fill('')
                        await human_delay(50, 100)
                        # Вводим год посимвольно
                        for char in str(year):
                            await self.page.keyboard.type(char, delay=random.randint(50, 120))
                        print(f"[BIRTH] Год: {year}")
                        year_entered = True
                        break
                except:
                    continue

            await human_delay(300, 600)

            # Нажимаем Next
            await human_click(self.page, 'button#iSignupAction, button[type="submit"], button:has-text("Next")')
            print("[BIRTH] ✓ Дата введена")
            return True

        except Exception as e:
            print(f"[BIRTH] Ошибка: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def _fill_name(self, identity: Dict) -> bool:
        """Заполняет имя и фамилию"""
        try:
            # Селекторы для Fluent UI
            first_selectors = [
                '[data-testid="firstNameInput"] input',
                'input[name="FirstName"]',
                'input#FirstName'
            ]
            last_selectors = [
                '[data-testid="lastNameInput"] input',
                'input[name="LastName"]',
                'input#LastName'
            ]

            # Случайное движение мыши перед вводом (человеческое поведение)
            await random_mouse_movement(self.page, random.randint(1, 3))
            await human_delay(300, 700)

            # First name
            for sel in first_selectors:
                try:
                    el = await self.page.query_selector(sel)
                    if el and await el.is_visible():
                        await human_type(self.page, sel, identity["first"], typo_rate=0.02)
                        print(f"[NAME] First: {identity['first']}")
                        break
                except:
                    continue

            # Более длинная пауза между полями (как человек)
            await human_delay(400, 800)

            # Случайное движение мыши
            await random_mouse_movement(self.page, 1)

            # Last name
            for sel in last_selectors:
                try:
                    el = await self.page.query_selector(sel)
                    if el and await el.is_visible():
                        await human_type(self.page, sel, identity["last"], typo_rate=0.02)
                        print(f"[NAME] Last: {identity['last']}")
                        break
                except:
                    continue

            # Пауза перед нажатием Next (человек "проверяет" данные)
            await human_delay(600, 1200)

            # Next
            await human_click(self.page, 'button#iSignupAction, button[type="submit"]')
            print("[NAME] ✓ Имя введено")
            return True

        except Exception as e:
            print(f"[NAME] Ошибка: {e}")
            return False

    async def create_account(self) -> Optional[Dict]:
        """Основной метод создания аккаунта"""
        print("=" * 60)
        print("Outlook Account Creator (PLAYWRIGHT + STEALTH)")
        print("=" * 60)

        try:
            # === РОТАЦИЯ IP (если доступна) ===
            if self.rotate_ip and self.proxy_manager:
                await self._rotate_ip()

            # Настраиваем браузер
            await self._setup_browser()

            # Генерируем личность
            identity = self._generate_identity()
            print(f"\n[IDENTITY] Email: {identity['email']}")
            print(f"[IDENTITY] Password: {identity['password']}")
            print(f"[IDENTITY] Name: {identity['first']} {identity['last']}")
            print(
                f"[IDENTITY] Birth: {identity['birth_month']}/{identity['birth_day']}/{identity['birth_year']}")

            # Открываем страницу регистрации
            print(f"\n[PAGE] Загрузка signup.live.com...")
            try:
                # Используем domcontentloaded вместо networkidle (быстрее)
                await self.page.goto(
                    "https://signup.live.com/signup",
                    wait_until="domcontentloaded",
                    timeout=60000  # 60 секунд
                )
            except PlaywrightTimeout:
                print("[PAGE] Таймаут загрузки, продолжаем...")

            # === ИНЖЕКТИРУЕМ COOKIES И STORAGE ПОСЛЕ ЗАГРУЗКИ ===
            await self._apply_cookies_and_storage()

            # Ждём появления формы
            try:
                await self.page.wait_for_selector(
                    'input[name="MemberName"], input[type="email"]',
                    timeout=30000
                )
            except PlaywrightTimeout:
                print("[PAGE] Форма не загрузилась")
                return None

            print(f"[PAGE] URL: {self.page.url}")

            await human_delay(PAGE_DELAY[0], PAGE_DELAY[1])
            await random_mouse_movement(self.page, 2)

            # === ШАГ 1: Email ===
            print("\n[STEP 1] Ввод email...")
            if not await self._fill_email(identity):
                print("[ERROR] Не удалось ввести email")
                return None

            await human_delay(700, 1200)

            # === ШАГ 2: Password ===
            print("\n[STEP 2] Ввод пароля...")
            if not await self._fill_password(identity):
                print("[ERROR] Не удалось ввести пароль")
                return None

            await human_delay(700, 1200)

            # === ШАГ 3: Определяем что дальше (имя или дата) ===
            print("\n[STEP 3] Определяем следующий шаг...")

            name_found = False
            birth_found = False

            for _ in range(20):
                # Проверяем поля имени
                name_el = await self.page.query_selector(
                    '[data-testid="firstNameInput"], input[name="LastName"]'
                )
                if name_el and await name_el.is_visible():
                    name_found = True
                    break

                # Проверяем поля даты
                birth_el = await self.page.query_selector(
                    'button#BirthMonthDropdown, button[name="BirthMonth"]'
                )
                if birth_el and await birth_el.is_visible():
                    birth_found = True
                    break

                await asyncio.sleep(0.5)

            if name_found:
                print("[STEP 3] Заполняем имя...")
                if not await self._fill_name(identity):
                    print("[ERROR] Не удалось ввести имя")
                    return None
                await human_delay(500, 800)

                # Проверяем блокировку после ввода имени
                await asyncio.sleep(2)  # Ждём ответ сервера
                block_error = await self._check_block_error()
                if block_error:
                    print(f"\n[BLOCK] ❌ {block_error}")
                    print("[BLOCK] Microsoft детектировал автоматизацию!")
                    print("[BLOCK] Рекомендации:")
                    print("  1. Смените прокси/IP")
                    print("  2. Подождите 30-60 минут")
                    print("  3. Очистите cookies браузера")
                    print("  4. Используйте другой профиль")
                    return None

            elif birth_found:
                print("[STEP 3] Сразу дата рождения")
            else:
                print("[STEP 3] Неизвестный шаг")

            # === Автоматическая проверка и решение капчи ===
            await human_delay(500, 1000)
            await self._check_and_solve_captcha()

            # === ШАГ 4: Дата рождения ===
            print("\n[STEP 4] Дата рождения...")

            # Ждём появления полей даты
            try:
                await self.page.wait_for_selector(
                    'button#BirthMonthDropdown, button[name="BirthMonth"], [data-testid="birthdateControls"]',
                    timeout=15000
                )
                if not await self._fill_birthdate(identity):
                    print("[ERROR] Не удалось ввести дату")
                    return None
            except PlaywrightTimeout:
                print("[STEP 4] Поля даты не найдены, пропускаем")

            await human_delay(700, 1200)

            # === ШАГ 5: Имя (если не было раньше) ===
            print("\n[STEP 5] Проверяем поля имени...")

            name_filled_step5 = False
            for _ in range(10):
                name_el = await self.page.query_selector(
                    '[data-testid="firstNameInput"], input[name="FirstName"]'
                )
                if name_el and await name_el.is_visible():
                    print("[STEP 5] Заполняем имя...")
                    await self._fill_name(identity)
                    name_filled_step5 = True
                    break
                await asyncio.sleep(1)
            else:
                print("[STEP 5] Поля имени не найдены")

            await human_delay(500, 800)

            # Проверяем блокировку после ввода имени (STEP 5)
            if name_filled_step5:
                await asyncio.sleep(2)  # Ждём ответ сервера
                block_error = await self._check_block_error()
                if block_error:
                    print(f"\n[BLOCK] ❌ {block_error}")
                    print("[BLOCK] Microsoft детектировал автоматизацию!")
                    print("[BLOCK] Рекомендации:")
                    print("  1. Смените прокси/IP")
                    print("  2. Подождите 30-60 минут")
                    print("  3. Очистите cookies браузера")
                    print("  4. Используйте другой профиль")
                    return None

            # === ШАГ 6: Автоматическое решение капчи ===
            print("\n" + "=" * 60)
            print("[STEP 6] ПРОВЕРКА И РЕШЕНИЕ КАПЧИ")
            print("=" * 60)

            # Ждём немного для появления капчи
            await asyncio.sleep(2)

            # Пробуем решить капчу
            captcha_result = await self._check_and_solve_captcha()

            if captcha_result:
                print("[STEP 6] ✓ Капча обработана")
            else:
                print(
                    "[STEP 6] ⚠ Капча не пройдена, возможно требуется ручное решение")

            # Ждём финальную загрузку
            await asyncio.sleep(3)

            # === ШАГ 7: Обработка пост-регистрационных диалогов ===
            print("\n[STEP 7] Обработка пост-регистрационных окон...")
            await self._handle_post_registration_dialogs()

            # Проверяем итоговый результат
            try:
                final_url = self.page.url.lower()
                body_text = await self.page.inner_text('body')
                body_lower = body_text.lower()

                if 'outlook' in final_url or 'office' in final_url or 'inbox' in final_url or 'mail' in final_url:
                    print("\n" + "=" * 60)
                    print("[SUCCESS] ✓ Аккаунт создан! Перешли в почту.")
                    print("=" * 60)

                    # === ШАГ 8: Отправка тестового письма ===
                    print("\n[STEP 8] Отправка тестового письма...")
                    await self.send_test_email(
                        to_email="mfrizin@sanador.ru",
                        subject="test",
                        body="test"
                    )

                elif 'welcome' in body_lower or 'quick note' in body_lower:
                    print("\n" + "=" * 60)
                    print("[SUCCESS] ✓ Аккаунт создан!")
                    print("=" * 60)
                elif 'hold' in body_lower or "prove you're human" in body_lower:
                    print("\n" + "=" * 60)
                    print("[PENDING] Капча ещё активна - решите вручную")
                    print("=" * 60)
                else:
                    print("\n" + "=" * 60)
                    print("[INFO] Все шаги пройдены")
                    print(f"[INFO] URL: {self.page.url}")
                    print("=" * 60)
            except:
                print("\n" + "=" * 60)
                print("[SUCCESS] Все шаги пройдены!")
                print("=" * 60)

            return identity

        except Exception as e:
            print(f"\n[FATAL] {e}")
            import traceback
            traceback.print_exc()
            return None

        finally:
            print("\n" + "=" * 60)
            print("[INFO] Браузер остаётся открытым.")
            print("[INFO] Закройте окно браузера или нажмите Ctrl+C для выхода.")
            print("=" * 60)
            try:
                # Держим браузер открытым пока пользователь не закроет
                while True:
                    await asyncio.sleep(1)
                    if not self.page or self.page.is_closed():
                        print("[INFO] Окно браузера закрыто пользователем")
                        break
            except (KeyboardInterrupt, asyncio.CancelledError):
                print("\n[INFO] Получен сигнал завершения")
            finally:
                print("[INFO] Закрытие браузера...")
                if self.browser:
                    await self.browser.close()
                if self.playwright:
                    await self.playwright.stop()

    async def _handle_post_registration_dialogs(self) -> bool:
        """Обрабатывает пост-регистрационные диалоги"""
        print("\n[POST-REG] Обработка пост-регистрационных окон...")

        max_attempts = 10
        for attempt in range(max_attempts):
            await asyncio.sleep(1)

            try:
                body_text = await self.page.inner_text('body')
                body_lower = body_text.lower()

                # "A quick note about your Microsoft account" -> OK
                if 'quick note' in body_lower or 'important things' in body_lower:
                    print("[POST-REG] Окно 'Quick note' - нажимаем OK...")
                    ok_btn = await self.page.query_selector('button:has-text("OK"), input[value="OK"]')
                    if ok_btn:
                        await ok_btn.click()
                        await asyncio.sleep(2)
                        continue

                # "Stay signed in?" -> Yes
                if 'stay signed in' in body_lower:
                    print("[POST-REG] Окно 'Stay signed in' - нажимаем Yes...")
                    yes_btn = await self.page.query_selector('button:has-text("Yes"), input[value="Yes"]')
                    if yes_btn:
                        await yes_btn.click()
                        await asyncio.sleep(2)
                        continue

                # "Don't lose access" или "Security info" -> Skip/No
                if 'security info' in body_lower or "don't lose access" in body_lower:
                    print("[POST-REG] Окно безопасности - пропускаем...")
                    skip_btn = await self.page.query_selector(
                        'button:has-text("Skip"), a:has-text("Skip"), button:has-text("No")'
                    )
                    if skip_btn:
                        await skip_btn.click()
                        await asyncio.sleep(2)
                        continue

                # Проверяем, попали ли мы в почту
                url = self.page.url.lower()
                if 'outlook' in url or 'mail' in url or 'inbox' in url:
                    print("[POST-REG] ✓ Попали в почтовый ящик!")
                    return True

            except Exception as e:
                print(f"[POST-REG] Ошибка: {e}")

        print("[POST-REG] Диалоги обработаны")
        return True

    async def send_test_email(self, to_email: str, subject: str, body: str) -> bool:
        """Отправляет тестовое письмо"""
        print(f"\n[EMAIL] Отправка письма на {to_email}...")

        try:
            # Ждём загрузки интерфейса почты
            await asyncio.sleep(3)

            # Переходим в Outlook если ещё не там
            current_url = self.page.url.lower()
            if 'outlook' not in current_url and 'mail' not in current_url:
                print("[EMAIL] Переход в Outlook...")
                await self.page.goto('https://outlook.live.com/mail/', wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(5)

            # Ищем кнопку "New mail" / "Новое сообщение"
            new_mail_selectors = [
                'button[aria-label*="New mail"]',
                'button[aria-label*="New message"]',
                'button[aria-label*="Новое"]',
                'button:has-text("New mail")',
                'button:has-text("New message")',
                '[data-icon-name="Edit"]',
                'button[title*="New"]',
            ]

            new_btn = None
            for sel in new_mail_selectors:
                try:
                    new_btn = await self.page.query_selector(sel)
                    if new_btn and await new_btn.is_visible():
                        break
                except:
                    continue

            if not new_btn:
                print(
                    "[EMAIL] Кнопка 'New mail' не найдена, пробуем горячую клавишу...")
                await self.page.keyboard.press('n')
                await asyncio.sleep(2)
            else:
                await new_btn.click()
                print("[EMAIL] Нажали 'New mail'")
                await asyncio.sleep(2)

            # Заполняем поле "To"
            to_selectors = [
                'input[aria-label*="To"]',
                'input[placeholder*="To"]',
                'div[aria-label*="To"] input',
                '[role="textbox"][aria-label*="To"]',
            ]

            for sel in to_selectors:
                try:
                    to_field = await self.page.query_selector(sel)
                    if to_field:
                        await to_field.click()
                        await to_field.fill(to_email)
                        print(f"[EMAIL] To: {to_email}")
                        await asyncio.sleep(0.5)
                        break
                except:
                    continue

            # Заполняем Subject
            subject_selectors = [
                'input[aria-label*="Subject"]',
                'input[placeholder*="Subject"]',
                'input[aria-label*="Тема"]',
            ]

            for sel in subject_selectors:
                try:
                    subj_field = await self.page.query_selector(sel)
                    if subj_field:
                        await subj_field.click()
                        await subj_field.fill(subject)
                        print(f"[EMAIL] Subject: {subject}")
                        await asyncio.sleep(0.5)
                        break
                except:
                    continue

            # Заполняем Body
            body_selectors = [
                'div[aria-label*="Message body"]',
                'div[role="textbox"][aria-multiline="true"]',
                'div[contenteditable="true"]',
            ]

            for sel in body_selectors:
                try:
                    body_field = await self.page.query_selector(sel)
                    if body_field:
                        await body_field.click()
                        await body_field.fill(body)
                        print(f"[EMAIL] Body: {body}")
                        await asyncio.sleep(0.5)
                        break
                except:
                    continue

            # Нажимаем Send
            send_selectors = [
                'button[aria-label*="Send"]',
                'button:has-text("Send")',
                'button[title*="Send"]',
            ]

            for sel in send_selectors:
                try:
                    send_btn = await self.page.query_selector(sel)
                    if send_btn and await send_btn.is_visible():
                        await send_btn.click()
                        print("[EMAIL] ✓ Письмо отправлено!")
                        await asyncio.sleep(3)
                        return True
                except:
                    continue

            # Fallback: Ctrl+Enter
            print("[EMAIL] Пробуем Ctrl+Enter...")
            await self.page.keyboard.press('Control+Enter')
            await asyncio.sleep(3)
            print("[EMAIL] ✓ Письмо отправлено (Ctrl+Enter)")
            return True

        except Exception as e:
            print(f"[EMAIL] Ошибка: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Точка входа"""
    headless = "--headless" in sys.argv
    proxy = None

    rotate_ip = "--rotate-ip" in sys.argv  # По умолчанию ВЫКЛЮЧЕНО

    for arg in sys.argv:
        if arg.startswith("--proxy="):
            proxy = arg.split("=", 1)[1]

    creator = OutlookPlaywrightCreator(
        proxy=proxy, headless=headless, rotate_ip=rotate_ip)
    result = await creator.create_account()

    if result:
        print("\n" + "=" * 60)
        print("Созданные учётные данные:")
        print(f"  Email: {result['email']}")
        print(f"  Password: {result['password']}")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
