"""
AZcaptcha solver module for hCaptcha
Официальная документация: https://azcaptcha.com/document

Этот модуль использует API AZcaptcha для решения hCaptcha.
Стоимость: $1 за 1000 решённых капч
"""

import time
import requests
from typing import Optional, Dict, Any


class AZcaptchaSolver:
    """
    Класс для решения hCaptcha через сервис AZcaptcha

    API Flow:
    1. Отправка задачи на in.php -> получение ID
    2. Ожидание обработки (5-20 секунд)
    3. Получение результата с res.php -> получение токена
    4. Токен вставляется в поля h-captcha-response и g-recaptcha-response
    """

    # API endpoints
    API_IN = "https://azcaptcha.com/in.php"
    API_RES = "https://azcaptcha.com/res.php"

    def __init__(self, api_key: str, debug: bool = False):
        """
        Инициализация AZcaptcha solver

        :param api_key: 32-символьный API ключ AZcaptcha
        :param debug: Режим отладки (вывод подробной информации)
        """
        self.api_key = api_key
        self.debug = debug

        if self.debug:
            print("✓ Инициализирован AZcaptcha Solver")

    def solve_hcaptcha(self,
                      website_url: str,
                      website_key: str,
                      user_agent: Optional[str] = None,
                      proxy: Optional[str] = None,
                      proxy_type: str = "HTTP",
                      max_attempts: int = 60,
                      poll_interval: int = 5) -> Optional[str]:
        """
        Полный цикл решения hCaptcha: создание задачи + получение результата

        :param website_url: Полный URL страницы с капчей
        :param website_key: Значение data-sitekey из элемента hCaptcha
        :param user_agent: User-Agent браузера (опционально)
        :param proxy: Прокси в формате login:password@IP:PORT (опционально)
        :param proxy_type: Тип прокси: HTTP, HTTPS, SOCKS4, SOCKS5
        :param max_attempts: Максимальное количество попыток проверки результата
        :param poll_interval: Интервал между проверками в секундах (рекомендуется 5)
        :return: Токен решения (h-captcha-response) или None в случае ошибки
        """
        # Создаем задачу
        task_id = self._create_task(
            website_url=website_url,
            website_key=website_key,
            user_agent=user_agent,
            proxy=proxy,
            proxy_type=proxy_type
        )

        if not task_id:
            return None

        # Получаем результат
        solution_token = self._get_task_result(
            task_id=task_id,
            max_attempts=max_attempts,
            poll_interval=poll_interval
        )

        return solution_token

    def _create_task(self,
                    website_url: str,
                    website_key: str,
                    user_agent: Optional[str] = None,
                    proxy: Optional[str] = None,
                    proxy_type: str = "HTTP") -> Optional[str]:
        """
        Создает задачу для решения hCaptcha через API

        :return: ID задачи или None в случае ошибки
        """
        try:
            print(f"🔄 Отправка задачи на AZcaptcha...")
            print(f"   Website: {website_url}")
            print(f"   Sitekey: {website_key}")

            # Формируем параметры запроса
            params = {
                "key": self.api_key,
                "method": "hcaptcha",
                "sitekey": website_key,
                "pageurl": website_url,
                "json": 1  # Используем JSON формат ответа
            }

            # Добавляем опциональные параметры
            if user_agent:
                params["userAgent"] = user_agent
                if self.debug:
                    print(f"   User-Agent: {user_agent[:50]}...")

            if proxy:
                params["proxy"] = proxy
                params["proxytype"] = proxy_type.upper()
                # Скрываем пароль в логах
                safe_proxy = proxy.split('@')[1] if '@' in proxy else proxy
                print(f"   Proxy: {safe_proxy} ({proxy_type})")

            # Отправляем запрос (GET или POST - AZcaptcha поддерживает оба)
            response = requests.get(
                self.API_IN,
                params=params,
                timeout=30
            )

            # Проверяем статус код
            if response.status_code != 200:
                print(f"❌ HTTP Error {response.status_code}")
                return None

            # Парсим JSON ответ
            try:
                result = response.json()
            except ValueError:
                # Fallback на plain text парсинг
                text = response.text.strip()
                if text.startswith("OK|"):
                    task_id = text.split("|")[1]
                    print(f"✓ Задача создана. ID: {task_id}")
                    return task_id
                elif text.startswith("ERROR_"):
                    print(f"❌ Ошибка AZcaptcha: {text}")
                    return None
                else:
                    print(f"❌ Неизвестный ответ: {text}")
                    return None

            # Проверяем JSON ответ
            if result.get("status") == 1:
                task_id = result.get("request")
                print(f"✓ Задача создана. ID: {task_id}")
                return task_id
            else:
                error = result.get("request", "Unknown error")
                print(f"❌ Ошибка создания задачи: {error}")
                self._print_error_description(error)
                return None

        except requests.RequestException as e:
            print(f"❌ Ошибка при отправке запроса на AZcaptcha: {e}")
            return None
        except Exception as e:
            print(f"❌ Неожиданная ошибка при создании задачи: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return None

    def _get_task_result(self,
                        task_id: str,
                        max_attempts: int = 60,
                        poll_interval: int = 5) -> Optional[str]:
        """
        Получает результат решения задачи через API

        :param task_id: ID задачи
        :param max_attempts: Максимальное количество попыток проверки
        :param poll_interval: Интервал между проверками в секундах
        :return: Токен решения или None в случае ошибки
        """
        try:
            print(f"⏳ Ожидание решения задачи {task_id}...")
            print(f"   (может занять до {max_attempts * poll_interval} секунд)")

            for attempt in range(max_attempts):
                # Задержка перед проверкой (первый раз подождем poll_interval секунд)
                time.sleep(poll_interval)

                # Формируем параметры запроса
                params = {
                    "key": self.api_key,
                    "action": "get",
                    "id": task_id,
                    "json": 1
                }

                # Запрашиваем результат
                response = requests.get(
                    self.API_RES,
                    params=params,
                    timeout=30
                )

                # Проверяем статус код
                if response.status_code != 200:
                    print(f"❌ HTTP Error {response.status_code}")
                    continue

                # Парсим ответ
                try:
                    result = response.json()
                except ValueError:
                    # Fallback на plain text парсинг
                    text = response.text.strip()

                    if text == "CAPCHA_NOT_READY":
                        if self.debug:
                            print(f"   Попытка {attempt + 1}/{max_attempts}: обработка...")
                        continue
                    elif text.startswith("ERROR_"):
                        print(f"❌ Ошибка: {text}")
                        self._print_error_description(text)
                        return None
                    else:
                        # Это токен решения
                        print(f"✓ Капча решена успешно через AZcaptcha!")
                        if self.debug:
                            print(f"   Токен: {text[:50]}...")
                        return text

                # Проверяем JSON ответ
                status = result.get("status")

                if status == 1:
                    # Решение готово
                    solution_token = result.get("request")
                    print(f"✓ Капча решена успешно через AZcaptcha!")
                    if self.debug:
                        print(f"   Токен: {solution_token[:50]}...")
                    return solution_token
                elif status == 0:
                    error = result.get("request", "Unknown error")

                    if error == "CAPCHA_NOT_READY":
                        if self.debug:
                            print(f"   Попытка {attempt + 1}/{max_attempts}: обработка...")
                        continue
                    else:
                        print(f"❌ Ошибка: {error}")
                        self._print_error_description(error)
                        return None
                else:
                    print(f"❌ Неизвестный статус: {status}")
                    return None

            print(f"❌ Превышено максимальное количество попыток ({max_attempts})")
            return None

        except requests.RequestException as e:
            print(f"❌ Ошибка при запросе результата: {e}")
            return None
        except Exception as e:
            print(f"❌ Неожиданная ошибка при получении результата: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return None

    def _print_error_description(self, error_code: str):
        """
        Выводит описание ошибки AZcaptcha

        :param error_code: Код ошибки
        """
        error_descriptions = {
            "ERROR_WRONG_USER_KEY": "Неверный формат API ключа (должен быть 32 символа)",
            "ERROR_KEY_DOES_NOT_EXIST": "API ключ не существует",
            "ERROR_ZERO_BALANCE": "Недостаточно средств на балансе аккаунта",
            "ERROR_PAGEURL": "Отсутствует параметр pageurl",
            "ERROR_INVALID_SITEKEY": "Неверный или устаревший sitekey (проверьте актуальность)",
            "ERROR_NO_SLOT_AVAILABLE": "Нет доступных слотов (очередь переполнена)",
            "ERROR_ZERO_CAPTCHA_FILESIZE": "Размер файла капчи равен 0",
            "ERROR_TOO_BIG_CAPTCHA_FILESIZE": "Файл капчи слишком большой",
            "ERROR_WRONG_FILE_EXTENSION": "Неверное расширение файла",
            "ERROR_IMAGE_TYPE_NOT_SUPPORTED": "Тип изображения не поддерживается",
            "ERROR_CAPTCHA_UNSOLVABLE": "Капча не может быть решена (после нескольких попыток)",
            "ERROR_BAD_PARAMETERS": "Неверные параметры запроса",
            "ERROR_BAD_PROXY": "Неверный формат прокси",
            "ERROR_PROXY_CONNECTION_FAILED": "Не удалось подключиться к прокси",
            "CAPCHA_NOT_READY": "Решение еще не готово, попробуйте позже"
        }

        description = error_descriptions.get(error_code)
        if description:
            print(f"   Описание: {description}")

    def get_balance(self) -> Optional[float]:
        """
        Получает текущий баланс аккаунта

        :return: Баланс в USD или None в случае ошибки
        """
        try:
            params = {
                "key": self.api_key,
                "action": "getbalance",
                "json": 1
            }

            response = requests.get(
                self.API_RES,
                params=params,
                timeout=10
            )

            if response.status_code != 200:
                return None

            try:
                result = response.json()
                if result.get("status") == 1:
                    balance = float(result.get("request", 0))
                    return balance
            except (ValueError, TypeError):
                text = response.text.strip()
                try:
                    return float(text)
                except ValueError:
                    return None

            return None

        except Exception as e:
            if self.debug:
                print(f"❌ Ошибка получения баланса: {e}")
            return None


def load_azcaptcha_config(config_file: str = "azcaptcha_config.txt") -> Optional[str]:
    """
    Загружает API ключ AZcaptcha из файла или переменной окружения

    :param config_file: Путь к файлу конфигурации
    :return: API ключ или None
    """
    import os

    # Пытаемся загрузить из переменной окружения
    api_key = os.getenv("AZCAPTCHA_API_KEY")
    if api_key:
        return api_key.strip()

    # Пытаемся загрузить из файла
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        return line
        except Exception as e:
            print(f"⚠️ Ошибка чтения {config_file}: {e}")

    return None