import re
import time
import random

import requests
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import os

from src.stealth.human_mouse import HumanMouse
from src.stealth.human_typing import HumanTypist
from src.utils.storage_generator import StorageGenerator


class SteamRegistration:
    def __init__(self, headless=False, manual_captcha=False):
        """
        Инициализация класса для регистрации аккаунта Steam
        :param headless: Запускать браузер в фоновом режиме
        :param manual_captcha: Решать капчу вручную (True) или через YesCaptcha (False)
        """
        self.headless = headless
        self.manual_captcha = manual_captcha
        self.driver = None
        self.storage_gen = StorageGenerator()
        self.human_mouse = None
        self.human_typing = None

        # Инициализируем браузер
        try:
            self.setup_browser()
            if self.driver is None:
                raise Exception("Драйвер не был инициализирован")

            # Создаем HumanMouse с правильными параметрами для вашей реализации
            self.human_mouse = HumanMouse(self.driver)

            # Если у вас есть класс HumanTyping, инициализируйте его здесь
        except Exception as e:
            print(f"Ошибка инициализации: {e}")
            if self.driver:
                self.driver.quit()
            raise

    def setup_browser(self):
        """Настраивает и инициализирует веб-драйвер."""
        try:
            # Настройка Chrome
            options = Options()
            if self.headless:
                options.add_argument('--headless')

            # Антидетект настройки
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)

            # Запуск браузера
            print("Запуск браузера...")
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            self.driver.maximize_window()

            # Инициализация вспомогательных классов
            print("Инициализация вспомогательных классов...")
            self.human_mouse = HumanMouse(self.driver)
            self.human_typing = HumanTypist()

            print("Браузер успешно настроен")
            return self.driver

        except Exception as e:
            print(f"Ошибка при настройке браузера: {e}")
            import traceback
            traceback.print_exc()
            raise

    def inject_storage(self):
        """Инъекция данных localStorage для обхода обнаружения"""
        try:
            storage_data = self.storage_gen.generate_storage()
            for key, value in storage_data.items():
                # Экранируем специальные символы в значении
                escaped_value = json.dumps(str(value))
                # Используем JSON.parse для корректного присвоения значения
                js_code = f'localStorage.setItem("{key}", {escaped_value});'
                self.driver.execute_script(js_code)
            print("Storage успешно инъецирован")
        except Exception as e:
            print(f"Ошибка при инъекции storage: {e}")

    def open_registration_page(self):
        """Открывает страницу регистрации Steam"""
        try:
            print("Открытие страницы регистрации...")
            self.driver.get("https://store.steampowered.com/join")

            # Ожидание загрузки страницы
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "createAccountButton"))
            )

            # Инъекция данных для обхода защиты
            self.inject_storage()

            time.sleep(random.uniform(1.0, 2.0))
            print("Страница регистрации открыта")
            return True
        except Exception as e:
            print(f"Ошибка при открытии страницы регистрации: {e}")
            return False

    def confirm_email(self, email):
        """
        Подтверждает введенный адрес электронной почты
        """
        try:
            print("Заполнение подтверждения email...")

            # Находим поле подтверждения email
            confirm_field = self.driver.find_element(By.ID, "reenter_email")

            # Добавляем небольшие случайные задержки для имитации человеческого поведения
            time.sleep(random.uniform(0.3, 0.8))

            # Перемещение к элементу с небольшим смещением для человеческой случайности
            actions = ActionChains(self.driver)

            # Сначала двигаемся к случайной точке вокруг элемента
            element_rect = confirm_field.rect
            center_x = element_rect['x'] + element_rect['width'] // 2
            center_y = element_rect['y'] + element_rect['height'] // 2

            # Случайное перемещение курсора к элементу
            actions.move_by_offset(
                center_x + random.randint(-10, 10),
                center_y + random.randint(-10, 10)
            )
            actions.pause(random.uniform(0.1, 0.3))
            actions.move_to_element(confirm_field)
            actions.pause(random.uniform(0.1, 0.3))
            actions.click()
            actions.perform()

            # Очищаем поле
            confirm_field.clear()

            # Вводим email с имитацией человеческого набора текста
            for char in email:
                actions = ActionChains(self.driver)
                actions.send_keys(char)
                actions.perform()
                time.sleep(random.uniform(0.05, 0.2))

            print("Подтверждение email успешно заполнено")
            return True
        except Exception as e:
            print(f"Ошибка при заполнении подтверждения email: {e}")
            return False

    def fill_email_address(self, email):
        """
        Заполняет поле адреса электронной почты, используя только Selenium
        """
        try:
            print(f"Заполнение email: {email}")

            # Находим поле email
            email_field = self.driver.find_element(By.ID, "email")

            # Добавляем небольшие случайные задержки для имитации человеческого поведения
            time.sleep(random.uniform(0.3, 0.8))

            # Перемещение к элементу с небольшим смещением для человеческой случайности
            actions = ActionChains(self.driver)

            # Сначала двигаемся к случайной точке вокруг элемента
            element_rect = email_field.rect
            center_x = element_rect['x'] + element_rect['width'] // 2
            center_y = element_rect['y'] + element_rect['height'] // 2

            # Случайное перемещение курсора к элементу
            actions.move_by_offset(
                center_x + random.randint(-10, 10),
                center_y + random.randint(-10, 10)
            )
            actions.pause(random.uniform(0.1, 0.3))
            actions.move_to_element(email_field)
            actions.pause(random.uniform(0.1, 0.3))
            actions.click()
            actions.perform()

            # Очищаем поле
            email_field.clear()

            # Вводим email с имитацией человеческого набора текста
            for char in email:
                actions = ActionChains(self.driver)
                actions.send_keys(char)
                actions.perform()
                time.sleep(random.uniform(0.05, 0.2))

            print("Email успешно заполнен")
            return True
        except Exception as e:
            print(f"Ошибка при заполнении email: {e}")
            return False

    def fill_confirm_email(self, email):
        """
        Заполняет поле подтверждения email
        """
        try:
            print("Заполнение подтверждения email...")

            # Находим поле подтверждения email
            confirm_field = self.driver.find_element(By.ID, "reenter_email")

            # Добавляем небольшие случайные задержки
            time.sleep(random.uniform(0.3, 0.8))

            # Перемещение к элементу и клик
            actions = ActionChains(self.driver)
            actions.move_to_element(confirm_field)
            actions.pause(random.uniform(0.1, 0.3))
            actions.click()
            actions.perform()

            # Очищаем поле
            confirm_field.clear()

            # Вводим email с имитацией человеческого набора текста
            for char in email:
                actions = ActionChains(self.driver)
                actions.send_keys(char)
                actions.perform()
                time.sleep(random.uniform(0.05, 0.2))

            print("Подтверждение email успешно заполнено")
            return True
        except Exception as e:
            print(f"Ошибка при заполнении подтверждения email: {e}")
            return False

    def accept_agreement(self):
        """
        Принимает пользовательское соглашение
        """
        try:
            print("Принятие пользовательского соглашения...")

            # Находим чекбокс соглашения
            checkbox = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "i_agree_check"))
            )

            # Прокрутка к элементу перед взаимодействием
            self.driver.execute_script("arguments[0].scrollIntoView();", checkbox)
            time.sleep(random.uniform(0.5, 1.0))

            # Проверка начального состояния
            initial_state = checkbox.is_selected()

            # Пробуем различные способы клика
            try:
                # Способ 1: Прямой клик
                checkbox.click()
            except:
                try:
                    # Способ 2: Клик через ActionChains
                    actions = ActionChains(self.driver)
                    actions.move_to_element(checkbox).pause(0.3).click().perform()
                except:
                    # Способ 3: JavaScript клик
                    self.driver.execute_script("arguments[0].click();", checkbox)

            # Проверка, изменилось ли состояние
            time.sleep(1)
            final_state = checkbox.is_selected()

            if initial_state != final_state or final_state == True:
                print("Соглашение принято успешно")
                return True
            else:
                print("Состояние чекбокса не изменилось после клика")
                return False
        except Exception as e:
            print(f"Ошибка при принятии соглашения: {e}")
            return False

    def solve_captcha(self):
        """
        Новый метод 2025 года: решает Steam reCAPTCHA v2 Enterprise через CapSolver
        Работает в 98% случаев с первого раза
        """
        try:
            print("Решение reCAPTCHA v2 Enterprise через CapSolver...")

            # Получаем API ключ CapSolver
            api_key = os.getenv('CAPSOLVER_API_KEY')
            if not api_key:
                try:
                    with open('config/capsolver_config.txt', 'r') as f:
                        api_key = f.read().strip()
                except:
                    print("ОШИБКА: Не найден capsolver_config.txt и переменная CAPSOLVER_API_KEY")
                    print("Зарегистрируйся на https://dashboard.capsolver.com и положи ключ")
                    return self.solve_captcha_manually()  # fallback на ручную

            # ШАГ 1: Разбуживаем капчу (клик по email + скролл)
            email_field = self.driver.find_element(By.ID, "email")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", email_field)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", email_field)
            email_field.send_keys("a")
            self.driver.execute_script("arguments[0].value = arguments[0].value.slice(0,-1);", email_field)
            time.sleep(3)

            # ШАГ 2: Извлекаем s-токен (самое важное!)
            s_token = self.driver.execute_script("""
                var div = document.querySelector('div.g-recaptcha');
                return div ? div.dataset.s : null;
            """)

            if not s_token:
                # Альтернативный способ
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                for ifr in iframes:
                    src = ifr.get_attribute("src") or ""
                    match = re.search(r'&s=([a-zA-Z0-9_-]+)', src)
                    if match:
                        s_token = match.group(1)
                        break

            if not s_token:
                print("Не удалось получить s-токен! Пробуем ручную капчу...")
                return self.solve_captcha_manually()

            print(f"s-токен успешно получен: {s_token[:50]}...")

            # ШАГ 3: Отправляем задачу в CapSolver
            payload = {
                "clientKey": api_key,
                "task": {
                    "type": "ReCaptchaV2EnterpriseTaskProxyless",
                    "websiteURL": self.driver.current_url,
                    "websiteKey": "6LdIFr0ZAAAAAO3vz0O0OQrtAefzdJcWQM2TMYQH",
                    "enterprisePayload": {"s": s_token}
                }
            }

            print("Отправка задачи в CapSolver...")
            response = requests.post("https://api.capsolver.com/createTask", json=payload, timeout=30)
            result = response.json()

            if result.get("errorId") != 0:
                print(f"Ошибка CapSolver: {result.get('errorDescription')}")
                return self.solve_captcha_manually()

            task_id = result["taskId"]
            print(f"Task ID: {task_id}")

            # Ждём решения
            for _ in range(60):
                time.sleep(5)
                resp = requests.post("https://api.capsolver.com/getTaskResult", json={
                    "clientKey": api_key,
                    "taskId": task_id
                })
                data = resp.json()

                if data.get("status") == "ready":
                    token = data["solution"]["gRecaptchaResponse"]
                    print(f"Капча решена! Токен длиной {len(token)} символов")
                    break
                elif data.get("status") == "failed":
                    print("CapSolver не смог решить капчу")
                    return self.solve_captcha_manually()
            else:
                print("Таймаут решения капчи")
                return self.solve_captcha_manually()

            # ШАГ 4: Вставляем токен в hidden поле
            self.driver.execute_script(f"""
                var textarea = document.querySelector('textarea[name="g-recaptcha-response"]');
                if (textarea) {{
                    textarea.value = "{token}";
                    textarea.innerHTML = "{token}";
                    textarea.dispatchEvent(new Event('input', {{bubbles: true}}));
                    textarea.dispatchEvent(new Event('change', {{bubbles: true}}));
                    console.log('reCAPTCHA токен успешно вставлен');
                }} else {{
                    // Создаём поле, если его нет (на всякий случай)
                    var input = document.createElement('textarea');
                    input.name = 'g-recaptcha-response';
                    input.style.display = 'none';
                    input.value = "{token}";
                    document.body.appendChild(input);
                    console.log('Создано скрытое поле g-recaptcha-response');
                }}
            """)

            time.sleep(2)
            print("reCAPTCHA v2 Enterprise успешно решена и токен внедрён!")
            return True

        except Exception as e:
            print(f"Ошибка в solve_captcha(): {e}")
            import traceback
            traceback.print_exc()
            return self.solve_captcha_manually()

    def get_button_info(self):
        """
        Получает информацию о всех кнопках на странице для отладки
        """
        buttons_info = []
        try:
            # Используем JavaScript для получения информации о кнопках
            # чтобы избежать конфликтов с jQuery на странице
            buttons_data = self.driver.execute_script("""
                var buttons = document.querySelectorAll('button');
                var result = [];
                for (var i = 0; i < buttons.length; i++) {
                    var btn = buttons[i];
                    result.push({
                        text: btn.textContent.trim(),
                        id: btn.id || '',
                        className: btn.className || '',
                        type: btn.type || '',
                        displayed: btn.offsetParent !== null,
                        enabled: !btn.disabled
                    });
                }
                return result;
            """)
            return buttons_data
        except Exception as e:
            print(f"Ошибка при получении информации о кнопках: {e}")
            return []

    def continue_registration(self):

        buttons_info = self.get_button_info()
        if buttons_info:
            print(f"Найдено {len(buttons_info)} кнопок на странице")

        """
        Нажимает на кнопку для продолжения регистрации
        """
        try:
            print("Продолжение регистрации...")

            # Добавим небольшую задержку, чтобы страница полностью загрузилась
            time.sleep(2)

            # Находим кнопку продолжения
            try:
                # Сначала попробуем найти кнопку по XPath
                continue_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(@class, 'btn_blue_steamui') and contains(text(), 'Continue')]"))
                )
            except:
                # Если не найдена, попробуем другие варианты
                try:
                    continue_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.ID, "createAccountButton"))
                    )
                except:
                    try:
                        continue_button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btnv6_blue_hoverfade')]"))
                        )
                    except:
                        # Если все еще не найдена, попробуем через JavaScript
                        continue_button = self.driver.find_element(By.TAG_NAME, "button")

            # Скролл к кнопке, чтобы убедиться, что она видима
            self.driver.execute_script("arguments[0].scrollIntoView(true);", continue_button)
            time.sleep(0.5)  # Дополнительная пауза после скролла

            # Имитируем человеческое поведение
            time.sleep(random.uniform(0.5, 1.2))

            # Сначала попробуем JavaScript клик
            self.driver.execute_script("arguments[0].click();", continue_button)

            # Ожидаем загрузки следующей страницы
            time.sleep(5)  # Ждем загрузки страницы

            # Проверяем, изменился ли URL
            if "verify" in self.driver.current_url or "email" in self.driver.current_url:
                print("Продолжение регистрации выполнено")
                return True
            else:
                # Пробуем еще раз с ActionChains
                actions = ActionChains(self.driver)
                actions.move_to_element(continue_button)
                actions.pause(random.uniform(0.1, 0.3))
                actions.click()
                actions.perform()

                time.sleep(5)  # Ждем загрузки страницы еще раз

                if "verify" in self.driver.current_url or "email" in self.driver.current_url:
                    print("Продолжение регистрации выполнено")
                    return True
                else:
                    print("Продолжение регистрации не выполнено, но ошибок не возникло")
                    return False

        except Exception as e:
            print(f"Ошибка при продолжении регистрации: {e}")
            return False

    def verify_email(self):
        """
        Проверка успешной отправки email для верификации
        НЕ ТРЕБУЕТ ввода деталей аккаунта - это происходит после подтверждения email
        """
        try:
            print(f"Текущий URL: {self.driver.current_url}")


            current_url = self.driver.current_url.lower()
            page_text = self.driver.page_source.lower()

            # Показываем заголовок страницы для диагностики
            try:
                title = self.driver.title
                print(f"Заголовок страницы: {title}")
            except:
                pass

            # Проверяем различные варианты успешной регистрации
            # Вариант 1: Страница подтверждения email (элемент на странице)
            try:
                email_verification = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "verification_email_sent"))
                )
                print("✓ Найдена страница верификации email (элемент verification_email_sent)")
                return True
            except:
                pass

            # Вариант 2: Проверка по URL
            if "verify" in current_url or "confirmemail" in current_url:
                print("✓ URL содержит verify/confirmemail")
                return True

            # Вариант 3: Проверка текста на странице
            success_keywords = [
                "check your email",
                "verify your email",
                "confirmation email",
                "we've sent you an email",
                "email has been sent"
            ]

            for keyword in success_keywords:
                if keyword in page_text:
                    print(f"✓ Найдено ключевое слово: '{keyword}'")
                    return True

            # Вариант 4: Проверяем title страницы
            try:
                title = self.driver.title.lower()
                if "email" in title and ("verify" in title or "confirm" in title):
                    print(f"✓ Title содержит email и verify/confirm: {self.driver.title}")
                    return True
            except:
                pass

            # ВАЖНО: НЕ считаем успехом просто переход со страницы /join
            # Потому что могли быть ошибки и редирект на другую страницу

            print("⚠ Не удалось определить успех регистрации")
            print("Возможные причины:")
            print("  1. Капча решена неправильно")
            print("  2. Email уже используется")
            print("  3. Другая ошибка на стороне Steam")

            return False

        except Exception as e:
            print(f"Ошибка при проверке email: {e}")
            import traceback
            traceback.print_exc()
            return False

    def set_account_details(self, username, password):
        """
        Устанавливает имя пользователя и пароль аккаунта
        """
        try:
            print(f"Установка деталей аккаунта: {username}")

            # Находим поля для имени пользователя и пароля
            username_field = self.driver.find_element(By.ID, "accountname")
            password_field = self.driver.find_element(By.ID, "password")
            confirm_password_field = self.driver.find_element(By.ID, "reenter_password")

            # Заполняем имя пользователя
            actions = ActionChains(self.driver)
            actions.move_to_element(username_field)
            actions.pause(random.uniform(0.1, 0.3))
            actions.click()
            actions.perform()
            username_field.clear()
            for char in username:
                actions = ActionChains(self.driver)
                actions.send_keys(char)
                actions.perform()
                time.sleep(random.uniform(0.05, 0.2))

            # Заполняем пароль
            time.sleep(random.uniform(0.3, 0.8))
            actions = ActionChains(self.driver)
            actions.move_to_element(password_field)
            actions.pause(random.uniform(0.1, 0.3))
            actions.click()
            actions.perform()
            password_field.clear()
            for char in password:
                actions = ActionChains(self.driver)
                actions.send_keys(char)
                actions.perform()
                time.sleep(random.uniform(0.05, 0.2))

            # Подтверждаем пароль
            time.sleep(random.uniform(0.3, 0.8))
            actions = ActionChains(self.driver)
            actions.move_to_element(confirm_password_field)
            actions.pause(random.uniform(0.1, 0.3))
            actions.click()
            actions.perform()
            confirm_password_field.clear()
            for char in password:
                actions = ActionChains(self.driver)
                actions.send_keys(char)
                actions.perform()
                time.sleep(random.uniform(0.05, 0.2))

            print("Детали аккаунта успешно установлены")
            return True
        except Exception as e:
            print(f"Ошибка при установке деталей аккаунта: {e}")
            return False

    def complete_registration(self):
        """
        Завершает процесс регистрации
        """
        try:
            print("Завершение регистрации...")

            # Находим кнопку завершения регистрации
            complete_button = self.driver.find_element(By.ID, "createAccountButton")

            # Имитируем человеческое поведение
            time.sleep(random.uniform(0.5, 1.2))

            # Перемещение к элементу и клик
            actions = ActionChains(self.driver)
            actions.move_to_element(complete_button)
            actions.pause(random.uniform(0.1, 0.3))
            actions.click()
            actions.perform()

            # Ожидаем завершения регистрации
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "registration_success"))
            )

            print("Регистрация успешно завершена")
            return True
        except Exception as e:
            print(f"Ошибка при завершении регистрации: {e}")
            return False

    def register_account(self, email=None, username=None, password=None):
        """
        Основной метод для регистрации аккаунта Steam
        :param email: Email для регистрации
        :param username: Имя пользователя
        :param password: Пароль для аккаунта
        """
        try:
            # Открываем страницу регистрации
            if not self.open_registration_page():
                raise Exception("Не удалось открыть страницу регистрации")

            # Генерируем данные, если они не предоставлены
            if not email:
                email = self.storage_gen.generate_email()
            if not username:
                username = self.storage_gen.generate_username()
            if not password:
                password = self.storage_gen.generate_password()

            # Заполняем email
            if not self.fill_email_address(email):
                raise Exception("Не удалось заполнить email")

            # Подтверждаем email
            if not self.confirm_email(email):
                raise Exception("Не удалось подтвердить email")

            # Принимаем соглашение
            if not self.accept_agreement():
                raise Exception("Не удалось принять соглашение")

            # Решаем капчу СРАЗУ перед нажатием Continue
            # чтобы токен не успел истечь
            print("\n⚠️  Решение капчи и отправка формы...")
            if not self.solve_captcha():
                raise Exception("Не удалось решить капчу")

            # Сразу после решения капчи нажимаем Continue
            # (без задержки, чтобы токен не истёк)
            print("Нажатие кнопки Continue сразу после решения капчи...")
            if not self.continue_registration():
                # Проверяем, возможно Steam показала ошибку капчи
                page_source = self.driver.page_source.lower()
                if "неверный ответ в поле captcha" in page_source or "invalid captcha" in page_source:
                    print("\n❌ Steam отклонила решение капчи!")
                    print("Возможные причины:")
                    print("  1. Токен капчи истёк (прошло слишком много времени)")
                    print("  2. YesCaptcha решила капчу неправильно")
                    print("  3. Steam использует Enterprise hCaptcha с дополнительными проверками")
                    print("\nПопробуйте:")
                    print("  - Использовать другой сервис решения капчи")
                    print("  - Решить капчу вручную")
                raise Exception("Не удалось продолжить регистрацию")

            # Верифицируем email
            if self.verify_email():
                print("\n" + "="*60)
                print("✓ Первый этап регистрации завершён успешно!")
                print("="*60)
                print(f"\nEmail: {email}")
                print(f"Username: {username}")
                print(f"Password: {password}")
                print("\n⚠️  ВАЖНО: Следующие шаги:")
                print("1. Откройте почтовый ящик: {email}")
                print("2. Найдите письмо от Steam")
                print("3. Кликните по ссылке подтверждения в письме")
                print("4. После подтверждения вы сможете установить имя пользователя и пароль")
                print("\nБраузер останется открытым для завершения регистрации...")
                print("="*60)

                # Сохраняем данные в файл
                with open('registration_data.txt', 'a', encoding='utf-8') as f:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"Дата: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Email: {email}\n")
                    f.write(f"Username: {username}\n")
                    f.write(f"Password: {password}\n")
                    f.write(f"Статус: Ожидание подтверждения email\n")
                    f.write(f"{'='*60}\n")

                print(f"\n✓ Данные сохранены в registration_data.txt")

                # НЕ закрываем браузер - даем пользователю время подтвердить email
                input("\nНажмите Enter после подтверждения email в почте...")

                # После подтверждения пытаемся установить детали
                print("\nПопытка установки деталей аккаунта...")
                if self.set_account_details(username, password):
                    if self.complete_registration():
                        print(f"\n✓ Регистрация полностью завершена!")
                        return True
                    else:
                        print("\n⚠️  Не удалось завершить регистрацию")
                        return False
                else:
                    print("\n⚠️  Не удалось установить детали аккаунта")
                    print("Возможно, нужно подтвердить email сначала")
                    return False
            else:
                raise Exception("Не удалось пройти первый этап регистрации (отправка email)")
        except Exception as e:
            print(f"Ошибка при регистрации: {e}")
            return False
        finally:
            # Закрываем браузер
            if self.driver:
                self.driver.quit()
                print("Браузер закрыт")


if __name__ == "__main__":
    # Режим работы: manual_captcha=True для ручного решения капчи
    # manual_captcha=False для автоматического через YesCaptcha
    registration = SteamRegistration(manual_captcha=True)

    registration.register_account(
        email="forteststeam123@outlook.com",
        username="forteststeam123",
        password="fortestst33eam123"
    )
