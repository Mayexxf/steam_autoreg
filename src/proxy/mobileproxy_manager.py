#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MobileProxy Manager для mobileproxy.space

Управление мобильными прокси через API:
- Смена IP адреса
- Получение информации о прокси
- Автоматическое определение геолокации
"""

import requests
import time
import os


class MobileProxyManager:
    """Менеджер для работы с mobileproxy.space API"""

    API_ENDPOINT = "https://changeip.mobileproxy.space/"

    def __init__(self, proxy_key=None):
        """
        Инициализация менеджера

        Args:
            proxy_key: API ключ прокси (загружается из mobileproxy_config.txt или env)
        """
        self.proxy_key = proxy_key or self._load_proxy_key()

        if not self.proxy_key:
            raise ValueError("Proxy key not found! Set MOBILEPROXY_KEY env or create mobileproxy_config.txt")

    def _load_proxy_key(self):
        """Загружает proxy_key из конфига или переменной окружения"""
        # Пробуем загрузить из переменной окружения
        proxy_key = os.getenv("MOBILEPROXY_KEY")
        if proxy_key:
            return proxy_key.strip()

        # Пробуем загрузить из файла
        try:
            with open("mobileproxy_config.txt", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        return line
        except FileNotFoundError:
            pass

        return None

    def change_ip(self, wait_time=3):
        """
        Меняет IP адрес мобильного прокси

        Args:
            wait_time: Время ожидания после смены IP (секунды)

        Returns:
            dict: {
                'success': bool,
                'new_ip': str,
                'change_time': float,
                'proxy_id': str,
                'message': str
            }
        """
        try:
            print(f"[MOBILEPROXY] Changing IP...")

            # Формируем URL с параметрами
            url = f"{self.API_ENDPOINT}?proxy_key={self.proxy_key}&format=json"

            # ВАЖНО: User-Agent обязателен по документации API!
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }

            # Отправляем GET запрос
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                try:
                    result = response.json()

                    # Проверяем успешность операции
                    if result.get('status') == 'ok' or result.get('code') == 200:
                        new_ip = result.get('new_ip', 'unknown')
                        change_time = result.get('rt', 0)
                        proxy_id = result.get('proxy_id', 'unknown')

                        print(f"[MOBILEPROXY] ✓ IP changed successfully!")
                        print(f"[MOBILEPROXY]   New IP: {new_ip}")
                        print(f"[MOBILEPROXY]   Change time: {change_time}s")
                        print(f"[MOBILEPROXY]   Proxy ID: {proxy_id}")

                        # Ждем применения изменений
                        if wait_time > 0:
                            time.sleep(wait_time)

                        return {
                            'success': True,
                            'new_ip': new_ip,
                            'change_time': change_time,
                            'proxy_id': proxy_id,
                            'message': 'IP changed successfully'
                        }
                    else:
                        # Ошибка от API
                        code = result.get('code', 'unknown')
                        message = result.get('message', 'Unknown error')

                        print(f"[MOBILEPROXY] ✗ API Error: {message}")
                        print(f"[MOBILEPROXY]   Error code: {code}")

                        return {
                            'success': False,
                            'new_ip': None,
                            'change_time': 0,
                            'proxy_id': None,
                            'message': f"API Error: {message} (code: {code})"
                        }

                except ValueError:
                    # Ответ не JSON
                    print(f"[MOBILEPROXY] ✗ Invalid JSON response")
                    return {
                        'success': False,
                        'new_ip': None,
                        'change_time': 0,
                        'proxy_id': None,
                        'message': 'Invalid JSON response'
                    }
            else:
                print(f"[MOBILEPROXY] ✗ HTTP Error: {response.status_code}")
                return {
                    'success': False,
                    'new_ip': None,
                    'change_time': 0,
                    'proxy_id': None,
                    'message': f"HTTP {response.status_code}"
                }

        except requests.exceptions.Timeout:
            print(f"[MOBILEPROXY] ✗ Timeout - API not responding")
            return {
                'success': False,
                'new_ip': None,
                'change_time': 0,
                'proxy_id': None,
                'message': 'API timeout'
            }
        except Exception as e:
            print(f"[MOBILEPROXY] ✗ Error: {str(e)[:100]}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'new_ip': None,
                'change_time': 0,
                'proxy_id': None,
                'message': str(e)[:100]
            }

    def get_geolocation(self, ip_address):
        """
        Определяет геолокацию по IP адресу

        Args:
            ip_address: IP адрес для определения геолокации

        Returns:
            dict: {
                'success': bool,
                'country': str,
                'city': str,
                'timezone': str,
                'currency': str,
                'locale': str
            }
        """
        if not ip_address or ip_address == 'unknown':
            return {'success': False, 'message': 'Invalid IP address'}

        try:
            print(f"[GEO] Detecting geolocation for IP: {ip_address}")

            # Используем бесплатный API для определения геолокации
            response = requests.get(
                f"http://ip-api.com/json/{ip_address}?fields=status,country,countryCode,city,timezone,currency",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                if data.get('status') == 'success':
                    country = data.get('country', '')
                    city = data.get('city', '')
                    timezone = data.get('timezone', '')
                    currency = data.get('currency', '')

                    print(f"[GEO] ✓ Location detected:")
                    print(f"[GEO]   Country: {country}")
                    print(f"[GEO]   City: {city}")
                    print(f"[GEO]   Timezone: {timezone}")
                    print(f"[GEO]   Currency: {currency}")

                    # Определяем locale на основе страны
                    from ..stealth.geo_config import get_geo_config
                    geo_config = get_geo_config(country)

                    # Переопределяем данными от API
                    if timezone:
                        geo_config['timezone'] = timezone
                    if currency:
                        geo_config['currency'] = currency

                    geo_config['city'] = city
                    geo_config['country'] = country
                    geo_config['success'] = True

                    return geo_config
                else:
                    print(f"[GEO] ✗ API returned error status")
                    return {'success': False, 'message': 'Geolocation API error'}
            else:
                print(f"[GEO] ✗ HTTP {response.status_code}")
                return {'success': False, 'message': f'HTTP {response.status_code}'}

        except Exception as e:
            print(f"[GEO] ✗ Error: {str(e)[:100]}")
            return {'success': False, 'message': str(e)[:100]}

    def change_ip_and_get_geo(self, wait_time=3):
        """
        Меняет IP и автоматически определяет геолокацию

        Args:
            wait_time: Время ожидания после смены IP (секунды)

        Returns:
            dict: {
                'success': bool,
                'new_ip': str,
                'change_time': float,
                'proxy_id': str,
                'geo': dict (геолокация)
            }
        """
        # Меняем IP
        result = self.change_ip(wait_time=wait_time)

        if not result['success']:
            return result

        # Определяем геолокацию
        geo = self.get_geolocation(result['new_ip'])
        result['geo'] = geo

        return result
