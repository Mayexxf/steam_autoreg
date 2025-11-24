import time
import random
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from twocaptcha import TwoCaptcha

from src.stealth.human_mouse import HumanMouse
from src.stealth.human_typing import HumanTypist
from src.utils.storage_generator import StorageGenerator


class SteamRegistration:
    def __init__(self, headless=False):
        """
        Инициализация класса для регистрации аккаунта Steam
        :param headless: Запускать браузер в фоновом режиме
        """
        self.headless = headless
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
        Решает hCaptcha на странице Steam с использованием сервиса 2captcha
        """
        try:
            print("Решение CAPTCHA...")

            # Создаем экземпляр решателя с вашим API-ключом
            solver = TwoCaptcha('ВАШ_API_КЛЮЧ_2CAPTCHA')

            # Найдем iframe с hCaptcha
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            captcha_iframe = None
            site_key = None

            print(f"Найдено {len(iframes)} iframe на странице")

            for iframe in iframes:
                src = iframe.get_attribute("src") or ""
                if "hcaptcha.com" in src.lower():
                    captcha_iframe = iframe
                    print(f"Найден iframe с hCaptcha: {src}")

                    # Извлекаем sitekey из URL
                    import re
                    sitekey_pattern = re.compile(r'sitekey=([^&]+)')
                    match = sitekey_pattern.search(src)
                    if match:
                        site_key = match.group(1)
                        print(f"Извлечен site_key из URL iframe: {site_key}")
                    break

            # Если не нашли sitekey в URL, используем значение из предыдущего запуска
            if site_key is None:
                site_key = "e18a349a-46c2-46a0-87a8-74be79345c92"  # значение с предыдущего запуска
                print(f"Используем известный site_key для hCaptcha на Steam: {site_key}")

            # Получим URL страницы
            page_url = self.driver.current_url
            print(f"URL страницы: {page_url}")

            # Решаем hCaptcha через 2captcha
            # ИСПРАВЛЕНИЕ: Используем метод solve() вместо hcaptcha()
            print(f"Отправляем hCaptcha на решение (sitekey: {site_key})...")

            # Вариант 1: Использование общего метода solve()
            result = solver.solve(
                {
                    'method': 'hcaptcha',
                    'sitekey': site_key,
                    'url': page_url,
                }
            )

            # Вариант 2: Альтернативный метод (если первый не сработает)
            # Используйте только один вариант из двух
            """
            result = solver.normal(
                {
                    'method': 'hcaptcha',
                    'sitekey': site_key,
                    'url': page_url,
                }
            )
            """

            captcha_response = result
            print(f"Получен ответ от 2captcha: {str(captcha_response)[:30]}...")

            # Находим основной элемент hCaptcha на странице
            # Если у нас есть iframe, то нам нужно вернуться на основную страницу
            self.driver.switch_to.default_content()
            print("Вернулись на основную страницу")

            # Теперь ищем скрытое поле для ввода ответа
            h_captcha_response_elem = None
            try:
                h_captcha_response_elem = self.driver.find_element(By.NAME, "h-captcha-response")
                print("Найден элемент h-captcha-response по имени")
            except:
                try:
                    h_captcha_response_elem = self.driver.find_element(By.ID, "h-captcha-response")
                    print("Найден элемент h-captcha-response по ID")
                except:
                    try:
                        # Ищем любой скрытый элемент, связанный с hcaptcha
                        h_captcha_response_elem = self.driver.find_element(
                            By.CSS_SELECTOR, "[name*='captcha'], [id*='captcha']"
                        )
                        print(
                            f"Найден элемент captcha: {h_captcha_response_elem.get_attribute('name') or h_captcha_response_elem.get_attribute('id')}")
                    except:
                        print("Не удалось найти элемент для ввода ответа капчи")

            # Если нашли элемент для ввода ответа, вставляем его
            if h_captcha_response_elem:
                # Используем JavaScript для вставки ответа, так как элемент обычно скрыт
                self.driver.execute_script(
                    f"arguments[0].value = '{captcha_response}';",
                    h_captcha_response_elem
                )
                self.driver.execute_script(
                    f"arguments[0].innerHTML = '{captcha_response}';",
                    h_captcha_response_elem
                )
                print("Ответ вставлен в элемент h-captcha-response")

            # Дополнительно установим ответ через JavaScript глобально
            try:
                js_script = f"""
                // Установка глобальной переменной
                window.hcaptchaResponse = '{captcha_response}';

                // Попытка найти и заполнить все возможные поля для ответа капчи
                var possibleResponseElems = document.querySelectorAll('[name*="captcha"], [id*="captcha"], input[type="hidden"]');
                for(var i = 0; i < possibleResponseElems.length; i++) {{
                    var elem = possibleResponseElems[i];
                    elem.value = '{captcha_response}';
                    try {{ elem.innerHTML = '{captcha_response}'; }} catch(e) {{}}
                }}

                // Попытка вызвать callback функции hCaptcha
                try {{
                    if(window.hcaptcha && window.hcaptcha.setResponse) {{
                        window.hcaptcha.setResponse('{captcha_response}');
                    }}

                    // Также попробуем найти и вызвать другие обработчики
                    if(typeof window.onCaptchaSuccess === 'function') {{
                        window.onCaptchaSuccess('{captcha_response}');
                    }}

                    if(typeof window.onHCaptchaSuccess === 'function') {{
                        window.onHCaptchaSuccess('{captcha_response}');
                    }}

                    // Попробуем найти и заполнить все формы
                    var forms = document.forms;
                    for(var i = 0; i < forms.length; i++) {{
                        var form = forms[i];
                        var hiddenInput = document.createElement('input');
                        hiddenInput.type = 'hidden';
                        hiddenInput.name = 'h-captcha-response';
                        hiddenInput.value = '{captcha_response}';
                        form.appendChild(hiddenInput);
                    }}

                }} catch(e) {{
                    console.log("Ошибка при установке ответа hCaptcha:", e);
                }}

                console.log('hCaptcha ответ установлен через JavaScript');
                """

                self.driver.execute_script(js_script)
                print("Выполнен расширенный JavaScript для установки ответа капчи")
            except Exception as js_error:
                print(f"Ошибка при выполнении JavaScript: {js_error}")

            # Даем время на применение решения
            time.sleep(2)

            # Делаем скриншот для проверки
            self.driver.save_screenshot("captcha_after_solution.png")

            # Попробуем найти и нажать кнопку отправки формы, если она есть
            try:
                # Ищем кнопки отправки по различным селекторам
                submit_button_candidates = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "button[type='submit'], input[type='submit'], button.submit, .submit_btn, .btn_green_white_innerfade, [class*='submit'], [id*='submit']"
                )

                if submit_button_candidates:
                    print(f"Найдено {len(submit_button_candidates)} возможных кнопок отправки")
                    # Нажимаем на первую видимую кнопку
                    for button in submit_button_candidates:
                        if button.is_displayed():
                            print(
                                f"Нажимаем на кнопку: {button.get_attribute('class') or button.get_attribute('id') or 'безымянная кнопка'}")
                            button.click()
                            time.sleep(1)
                            break

                # Если не нашли кнопок, попробуем отправить форму напрямую
                else:
                    forms = self.driver.find_elements(By.TAG_NAME, "form")
                    if forms:
                        print(f"Найдено {len(forms)} форм на странице")
                        for form in forms:
                            print(f"Отправляем форму с id: {form.get_attribute('id') or 'без id'}")
                            self.driver.execute_script("arguments[0].submit();", form)
                            time.sleep(1)
                            break

            except Exception as btn_error:
                print(f"Ошибка при попытке отправить форму: {btn_error}")

            print("CAPTCHA обработана успешно")
            return True

        except Exception as e:
            print(f"Ошибка при решении CAPTCHA: {e}")
            import traceback
            traceback.print_exc()
            self.driver.save_screenshot("captcha_error.png")
            return False

    def get_button_info(self):
        """
        Получает информацию о всех кнопках на странице для отладки
        """
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        buttons_info = []
        for button in buttons:
            try:
                info = {
                    "text": button.text,
                    "id": button.get_attribute("id"),
                    "class": button.get_attribute("class"),
                    "type": button.get_attribute("type"),
                    "is_displayed": button.is_displayed(),
                    "is_enabled": button.is_enabled()
                }
                buttons_info.append(info)
            except Exception as e:
                print(f"Ошибка при получении информации о кнопке: {e}")

        return buttons_info

    def continue_registration(self):

        buttons_info = self.get_button_info()
        print(f"Информация о кнопках на странице: {buttons_info}")

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
        """Проверка успешной верификации email"""
        try:
            # Ожидаем сообщение о проверке email
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "verification_email_sent"))
            )
            print("Проверка email требуется")
            return True
        except:
            print("Не удалось найти страницу проверки email")
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

            # Решаем капчу, если она есть
            if not self.solve_captcha():
                raise Exception("Не удалось решить капчу")

            # Продолжаем регистрацию
            if not self.continue_registration():
                raise Exception("Не удалось продолжить регистрацию")

            # Верифицируем email
            if not self.verify_email():
                raise Exception("Не удалось верифицировать email")

            # Устанавливаем детали аккаунта
            if not self.set_account_details(username, password):
                raise Exception("Не удалось установить детали аккаунта")

            # Завершаем регистрацию
            if not self.complete_registration():
                raise Exception("Не удалось завершить регистрацию")

            print(f"Регистрация успешно завершена: {email}, {username}, {password}")
            return True
        except Exception as e:
            print(f"Ошибка при регистрации: {e}")
            return False
        finally:
            # Закрываем браузер
            if self.driver:
                self.driver.quit()
                print("Браузер закрыт")


if __name__ == "__main__":
    registration = SteamRegistration()
    registration.register_account(
        email="forteststeam123@outlook.com",
        username="forteststeam123",
        password="fortestst33eam123"

    )
