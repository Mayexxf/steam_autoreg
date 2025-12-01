#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест интеграции с MobileProxy API

Простой скрипт для проверки работы смены IP через mobileproxy.space
"""

import sys
import io

# Настройка кодировки для Windows консоли
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from src.proxy.mobileproxy_manager import MobileProxyManager

def test_api():
    """Тестирование API смены IP"""
    print("="*70)
    print("MobileProxy API Test")
    print("="*70)

    try:
        # Инициализируем менеджер
        print("\n[1/3] Initializing MobileProxyManager...")
        manager = MobileProxyManager()
        print("✓ Manager initialized successfully")

        # Меняем IP
        print("\n[2/3] Changing IP address...")
        result = manager.change_ip(wait_time=10)

        if result['success']:
            print(f"✓ IP changed successfully!")
            print(f"  New IP: {result['new_ip']}")
            print(f"  Change time: {result['change_time']}s")
            print(f"  Proxy ID: {result['proxy_id']}")
        else:
            print(f"✗ Failed to change IP: {result['message']}")
            return False

        # Определяем геолокацию
        print("\n[3/3] Detecting geolocation...")
        geo = manager.get_geolocation(result['new_ip'])

        if geo.get('success'):
            print(f"✓ Geolocation detected:")
            print(f"  Country: {geo.get('country')}")
            print(f"  City: {geo.get('city')}")
            print(f"  Timezone: {geo.get('timezone')}")
            print(f"  Currency: {geo.get('currency')}")
            print(f"  Locale: {geo.get('locale')}")
        else:
            print(f"✗ Failed to detect geolocation: {geo.get('message')}")

        print("\n" + "="*70)
        print("Test completed successfully!")
        print("="*70)

        return True

    except ValueError as e:
        print(f"\n✗ Configuration Error: {e}")
        print("\nPlease create mobileproxy_config.txt with your API key:")
        print("  1. Copy mobileproxy_config.txt.example to mobileproxy_config.txt")
        print("  2. Replace 'your_proxy_key_here_32_characters' with your actual key")
        print("  3. Get your key from https://mobileproxy.space (section 'Мои прокси')")
        return False

    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)
