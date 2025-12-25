"""
Конфигурация геолокации для разных стран
Маппинг стран на языки, таймзоны, валюты и Accept-Language заголовки
"""

# Маппинг стран на локали и настройки
GEO_MAPPING = {
    # Украина
    "ukraine": {
        "locale": "uk-UA",
        "timezone": "Europe/Kiev",
        "timezone_offset": -120,  # UTC+2 (зимой) = -120 минут
        "currency": "UAH",
        "country_code": "UA",  # ISO 3166-1 alpha-2 (для Steam)
        "steam_language": "ukrainian",  # Язык Steam
        "accept_language": "uk-UA,uk;q=0.9,en;q=0.8",
        "keyboard_layout": "ukrainian",
    },
    "київ": {
        "locale": "uk-UA",
        "timezone": "Europe/Kiev",
        "currency": "UAH",
        "accept_language": "uk-UA,uk;q=0.9,en;q=0.8",
        "keyboard_layout": "ukrainian",
    },

    # Россия
    "russia": {
        "locale": "ru-RU",
        "timezone": "Europe/Moscow",
        "currency": "RUB",
        "accept_language": "ru-RU,ru;q=0.9,en;q=0.8",
        "keyboard_layout": "russian",
    },
    "москва": {
        "locale": "ru-RU",
        "timezone": "Europe/Moscow",
        "currency": "RUB",
        "accept_language": "ru-RU,ru;q=0.9,en;q=0.8",
        "keyboard_layout": "russian",
    },

    # США
    "usa": {
        "locale": "en-US",
        "timezone": "America/New_York",
        "currency": "USD",
        "accept_language": "en-US,en;q=0.9",
        "keyboard_layout": "us",
    },
    "united states": {
        "locale": "en-US",
        "timezone": "America/New_York",
        "currency": "USD",
        "accept_language": "en-US,en;q=0.9",
        "keyboard_layout": "us",
    },

    # Великобритания
    "uk": {
        "locale": "en-GB",
        "timezone": "Europe/London",
        "currency": "GBP",
        "accept_language": "en-GB,en;q=0.9",
        "keyboard_layout": "gb",
    },
    "united kingdom": {
        "locale": "en-GB",
        "timezone": "Europe/London",
        "currency": "GBP",
        "accept_language": "en-GB,en;q=0.9",
        "keyboard_layout": "gb",
    },

    # Германия
    "germany": {
        "locale": "de-DE",
        "timezone": "Europe/Berlin",
        "currency": "EUR",
        "accept_language": "de-DE,de;q=0.9,en;q=0.8",
        "keyboard_layout": "de",
    },

    # Франция
    "france": {
        "locale": "fr-FR",
        "timezone": "Europe/Paris",
        "currency": "EUR",
        "accept_language": "fr-FR,fr;q=0.9,en;q=0.8",
        "keyboard_layout": "fr",
    },

    # Испания
    "spain": {
        "locale": "es-ES",
        "timezone": "Europe/Madrid",
        "currency": "EUR",
        "accept_language": "es-ES,es;q=0.9,en;q=0.8",
        "keyboard_layout": "es",
    },

    # Италия
    "italy": {
        "locale": "it-IT",
        "timezone": "Europe/Rome",
        "currency": "EUR",
        "accept_language": "it-IT,it;q=0.9,en;q=0.8",
        "keyboard_layout": "it",
    },

    # Польша
    "poland": {
        "locale": "pl-PL",
        "timezone": "Europe/Warsaw",
        "currency": "PLN",
        "accept_language": "pl-PL,pl;q=0.9,en;q=0.8",
        "keyboard_layout": "pl",
    },

    # Турция
    "turkey": {
        "locale": "tr-TR",
        "timezone": "Europe/Istanbul",
        "currency": "TRY",
        "accept_language": "tr-TR,tr;q=0.9,en;q=0.8",
        "keyboard_layout": "tr",
    },

    # Бразилия
    "brazil": {
        "locale": "pt-BR",
        "timezone": "America/Sao_Paulo",
        "currency": "BRL",
        "accept_language": "pt-BR,pt;q=0.9,en;q=0.8",
        "keyboard_layout": "br",
    },

    # Канада
    "canada": {
        "locale": "en-CA",
        "timezone": "America/Toronto",
        "currency": "CAD",
        "accept_language": "en-CA,en;q=0.9,fr;q=0.8",
        "keyboard_layout": "us",
    },

    # Австралия
    "australia": {
        "locale": "en-AU",
        "timezone": "Australia/Sydney",
        "currency": "AUD",
        "accept_language": "en-AU,en;q=0.9",
        "keyboard_layout": "us",
    },

    # Япония
    "japan": {
        "locale": "ja-JP",
        "timezone": "Asia/Tokyo",
        "currency": "JPY",
        "accept_language": "ja-JP,ja;q=0.9,en;q=0.8",
        "keyboard_layout": "jp",
    },

    # Южная Корея
    "south korea": {
        "locale": "ko-KR",
        "timezone": "Asia/Seoul",
        "currency": "KRW",
        "accept_language": "ko-KR,ko;q=0.9,en;q=0.8",
        "keyboard_layout": "kr",
    },

    # Китай
    "china": {
        "locale": "zh-CN",
        "timezone": "Asia/Shanghai",
        "currency": "CNY",
        "accept_language": "zh-CN,zh;q=0.9,en;q=0.8",
        "keyboard_layout": "cn",
    },

    # Индия
    "india": {
        "locale": "en-IN",
        "timezone": "Asia/Kolkata",
        "currency": "INR",
        "accept_language": "en-IN,en;q=0.9,hi;q=0.8",
        "keyboard_layout": "us",
    },

    # Мексика
    "mexico": {
        "locale": "es-MX",
        "timezone": "America/Mexico_City",
        "currency": "MXN",
        "accept_language": "es-MX,es;q=0.9,en;q=0.8",
        "keyboard_layout": "latam",
    },

    # Аргентина
    "argentina": {
        "locale": "es-AR",
        "timezone": "America/Argentina/Buenos_Aires",
        "currency": "ARS",
        "accept_language": "es-AR,es;q=0.9,en;q=0.8",
        "keyboard_layout": "latam",
    },

    # Нидерланды
    "netherlands": {
        "locale": "nl-NL",
        "timezone": "Europe/Amsterdam",
        "currency": "EUR",
        "accept_language": "nl-NL,nl;q=0.9,en;q=0.8",
        "keyboard_layout": "us-intl",
    },

    # Швеция
    "sweden": {
        "locale": "sv-SE",
        "timezone": "Europe/Stockholm",
        "currency": "SEK",
        "accept_language": "sv-SE,sv;q=0.9,en;q=0.8",
        "keyboard_layout": "se",
    },

    # Норвегия
    "norway": {
        "locale": "nb-NO",
        "timezone": "Europe/Oslo",
        "currency": "NOK",
        "accept_language": "nb-NO,nb;q=0.9,en;q=0.8",
        "keyboard_layout": "no",
    },

    # Финляндия
    "finland": {
        "locale": "fi-FI",
        "timezone": "Europe/Helsinki",
        "currency": "EUR",
        "accept_language": "fi-FI,fi;q=0.9,en;q=0.8",
        "keyboard_layout": "fi",
    },

    # Чехия
    "czech republic": {
        "locale": "cs-CZ",
        "timezone": "Europe/Prague",
        "currency": "CZK",
        "accept_language": "cs-CZ,cs;q=0.9,en;q=0.8",
        "keyboard_layout": "cz",
    },

    # Румыния
    "romania": {
        "locale": "ro-RO",
        "timezone": "Europe/Bucharest",
        "currency": "RON",
        "accept_language": "ro-RO,ro;q=0.9,en;q=0.8",
        "keyboard_layout": "ro",
    },

    # Беларусь
    "belarus": {
        "locale": "be-BY",
        "timezone": "Europe/Minsk",
        "currency": "BYN",
        "accept_language": "be-BY,be;q=0.9,ru;q=0.8,en;q=0.7",
        "keyboard_layout": "by",
    },

    # Казахстан
    "kazakhstan": {
        "locale": "kk-KZ",
        "timezone": "Asia/Almaty",
        "currency": "KZT",
        "accept_language": "kk-KZ,kk;q=0.9,ru;q=0.8,en;q=0.7",
        "keyboard_layout": "kz",
    },
}

