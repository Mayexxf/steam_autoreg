"""
Storage Generator - создаёт правдоподобные localStorage/sessionStorage данные
Имитирует реального пользователя с историей активности
"""

import random
import string
import time
import json
from typing import Dict, Any


class StorageGenerator:
    """Генератор искусственных localStorage/sessionStorage данных"""
    
    def __init__(self):
        """Инициализация генератора"""
        self.current_time = int(time.time())
        # "Возраст" браузера (от 30 до 180 дней назад)
        self.browser_age_days = random.randint(30, 180)
        self.install_timestamp = self.current_time - (self.browser_age_days * 86400)
    
    def _random_string(self, length: int) -> str:
        """Генерирует случайную строку"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def _random_hex(self, length: int) -> str:
        """Генерирует случайную hex строку"""
        return ''.join(random.choices(string.hexdigits.lower(), k=length))
    
    def _random_uuid(self) -> str:
        """Генерирует UUID v4"""
        return f"{self._random_hex(8)}-{self._random_hex(4)}-4{self._random_hex(3)}-{random.choice(['8','9','a','b'])}{self._random_hex(3)}-{self._random_hex(12)}"
    
    def generate_common_storage(self) -> Dict[str, Any]:
        """
        Генерирует общие localStorage данные которые есть у большинства браузеров
        
        Returns:
            Dict[str, Any]: Словарь с ключами и значениями для localStorage
        """
        storage = {}
        
        # Google Analytics / Google Tag Manager (есть почти везде)
        storage['_ga'] = f"GA1.1.{random.randint(100000000, 999999999)}.{self.install_timestamp}"
        storage['_ga_CONTAINER'] = f"GS1.1.{self.current_time}.{random.randint(1, 50)}.{random.randint(0, 1)}.{self.current_time}.{random.randint(0, 1)}.{random.randint(0, 1)}"
        
        # Google Consent Mode
        storage['googleConsent'] = json.dumps({
            'ad_storage': 'denied',
            'analytics_storage': 'granted',
            'ad_user_data': 'denied',
            'ad_personalization': 'denied'
        })
        
        # Client ID (общий идентификатор)
        storage['clientId'] = self._random_uuid()
        storage['sessionId'] = self._random_uuid()
        
        # Preferences (общие настройки)
        storage['theme'] = random.choice(['light', 'dark', 'auto'])
        storage['lang'] = 'en-US'
        storage['timezone'] = 'America/New_York'
        
        # Last visit timestamp (показывает что браузер не новый)
        storage['lastVisit'] = str(self.current_time - random.randint(3600, 86400))  # 1-24 часа назад
        storage['visitCount'] = str(random.randint(5, 50))  # Количество визитов
        
        # Browser install time (критично!)
        storage['browserInstallDate'] = str(self.install_timestamp * 1000)  # В миллисекундах
        storage['firstVisit'] = str(self.install_timestamp)
        
        # Feature flags / experiments (обычно есть на современных сайтах)
        storage['features'] = json.dumps({
            'newUI': random.choice([True, False]),
            'darkMode': random.choice([True, False]),
            'notifications': random.choice([True, False])
        })
        
        # Device ID (постоянный идентификатор устройства)
        storage['deviceId'] = self._random_hex(32)
        storage['fingerprintId'] = self._random_hex(16)
        
        # Consent / Privacy (GDPR/CCPA)
        storage['cookieConsent'] = json.dumps({
            'necessary': True,
            'analytics': True,
            'marketing': False,
            'timestamp': self.install_timestamp
        })
        
        # Metrics / Performance (собирается браузером)
        storage['performanceMetrics'] = json.dumps({
            'loadTime': random.randint(500, 2000),
            'renderTime': random.randint(100, 500),
            'timestamp': self.current_time - random.randint(60, 3600)
        })
        
        return storage
    
    def generate_google_storage(self) -> Dict[str, Any]:
        """Генерирует localStorage данные от Google сервисов"""
        storage = {}
        
        # Google Search history indicators
        storage['google_search_history'] = json.dumps({
            'enabled': True,
            'lastUpdate': self.current_time - random.randint(3600, 86400)
        })
        
        # YouTube watch history
        storage['yt_player_quality'] = 'hd720'
        storage['yt_player_volume'] = str(random.randint(50, 100))
        storage['yt_remote_device_id'] = self._random_string(20)
        storage['yt_remote_session_name'] = f"session-{self._random_hex(8)}"
        
        return storage
    
    def generate_discord_pre_storage(self) -> Dict[str, Any]:
        """
        Генерирует localStorage данные ДО регистрации на Discord
        Имитирует пользователя который уже посещал Discord (но не регистрировался)
        """
        storage = {}

        # Discord analytics/tracking (даже у незарегистрированных)
        storage['OptimizelyEndUserId'] = f"oeu{self.current_time}{random.randint(1000, 9999)}"

        # Discord experiments (A/B тесты)
        storage['ExperimentStore'] = json.dumps({
            'version': 1,
            'guild_ids': [],
            'user_experiments': []
        })

        # Discord locale/language
        storage['locale'] = 'en-US'

        # Discord last visit (показывает что пользователь уже был)
        days_ago = random.randint(7, 30)  # Был на сайте 7-30 дней назад
        last_visit = self.current_time - (days_ago * 86400) - random.randint(0, 86400)
        storage['lastVisitTimestamp'] = str(last_visit)

        return storage

    def generate_steam_storage(self, geo_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Генерирует localStorage данные для Steam (КРИТИЧНО!)
        Это данные которые ДОЛЖНЫ быть у пользователя Steam

        Args:
            geo_config: Конфигурация геолокации (timezone, country_code, steam_language)
                       Если None - используются дефолтные значения (US)

        Returns:
            Dict[str, Any]: localStorage ключи для Steam
        """
        storage = {}

        # Извлекаем данные из geo_config или используем дефолты
        if geo_config:
            country_code = geo_config.get('country_code', 'US')
            timezone = geo_config.get('timezone', 'America/New_York')
            steam_language = geo_config.get('steam_language', 'english')
        else:
            country_code = 'US'
            timezone = 'America/New_York'
            steam_language = 'english'

        # Steam Language (синхронизируется с cookie)
        # КРИТИЧНО: должен совпадать с Steam_Language cookie!
        storage['steam_language'] = steam_language

        # Steam Country (синхронизируется с cookie и IP)
        # КРИТИЧНО: должен совпадать с steamCountry cookie!
        storage['steam_country'] = country_code

        # WebUI Config (настройки интерфейса Steam)
        storage['webui_config'] = json.dumps({
            'timestamp': self.current_time - random.randint(3600, 86400 * 7),
            'version': random.randint(100, 200),
            'language': steam_language  # Добавляем язык в config
        })

        # Store Preferences (настройки магазина)
        storage['store_preferences'] = json.dumps({
            'show_adult_content': False,
            'timestamp': self.install_timestamp,
            'country': country_code  # Добавляем страну в preferences
        })

        # Community Preferences
        storage['Community_Preferences'] = json.dumps({
            'hide_adult_content_violence': False,
            'hide_adult_content_sex': False,
            'timestamp': self.install_timestamp
        })

        # Last Visited Pages (история посещений - показывает активность)
        # НЕ добавляем реальные URLs - это может быть проверено!
        # Вместо этого добавляем пустой массив (новый пользователь)
        storage['last_visited_store_pages'] = json.dumps([])

        # Shopping Cart (пустая корзина для нового пользователя)
        storage['shopping_cart'] = json.dumps({
            'items': [],
            'timestamp': self.current_time
        })

        # Notification Preferences
        storage['notification_preferences'] = json.dumps({
            'show_notifications': True,
            'timestamp': self.install_timestamp
        })

        # Steam Browser Session (показывает сколько времени пользователь на сайте)
        # Генерируем реалистичную сессию (5-60 минут назад)
        session_start = self.current_time - random.randint(300, 3600)
        storage['session_start'] = str(session_start)

        # Steam Analytics Tracking (аналитика Steam)
        storage['steam_analytics_id'] = self._random_hex(32)

        # Timezone (должен совпадать с cookie timezoneOffset!)
        # КРИТИЧНО: должен совпадать с timezone из geo_config!
        storage['timezone'] = timezone

        return storage
    
    def get_storage_script(self, storage_data: Dict[str, Any]) -> str:
        """
        Создаёт JavaScript скрипт для заполнения localStorage
        
        Args:
            storage_data: Словарь с данными для localStorage
        
        Returns:
            str: JavaScript код для выполнения
        """
        script_lines = []
        
        for key, value in storage_data.items():
            # Экранируем значение для JavaScript
            if isinstance(value, str):
                # Если уже JSON строка - не двойное кодирование
                if value.startswith('{') or value.startswith('['):
                    safe_value = value.replace('\\', '\\\\').replace("'", "\\'")
                else:
                    safe_value = value.replace('\\', '\\\\').replace("'", "\\'")
            else:
                safe_value = str(value).replace('\\', '\\\\').replace("'", "\\'")
            
            script_lines.append(f"localStorage.setItem('{key}', '{safe_value}');")
        
        return '\n'.join(script_lines)
    
    def generate_full_storage(self) -> Dict[str, Any]:
        """
        Генерирует полный набор localStorage данных
        
        Returns:
            Dict[str, Any]: Все данные для localStorage
        """
        full_storage = {}
        
        # Добавляем общие данные
        full_storage.update(self.generate_common_storage())
        
        # Добавляем Google данные (50% шанс)
        if random.random() < 0.5:
            full_storage.update(self.generate_google_storage())
        
        # Добавляем Discord предварительные данные (показывает что пользователь УЖЕ был на Discord)
        full_storage.update(self.generate_discord_pre_storage())
        
        return full_storage
    
    def get_summary(self, storage_data: Dict[str, Any]) -> str:
        """Возвращает краткую сводку о сгенерированных данных"""
        age_days = self.browser_age_days
        return f"Browser age: {age_days} days | Storage items: {len(storage_data)}"


if __name__ == '__main__':
    # Тест генератора
    gen = StorageGenerator()
    storage = gen.generate_full_storage()
    
    print("=" * 70)
    print("STORAGE GENERATOR TEST")
    print("=" * 70)
    print(gen.get_summary(storage))
    print(f"\n[STORAGE DATA] ({len(storage)} items):")
    for key, value in list(storage.items())[:10]:  # Показываем первые 10
        value_str = str(value)[:60] + '...' if len(str(value)) > 60 else str(value)
        print(f"  {key}: {value_str}")
    print(f"  ... and {len(storage) - 10} more")

