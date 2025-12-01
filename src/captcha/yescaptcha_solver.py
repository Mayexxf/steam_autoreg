"""
YesCaptcha solver module for hCaptcha
Официальная документация: https://yescaptcha.atlassian.net/wiki/spaces/YESCAPTCHA/pages/30113813/HCaptcha+Python+selenium+DEMO
API SDK: https://github.com/yescaptcha/yescaptcha-python

Этот модуль использует официальный API YesCaptcha для решения hCaptcha.
Рекомендуется установить официальный SDK: pip install yescaptcha
"""

import time
import requests
from typing import Optional, Dict, Any

# Попытка импортировать официальный SDK
try:
    from yescaptcha.task import HCaptchaTaskProxyless
    from yescaptcha.client import Client
    YESCAPTCHA_SDK_AVAILABLE = True
except ImportError:
    YESCAPTCHA_SDK_AVAILABLE = False
    print("⚠️  Официальный YesCaptcha SDK не установлен. Используется fallback-реализация.")
    print("Установите SDK для лучшей производительности: pip install yescaptcha")


class YesCaptchaSolver:
    """
    Класс для решения hCaptcha через сервис YesCaptcha

    Поддерживает два режима работы:
    1. Использование официального SDK yescaptcha (рекомендуется)
    2. Прямое взаимодействие с API через requests (fallback)
    """

    def __init__(self, client_key: str, api_url: str = "https://api.yescaptcha.com", debug: bool = False):
        """
        Инициализация YesCaptcha solver

        :param client_key: API ключ YesCaptcha (ClientKey)
        :param api_url: URL API YesCaptcha (по умолчанию международный узел)
        :param debug: Режим отладки (вывод подробной информации)
        """
        self.client_key = client_key
        self.api_url = api_url.rstrip('/')
        self.debug = debug

        # Если доступен официальный SDK, используем его
        if YESCAPTCHA_SDK_AVAILABLE:
            self.client = Client(client_key=client_key, debug=debug)
            if debug:
                print("✓ Инициализирован YesCaptcha Client (официальный SDK)")
        else:
            self.client = None
            self.create_task_url = f"{self.api_url}/createTask"
            self.get_result_url = f"{self.api_url}/getTaskResult"
            if debug:
                print("✓ Инициализирован YesCaptcha Solver (fallback режим)")

    def solve_hcaptcha(self, website_url: str, website_key: str,
                      user_agent: Optional[str] = None,
                      is_invisible: bool = False,
                      enterprise_payload: Optional[Dict] = None,
                      max_attempts: int = 60,
                      poll_interval: int = 3) -> Optional[str]:
        """
        Полный цикл решения hCaptcha: создание задачи + получение результата

        :param website_url: URL страницы с капчей
        :param website_key: Ключ сайта hCaptcha (sitekey)
        :param user_agent: User-Agent браузера (опционально)
        :param is_invisible: Невидимая капча (опционально)
        :param enterprise_payload: Дополнительные данные для enterprise версии (опционально)
        :param max_attempts: Максимальное количество попыток проверки результата
        :param poll_interval: Интервал между проверками в секундах
        :return: Токен решения (gRecaptchaResponse) или None в случае ошибки
        """
        if YESCAPTCHA_SDK_AVAILABLE and self.client:
            return self._solve_with_sdk(
                website_url=website_url,
                website_key=website_key,
                user_agent=user_agent,
                is_invisible=is_invisible,
                enterprise_payload=enterprise_payload
            )
        else:
            return self._solve_with_api(
                website_url=website_url,
                website_key=website_key,
                user_agent=user_agent,
                is_invisible=is_invisible,
                enterprise_payload=enterprise_payload,
                max_attempts=max_attempts,
                poll_interval=poll_interval
            )

    def _solve_with_sdk(self, website_url: str, website_key: str,
                       user_agent: Optional[str] = None,
                       is_invisible: bool = False,
                       enterprise_payload: Optional[Dict] = None) -> Optional[str]:
        """
        Решение hCaptcha с использованием официального SDK

        :return: Токен решения или None в случае ошибки
        """
        try:
            print(f"Отправка задачи на YesCaptcha (SDK)...")
            print(f"Website URL: {website_url}")
            print(f"Website Key: {website_key}")

            # Создаем задачу используя официальный SDK
            task_params = {
                'website_key': website_key,
                'website_url': website_url
            }

            if user_agent:
                task_params['user_agent'] = user_agent
            if is_invisible:
                task_params['is_invisible'] = is_invisible
            if enterprise_payload:
                task_params['enterprise_payload'] = enterprise_payload

            task = HCaptchaTaskProxyless(**task_params)
            job = self.client.create_task(task)

            print(f"Задача создана. Ожидание решения...")

            # Получаем решение
            solution = job.get_solution()

            if solution and 'gRecaptchaResponse' in solution:
                captcha_response = solution['gRecaptchaResponse']
                print(f"✓ Капча решена успешно (SDK)!")
                if self.debug:
                    print(f"Токен: {captcha_response[:50]}...")
                return captcha_response
            else:
                print(f"❌ Не удалось получить решение капчи")
                return None

        except Exception as e:
            print(f"Ошибка при решении капчи через SDK: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return None

    def _solve_with_api(self, website_url: str, website_key: str,
                       user_agent: Optional[str] = None,
                       is_invisible: bool = False,
                       enterprise_payload: Optional[Dict] = None,
                       max_attempts: int = 60,
                       poll_interval: int = 3) -> Optional[str]:
        """
        Решение hCaptcha через прямое взаимодействие с API (fallback)

        :return: Токен решения или None в случае ошибки
        """
        # Создаем задачу
        task_id = self._create_task(
            website_url=website_url,
            website_key=website_key,
            user_agent=user_agent,
            is_invisible=is_invisible,
            enterprise_payload=enterprise_payload
        )

        if not task_id:
            return None

        # Получаем результат
        solution = self._get_task_result(
            task_id=task_id,
            max_attempts=max_attempts,
            poll_interval=poll_interval
        )

        if solution and "gRecaptchaResponse" in solution:
            return solution["gRecaptchaResponse"]

        return None

    def _create_task(self, website_url: str, website_key: str,
                    user_agent: Optional[str] = None,
                    is_invisible: bool = False,
                    enterprise_payload: Optional[Dict] = None) -> Optional[str]:
        """
        Создает задачу для решения hCaptcha через API

        :return: ID задачи или None в случае ошибки
        """
        try:
            # Формируем задачу
            task_data = {
                "type": "HCaptchaTaskProxyless",
                "websiteURL": website_url,
                "websiteKey": website_key
            }

            # Добавляем опциональные параметры
            if user_agent:
                task_data["userAgent"] = user_agent
            if is_invisible:
                task_data["isInvisible"] = is_invisible
            if enterprise_payload:
                task_data["enterprisePayload"] = enterprise_payload

            # Формируем запрос
            payload = {
                "clientKey": self.client_key,
                "task": task_data
            }

            print(f"Отправка задачи на YesCaptcha (API)...")
            print(f"Website URL: {website_url}")
            print(f"Website Key: {website_key}")

            # Отправляем запрос
            response = requests.post(
                self.create_task_url,
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            # Проверяем ответ
            if result.get("errorId") == 0:
                task_id = result.get("taskId")
                print(f"Задача создана успешно. Task ID: {task_id}")
                return task_id
            else:
                error_code = result.get("errorCode")
                error_description = result.get("errorDescription")
                print(f"Ошибка при создании задачи: {error_code} - {error_description}")
                return None

        except requests.RequestException as e:
            print(f"Ошибка при отправке запроса на YesCaptcha: {e}")
            return None
        except Exception as e:
            print(f"Неожиданная ошибка при создании задачи: {e}")
            return None

    def _get_task_result(self, task_id: str, max_attempts: int = 60,
                        poll_interval: int = 3) -> Optional[Dict[str, Any]]:
        """
        Получает результат решения задачи через API

        :param task_id: ID задачи
        :param max_attempts: Максимальное количество попыток проверки
        :param poll_interval: Интервал между проверками в секундах
        :return: Результат решения или None в случае ошибки
        """
        try:
            payload = {
                "clientKey": self.client_key,
                "taskId": task_id
            }

            print(f"Ожидание решения задачи {task_id}...")

            for attempt in range(max_attempts):
                # Небольшая задержка перед проверкой
                if attempt > 0:
                    time.sleep(poll_interval)
                else:
                    time.sleep(1)

                # Запрашиваем результат
                response = requests.post(
                    self.get_result_url,
                    json=payload,
                    timeout=30
                )

                response.raise_for_status()
                result = response.json()

                # Проверяем статус
                error_id = result.get("errorId")

                if error_id == 0:
                    status = result.get("status")

                    if status == "ready":
                        solution = result.get("solution")
                        print(f"✓ Капча решена успешно!")
                        return solution
                    elif status == "processing":
                        print(f"Попытка {attempt + 1}/{max_attempts}: задача в обработке...")
                        continue
                    else:
                        print(f"Неизвестный статус задачи: {status}")
                        return None
                else:
                    error_code = result.get("errorCode")
                    error_description = result.get("errorDescription")
                    print(f"Ошибка при получении результата: {error_code} - {error_description}")
                    return None

            print(f"Превышено максимальное количество попыток ({max_attempts})")
            return None

        except requests.RequestException as e:
            print(f"Ошибка при запросе результата: {e}")
            return None
        except Exception as e:
            print(f"Неожиданная ошибка при получении результата: {e}")
            return None