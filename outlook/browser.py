#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Настройка браузера со stealth для Outlook
"""

import random
import asyncio
import requests
from typing import Optional, Dict, Any

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from .config import VIEWPORT_OPTIONS

# Stealth библиотеки
try:
    from playwright_stealth import stealth_async
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

try:
    from src.stealth.fingerprint_generator import FingerprintGenerator
    from src.stealth.cookie_generator import CookieGenerator
    from src.stealth.storage_generator import StorageGenerator
    from src.stealth.geo_config import get_geo_config, enrich_geo_config
    STEALTH_MODULES_AVAILABLE = True
except ImportError:
    STEALTH_MODULES_AVAILABLE = False


class BrowserManager:
    """Управление браузером со stealth-настройками"""

    def __init__(self, proxy: str = None, headless: bool = False):
        self.proxy = proxy
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.geo_config = None
        self.fingerprint_config = None
        self.fingerprint_script = None
        self.pending_cookies = []
        self.pending_storage_script = None

    def parse_proxy(self) -> Optional[Dict[str, Any]]:
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
            if len(parts) == 4:
                username, password, host, port = parts
            else:
                return None
        else:
            return None

        return {
            "server": f"http://{host}:{port}",
            "username": username,
            "password": password
        }

    async def detect_proxy_geo(self) -> Dict:
        """Определяет геолокацию по IP прокси"""
        if not self.proxy or not STEALTH_MODULES_AVAILABLE:
            return enrich_geo_config(get_geo_config('United States'))

        try:
            proxy_config = self.parse_proxy()
            proxies = None
            auth = None
            if proxy_config:
                proxies = {
                    'http': proxy_config['server'],
                    'https': proxy_config['server']
                }
                auth = (proxy_config['username'], proxy_config['password'])

            response = requests.get(
                "http://ip-api.com/json/?fields=status,country,countryCode,city,timezone,query",
                proxies=proxies,
                auth=auth,
                timeout=12
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    country = data.get('country', 'United States')
                    geo_config = get_geo_config(country)
                    geo_config = enrich_geo_config(geo_config)
                    geo_config['detected_ip'] = data.get('query', 'unknown')
                    geo_config['city'] = data.get('city', '')
                    if data.get('timezone'):
                        geo_config['timezone'] = data['timezone']

                    print(f"[GEO] Обнаружено: {country} ({geo_config['city']}), IP: {geo_config['detected_ip']}")
                    print(f"[GEO] Timezone: {geo_config['timezone']}, Locale: {geo_config['locale']}")
                    return geo_config
        except Exception as e:
            print(f"[GEO] Ошибка определения: {e}")

        return enrich_geo_config(get_geo_config('United States'))

    async def setup(self):
        """Настраивает браузер с полным stealth"""
        self.playwright = await async_playwright().start()

        # Определение геолокации
        if not self.geo_config:
            self.geo_config = await self.detect_proxy_geo()

        # 2. Fingerprint
        if STEALTH_MODULES_AVAILABLE:
            self.fingerprint_config = FingerprintGenerator.generate(browser_type='chrome')
            viewport = self.fingerprint_config['viewport']
            chrome_version = "143.0.0.0"
            self.fingerprint_script = FingerprintGenerator.get_injector_script(
              self.fingerprint_config,
              browser_version=chrome_version,
              browser_type='chrome'
            )
            print(f"[FINGERPRINT] Сгенерирован (cores: {self.fingerprint_config['hardware']['cores']}, "
                   f"memory: {self.fingerprint_config['hardware']['memory']}GB, canvas_noise: {self.fingerprint_config['canvas_noise']})")
        else:
            viewport = random.choice(VIEWPORT_OPTIONS)

        proxy_config = self.parse_proxy()

        # 3. Запуск браузера БЕЗ палевных аргументов!
        print(f"[BROWSER] Запуск Chromium (headless={self.headless})")
        print(f"[BROWSER] Viewport: {viewport['width']}x{viewport['height']}")
        if proxy_config:
          print(f"[BROWSER] Proxy: {proxy_config['server']}")

        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            # Убраны все --disable-* флаги — они детектятся в 2025
        )

        user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36"

        locale = self.geo_config.get('locale', 'en-US')
        timezone_id = self.geo_config.get('timezone', 'America/New_York')
        accept_language = self.geo_config.get('accept_language', 'en-US,en;q=0.9')

        context_options = {
            "viewport": viewport,
            "user_agent": user_agent,
            "locale": locale,
            "timezone_id": timezone_id,
            "color_scheme": random.choice(['light', 'dark']),
            "extra_http_headers": {
                "Accept-Language": accept_language,
            },
            "permissions": ["geolocation", "notifications"],
        }

        if proxy_config:
            context_options["proxy"] = proxy_config

        self.context = await self.browser.new_context(**context_options)

        # 5. Ранний инжект fingerprint (до всего!)
        if self.fingerprint_script:
            await self.context.add_init_script(self.fingerprint_script)
            print("[FINGERPRINT] [+] Инжект через add_init_script")

        # 6. Генерация и применение cookies ДО создания страницы
        if STEALTH_MODULES_AVAILABLE:
            await self._inject_cookies()
            await self._apply_cookies_to_context()  # Теперь работает правильно!

        self.page = await self.context.new_page()

        # ❌ ОТКЛЮЧАЕМ playwright-stealth - он ДЕТЕКТИРУЕТСЯ CreepJS!
        # Вместо этого используем собственные stealth обходы в fingerprint_generator
        # if STEALTH_AVAILABLE:
        #     await stealth_async(self.page)
        #     print("[STEALTH] playwright-stealth применён [+]")

        if STEALTH_MODULES_AVAILABLE:
            await self._inject_storage_via_init_script()  # Новый метод через add_init_script
            # НЕ вызываем apply_storage() сразу - будет SecurityError!

        webdriver_check = await self.page.evaluate("() => navigator.webdriver")
        print(f"[STEALTH] navigator.webdriver = {webdriver_check}")

    async def _inject_cookies(self):
        """Инжектирует реалистичные cookies"""
        if not STEALTH_MODULES_AVAILABLE:
            return

        try:
            cookie_gen = CookieGenerator()
            all_cookies = cookie_gen.generate_realistic_cookies(num_sites=7)
            ms_cookies = cookie_gen._generate_microsoft_cookies()
            all_cookies.extend(ms_cookies)
            self.pending_cookies = all_cookies
            print(
                f"[COOKIES] Prepared {len(all_cookies)} cookies from popular sites")
        except Exception as e:
            print(f"[COOKIES] Error: {e}")

    async def _inject_storage_via_init_script(self):
        """
        Инжектирует localStorage данные через add_init_script
        Это безопаснее и работает на всех страницах без SecurityError
        """
        if not STEALTH_MODULES_AVAILABLE:
            return

        try:
            storage_gen = StorageGenerator()
            storage_data = storage_gen.generate_full_storage(self.geo_config)
            storage_script = storage_gen.get_storage_script(storage_data)

            # ✅ Используем add_init_script вместо evaluate
            # Это автоматически применяется на всех страницах
            await self.context.add_init_script(f"""
                (function() {{
                    try {{
                        // Проверяем доступность localStorage
                        if (typeof localStorage !== 'undefined' && localStorage !== null) {{
                            {storage_script}
                            console.log('[STORAGE] Applied {len(storage_data)} items via add_init_script');
                        }}
                    }} catch(e) {{
                        console.log('[STORAGE] Skipped due to security policy:', e.message);
                    }}
                }})();
            """)

            print(f"[STORAGE] [+] Injected {len(storage_data)} localStorage items via add_init_script")
        except Exception as e:
            print(f"[STORAGE] Error: {e}")

    async def _apply_cookies_to_context(self):
        """Правильно применяет cookies через 'url' — работает в 100% случаев"""
        if not self.pending_cookies:
            return

        applied_count = 0
        skipped = 0

        for cookie in self.pending_cookies:
            try:
                domain = cookie.get('domain', '').lstrip('.')  # убираем ведущую точку
                if not domain:
                    skipped += 1
                    continue

                cookie_data = {
                    'name': cookie['name'],
                    'value': cookie['value'],
                    'url': f"https://{domain}",  # КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ!
                }

                if 'expires' in cookie:
                    cookie_data['expires'] = cookie['expires']
                if 'secure' in cookie:
                    cookie_data['secure'] = cookie['secure']
                if 'httpOnly' in cookie:
                    cookie_data['httpOnly'] = cookie['httpOnly']

                await self.context.add_cookies([cookie_data])
                applied_count += 1
            except Exception as e:
                skipped += 1
                # print(f"[COOKIES] Пропущен {cookie['name']}@{domain}: {e}")

        print(f"[COOKIES] [+] Применено {applied_count} cookies (через 'url'), пропущено {skipped}")

    async def apply_storage(self):
        """Применяет localStorage ПОСЛЕ загрузки нейтральной страницы"""
        if self.pending_storage_script:
            try:
                await self.page.evaluate(self.pending_storage_script)
                print(f"[STORAGE] [+] Applied localStorage data")
            except Exception as e:
                print(f"[STORAGE] Error applying: {e}")

    async def close(self):
        """Закрывает всё"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            print("[BROWSER] Закрыт")
        except Exception as e:
            print(f"[ERROR] При закрытии: {e}")