# Дефолтная конфигурация (если страна не найдена)
DEFAULT_GEO_CONFIG = {
    "locale": "en-US",
    "timezone": "Europe/Kiev",
    "currency": "USD",
    "accept_language": "en-US,en;q=0.9",
    "keyboard_layout": "us",
}


def get_geo_config(geo_name):
    """
    Получает конфигурацию локали по названию GEO

    Args:
        geo_name: Название GEO (например, "Київ", "Moscow", "New York")

    Returns:
        dict с конфигурацией локали или DEFAULT_GEO_CONFIG
    """
    if not geo_name:
        return DEFAULT_GEO_CONFIG.copy()

    # Нормализуем название (lowercase для поиска)
    geo_lower = geo_name.lower().strip()

    # Пробуем найти прямое совпадение
    if geo_lower in GEO_MAPPING:
        return GEO_MAPPING[geo_lower].copy()

    # Пробуем найти частичное совпадение (например, "Київ, Україна" -> "київ")
    for key, config in GEO_MAPPING.items():
        if key in geo_lower or geo_lower in key:
            return config.copy()

    # Если не найдено - возвращаем дефолтную конфигурацию
    print(f"[GEO CONFIG] No mapping found for '{geo_name}', using default (en-US)")
    return DEFAULT_GEO_CONFIG.copy()


