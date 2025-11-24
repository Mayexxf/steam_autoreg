import random
import string
import time
import json
from datetime import datetime, timedelta


class StorageGenerator:
    def __init__(self):
        """
        Генератор фейковых данных localStorage для обхода детекта автоматизации
        """
        pass

    def generate_id(self, length=16):
        """Генерирует случайный ID"""
        characters = string.ascii_lowercase + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    def generate_timestamp(self, days_ago=0, hours_ago=0):
        """Генерирует временную метку"""
        dt = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
        return int(dt.timestamp() * 1000)

    def generate_storage(self):
        """Генерирует данные localStorage для имитации обычного пользователя"""
        storage_data = {}

        # Данные по ключам, которые часто встречаются в localStorage пользователей
        storage_data["steam_client"] = "false"
        storage_data["steam_wizard"] = str(random.randint(0, 1))

        # Имитация данных о посещениях
        visits = {
            "first_visit": self.generate_timestamp(days_ago=random.randint(10, 30)),
            "last_visit": self.generate_timestamp(hours_ago=random.randint(1, 24)),
            "visit_count": str(random.randint(5, 20))
        }
        storage_data["steam_visits"] = json.dumps(visits)

        # Имитация пользовательских настроек
        settings = {
            "language": random.choice(["english", "russian", "german", "french"]),
            "theme": random.choice(["light", "dark", "default"]),
            "notifications": str(random.randint(0, 1)),
            "adult_content": str(random.randint(0, 1)),
            "session_id": self.generate_id(24)
        }
        storage_data["steam_settings"] = json.dumps(settings)

        # Другие распространенные ключи
        storage_data["gdpr_preferences"] = json.dumps({"consent": "true", "timestamp": self.generate_timestamp()})

        return storage_data
