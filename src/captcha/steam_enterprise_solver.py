#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam reCAPTCHA v2 Enterprise Solver
Модуль для решения Enterprise капчи при регистрации Steam с поддержкой нескольких сервисов
"""

import os
import re
import time
import json
import requests
from typing import Optional, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class SteamEnterpriseCaptchaSolver:
    """Решатель Steam reCAPTCHA v2 Enterprise через различные сервисы"""

    # Константы Steam
    STEAM_SITEKEY = "6LdIFr0ZAAAAAO3vz0O0OQrtAefzdJcWQM2TMYQH"

    # Поддерживаемые сервисы
    SUPPORTED_SERVICES = ["capsolver", "2captcha", "anticaptcha"]

    def __init__(self, service: str = "capsolver", api_key: Optional[str] = None, debug: bool = True):
        """
        Инициализация решателя капчи

        Args:
            service: Имя сервиса ('capsolver', '2captcha', 'anticaptcha')
            api_key: API ключ сервиса (если None, берется из переменных окружения)
            debug: Включить подробное логирование
        """
        self.service = service.lower()
        self.debug = debug

        if self.service not in self.SUPPORTED_SERVICES:
            raise ValueError(f"Неподдерживаемый сервис: {service}. Доступны: {self.SUPPORTED_SERVICES}")

        # Получаем API ключ
        self.api_key = api_key or self._get_api_key_from_env()

        if not self.api_key or len(self.api_key) < 30:
            raise ValueError(f"Не указан API ключ для {self.service}")

        self._log(f"Инициализирован {self.service} solver")

    def _get_api_key_from_env(self) -> Optional[str]:
        """Получает API ключ из переменных окружения или конфигурационных файлов"""
        if self.service == "capsolver":
            # Пробуем переменную окружения
            key = os.getenv("CAPSOLVER_API_KEY")
            if key:
                return key
            # Пробуем файл конфигурации
            try:
                with open("capsolver_config.txt", "r", encoding="utf-8") as f:
                    return f.read().strip()
            except FileNotFoundError:
                pass

        elif self.service == "2captcha":
            key = os.getenv("TWOCAPTCHA_API_KEY")
            if key:
                return key
            try:
                with open("2captcha_config.txt", "r", encoding="utf-8") as f:
                    return f.read().strip()
            except FileNotFoundError:
                pass

        elif self.service == "anticaptcha":
            key = os.getenv("ANTICAPTCHA_API_KEY")
            if key:
                return key
            try:
                with open("anticaptcha_config.txt", "r", encoding="utf-8") as f:
                    return f.read().strip()
            except FileNotFoundError:
                pass

        return None

    def _log(self, message: str):
        """Логирование сообщений"""
        if self.debug:
            print(f"[SteamCaptcha] {message}")

    def wake_up_captcha(self, driver, wait_time: int = 40) -> bool:
        """
        "Разбуживает" капчу на странице Steam, эмулируя взаимодействие пользователя

        Args:
            driver: WebDriver экземпляр
            wait_time: Максимальное время ожидания загрузки страницы

        Returns:
            True если капча успешно активирована, False в противном случае
        """
        try:
            self._log("Разбуживаем капчу через взаимодействие с формой...")

            wait = WebDriverWait(driver, wait_time)

            # Ждём появления поля email
            email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
            self._log("Поле email найдено")

            # Прокручиваем к полю и центрируем его
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", email_field)
            time.sleep(1.5)

            # Кликаем через JavaScript (избегаем событий мыши Selenium)
            driver.execute_script("arguments[0].click();", email_field)
            self._log("Клик по полю email выполнен")

            # Вводим и удаляем символ (эмулируем реальное взаимодействие)
            email_field.send_keys("a")
            driver.execute_script("arguments[0].value = arguments[0].value.slice(0,-1);", email_field)

            # Даём время капче инициализироваться
            self._log("Ожидаем инициализацию капчи (3 сек)...")
            time.sleep(3)

            self._log("Капча успешно разбужена")
            return True

        except Exception as e:
            self._log(f"Ошибка при разбуживании капчи: {e}")
            return False

    def extract_captcha_data(self, driver, max_wait: int = 25) -> Optional[Dict[str, Any]]:
        """
        Извлекает данные капчи со страницы (sitekey, s-token, page_url)

        Args:
            driver: WebDriver экземпляр
            max_wait: Максимальное время ожидания появления iframe (секунды)

        Returns:
            Словарь с данными капчи или None при ошибке
        """
        try:
            self._log("Ищем iframe с капчей...")

            # Ждём появления iframe с капчей
            iframe = None
            for attempt in range(max_wait):
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for ifr in iframes:
                    src = ifr.get_attribute("src") or ""
                    if "recaptcha" in src.lower():
                        iframe = ifr
                        break

                if iframe:
                    self._log(f"Iframe найден на попытке {attempt + 1}")
                    break

                time.sleep(1)

            if not iframe:
                self._log("ОШИБКА: Iframe с капчей не найден")
                return None

            # Извлекаем s-token
            s_token = driver.execute_script(
                "return document.querySelector('div.g-recaptcha')?.dataset.s || null;"
            )

            # Если не нашли в dataset, парсим из URL iframe
            if not s_token:
                self._log("s-token не найден в dataset, парсим из URL iframe...")
                src = iframe.get_attribute("src")
                match = re.search(r"s=([a-zA-Z0-9_-]+)", src)
                s_token = match.group(1) if match else "NO_S"

            if s_token and s_token != "NO_S":
                self._log(f"s-token извлечен: {s_token[:60]}...")
            else:
                self._log("ВНИМАНИЕ: s-token не найден, капча может не решиться")

            captcha_data = {
                "page_url": driver.current_url,
                "sitekey": self.STEAM_SITEKEY,
                "s_token": s_token,
                "user_agent": driver.execute_script("return navigator.userAgent")
            }

            self._log(f"Данные капчи извлечены:")
            self._log(f"  • URL: {captcha_data['page_url']}")
            self._log(f"  • Sitekey: {captcha_data['sitekey']}")
            self._log(f"  • s-token: {'✓' if s_token and s_token != 'NO_S' else '✗'}")

            return captcha_data

        except Exception as e:
            self._log(f"Ошибка при извлечении данных капчи: {e}")
            return None

    def solve_captcha(self, captcha_data: Dict[str, Any], timeout: int = 300) -> Optional[str]:
        """
        Решает капчу через выбранный сервис

        Args:
            captcha_data: Данные капчи (из extract_captcha_data)
            timeout: Максимальное время ожидания решения (секунды)

        Returns:
            Токен g-recaptcha-response или None при ошибке
        """
        if self.service == "capsolver":
            return self._solve_with_capsolver(captcha_data, timeout)
        elif self.service == "2captcha":
            return self._solve_with_2captcha(captcha_data, timeout)
        elif self.service == "anticaptcha":
            return self._solve_with_anticaptcha(captcha_data, timeout)
        else:
            self._log(f"ОШИБКА: Неизвестный сервис {self.service}")
            return None

    def _solve_with_capsolver(self, data: Dict[str, Any], timeout: int) -> Optional[str]:
        """Решает капчу через CapSolver API"""
        self._log("Отправляем задачу в CapSolver...")

        try:
            payload = {
                "clientKey": self.api_key,
                "task": {
                    "type": "ReCaptchaV2EnterpriseTaskProxyless",
                    "websiteURL": data["page_url"],
                    "websiteKey": data["sitekey"],
                    "enterprisePayload": {
                        "s": data["s_token"]
                    }
                }
            }

            # Создаём задачу
            response = requests.post(
                "https://api.capsolver.com/createTask",
                json=payload,
                timeout=30
            )
            result = response.json()

            if result.get("errorId") != 0:
                self._log(f"Ошибка создания задачи: {result}")
                return None

            task_id = result["taskId"]
            self._log(f"Task ID: {task_id}")

            # Ждём решения
            start_time = time.time()
            while time.time() - start_time < timeout:
                time.sleep(5)

                resp = requests.post(
                    "https://api.capsolver.com/getTaskResult",
                    json={
                        "clientKey": self.api_key,
                        "taskId": task_id
                    },
                    timeout=30
                )

                res = resp.json()

                if res.get("status") == "ready":
                    token = res["solution"]["gRecaptchaResponse"]
                    self._log(f"✓ Капча решена! Токен получен ({len(token)} символов)")
                    return token
                elif res.get("status") == "failed":
                    self._log("✗ Капча не решена сервисом (status: failed)")
                    return None

                elapsed = int(time.time() - start_time)
                self._log(f"Ожидание... {elapsed} сек")

            self._log(f"✗ Таймаут {timeout} сек истёк")
            return None

        except Exception as e:
            self._log(f"Исключение при решении через CapSolver: {e}")
            return None

    def _solve_with_2captcha(self, data: Dict[str, Any], timeout: int) -> Optional[str]:
        """Решает капчу через 2Captcha API"""
        self._log("Отправляем задачу в 2Captcha...")

        try:
            # Создаём задачу
            create_params = {
                "key": self.api_key,
                "method": "userrecaptcha",
                "googlekey": data["sitekey"],
                "pageurl": data["page_url"],
                "enterprise": 1,
                "json": 1
            }

            # Добавляем s-token если есть
            if data.get("s_token") and data["s_token"] != "NO_S":
                create_params["data-s"] = data["s_token"]

            response = requests.post(
                "https://2captcha.com/in.php",
                data=create_params,
                timeout=30
            )
            result = response.json()

            if result.get("status") != 1:
                self._log(f"Ошибка создания задачи: {result}")
                return None

            task_id = result["request"]
            self._log(f"Task ID: {task_id}")

            # Ждём решения
            start_time = time.time()
            while time.time() - start_time < timeout:
                time.sleep(5)

                resp = requests.get(
                    "https://2captcha.com/res.php",
                    params={
                        "key": self.api_key,
                        "action": "get",
                        "id": task_id,
                        "json": 1
                    },
                    timeout=30
                )

                res = resp.json()

                if res.get("status") == 1:
                    token = res["request"]
                    self._log(f"✓ Капча решена! Токен получен ({len(token)} символов)")
                    return token
                elif res.get("request") == "CAPCHA_NOT_READY":
                    elapsed = int(time.time() - start_time)
                    self._log(f"Ожидание... {elapsed} сек")
                    continue
                else:
                    self._log(f"✗ Ошибка от 2Captcha: {res}")
                    return None

            self._log(f"✗ Таймаут {timeout} сек истёк")
            return None

        except Exception as e:
            self._log(f"Исключение при решении через 2Captcha: {e}")
            return None

    def _solve_with_anticaptcha(self, data: Dict[str, Any], timeout: int) -> Optional[str]:
        """Решает капчу через AntiCaptcha API"""
        self._log("Отправляем задачу в AntiCaptcha...")

        try:
            payload = {
                "clientKey": self.api_key,
                "task": {
                    "type": "RecaptchaV2EnterpriseTaskProxyless",
                    "websiteURL": data["page_url"],
                    "websiteKey": data["sitekey"],
                    "enterprisePayload": {
                        "s": data["s_token"]
                    }
                }
            }

            # Создаём задачу
            response = requests.post(
                "https://api.anti-captcha.com/createTask",
                json=payload,
                timeout=30
            )
            result = response.json()

            if result.get("errorId") != 0:
                self._log(f"Ошибка создания задачи: {result}")
                return None

            task_id = result["taskId"]
            self._log(f"Task ID: {task_id}")

            # Ждём решения
            start_time = time.time()
            while time.time() - start_time < timeout:
                time.sleep(5)

                resp = requests.post(
                    "https://api.anti-captcha.com/getTaskResult",
                    json={
                        "clientKey": self.api_key,
                        "taskId": task_id
                    },
                    timeout=30
                )

                res = resp.json()

                if res.get("status") == "ready":
                    token = res["solution"]["gRecaptchaResponse"]
                    self._log(f"✓ Капча решена! Токен получен ({len(token)} символов)")
                    return token
                elif res.get("status") == "failed":
                    self._log("✗ Капча не решена сервисом (status: failed)")
                    return None

                elapsed = int(time.time() - start_time)
                self._log(f"Ожидание... {elapsed} сек")

            self._log(f"✗ Таймаут {timeout} сек истёк")
            return None

        except Exception as e:
            self._log(f"Исключение при решении через AntiCaptcha: {e}")
            return None

    def inject_captcha_token(self, driver, token: str) -> bool:
        """
        Инжектирует токен капчи в форму

        Args:
            driver: WebDriver экземпляр
            token: Токен g-recaptcha-response

        Returns:
            True если инжекция успешна, False в противном случае
        """
        try:
            self._log("Инжектируем токен в форму...")

            # Находим или создаём поле g-recaptcha-response
            script = f"""
            var responseField = document.getElementById('g-recaptcha-response');
            if (!responseField) {{
                responseField = document.createElement('textarea');
                responseField.id = 'g-recaptcha-response';
                responseField.name = 'g-recaptcha-response';
                responseField.style.display = 'none';
                document.querySelector('form').appendChild(responseField);
            }}
            responseField.value = '{token}';

            // Также пробуем установить в возможные скрытые поля
            var hiddenFields = document.querySelectorAll('[name="g-recaptcha-response"]');
            hiddenFields.forEach(function(field) {{
                field.value = '{token}';
            }});

            return true;
            """

            result = driver.execute_script(script)

            if result:
                self._log("✓ Токен успешно инжектирован")
                return True
            else:
                self._log("✗ Не удалось инжектировать токен")
                return False

        except Exception as e:
            self._log(f"Ошибка при инжекции токена: {e}")
            return False

    def solve_and_inject(self, driver) -> bool:
        """
        Полный цикл: разбуживание капчи, извлечение данных, решение и инжекция токена

        Args:
            driver: WebDriver экземпляр

        Returns:
            True если весь процесс успешен, False в противном случае
        """
        self._log("=" * 60)
        self._log("Начинаем полный цикл решения Steam Enterprise reCAPTCHA")
        self._log("=" * 60)

        # Шаг 1: Разбуживаем капчу
        if not self.wake_up_captcha(driver):
            self._log("✗ Не удалось разбудить капчу")
            return False

        # Шаг 2: Извлекаем данные капчи
        captcha_data = self.extract_captcha_data(driver)
        if not captcha_data:
            self._log("✗ Не удалось извлечь данные капчи")
            return False

        # Шаг 3: Решаем капчу
        token = self.solve_captcha(captcha_data)
        if not token:
            self._log("✗ Не удалось решить капчу")
            return False

        # Шаг 4: Инжектируем токен
        if not self.inject_captcha_token(driver, token):
            self._log("✗ Не удалось инжектировать токен")
            return False

        self._log("=" * 60)
        self._log("✓ Капча успешно решена и токен инжектирован!")
        self._log("=" * 60)
        return True


# Пример использования
if __name__ == "__main__":
    print("Этот модуль предназначен для импорта в другие скрипты")
    print("\nПример использования:")
    print("""
from src.captcha.steam_enterprise_solver import SteamEnterpriseCaptchaSolver

# Создаём solver (по умолчанию CapSolver)
solver = SteamEnterpriseCaptchaSolver(service='capsolver')

# В вашем коде с Selenium WebDriver:
success = solver.solve_and_inject(driver)
if success:
    # Теперь можно отправлять форму регистрации
    submit_button.click()
""")
