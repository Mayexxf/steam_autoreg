"""
Cookie Generator - создаёт правдоподобные cookies от популярных сайтов
Чтобы Discord видел, что это "реальный" пользователь с историей посещений
"""

import random
import string
import time
from typing import List, Dict


class CookieGenerator:
    """Генератор искусственных cookies для эмуляции реального пользователя"""
    
    # Популярные сайты которые посещает обычный пользователь
    COMMON_SITES = [
        'google.com',
        'youtube.com',
        'wikipedia.org',
        'reddit.com',
        'github.com',
        'stackoverflow.com',
        'twitter.com',
        'facebook.com',
        'amazon.com',
        'microsoft.com',
    ]
    
    def __init__(self):
        """Инициализация генератора"""
        self.current_time = int(time.time())
    
    def _random_string(self, length: int, charset: str = None) -> str:
        """Генерирует случайную строку"""
        if charset is None:
            charset = string.ascii_letters + string.digits
        return ''.join(random.choices(charset, k=length))
    
    def _random_hex(self, length: int) -> str:
        """Генерирует случайную hex строку (для session IDs)"""
        return ''.join(random.choices(string.hexdigits.lower(), k=length))
    
    def _random_base64(self, length: int) -> str:
        """Генерирует случайную base64-подобную строку"""
        charset = string.ascii_letters + string.digits + '+/='
        return ''.join(random.choices(charset, k=length))
    
    def _generate_google_cookies(self) -> List[Dict]:
        """Генерирует cookies для Google (самые важные!)"""
        cookies = []
        
        # Google Session ID (NID)
        cookies.append({
            'name': 'NID',
            'value': f"{random.randint(100, 999)}={self._random_string(32)}",
            'domain': '.google.com',
            'path': '/',
            'expires': self.current_time + 180 * 86400,  # 180 дней
            'httpOnly': True,
            'secure': True,
            'sameSite': 'None'
        })
        
        # Google Search preferences
        cookies.append({
            'name': 'SEARCH_SAMESITE',
            'value': 'CgQIvJoB',
            'domain': '.google.com',
            'path': '/',
            'expires': self.current_time + 180 * 86400,
            'httpOnly': False,
            'secure': True,
            'sameSite': 'Lax'
        })
        
        # Google Consent (GDPR)
        cookies.append({
            'name': 'CONSENT',
            'value': f"YES+US.en+{random.randint(20200101, 20241231)}",
            'domain': '.google.com',
            'path': '/',
            'expires': self.current_time + 365 * 86400,  # 1 год
            'httpOnly': False,
            'secure': True,
            'sameSite': 'None'
        })
        
        return cookies
    
    def _generate_youtube_cookies(self) -> List[Dict]:
        """Генерирует cookies для YouTube"""
        cookies = []
        
        # YouTube Preferences
        cookies.append({
            'name': 'PREF',
            'value': f"tz=America.New_York&f5={random.randint(20000, 30000)}",
            'domain': '.youtube.com',
            'path': '/',
            'expires': self.current_time + 365 * 86400,
            'httpOnly': False,
            'secure': True,
            'sameSite': 'Lax'
        })
        
        # YouTube Visitor ID
        cookies.append({
            'name': 'VISITOR_INFO1_LIVE',
            'value': self._random_string(11),
            'domain': '.youtube.com',
            'path': '/',
            'expires': self.current_time + 180 * 86400,
            'httpOnly': True,
            'secure': True,
            'sameSite': 'None'
        })
        
        return cookies
    
    def _generate_wikipedia_cookies(self) -> List[Dict]:
        """Генерирует cookies для Wikipedia"""
        cookies = []
        
        # Wikipedia Session
        cookies.append({
            'name': 'WMF-Last-Access',
            'value': time.strftime('%d-%b-%Y', time.gmtime()),
            'domain': '.wikipedia.org',
            'path': '/',
            'expires': self.current_time + 30 * 86400,
            'httpOnly': False,
            'secure': True,
            'sameSite': 'Lax'
        })
        
        return cookies
    
    def _generate_reddit_cookies(self) -> List[Dict]:
        """Генерирует cookies для Reddit"""
        cookies = []
        
        # Reddit Session
        cookies.append({
            'name': 'session_tracker',
            'value': self._random_base64(40),
            'domain': '.reddit.com',
            'path': '/',
            'expires': self.current_time + 365 * 86400,
            'httpOnly': False,
            'secure': True,
            'sameSite': 'None'
        })
        
        # Reddit EDGEBUCKET
        cookies.append({
            'name': 'edgebucket',
            'value': self._random_string(16),
            'domain': '.reddit.com',
            'path': '/',
            'expires': self.current_time + 365 * 86400,
            'httpOnly': False,
            'secure': False,
            'sameSite': 'Lax'
        })
        
        return cookies
    
    def _generate_github_cookies(self) -> List[Dict]:
        """Генерирует cookies для GitHub"""
        cookies = []
        
        # GitHub timezone
        cookies.append({
            'name': 'tz',
            'value': 'America%2FNew_York',
            'domain': '.github.com',
            'path': '/',
            'expires': self.current_time + 365 * 86400,
            'httpOnly': False,
            'secure': True,
            'sameSite': 'Lax'
        })
        
        # GitHub color mode
        cookies.append({
            'name': 'color_mode',
            'value': random.choice(['%7B%22color_mode%22%3A%22auto%22%7D', 
                                     '%7B%22color_mode%22%3A%22light%22%7D',
                                     '%7B%22color_mode%22%3A%22dark%22%7D']),
            'domain': '.github.com',
            'path': '/',
            'expires': self.current_time + 365 * 86400,
            'httpOnly': False,
            'secure': True,
            'sameSite': 'Lax'
        })
        
        return cookies
    
    def _generate_stackoverflow_cookies(self) -> List[Dict]:
        """Генерирует cookies для StackOverflow"""
        cookies = []
        
        # StackOverflow preferences
        cookies.append({
            'name': 'prov',
            'value': self._random_hex(32),
            'domain': '.stackoverflow.com',
            'path': '/',
            'expires': self.current_time + 365 * 86400,
            'httpOnly': False,
            'secure': True,
            'sameSite': 'None'
        })
        
        return cookies
    
    def _generate_twitter_cookies(self) -> List[Dict]:
        """Генерирует cookies для Twitter/X"""
        cookies = []
        
        # Twitter Guest ID
        cookies.append({
            'name': 'guest_id',
            'value': f"v1%3A{self.current_time}{random.randint(100000, 999999)}",
            'domain': '.twitter.com',
            'path': '/',
            'expires': self.current_time + 365 * 86400,
            'httpOnly': False,
            'secure': True,
            'sameSite': 'None'
        })
        
        # Twitter Personalization ID
        cookies.append({
            'name': 'personalization_id',
            'value': f'"{self._random_hex(16)}"',
            'domain': '.twitter.com',
            'path': '/',
            'expires': self.current_time + 365 * 86400,
            'httpOnly': False,
            'secure': True,
            'sameSite': 'None'
        })
        
        return cookies
    
    def _generate_amazon_cookies(self) -> List[Dict]:
        """Генерирует cookies для Amazon"""
        cookies = []
        
        # Amazon Session
        cookies.append({
            'name': 'session-id',
            'value': f"{self._random_string(3, string.digits)}-{self._random_string(7, string.digits)}-{self._random_string(7, string.digits)}",
            'domain': '.amazon.com',
            'path': '/',
            'expires': self.current_time + 365 * 86400,
            'httpOnly': False,
            'secure': True,
            'sameSite': 'Lax'
        })
        
        return cookies
    
    def _generate_microsoft_cookies(self) -> List[Dict]:
        """Генерирует cookies для Microsoft"""
        cookies = []

        # Microsoft MUID
        cookies.append({
            'name': 'MUID',
            'value': self._random_hex(32).upper(),
            'domain': '.microsoft.com',
            'path': '/',
            'expires': self.current_time + 365 * 86400,
            'httpOnly': False,
            'secure': True,
            'sameSite': 'None'
        })

        return cookies

    def _generate_steam_cookies(self, geo_config: Dict = None) -> List[Dict]:
        """
        Генерирует cookies для Steam (КРИТИЧНО!)
        Это cookies которые ДОЛЖНЫ быть у пользователя Steam

        Args:
            geo_config: Конфигурация геолокации (timezone, country_code, steam_language)
                       Если None - используются дефолтные значения (US)

        Returns:
            List[Dict]: Список Steam cookies
        """
        cookies = []

        # Извлекаем данные из geo_config или используем дефолты
        if geo_config:
            country_code = geo_config.get('country_code', 'US')
            timezone_offset = geo_config.get('timezone_offset', 300)  # UTC-5 по умолчанию
            steam_language = geo_config.get('steam_language', 'english')
        else:
            country_code = 'US'
            timezone_offset = 300  # UTC-5 (America/New_York)
            steam_language = 'english'

        # Steam Browser ID (ОЧЕНЬ ВАЖНО!)
        # browserid - уникальный ID браузера, генерируется при первом визите
        # Формат: числовое значение (timestamp-based)
        browser_id = str(self.current_time - random.randint(86400 * 30, 86400 * 180))  # 1-6 месяцев назад

        cookies.append({
            'name': 'browserid',
            'value': browser_id,
            'domain': '.steampowered.com',
            'path': '/',
            'expires': self.current_time + 365 * 86400,  # 1 год
            'httpOnly': False,
            'secure': True,
            'sameSite': 'None'
        })

        # Steam Timezone Offset (важно для локализации)
        # Формат: offset в минутах от UTC (например: 300 = UTC-5)
        # КРИТИЧНО: Должен совпадать с timezone Playwright!
        cookies.append({
            'name': 'timezoneOffset',
            'value': f'{timezone_offset},0',  # offset,dst (DST всегда 0 для простоты)
            'domain': '.steampowered.com',
            'path': '/',
            'expires': self.current_time + 365 * 86400,
            'httpOnly': False,
            'secure': False,
            'sameSite': 'Lax'
        })

        # Steam Country (геолокация пользователя)
        # КРИТИЧНО: должен совпадать с IP прокси!
        # Формат: COUNTRY_CODE%7C0 (например: US%7C0, GB%7C0, DE%7C0)
        cookies.append({
            'name': 'steamCountry',
            'value': f'{country_code}%7C0',  # country_code|region (region=0 для большинства стран)
            'domain': '.steampowered.com',
            'path': '/',
            'expires': self.current_time + 86400,  # 1 день (обновляется часто)
            'httpOnly': False,
            'secure': False,
            'sameSite': 'Lax'
        })

        # Steam Language (язык интерфейса)
        # КРИТИЧНО: должен совпадать со страной!
        cookies.append({
            'name': 'Steam_Language',
            'value': steam_language,
            'domain': '.steampowered.com',
            'path': '/',
            'expires': self.current_time + 365 * 86400,
            'httpOnly': False,
            'secure': False,
            'sameSite': 'Lax'
        })

        # Cookie Preferences (GDPR consent)
        cookies.append({
            'name': 'cookieSettings',
            'value': '%7B%22version%22%3A1%2C%22preference_state%22%3A2%2C%22content_customization%22%3Anull%7D',
            # Декодировано: {"version":1,"preference_state":2,"content_customization":null}
            'domain': '.steampowered.com',
            'path': '/',
            'expires': self.current_time + 365 * 86400,
            'httpOnly': False,
            'secure': False,
            'sameSite': 'Lax'
        })

        # SteamCommunity cookies (тоже важны - должны быть идентичны steampowered.com!)
        # КРИТИЧНО: Те же значения для согласованности!
        cookies.append({
            'name': 'browserid',
            'value': browser_id,  # Тот же browser ID
            'domain': '.steamcommunity.com',
            'path': '/',
            'expires': self.current_time + 365 * 86400,
            'httpOnly': False,
            'secure': True,
            'sameSite': 'None'
        })

        cookies.append({
            'name': 'timezoneOffset',
            'value': f'{timezone_offset},0',  # Тот же offset
            'domain': '.steamcommunity.com',
            'path': '/',
            'expires': self.current_time + 365 * 86400,
            'httpOnly': False,
            'secure': False,
            'sameSite': 'Lax'
        })

        cookies.append({
            'name': 'steamCountry',
            'value': f'{country_code}%7C0',  # Та же страна
            'domain': '.steamcommunity.com',
            'path': '/',
            'expires': self.current_time + 86400,
            'httpOnly': False,
            'secure': False,
            'sameSite': 'Lax'
        })

        return cookies
    
    def generate_realistic_cookies(self, num_sites: int = None) -> List[Dict]:
        """
        Генерирует набор правдоподобных cookies от популярных сайтов
        
        Args:
            num_sites: Количество сайтов для генерации (None = все)
        
        Returns:
            List[Dict]: Список cookies для добавления в браузер
        """
        all_cookies = []
        
        # Генераторы для каждого сайта
        generators = {
            'google.com': self._generate_google_cookies,
            'youtube.com': self._generate_youtube_cookies,
            'wikipedia.org': self._generate_wikipedia_cookies,
            'reddit.com': self._generate_reddit_cookies,
            'github.com': self._generate_github_cookies,
            'stackoverflow.com': self._generate_stackoverflow_cookies,
            'twitter.com': self._generate_twitter_cookies,
            'amazon.com': self._generate_amazon_cookies,
            'microsoft.com': self._generate_microsoft_cookies,
        }
        
        # Выбираем случайные сайты если указано num_sites
        if num_sites:
            selected_sites = random.sample(list(generators.keys()), min(num_sites, len(generators)))
        else:
            selected_sites = list(generators.keys())
        
        # Генерируем cookies для выбранных сайтов
        for site in selected_sites:
            site_cookies = generators[site]()
            all_cookies.extend(site_cookies)
        
        # Перемешиваем для реалистичности
        random.shuffle(all_cookies)
        
        return all_cookies
    
    def get_cookie_summary(self, cookies: List[Dict]) -> str:
        """
        Возвращает краткую сводку о сгенерированных cookies
        
        Args:
            cookies: Список cookies
        
        Returns:
            str: Текстовая сводка
        """
        domains = {}
        for cookie in cookies:
            domain = cookie['domain'].lstrip('.')
            domains[domain] = domains.get(domain, 0) + 1
        
        summary = f"Generated {len(cookies)} cookies from {len(domains)} domains:\n"
        for domain, count in sorted(domains.items()):
            summary += f"  - {domain}: {count} cookie(s)\n"
        
        return summary


if __name__ == '__main__':
    # Тест генератора
    generator = CookieGenerator()
    cookies = generator.generate_realistic_cookies()
    
    print("=" * 70)
    print("COOKIE GENERATOR TEST")
    print("=" * 70)
    print(generator.get_cookie_summary(cookies))
    print("\nПример cookie:")
    print(cookies[0])