# Маппинг timezone → timezone_offset (в минутах от UTC)
# ВАЖНО: offset ОТРИЦАТЕЛЬНЫЙ для восточных timezone (UTC+X → -X*60)
TIMEZONE_OFFSETS = {
    "Europe/Kiev": -120,         # UTC+2
    "Europe/Moscow": -180,       # UTC+3
    "America/New_York": 300,     # UTC-5
    "America/Chicago": 360,      # UTC-6
    "America/Los_Angeles": 480,  # UTC-8
    "Europe/London": 0,          # UTC+0
    "Europe/Berlin": -60,        # UTC+1
    "Europe/Paris": -60,         # UTC+1
    "Europe/Madrid": -60,        # UTC+1
    "Europe/Rome": -60,          # UTC+1
    "Europe/Warsaw": -60,        # UTC+1
    "Europe/Istanbul": -180,     # UTC+3
    "America/Sao_Paulo": 180,    # UTC-3
    "America/Toronto": 300,      # UTC-5
    "Australia/Sydney": -660,    # UTC+11
    "Asia/Tokyo": -540,          # UTC+9
    "Asia/Seoul": -540,          # UTC+9
    "Asia/Shanghai": -480,       # UTC+8
    "Asia/Kolkata": -330,        # UTC+5:30
    "America/Mexico_City": 360,  # UTC-6
    "America/Argentina/Buenos_Aires": 180,  # UTC-3
    "Europe/Amsterdam": -60,     # UTC+1
    "Europe/Stockholm": -60,     # UTC+1
    "Europe/Oslo": -60,          # UTC+1
    "Europe/Helsinki": -120,     # UTC+2
    "Europe/Prague": -60,        # UTC+1
    "Europe/Bucharest": -120,    # UTC+2
    "Europe/Minsk": -180,        # UTC+3
    "Asia/Almaty": -360,         # UTC+6
}

