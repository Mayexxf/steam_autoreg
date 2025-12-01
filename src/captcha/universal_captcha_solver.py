"""
Универсальный модуль для решения hCaptcha с поддержкой нескольких сервисов
Поддерживаемые сервисы:
- 2Captcha (рекомендуется для Steam)
- CapSolver (специализируется на сложных капчах)
- AntiCaptcha
- AZcaptcha (дешёвый - $1/1000 капч)
- YesCaptcha (fallback)
"""

import time
import requests
from typing import Optional, Dict, Any, Literal
from enum import Enum


class CaptchaService(str, Enum):
    """Поддерживаемые сервисы решения капчи"""
    TWOCAPTCHA = "2captcha"
    CAPSOLVER = "capsolver"
    ANTICAPTCHA = "anticaptcha"
    YESCAPTCHA = "yescaptcha"
    AZCAPTCHA = "azcaptcha"


class UniversalCaptchaSolver:
    """
    Универсальный класс для решения hCaptcha через различные сервисы

    Рекомендуемые сервисы для Steam hCaptcha Enterprise:
    1. 2Captcha - самый надёжный и популярный
    2. CapSolver - специализируется на сложных капчах
    3. AntiCaptcha - хорошие результаты с Enterprise
    """

    # API endpoints для разных сервисов
    API_ENDPOINTS = {
        CaptchaService.TWOCAPTCHA: {
            "create": "https://2captcha.com/in.php",
            "result": "https://2captcha.com/res.php"
        },
        CaptchaService.CAPSOLVER: {
            "create": "https://api.capsolver.com/createTask",
            "result": "https://api.capsolver.com/getTaskResult"
        },
        CaptchaService.ANTICAPTCHA: {
            "create": "https://api.anti-captcha.com/createTask",
            "result": "https://api.anti-captcha.com/getTaskResult"
        },
        CaptchaService.YESCAPTCHA: {
            "create": "https://api.yescaptcha.com/createTask",
            "result": "https://api.yescaptcha.com/getTaskResult"
        }
    }

    def __init__(self, service: CaptchaService, api_key: str, debug: bool = False):
        """
        Инициализация универсального решателя капчи

        :param service: Сервис для решения капчи
        :param api_key: API ключ сервиса
        :param debug: Режим отладки
        """
        self.service = service
        self.api_key = api_key
        self.debug = debug

        if self.debug:
            print(f"✓ Инициализирован {service} solver")

    def solve_hcaptcha(self,
                      website_url: str,
                      website_key: str,
                      user_agent: Optional[str] = None,
                      is_invisible: bool = False,
                      enterprise_payload: Optional[Dict] = None,
                      max_attempts: int = 60,
                      poll_interval: int = 3,
                      proxy: Optional[str] = None,
                      cookies: Optional[str] = None) -> Optional[str]:
        """
        Решение hCaptcha через выбранный сервис

        :param website_url: URL страницы с капчей
        :param website_key: Ключ сайта (sitekey)
        :param user_agent: User-Agent браузера
        :param is_invisible: Невидимая капча
        :param enterprise_payload: Enterprise параметры (rqdata)
        :param max_attempts: Максимальное количество попыток проверки
        :param poll_interval: Интервал между проверками в секундах
        :param proxy: Прокси в формате login:pass@ip:port
        :param cookies: Cookie для улучшения решения
        :return: Токен решения или None
        """
        if self.service == CaptchaService.TWOCAPTCHA:
            return self._solve_2captcha(
                website_url, website_key, user_agent, is_invisible,
                enterprise_payload, max_attempts, poll_interval, proxy
            )
        elif self.service == CaptchaService.CAPSOLVER:
            return self._solve_capsolver(
                website_url, website_key, user_agent, is_invisible,
                enterprise_payload, max_attempts, poll_interval, proxy
            )
        elif self.service == CaptchaService.ANTICAPTCHA:
            return self._solve_anticaptcha(
                website_url, website_key, user_agent, is_invisible,
                enterprise_payload, max_attempts, poll_interval, proxy
            )
        elif self.service == CaptchaService.YESCAPTCHA:
            return self._solve_yescaptcha(
                website_url, website_key, user_agent, is_invisible,
                enterprise_payload, max_attempts, poll_interval
            )
        elif self.service == CaptchaService.AZCAPTCHA:
            return self._solve_azcaptcha(
                website_url, website_key, user_agent,
                max_attempts, poll_interval, proxy
            )
        else:
            print(f"❌ Неизвестный сервис: {self.service}")
            return None

    def _solve_2captcha(self, website_url: str, website_key: str,
                       user_agent: Optional[str], is_invisible: bool,
                       enterprise_payload: Optional[Dict],
                       max_attempts: int, poll_interval: int,
                       proxy: Optional[str]) -> Optional[str]:
        """Решение через 2Captcha (рекомендуется для Steam)"""
        try:
            print(f"🔄 Отправка задачи на 2Captcha...")
            print(f"   Website: {website_url}")
            print(f"   Sitekey: {website_key}")

            # Формируем параметры запроса
            params = {
                "key": self.api_key,
                "method": "hcaptcha",
                "sitekey": website_key,
                "pageurl": website_url,
                "json": 1
            }

            # Добавляем опциональные параметры
            # ВАЖНО: userAgent НЕ поддерживается для hcaptcha метода в 2Captcha!
            # Используется только для reCAPTCHA

            if is_invisible:
                params["invisible"] = 1
            if enterprise_payload:
                # 2Captcha поддерживает enterprise через data параметр
                if "rqdata" in enterprise_payload:
                    params["data"] = enterprise_payload["rqdata"]
            if proxy:
                # Формат: login:pass@ip:port
                params["proxy"] = proxy
                params["proxytype"] = "HTTP"

            # Debug: выводим параметры
            if self.debug:
                print(f"\n[DEBUG] Request parameters:")
                for key, value in params.items():
                    if key == "key":
                        print(f"   {key}: {value[:8]}...{value[-4:]}")
                    else:
                        print(f"   {key}: {value}")
                print()

            # Отправляем задачу
            response = requests.post(
                self.API_ENDPOINTS[CaptchaService.TWOCAPTCHA]["create"],
                data=params,
                timeout=30
            )

            # Debug: выводим ответ
            if self.debug:
                print(f"[DEBUG] Response status: {response.status_code}")
                print(f"[DEBUG] Response body: {response.text}")
                print()
            result = response.json()

            if result.get("status") != 1:
                error = result.get("request", "Unknown error")
                print(f"❌ Ошибка создания задачи 2Captcha: {error}")
                return None

            task_id = result.get("request")
            print(f"✓ Задача создана. ID: {task_id}")

            # Ожидаем решения
            print(f"⏳ Ожидание решения (может занять до {max_attempts * poll_interval} сек)...")

            for attempt in range(max_attempts):
                time.sleep(poll_interval)

                # Проверяем результат
                result_params = {
                    "key": self.api_key,
                    "action": "get",
                    "id": task_id,
                    "json": 1
                }

                result_response = requests.get(
                    self.API_ENDPOINTS[CaptchaService.TWOCAPTCHA]["result"],
                    params=result_params,
                    timeout=30
                )
                result_data = result_response.json()

                if result_data.get("status") == 1:
                    captcha_token = result_data.get("request")
                    print(f"✓ Капча решена успешно через 2Captcha!")
                    if self.debug:
                        print(f"   Токен: {captcha_token[:50]}...")
                    return captcha_token
                elif result_data.get("request") == "CAPCHA_NOT_READY":
                    if self.debug:
                        print(f"   Попытка {attempt + 1}/{max_attempts}: обработка...")
                    continue
                else:
                    error = result_data.get("request", "Unknown error")
                    print(f"❌ Ошибка решения: {error}")
                    return None

            print(f"❌ Превышено время ожидания ({max_attempts} попыток)")
            return None

        except Exception as e:
            print(f"❌ Исключение при работе с 2Captcha: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return None

    def _solve_capsolver(self, website_url: str, website_key: str,
                        user_agent: Optional[str], is_invisible: bool,
                        enterprise_payload: Optional[Dict],
                        max_attempts: int, poll_interval: int,
                        proxy: Optional[str]) -> Optional[str]:
        """Решение через CapSolver (специализируется на сложных капчах)"""
        try:
            print(f"🔄 Отправка задачи на CapSolver...")
            print(f"   Website: {website_url}")
            print(f"   Sitekey: {website_key}")

            # Формируем задачу
            task_data = {
                "type": "HCaptchaTaskProxyLess" if not proxy else "HCaptchaTask",
                "websiteURL": website_url,
                "websiteKey": website_key
            }

            # Добавляем опциональные параметры
            if user_agent:
                task_data["userAgent"] = user_agent
            if is_invisible:
                task_data["isInvisible"] = True
            if enterprise_payload:
                task_data["enterprisePayload"] = enterprise_payload
            if proxy:
                # CapSolver использует другой формат прокси
                task_data["proxy"] = proxy

            payload = {
                "clientKey": self.api_key,
                "task": task_data
            }

            # Создаём задачу
            response = requests.post(
                self.API_ENDPOINTS[CaptchaService.CAPSOLVER]["create"],
                json=payload,
                timeout=30
            )
            result = response.json()

            if result.get("errorId") != 0:
                error = result.get("errorDescription", "Unknown error")
                print(f"❌ Ошибка создания задачи CapSolver: {error}")
                return None

            task_id = result.get("taskId")
            print(f"✓ Задача создана. ID: {task_id}")

            # Ожидаем решения
            print(f"⏳ Ожидание решения...")

            for attempt in range(max_attempts):
                time.sleep(poll_interval)

                # Проверяем результат
                result_payload = {
                    "clientKey": self.api_key,
                    "taskId": task_id
                }

                result_response = requests.post(
                    self.API_ENDPOINTS[CaptchaService.CAPSOLVER]["result"],
                    json=result_payload,
                    timeout=30
                )
                result_data = result_response.json()

                if result_data.get("errorId") != 0:
                    error = result_data.get("errorDescription", "Unknown error")
                    print(f"❌ Ошибка получения результата: {error}")
                    return None

                status = result_data.get("status")

                if status == "ready":
                    solution = result_data.get("solution", {})
                    captcha_token = solution.get("gRecaptchaResponse")
                    print(f"✓ Капча решена успешно через CapSolver!")
                    if self.debug:
                        print(f"   Токен: {captcha_token[:50]}...")
                    return captcha_token
                elif status == "processing":
                    if self.debug:
                        print(f"   Попытка {attempt + 1}/{max_attempts}: обработка...")
                    continue
                else:
                    print(f"❌ Неизвестный статус: {status}")
                    return None

            print(f"❌ Превышено время ожидания")
            return None

        except Exception as e:
            print(f"❌ Исключение при работе с CapSolver: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return None

    def _solve_anticaptcha(self, website_url: str, website_key: str,
                          user_agent: Optional[str], is_invisible: bool,
                          enterprise_payload: Optional[Dict],
                          max_attempts: int, poll_interval: int,
                          proxy: Optional[str]) -> Optional[str]:
        """Решение через AntiCaptcha"""
        try:
            print(f"🔄 Отправка задачи на AntiCaptcha...")

            # AntiCaptcha использует такой же API как CapSolver
            task_data = {
                "type": "HCaptchaTaskProxyless" if not proxy else "HCaptchaTask",
                "websiteURL": website_url,
                "websiteKey": website_key
            }

            if user_agent:
                task_data["userAgent"] = user_agent
            if is_invisible:
                task_data["isInvisible"] = True
            if enterprise_payload:
                task_data["enterprisePayload"] = enterprise_payload
            if proxy:
                task_data["proxyAddress"] = proxy.split("@")[-1].split(":")[0]
                task_data["proxyPort"] = int(proxy.split(":")[-1])
                if "@" in proxy:
                    login_pass = proxy.split("@")[0]
                    task_data["proxyLogin"] = login_pass.split(":")[0]
                    task_data["proxyPassword"] = login_pass.split(":")[1]
                task_data["proxyType"] = "http"

            payload = {
                "clientKey": self.api_key,
                "task": task_data
            }

            # Создаём задачу
            response = requests.post(
                self.API_ENDPOINTS[CaptchaService.ANTICAPTCHA]["create"],
                json=payload,
                timeout=30
            )
            result = response.json()

            if result.get("errorId") != 0:
                error = result.get("errorDescription", "Unknown error")
                print(f"❌ Ошибка AntiCaptcha: {error}")
                return None

            task_id = result.get("taskId")
            print(f"✓ Задача создана. ID: {task_id}")

            # Ожидаем решения (аналогично CapSolver)
            for attempt in range(max_attempts):
                time.sleep(poll_interval)

                result_payload = {
                    "clientKey": self.api_key,
                    "taskId": task_id
                }

                result_response = requests.post(
                    self.API_ENDPOINTS[CaptchaService.ANTICAPTCHA]["result"],
                    json=result_payload,
                    timeout=30
                )
                result_data = result_response.json()

                if result_data.get("status") == "ready":
                    solution = result_data.get("solution", {})
                    captcha_token = solution.get("gRecaptchaResponse")
                    print(f"✓ Капча решена через AntiCaptcha!")
                    return captcha_token
                elif result_data.get("status") == "processing":
                    continue

            return None

        except Exception as e:
            print(f"❌ Исключение при работе с AntiCaptcha: {e}")
            return None

    def _solve_yescaptcha(self, website_url: str, website_key: str,
                         user_agent: Optional[str], is_invisible: bool,
                         enterprise_payload: Optional[Dict],
                         max_attempts: int, poll_interval: int) -> Optional[str]:
        """Решение через YesCaptcha (fallback)"""
        try:
            from src.captcha.yescaptcha_solver import YesCaptchaSolver

            solver = YesCaptchaSolver(
                client_key=self.api_key,
                debug=self.debug
            )

            return solver.solve_hcaptcha(
                website_url=website_url,
                website_key=website_key,
                user_agent=user_agent,
                is_invisible=is_invisible,
                enterprise_payload=enterprise_payload,
                max_attempts=max_attempts,
                poll_interval=poll_interval
            )

        except Exception as e:
            print(f"❌ Ошибка YesCaptcha: {e}")
            return None

    def _solve_azcaptcha(self, website_url: str, website_key: str,
                        user_agent: Optional[str],
                        max_attempts: int, poll_interval: int,
                        proxy: Optional[str]) -> Optional[str]:
        """Решение через AZcaptcha (дешёвый сервис - $1/1000 капч)"""
        try:
            from src.captcha.azcaptcha_solver import AZcaptchaSolver

            solver = AZcaptchaSolver(
                api_key=self.api_key,
                debug=self.debug
            )

            return solver.solve_hcaptcha(
                website_url=website_url,
                website_key=website_key,
                user_agent=user_agent,
                proxy=proxy,
                proxy_type="HTTP",
                max_attempts=max_attempts,
                poll_interval=poll_interval
            )

        except Exception as e:
            print(f"❌ Ошибка AZcaptcha: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return None


def load_captcha_config(config_file: str = "captcha_config.txt") -> Dict[str, str]:
    """
    Загружает конфигурацию сервиса капчи из файла

    Формат файла:
    service=2captcha
    api_key=ваш_api_ключ

    :param config_file: Путь к файлу конфигурации
    :return: Словарь с настройками
    """
    import os

    config = {
        "service": "2captcha",  # По умолчанию
        "api_key": ""
    }

    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        except Exception as e:
            print(f"⚠️ Ошибка чтения конфига {config_file}: {e}")

    # Проверяем переменные окружения
    if not config["api_key"]:
        service = config["service"].upper()
        env_var = f"{service}_API_KEY"
        config["api_key"] = os.getenv(env_var, "")

    return config