# Маппинг locale → ISO country code (для Steam)
COUNTRY_CODES = {
    "uk-UA": "UA",
    "ru-RU": "RU",
    "en-US": "US",
    "en-GB": "GB",
    "de-DE": "DE",
    "fr-FR": "FR",
    "es-ES": "ES",
    "it-IT": "IT",
    "pl-PL": "PL",
    "tr-TR": "TR",
    "pt-BR": "BR",
    "en-CA": "CA",
    "en-AU": "AU",
    "ja-JP": "JP",
    "ko-KR": "KR",
    "zh-CN": "CN",
    "en-IN": "IN",
    "es-MX": "MX",
    "es-AR": "AR",
    "nl-NL": "NL",
    "sv-SE": "SE",
    "nb-NO": "NO",
    "fi-FI": "FI",
    "cs-CZ": "CZ",
    "ro-RO": "RO",
    "be-BY": "BY",
    "kk-KZ": "KZ",
}

# Маппинг locale → Steam language
STEAM_LANGUAGES = {
    "uk-UA": "ukrainian",
    "ru-RU": "russian",
    "en-US": "english",
    "en-GB": "english",
    "de-DE": "german",
    "fr-FR": "french",
    "es-ES": "spanish",
    "it-IT": "italian",
    "pl-PL": "polish",
    "tr-TR": "turkish",
    "pt-BR": "portuguese",
    "en-CA": "english",
    "en-AU": "english",
    "ja-JP": "japanese",
    "ko-KR": "korean",
    "zh-CN": "schinese",  # simplified chinese
    "en-IN": "english",
    "es-MX": "spanish",
    "es-AR": "spanish",
    "nl-NL": "dutch",
    "sv-SE": "swedish",
    "nb-NO": "norwegian",
    "fi-FI": "finnish",
    "cs-CZ": "czech",
    "ro-RO": "romanian",
    "be-BY": "russian",  # Belarus использует русский в Steam
    "kk-KZ": "russian",  # Kazakhstan использует русский в Steam
}


def enrich_geo_config(config):
    """
    Обогащает geo config дополнительными полями для Steam

    Args:
        config: базовый geo config

    Returns:
        обогащенный config с timezone_offset, country_code, steam_language
    """
    locale = config.get('locale', 'en-US')
    timezone = config.get('timezone', 'America/New_York')

    # Добавляем timezone_offset
    if 'timezone_offset' not in config:
        config['timezone_offset'] = TIMEZONE_OFFSETS.get(timezone, 300)  # default UTC-5

    # Добавляем country_code
    if 'country_code' not in config:
        config['country_code'] = COUNTRY_CODES.get(locale, 'US')  # default US

    # Добавляем steam_language
    if 'steam_language' not in config:
        config['steam_language'] = STEAM_LANGUAGES.get(locale, 'english')  # default english

    return config


def detect_country_from_geo(geo_name):
    """
    Определяет название страны из GEO строки

    Args:
        geo_name: Название GEO

    Returns:
        str название страны или None
    """
    if not geo_name:
        return None

    geo_lower = geo_name.lower()

    # Словарь для определения страны по ключевым словам
    country_keywords = {
        "ukraine": ["україна", "ukraine", "київ", "kyiv", "kiev", "одеса", "львів"],
        "russia": ["россия", "russia", "москва", "moscow", "питер", "petersburg"],
        "usa": ["usa", "united states", "america", "new york", "los angeles"],
        "germany": ["germany", "deutschland", "berlin", "munich"],
        "france": ["france", "paris", "lyon"],
        "uk": ["uk", "united kingdom", "britain", "london"],
        "poland": ["poland", "polska", "warsaw", "warszawa"],
        "spain": ["spain", "españa", "madrid", "barcelona"],
        "italy": ["italy", "italia", "rome", "milan"],
        "turkey": ["turkey", "türkiye", "istanbul", "ankara"],
    }

    for country, keywords in country_keywords.items():
        for keyword in keywords:
            if keyword in geo_lower:
                return country

    return None
