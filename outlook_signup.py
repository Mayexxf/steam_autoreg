#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Outlook Account Creator - автоматизация создания почты на outlook.com
С полным стелс-функционалом (fingerprint, cookies, storage, antidetect extension)
"""
from src.stealth.geo_config import get_geo_config
from src.stealth.human_typing import HumanTypist
from src.stealth.storage_generator import StorageGenerator
from src.stealth.cookie_generator import CookieGenerator
from src.stealth.fingerprint_generator import FingerprintGenerator
import sys
import io
import os
import time
import random
import string

# Настройка кодировки для Windows консоли (с построчной буферизацией для реального времени)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding='utf-8', line_buffering=True)
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding='utf-8', line_buffering=True)

from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scipy.interpolate import CubicSpline

# Попытка импорта pyautogui для реального клика
try:
    import pyautogui
    pyautogui.FAILSAFE = False
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("[WARN] pyautogui не установлен. Установите: pip install pyautogui")

# Попытка импорта winsound для звукового уведомления (Windows)
try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False


def alert_user(message="Требуется действие!"):
    """Уведомляет пользователя звуком и выводом в консоль"""
    print(f"\n{'!'*60}")
    print(f"!!! {message} !!!")
    print(f"{'!'*60}\n")

    # Звуковой сигнал на Windows
    if WINSOUND_AVAILABLE:
        try:
            # 3 коротких бипа
            for _ in range(3):
                winsound.Beep(1000, 200)  # 1000Hz, 200ms
                time.sleep(0.1)
        except:
            pass


# Импорт стелс-модулей

# ============================================================================
# HARDCODED PROXY
# ============================================================================
HARDCODED_PROXY = "yB9Ryx:BAU1FUpyp2yb:nproxy.site:12392"


def human_delay(min_ms=500, max_ms=1500):
    """Случайная задержка как у человека"""
    delay = random.uniform(min_ms, max_ms)
    time.sleep(delay / 1000)
    return int(delay)


# Быстрые задержки для поиска/фокуса (можно настроить)
FAST_DELAY = (50, 150)      # Очень быстро (поиск элементов)
FOCUS_DELAY = (100, 250)    # Фокус на элементе
SCROLL_DELAY = (100, 300)   # После скролла
CLICK_DELAY = (150, 350)    # После клика
PAGE_DELAY = (800, 1500)    # Ожидание загрузки страницы


class SeleniumHumanTypist:
    """Адаптер HumanTypist для Selenium"""

    def __init__(self, driver, speed_profile='normal', typo_rate=0.06, typo_correct_rate=0.9):
        self.driver = driver
        self.typist = HumanTypist(
            speed_profile=speed_profile, typo_rate=typo_rate)

    def type_text(self, element, text):
        """Печатает текст человекоподобно через Selenium"""
        total_length = len(text)
        for i, char in enumerate(text):
            # Проверяем опечатку
            if self.typist._should_make_typo(i, total_length):
                typo_char = self.typist._get_typo_char(char)
                element.send_keys(typo_char)
                delay = self.typist._get_char_delay(typo_char, i, total_length)
                time.sleep(delay)
                time.sleep(random.uniform(0.1, 0.4))
                element.send_keys(Keys.BACKSPACE)
                time.sleep(random.uniform(0.05, 0.15))

            element.send_keys(char)
            delay = self.typist._get_char_delay(char, i, total_length)
            time.sleep(delay)


class SeleniumHumanMouse:
    """Человекоподобные движения мыши с Bézier кривыми"""

    def __init__(self, driver):
        self.driver = driver
        self.actions = ActionChains(driver)

    def random_movement(self, movements=3):
        width = self.driver.execute_script("return window.innerWidth")
        height = self.driver.execute_script("return window.innerHeight")
        margin = 50
        safe_width = max(200, width - margin * 2)
        safe_height = max(200, height - margin * 2)

        for _ in range(movements):
            start_x = random.randint(margin, margin + safe_width)
            start_y = random.randint(margin, margin + safe_height)
            end_x = random.randint(margin, margin + safe_width)
            end_y = random.randint(margin, margin + safe_height)

            mid1_x = random.randint(min(start_x, end_x), max(start_x, end_x))
            mid1_y = random.randint(min(start_y, end_y), max(start_y, end_y))
            mid2_x = random.randint(min(start_x, end_x), max(start_x, end_x))
            mid2_y = random.randint(min(start_y, end_y), max(start_y, end_y))

            points = [(start_x, start_y), (mid1_x, mid1_y),
                      (mid2_x, mid2_y), (end_x, end_y)]
            t = [0, 0.3, 0.7, 1]
            cs_x = CubicSpline(t, [p[0] for p in points])
            cs_y = CubicSpline(t, [p[1] for p in points])

            steps = 20
            current_x, current_y = start_x, start_y

            for i in range(steps):
                pos = i / steps
                new_x = int(cs_x(pos))
                new_y = int(cs_y(pos))
                dx = max(-100, min(100, new_x - current_x))
                dy = max(-100, min(100, new_y - current_y))
                try:
                    self.actions.move_by_offset(dx, dy).perform()
                    current_x += dx
                    current_y += dy
                except Exception:
                    pass
                time.sleep(random.uniform(0.01, 0.05))

            self.actions.reset_actions()
            time.sleep(random.uniform(0.3, 0.8))


def random_mouse_movement(driver, movements=3):
    mouse = SeleniumHumanMouse(driver)
    mouse.random_movement(movements=movements)


def human_type(driver, selector, text, speed_profile='normal', typo_rate=0.06):
    """Печатает текст РЕАЛИСТИЧНО как человек"""
    element = driver.find_element(By.CSS_SELECTOR, selector)

    # Движение мыши перед кликом
    mouse = SeleniumHumanMouse(driver)
    mouse.random_movement(movements=random.randint(1, 3))

    # Наведение и клик
    ActionChains(driver) \
        .move_to_element_with_offset(element, random.randint(-10, 10), random.randint(-5, 5)) \
        .pause(random.uniform(0.3, 1.1)) \
        .click() \
        .perform()

    # Пауза перед вводом
    time.sleep(random.uniform(0.6, 2.1))

    # Печать
    typist = SeleniumHumanTypist(
        driver, speed_profile=speed_profile, typo_rate=typo_rate, typo_correct_rate=0.92)
    typist.type_text(element, text)

    # Пауза после ввода
    time.sleep(random.uniform(0.7, 2.3))

    # Иногда двигаем мышку после ввода
    if random.random() < 0.4:
        ActionChains(driver).move_by_offset(
            random.randint(-80, 80), random.randint(-80, 80)
        ).pause(0.3).perform()


def _parse_proxy_for_firefox(proxy):
    """Парсит строку прокси для selenium-wire"""
    if not proxy:
        return None
    if proxy.startswith('socks5://'):
        protocol = 'socks5'
        proxy_str = proxy[9:]
    elif proxy.startswith('http://'):
        protocol = 'http'
        proxy_str = proxy[7:]
    else:
        protocol = 'http'
        proxy_str = proxy

    if '@' in proxy_str:
        auth, server = proxy_str.split('@')
        username, password = auth.split(':', 1)
        host, port = server.split(':', 1)
        return {'protocol': protocol, 'host': host, 'port': int(port), 'username': username, 'password': password}
    elif proxy_str.count(':') >= 3:
        parts = proxy_str.split(':', 3)
        if parts[1].isdigit():
            return {'protocol': protocol, 'host': parts[0], 'port': int(parts[1]), 'username': parts[2], 'password': parts[3]}
        return {'protocol': protocol, 'host': parts[2], 'port': int(parts[3]), 'username': parts[0], 'password': parts[1]}
    else:
        host, port = proxy_str.split(':', 1)
        return {'protocol': protocol, 'host': host, 'port': int(port), 'username': None, 'password': None}


class OutlookAccountCreator:
    """Создает новый аккаунт Outlook с полным стелс-функционалом"""

    MONTH_NAMES = ["", "January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]

    def __init__(self, proxy=None, headless=False):
        self.proxy = proxy or HARDCODED_PROXY
        self.headless = headless
        self.driver = None
        self.page_timeout = 60
        self.wait_after_load = 2

    def _build_stealth_driver(self):
        """Создаёт браузер с полным стелс-функционалом"""

        # === Fingerprint генерация ===
        fingerprint_config = FingerprintGenerator.generate()
        firefox_version = '133.0'
        user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{firefox_version}) Gecko/20100101 Firefox/{firefox_version}"
        fingerprint_script = FingerprintGenerator.get_injector_script(
            fingerprint_config, firefox_version)

        # Геолокация (по умолчанию US)
        locale = 'en-US'
        timezone_id = 'America/New_York'

        print(
            f"[STEALTH] Fingerprint generated: {fingerprint_config['viewport']}")
        print(f"[STEALTH] User-Agent: {user_agent[:60]}...")
        print(f"[STEALTH] Locale: {locale}, Timezone: {timezone_id}")

        # === Firefox options ===
        options = FirefoxOptions()
        options.set_preference("general.useragent.override", user_agent)
        options.set_preference("intl.accept_languages", locale)
        options.set_preference("intl.locale.requested", locale)
        options.add_argument(
            f"--width={fingerprint_config['viewport']['width']}")
        options.add_argument(
            f"--height={fingerprint_config['viewport']['height']}")
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        options.set_preference("privacy.resistFingerprinting", False)

        # WebRTC защита
        options.set_preference("media.peerconnection.enabled", False)
        options.set_preference("media.navigator.enabled", False)

        if self.headless:
            options.add_argument("--headless")

        # === Прокси ===
        seleniumwire_options = {}
        proxy_config = _parse_proxy_for_firefox(self.proxy)
        if proxy_config:
            auth = f"{proxy_config['username']}:{proxy_config['password']}@" if proxy_config.get(
                'username') else ""
            protocol = "socks5" if proxy_config['protocol'] == 'socks5' else "http"
            proxy_url = f"{protocol}://{auth}{proxy_config['host']}:{proxy_config['port']}"
            seleniumwire_options = {
                'proxy': {'http': proxy_url, 'https': proxy_url, 'no_proxy': 'localhost,127.0.0.1'},
                'verify_ssl': False
            }
            print(
                f"[STEALTH] Proxy: {proxy_config['host']}:{proxy_config['port']}")

        # === Запуск браузера ===
        self.driver = webdriver.Firefox(
            options=options, seleniumwire_options=seleniumwire_options)
        self.driver.set_window_size(
            fingerprint_config['viewport']['width'], fingerprint_config['viewport']['height'])
        self.driver.set_page_load_timeout(self.page_timeout)
        self.driver.implicitly_wait(10)

        # === Антидетект расширение ===
        extension_path = os.path.abspath("firefox_antidetect_extension")
        if os.path.exists(extension_path):
            try:
                self.driver.install_addon(extension_path, temporary=True)
                print(f"[STEALTH] Antidetect extension loaded")
            except Exception as e:
                print(f"[STEALTH] Extension load failed: {e}")

        # Сохраняем для инъекций
        self._fingerprint_script = fingerprint_script
        self._locale = locale
        self._timezone_id = timezone_id

    def _inject_stealth_scripts(self):
        """Инжектит стелс-скрипты после загрузки страницы"""

        # === Fingerprint injection ===
        self.driver.execute_script(self._fingerprint_script)

        # === Timezone spoof ===
        timezone_script = f"""
            const orig = Intl.DateTimeFormat;
            Intl.DateTimeFormat = function(...a) {{ if (!a[0]) a[0] = '{self._locale}'; return new orig(...a); }};
            Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {{
                value: function() {{
                    let o = Object.getOwnPropertyDescriptor(orig.prototype, 'resolvedOptions').value.call(this);
                    o.timeZone = '{self._timezone_id}';
                    return o;
                }}
            }});
        """
        self.driver.execute_script(timezone_script)

        # === Cookies injection ===
        cookies = CookieGenerator().generate_realistic_cookies(num_sites=5)
        injected = 0
        for cookie in cookies:
            domain = cookie.get('domain', '')
            # Инжектим только для текущего домена
            if 'live.com' in domain or 'microsoft' in domain:
                try:
                    sel_cookie = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': cookie.get('domain', '.live.com'),
                        'path': cookie.get('path', '/'),
                        'secure': cookie.get('secure', True)
                    }
                    if 'expiry' in cookie:
                        sel_cookie['expiry'] = cookie['expiry']
                    self.driver.add_cookie(sel_cookie)
                    injected += 1
                except Exception:
                    pass
        print(f"[STEALTH] Cookies injected: {injected}")

        # === LocalStorage injection ===
        storage_data = StorageGenerator().generate_full_storage()
        if self.driver.execute_script("return typeof(Storage) !== 'undefined'"):
            self.driver.execute_script(
                StorageGenerator().get_storage_script(storage_data))
            print(f"[STEALTH] LocalStorage injected")

        # === Проверка webdriver ===
        wd = self.driver.execute_script("return navigator.webdriver")
        status = "undefined ✓" if wd is None else f"{wd} ✗"
        print(f"[STEALTH] navigator.webdriver = {status}")

    @staticmethod
    def _generate_identity():
        first_names = ["Liam", "Noah", "Oliver", "Ethan", "Mason", "Logan", "Lucas", "Henry", "James", "Benjamin",
                       "Emma", "Olivia", "Ava", "Sophia", "Isabella", "Mia", "Charlotte", "Amelia", "Harper", "Evelyn"]
        last_names = ["Smith", "Johnson", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor", "Anderson", "Thomas",
                      "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson", "Clark", "Lewis"]
        first = random.choice(first_names)
        last = random.choice(last_names)
        suffix = random.randint(1000, 9999)
        username = f"{first.lower()}{last.lower()}{suffix}"
        password_chars = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(random.choices(password_chars, k=16))
        year = random.randint(1985, 2000)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        return {
            "first": first,
            "last": last,
            "username": username,
            "password": password,
            "birth_year": year,
            "birth_month": month,
            "birth_day": day,
            "email": f"{username}@outlook.com"
        }

    def _wait(self, locator, timeout=15):
        return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(locator))

    def _get_email_error(self):
        """Получает текст ошибки на шаге email (если есть)"""
        error_selectors = [
            "#MemberNameError",
            "div[id*='MemberNameError']",
            "#usernameError",
            ".alert-error",
            ".error-text",
            "div[role='alert']",
            ".text-error",
            "[aria-live='assertive']",
            "[aria-live='polite']",
            # Fluent UI ошибки
            ".fui-Field__validationMessage",
            "[id*='validationMessage']",
            "[class*='error']",
            "[class*='Error']",
            # Microsoft signup специфичные
            "#iSignupEmailError",
            "#iError",
            ".error",
            ".serverError",
        ]
        for sel in error_selectors:
            try:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for el in els:
                    if el.is_displayed():
                        text = el.text.strip()
                        if text and len(text) > 3:
                            return text
            except Exception:
                continue

        # Также проверяем через JavaScript (для скрытых элементов)
        try:
            error_text = self.driver.execute_script("""
                // Ищем любые видимые элементы с ошибками
                const selectors = [
                    '#MemberNameError', '[id*="Error"]', '[class*="error"]',
                    '[aria-live="assertive"]', '[role="alert"]'
                ];
                for (let sel of selectors) {
                    const els = document.querySelectorAll(sel);
                    for (let el of els) {
                        const text = el.innerText || el.textContent || '';
                        if (text.trim().length > 3 && 
                            (el.offsetWidth > 0 || el.offsetHeight > 0 || el.style.display !== 'none')) {
                            return text.trim();
                        }
                    }
                }
                return '';
            """)
            if error_text:
                return error_text
        except:
            pass

        return ""

    def _click_next_button(self):
        """Кликает кнопку Next/Submit"""
        selectors = [
            "button#iSignupAction",
            "button[type='submit']",
            "input[type='submit']",
            "button#idSIButton9",
        ]
        for sel in selectors:
            try:
                btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                human_delay(200, 500)
                # JS клик для надёжности
                self.driver.execute_script("arguments[0].click();", btn)
                print(f"[CLICK] Нажата кнопка: {sel}")
                return True
            except Exception:
                continue
        return False

    def _select_fluent_dropdown(self, button_selector, option_text):
        """Выбирает опцию в Fluent UI dropdown по тексту/aria-label"""
        try:
            btn = self.driver.find_element(By.CSS_SELECTOR, button_selector)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", btn)
            human_delay(100, 200)

            self.driver.execute_script("arguments[0].click();", btn)
            print(f"[DROPDOWN] JS-клик: {button_selector}")
            human_delay(400, 600)

            # Ищем listbox
            listbox = None
            for lsel in ['[role="listbox"]', '.fui-Listbox', 'div[role="listbox"]']:
                try:
                    listbox = WebDriverWait(self.driver, 3).until(
                        EC.visibility_of_element_located(
                            (By.CSS_SELECTOR, lsel))
                    )
                    if listbox:
                        break
                except:
                    continue

            if not listbox:
                print("[DROPDOWN] Listbox не найден")
                return False

            human_delay(150, 300)
            options = listbox.find_elements(By.CSS_SELECTOR, '[role="option"]')
            print(f"[DROPDOWN] Опций: {len(options)}")

            option_text_str = str(option_text).lower()
            for opt in options:
                opt_text = (opt.text or '').strip().lower()
                opt_aria = (opt.get_attribute('aria-label') or '').lower()
                opt_inner = (opt.get_attribute('innerText') or '').lower()

                if (opt_text == option_text_str or
                    opt_aria == option_text_str or
                    option_text_str in opt_inner or
                        option_text_str in opt_text):
                    human_delay(100, 200)
                    self.driver.execute_script("arguments[0].click();", opt)
                    print(
                        f"[DROPDOWN] Выбрано: {opt.text or opt_aria or option_text}")
                    human_delay(150, 300)
                    return True

            print(f"[DROPDOWN] Опция '{option_text}' не найдена")
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            return False

        except Exception as e:
            print(f"[DROPDOWN] Ошибка: {str(e)[:60]}")
            try:
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            except:
                pass
            return False

    def _select_fluent_dropdown_by_index(self, button_selector, index):
        """Выбирает опцию по индексу (1-based для месяца/дня)"""
        try:
            # Закрываем любой открытый dropdown сначала
            try:
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                human_delay(150, 250)
            except:
                pass

            btn = self.driver.find_element(By.CSS_SELECTOR, button_selector)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", btn)
            human_delay(100, 200)

            self.driver.execute_script("arguments[0].click();", btn)
            print(f"[DROPDOWN IDX] JS-клик: {button_selector}")
            human_delay(500, 700)

            # Ищем listbox
            listbox = None
            for lsel in ['[role="listbox"]', '.fui-Listbox', 'div[role="listbox"]']:
                try:
                    listbox = WebDriverWait(self.driver, 4).until(
                        EC.visibility_of_element_located(
                            (By.CSS_SELECTOR, lsel))
                    )
                    if listbox and listbox.is_displayed():
                        break
                except:
                    continue

            if not listbox:
                print("[DROPDOWN IDX] Listbox не найден")
                return False

            human_delay(150, 300)
            options = listbox.find_elements(By.CSS_SELECTOR, '[role="option"]')
            print(
                f"[DROPDOWN IDX] Опций: {len(options)}, нужен индекс: {index}")

            # Для месяца/дня: индекс 1-based
            if 0 < index <= len(options):
                opt = options[index - 1]
                human_delay(100, 200)
                self.driver.execute_script("arguments[0].click();", opt)
                opt_label = opt.text or opt.get_attribute(
                    'aria-label') or f"idx={index}"
                print(f"[DROPDOWN IDX] Выбрано: {opt_label}")
                human_delay(150, 300)
                return True
            else:
                print(
                    f"[DROPDOWN IDX] Индекс {index} вне диапазона (1-{len(options)})")
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                return False

        except Exception as e:
            print(f"[DROPDOWN IDX] Ошибка: {str(e)[:60]}")
            try:
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            except:
                pass
            return False

    def _fill_birth_date(self, identity):
        """Заполняет дату рождения"""
        month = identity["birth_month"]
        day = identity["birth_day"]
        year = identity["birth_year"]
        month_name = self.MONTH_NAMES[month] if 1 <= month <= 12 else "January"

        print(f"[BIRTH] Заполняем: {month_name} {day}, {year}")

        # === МЕСЯЦ ===
        month_selectors = [
            'button#BirthMonthDropdown',
            'button[name="BirthMonth"]',
            'button[aria-label="Birth month"]',
        ]
        month_selected = False
        for sel in month_selectors:
            try:
                self.driver.find_element(By.CSS_SELECTOR, sel)
                if self._select_fluent_dropdown(sel, month_name):
                    month_selected = True
                    break
                if self._select_fluent_dropdown_by_index(sel, month):
                    month_selected = True
                    break
            except Exception:
                continue

        if not month_selected:
            print("[BIRTH] Месяц не выбран")

        human_delay(150, 300)

        # === ДЕНЬ ===
        day_selectors = [
            'button#BirthDayDropdown',
            'button[name="BirthDay"]',
            'button[aria-label="Birth day"]',
        ]
        day_selected = False
        for sel in day_selectors:
            try:
                self.driver.find_element(By.CSS_SELECTOR, sel)
                if self._select_fluent_dropdown(sel, str(day)):
                    day_selected = True
                    break
                if self._select_fluent_dropdown_by_index(sel, day):
                    day_selected = True
                    break
            except Exception:
                continue

        if not day_selected:
            print("[BIRTH] День не выбран")

        human_delay(150, 300)

        # === ГОД ===
        year_selectors = [
            'input[name="BirthYear"]',
            'input#BirthYear',
            'input[aria-label="Birth year"]',
            'input[type="number"][name="BirthYear"]',
        ]
        year_entered = False
        for sel in year_selectors:
            try:
                year_input = self.driver.find_element(By.CSS_SELECTOR, sel)
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", year_input)
                human_delay(100, 200)
                year_input.click()
                human_delay(50, 150)
                year_input.clear()
                SeleniumHumanTypist(self.driver, speed_profile='normal', typo_rate=0.0).type_text(
                    year_input, str(year))
                year_entered = True
                print(f"[BIRTH] Год введён: {year}")
                break
            except Exception as e:
                continue

        if not year_entered:
            print("[BIRTH] Год не введён")

        return month_selected and day_selected and year_entered

    def _solve_human_challenge(self, timeout=90):
        """
        Проходит PerimeterX Press and Hold challenge.
        ВАЖНО: Кнопка "hold" рендерится скриптом captcha.js на ОСНОВНОЙ странице,
        НЕ в iframe (iframe скрыт с display:none).

        Структура HTML:
        <div id="px-captcha">
            <div id="xxx" role="button" aria-label="Press & Hold Human Challenge" tabindex="0">
                <div id="progress-bar" style="width: 0px;">  <- меняется при удержании
                <p>Press and hold</p>
            </div>
        </div>

        Returns:
            True если challenge пройден, False при ошибке
        """
        print("[CHALLENGE] Проверяем наличие human challenge...")

        # Ждём появления капчи
        human_delay(800, 1200)

        # Убеждаемся что мы на основной странице (не в iframe)
        try:
            self.driver.switch_to.default_content()
        except:
            pass

        hold_button = None

        # Селекторы для кнопки капчи (специфичные для PerimeterX)
        # Кнопка имеет role="button" и aria-label содержащий "Hold" или "Press"
        button_selectors = [
            '#px-captcha [role="button"][aria-label*="Hold"]',
            '#px-captcha [role="button"][aria-label*="Press"]',
            '#px-captcha div[tabindex="0"][role="button"]',
            '[role="button"][aria-label*="Hold Human Challenge"]',
            '[role="button"][aria-label*="Press"][aria-label*="Hold"]',
            'div[role="button"][aria-label*="Human Challenge"]',
            '#px-captcha div[tabindex="0"]',
        ]

        for attempt in range(30):  # Увеличил количество попыток
            # Метод 1: Прямой поиск по селекторам
            for sel in button_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    for el in elements:
                        try:
                            if el.is_displayed() and el.size['width'] > 30 and el.size['height'] > 20:
                                aria_label = el.get_attribute(
                                    'aria-label') or ''
                                inner_text = el.text.lower() if el.text else ''
                                # Не берём уже завершённые и информационные элементы
                                if ('completed' not in aria_label.lower() and
                                        'accessible' not in aria_label.lower()[:20]):
                                    # Проверяем что это интерактивный элемент
                                    if (el.get_attribute('tabindex') == '0' or
                                        'hold' in aria_label.lower() or
                                            'press' in aria_label.lower()):
                                        hold_button = el
                                        print(
                                            f"[CHALLENGE] Найдена кнопка: {sel}")
                                        print(
                                            f"[CHALLENGE] aria-label: '{aria_label[:80]}'")
                                        break
                        except Exception:
                            continue
                except Exception:
                    continue
                if hold_button:
                    break

            if hold_button:
                break

            # Метод 2: JavaScript поиск (более надёжный)
            if not hold_button:
                hold_button = self.driver.execute_script("""
                    // Сначала ищем в контейнере #px-captcha
                    const pxContainer = document.querySelector('#px-captcha');
                    if (pxContainer) {
                        // Ищем div с role="button" и aria-label
                        const buttons = pxContainer.querySelectorAll('[role="button"]');
                        for (let btn of buttons) {
                            const label = (btn.getAttribute('aria-label') || '').toLowerCase();
                            const tabindex = btn.getAttribute('tabindex');
                            // Кнопка "Press & Hold" имеет tabindex="0" и aria-label с "hold" или "press"
                            if (tabindex === '0' && 
                                (label.includes('hold') || label.includes('press')) && 
                                !label.includes('completed') &&
                                !label.startsWith('accessible') &&
                                btn.offsetWidth > 30 && btn.offsetHeight > 20) {
                                console.log('Found PX button:', btn.id, label);
                                return btn;
                            }
                        }
                        
                        // Fallback: любой div[tabindex="0"] внутри px-captcha с текстом "hold"
                        const divs = pxContainer.querySelectorAll('div[tabindex="0"]');
                        for (let div of divs) {
                            const text = (div.innerText || '').toLowerCase();
                            const label = (div.getAttribute('aria-label') || '').toLowerCase();
                            if ((text.includes('hold') || label.includes('hold')) && 
                                !label.includes('completed') &&
                                div.offsetWidth > 100) {
                                return div;
                            }
                        }
                    }
                    
                    // Глобальный поиск если не нашли в px-captcha
                    const allButtons = document.querySelectorAll('[role="button"][tabindex="0"]');
                    for (let btn of allButtons) {
                        const label = (btn.getAttribute('aria-label') || '').toLowerCase();
                        if ((label.includes('hold') || label.includes('press')) && 
                            label.includes('human') &&
                            !label.includes('completed') &&
                            btn.offsetWidth > 30) {
                            return btn;
                        }
                    }
                    
                    return null;
                """)

                if hold_button:
                    try:
                        if hold_button.is_displayed():
                            aria = hold_button.get_attribute(
                                'aria-label') or ''
                            print(
                                f"[CHALLENGE] Найдена кнопка (JS): '{aria[:80]}'")
                            break
                    except:
                        pass
                    hold_button = None

            if attempt % 5 == 0:
                print(
                    f"[CHALLENGE] Ищем кнопку Press & Hold... попытка {attempt+1}/30")
            time.sleep(0.4)

        if not hold_button:
            print("[CHALLENGE] Кнопка Press & Hold не найдена")
            # Попробуем вывести HTML для отладки
            try:
                px_html = self.driver.execute_script("""
                    const px = document.querySelector('#px-captcha');
                    return px ? px.innerHTML.substring(0, 500) : 'px-captcha not found';
                """)
                print(f"[CHALLENGE] px-captcha HTML: {px_html[:300]}...")
            except:
                pass
            return False

        px_captcha = hold_button

        try:
            # Скроллим к элементу
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", px_captcha)
            human_delay(300, 500)

            # Убедимся что элемент виден
            self.driver.execute_script("""
                const el = arguments[0];
                el.scrollIntoView({behavior: 'smooth', block: 'center', inline: 'center'});
            """, px_captcha)
            human_delay(200, 400)

            print("[CHALLENGE] Начинаем удержание кнопки (Press and Hold)...")

            # Получаем координаты через getBoundingClientRect (более точно)
            rect = self.driver.execute_script("""
                const el = arguments[0];
                const rect = el.getBoundingClientRect();
                return {
                    x: rect.left,
                    y: rect.top,
                    width: rect.width,
                    height: rect.height,
                    centerX: rect.left + rect.width / 2,
                    centerY: rect.top + rect.height / 2
                };
            """, px_captcha)

            print(f"[CHALLENGE] Rect элемента: x={rect['x']:.0f}, y={rect['y']:.0f}, " +
                  f"size={rect['width']:.0f}x{rect['height']:.0f}")

            # Позиция окна браузера
            window_x = self.driver.execute_script(
                "return window.screenX || window.screenLeft || 0;")
            window_y = self.driver.execute_script(
                "return window.screenY || window.screenTop || 0;")

            # Размер chrome (заголовок браузера + панели)
            inner_height = self.driver.execute_script(
                "return window.innerHeight;")
            outer_height = self.driver.execute_script(
                "return window.outerHeight;")
            chrome_height = outer_height - inner_height

            # Вычисляем абсолютные координаты на экране
            # Используем центр элемента + небольшое случайное смещение
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)

            abs_x = int(window_x + rect['centerX'] + offset_x)
            abs_y = int(window_y + chrome_height + rect['centerY'] + offset_y)

            print(f"[CHALLENGE] Экранные координаты: ({abs_x}, {abs_y})")
            print(
                f"[CHALLENGE] Окно: x={window_x}, y={window_y}, chrome_height={chrome_height}")

            # Используем pyautogui для РЕАЛЬНОГО клика (если доступен)
            if PYAUTOGUI_AVAILABLE:
                print("[CHALLENGE] Используем pyautogui для реального клика...")

                # Плавно двигаем мышь к элементу
                pyautogui.moveTo(
                    abs_x, abs_y, duration=random.uniform(0.3, 0.6))
                human_delay(100, 200)

                # Нажимаем и ДЕРЖИМ кнопку мыши
                pyautogui.mouseDown(button='left')
                print("[CHALLENGE] Кнопка мыши нажата (pyautogui)")
            else:
                # Fallback: JavaScript PointerEvents (PerimeterX слушает именно их)
                print("[CHALLENGE] Используем JavaScript PointerEvents...")

                # Сначала двигаем мышь через ActionChains
                ActionChains(self.driver).move_to_element(px_captcha).perform()
                human_delay(100, 200)

                # Диспатчим все необходимые события через JavaScript
                self.driver.execute_script("""
                    const el = arguments[0];
                    const rect = el.getBoundingClientRect();
                    const centerX = rect.left + rect.width / 2 + (Math.random() * 10 - 5);
                    const centerY = rect.top + rect.height / 2 + (Math.random() * 10 - 5);
                    
                    // PointerEvent - это то, что слушает PerimeterX
                    const pointerDownEvent = new PointerEvent('pointerdown', {
                        bubbles: true,
                        cancelable: true,
                        view: window,
                        clientX: centerX,
                        clientY: centerY,
                        pointerId: 1,
                        pointerType: 'mouse',
                        isPrimary: true,
                        button: 0,
                        buttons: 1,
                        pressure: 0.5
                    });
                    
                    // MouseEvent для совместимости
                    const mouseDownEvent = new MouseEvent('mousedown', {
                        bubbles: true,
                        cancelable: true,
                        view: window,
                        clientX: centerX,
                        clientY: centerY,
                        button: 0,
                        buttons: 1
                    });
                    
                    // TouchEvent для мобильной эмуляции
                    try {
                        const touch = new Touch({
                            identifier: Date.now(),
                            target: el,
                            clientX: centerX,
                            clientY: centerY,
                            radiusX: 2.5,
                            radiusY: 2.5,
                            rotationAngle: 10,
                            force: 0.5
                        });
                        const touchStartEvent = new TouchEvent('touchstart', {
                            bubbles: true,
                            cancelable: true,
                            view: window,
                            touches: [touch],
                            targetTouches: [touch],
                            changedTouches: [touch]
                        });
                        el.dispatchEvent(touchStartEvent);
                    } catch(e) {}
                    
                    // Фокус на элементе
                    el.focus();
                    
                    // Диспатчим события
                    el.dispatchEvent(pointerDownEvent);
                    el.dispatchEvent(mouseDownEvent);
                    
                    // Сохраняем для последующего отпускания
                    window.__pxCaptchaCoords = {x: centerX, y: centerY};
                    
                    console.log('PointerDown dispatched at', centerX, centerY);
                """, px_captcha)

                print("[CHALLENGE] PointerDown событие отправлено")

                # Также пробуем ActionChains для подстраховки
                try:
                    ActionChains(self.driver).click_and_hold(
                        px_captcha).perform()
                except Exception:
                    pass

            # Ждём успешного прохождения
            start_time = time.time()
            challenge_passed = False
            last_progress_width = 0

            success_indicators = [
                "completed",
                "verified",
                "success",
                "passed",
                "please wait",
            ]

            last_micro_move = time.time()
            micro_move_interval = 0.25  # Микро-движение каждые 0.25 сек
            last_log_time = 0

            while time.time() - start_time < timeout:
                time.sleep(0.08)  # Быстрая проверка (80мс)

                # === МИКРО-ДВИЖЕНИЯ мыши (человек не держит абсолютно неподвижно) ===
                if time.time() - last_micro_move > micro_move_interval:
                    try:
                        if PYAUTOGUI_AVAILABLE:
                            # Микро-дрожание: ±1-2 пикселя
                            dx = random.randint(-2, 2)
                            dy = random.randint(-2, 2)
                            pyautogui.move(dx, dy, duration=0.03)
                        else:
                            # JavaScript PointerMove (для PerimeterX)
                            dx = random.randint(-2, 2)
                            dy = random.randint(-2, 2)
                            self.driver.execute_script("""
                                const el = arguments[0];
                                const dx = arguments[1];
                                const dy = arguments[2];
                                const coords = window.__pxCaptchaCoords || {x: 100, y: 100};
                                coords.x += dx;
                                coords.y += dy;
                                window.__pxCaptchaCoords = coords;
                                
                                const pointerMoveEvent = new PointerEvent('pointermove', {
                                    bubbles: true, cancelable: true, view: window,
                                    clientX: coords.x, clientY: coords.y,
                                    pointerId: 1, pointerType: 'mouse', isPrimary: true,
                                    buttons: 1, pressure: 0.5
                                });
                                el.dispatchEvent(pointerMoveEvent);
                            """, px_captcha, dx, dy)
                    except Exception:
                        pass
                    last_micro_move = time.time()
                    micro_move_interval = random.uniform(0.15, 0.35)

                # === Проверяем прогресс по width полоски ===
                try:
                    progress_info = self.driver.execute_script("""
                        const btn = arguments[0];
                        // Ищем элемент прогресса внутри кнопки (div со style width)
                        const progressDivs = btn.querySelectorAll('div[style*="width"]');
                        for (let div of progressDivs) {
                            const width = div.style.width;
                            if (width && width !== '0px') {
                                return {width: width, found: true};
                            }
                        }
                        // Также проверяем aria-label
                        const label = btn.getAttribute('aria-label') || '';
                        return {width: '0px', found: false, label: label};
                    """, px_captcha)

                    if progress_info and progress_info.get('found'):
                        width_str = progress_info.get('width', '0px')
                        if width_str != '0px' and width_str != last_progress_width:
                            print(f"[CHALLENGE] Прогресс: {width_str}")
                            last_progress_width = width_str

                    # Проверяем aria-label на завершение
                    label = progress_info.get('label', '').lower()
                    if any(ind in label for ind in success_indicators):
                        print(
                            f"[CHALLENGE] ✓ aria-label: '{progress_info.get('label', '')[:60]}'")
                        challenge_passed = True
                        break
                except Exception:
                    pass

                # === Проверяем aria-label кнопки напрямую ===
                try:
                    aria_label = px_captcha.get_attribute('aria-label') or ''
                    label_lower = aria_label.lower()
                    if 'completed' in label_lower or 'please wait' in label_lower:
                        print(
                            f"[CHALLENGE] ✓ aria-label изменился: '{aria_label[:60]}'")
                        challenge_passed = True
                        break
                except Exception:
                    pass

                # === Проверяем наличие checkmark или success класса ===
                try:
                    success_check = self.driver.execute_script("""
                        const btn = arguments[0];
                        // Проверяем наличие checkmark с классом 'draw'
                        const checkmark = btn.querySelector('#checkmark.draw, .draw');
                        if (checkmark) return 'checkmark';
                        // Проверяем изменение текста
                        const text = btn.innerText || '';
                        if (text.toLowerCase().includes('please wait')) return 'please_wait';
                        if (text.toLowerCase().includes('completed')) return 'completed';
                        return null;
                    """, px_captcha)

                    if success_check:
                        print(
                            f"[CHALLENGE] ✓ Обнаружен индикатор: {success_check}")
                        challenge_passed = True
                        break
                except Exception:
                    pass

                # === Проверяем, не исчез ли элемент ===
                try:
                    if not px_captcha.is_displayed():
                        print("[CHALLENGE] ✓ Кнопка исчезла, challenge пройден")
                        challenge_passed = True
                        break
                except Exception:
                    print(
                        "[CHALLENGE] ✓ Элемент недоступен, возможно challenge пройден")
                    challenge_passed = True
                    break

                # Лог каждые 3 секунды
                elapsed = int(time.time() - start_time)
                if elapsed > last_log_time and elapsed % 3 == 0:
                    last_log_time = elapsed
                    print(f"[CHALLENGE] Удерживаем... {elapsed}сек")

            # Отпускаем кнопку мыши
            if PYAUTOGUI_AVAILABLE:
                pyautogui.mouseUp(button='left')
                print("[CHALLENGE] Кнопка мыши отпущена (pyautogui)")
            else:
                # JavaScript PointerUp событие
                try:
                    self.driver.execute_script("""
                        const el = arguments[0];
                        const coords = window.__pxCaptchaCoords || {x: 0, y: 0};
                        
                        const pointerUpEvent = new PointerEvent('pointerup', {
                            bubbles: true,
                            cancelable: true,
                            view: window,
                            clientX: coords.x,
                            clientY: coords.y,
                            pointerId: 1,
                            pointerType: 'mouse',
                            isPrimary: true,
                            button: 0,
                            buttons: 0
                        });
                        
                        const mouseUpEvent = new MouseEvent('mouseup', {
                            bubbles: true,
                            cancelable: true,
                            view: window,
                            clientX: coords.x,
                            clientY: coords.y,
                            button: 0,
                            buttons: 0
                        });
                        
                        const clickEvent = new MouseEvent('click', {
                            bubbles: true,
                            cancelable: true,
                            view: window,
                            clientX: coords.x,
                            clientY: coords.y,
                            button: 0
                        });
                        
                        el.dispatchEvent(pointerUpEvent);
                        el.dispatchEvent(mouseUpEvent);
                        el.dispatchEvent(clickEvent);
                        
                        console.log('PointerUp dispatched');
                    """, px_captcha)
                    print("[CHALLENGE] PointerUp событие отправлено")
                except Exception:
                    pass

                try:
                    ActionChains(self.driver).release().perform()
                except Exception:
                    pass

            human_delay(1000, 2000)

            # Не нужно switch_to.default_content() - мы не переключались в iframe

            if challenge_passed:
                print("[CHALLENGE] Challenge пройден ✓")
                human_delay(700, 1200)
                return True
            else:
                print(f"[CHALLENGE] Timeout после {timeout}сек")
                return False

        except Exception as e:
            print(f"[CHALLENGE] Ошибка: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _check_and_solve_challenge(self):
        """Проверяет и решает human challenge если он появился"""
        # Убедимся что мы на основной странице
        try:
            self.driver.switch_to.default_content()
        except:
            pass

        # Проверяем наличие #px-captcha (основной контейнер PerimeterX)
        try:
            px_captcha = self.driver.find_element(
                By.CSS_SELECTOR, '#px-captcha')
            if px_captcha and px_captcha.is_displayed():
                size = px_captcha.size
                if size.get('width', 0) > 50 and size.get('height', 0) > 20:
                    print(
                        f"[CHALLENGE] #px-captcha найден: {size['width']}x{size['height']}")
                    return self._solve_human_challenge(timeout=90)
        except Exception:
            pass

        # Проверяем наличие iframe challenge (для старых версий)
        iframe_selectors = [
            'iframe[src*="hsprotect"]',
            'iframe[title*="Human"]',
            'iframe[src*="px-captcha"]',
        ]

        for sel in iframe_selectors:
            try:
                iframes = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for iframe in iframes:
                    if iframe.is_displayed():
                        size = iframe.size
                        if size.get('width', 0) > 50 and size.get('height', 0) > 50:
                            print(
                                f"[CHALLENGE] Iframe найден: {sel} ({size['width']}x{size['height']})")
                            return self._solve_human_challenge(timeout=90)
            except Exception:
                continue

        return True

    def create_account(self):
        """Основной метод создания аккаунта"""

        print("=" * 60)
        print("Outlook Account Creator (STEALTH MODE)")
        print("=" * 60)

        # === Создаём стелс-браузер ===
        self._build_stealth_driver()
        identity = self._generate_identity()

        print(f"\n[IDENTITY] Email: {identity['email']}")
        print(f"[IDENTITY] Password: {identity['password']}")
        print(f"[IDENTITY] Name: {identity['first']} {identity['last']}")
        print(
            f"[IDENTITY] Birth: {identity['birth_month']}/{identity['birth_day']}/{identity['birth_year']}")

        try:
            # === Открываем страницу ===
            self.driver.get("https://signup.live.com/signup")
            print(f"\n[PAGE] URL: {self.driver.current_url}")
            time.sleep(self.wait_after_load)

            # === Инжектим стелс-скрипты ===
            self._inject_stealth_scripts()

            human_delay(500, 1000)
            random_mouse_movement(self.driver, movements=1)

            # === ШАГ 1: Email (с проверкой занятости) ===
            print("\n[STEP 1] Ввод email...")
            max_email_attempts = 5
            email_accepted = False

            for attempt in range(1, max_email_attempts + 1):
                try:
                    # Ждём поле email
                    email_field = self._wait(
                        (By.CSS_SELECTOR, 'input[name="MemberName"], input#MemberName, input[type="email"]'))

                    # Очищаем поле если это повторная попытка
                    if attempt > 1:
                        email_field.clear()
                        human_delay(200, 400)

                    # Вводим email
                    human_type(
                        self.driver, 'input[name="MemberName"], input#MemberName, input[type="email"]',
                        identity["email"], typo_rate=0.03)
                    human_delay(300, 600)

                    # Нажимаем Next
                    if not self._click_next_button():
                        ActionChains(self.driver).send_keys(
                            Keys.ENTER).perform()

                    # Ждём ответа сервера (важно для проверки занятости)
                    human_delay(1500, 2500)

                    # Проверяем, появилось ли поле пароля (успех)
                    password_fields = self.driver.find_elements(
                        By.CSS_SELECTOR, 'input[type="password"]')
                    if password_fields and any(p.is_displayed() for p in password_fields):
                        print(f"[STEP 1] Email принят: {identity['email']} ✓")
                        email_accepted = True
                        break

                    # Ждём ещё немного для появления ошибки
                    human_delay(500, 800)

                    # Проверяем ошибку занятости
                    error_text = self._get_email_error()
                    if error_text:
                        print(f"[STEP 1] Ошибка: {error_text}")

                        # Проверяем, это ошибка занятости
                        error_lower = error_text.lower()
                        if any(kw in error_lower for kw in ['taken', 'already', 'exist', 'use', 'занят', 'используется']):
                            print(
                                f"[STEP 1] Логин занят, генерируем новый ({attempt}/{max_email_attempts})")
                            # Генерируем новую identity
                            identity = self._generate_identity()
                            print(f"[STEP 1] Новый email: {identity['email']}")
                            continue
                        else:
                            # Другая ошибка - пробуем ещё раз с тем же email
                            print(
                                f"[STEP 1] Неизвестная ошибка, повтор ({attempt}/{max_email_attempts})")
                            continue

                    # Нет ни пароля, ни ошибки - ждём ещё
                    print(
                        f"[STEP 1] Ожидание ответа... ({attempt}/{max_email_attempts})")
                    human_delay(500, 1000)

                except Exception as e:
                    print(f"[STEP 1] Ошибка попытки {attempt}: {e}")
                    if attempt == max_email_attempts:
                        self.driver.save_screenshot("error_email.png")
                        return None

            if not email_accepted:
                print("[ERROR] Не удалось найти свободный логин")
                self.driver.save_screenshot("error_email_all_taken.png")
                return None

            human_delay(1000, 2000)

            # === ШАГ 2: Password ===
            print("[STEP 2] Ввод пароля...")
            try:
                self._wait(
                    (By.CSS_SELECTOR, 'input[type="password"]'), timeout=20)
                human_type(
                    self.driver, 'input[type="password"]', identity["password"], typo_rate=0.02)
                human_delay(300, 600)
                if not self._click_next_button():
                    ActionChains(self.driver).send_keys(Keys.ENTER).perform()
                print("[STEP 2] Пароль введён ✓")
            except Exception as e:
                print(f"[ERROR] Пароль: {e}")
                self.driver.save_screenshot("error_password.png")
                return None

            human_delay(700, 1200)

            # === ШАГ 3: Имя ИЛИ Дата рождения ===
            print("[STEP 3] Определяем следующий шаг...")

            name_found = False
            birth_found = False

            # Селекторы для Fluent UI полей имени
            name_field_selector = '[data-testid="firstNameInput"], [data-testid="lastNameInput"], input[name="LastName"], input#LastName'

            for iteration in range(30):  # 30 секунд максимум
                # Проверяем поля имени
                name_fields = self.driver.find_elements(
                    By.CSS_SELECTOR, name_field_selector)
                if name_fields:
                    name_found = True
                    break

                # Проверяем поля даты
                birth_fields = self.driver.find_elements(By.CSS_SELECTOR,
                                                         'button#BirthMonthDropdown, button[name="BirthMonth"], [data-testid="birthdateControls"]')
                if birth_fields:
                    birth_found = True
                    break

                time.sleep(1)

            if name_found:
                print("[STEP 3] Заполняем имя...")
                try:
                    # Пробуем Fluent UI селекторы
                    first_sel = '[data-testid="firstNameInput"] input, input[name="FirstName"], input#FirstName'
                    last_sel = '[data-testid="lastNameInput"] input, input[name="LastName"], input#LastName'

                    human_type(self.driver, first_sel,
                               identity["first"], typo_rate=0.02)
                    human_delay(200, 500)
                    human_type(self.driver, last_sel,
                               identity["last"], typo_rate=0.02)
                    human_delay(300, 600)
                    if not self._click_next_button():
                        ActionChains(self.driver).send_keys(
                            Keys.ENTER).perform()
                    print("[STEP 3] Имя введено ✓")
                    human_delay(700, 1200)
                except Exception as e:
                    print(f"[ERROR] Имя: {e}")
                    self.driver.save_screenshot("error_name.png")
                    return None
            elif birth_found:
                print("[STEP 3] Шаг имени пропущен, сразу дата")
            else:
                print("[ERROR] Неизвестный шаг")
                self.driver.save_screenshot("error_unknown.png")
                return None

            # === Проверка PerimeterX Challenge (после шага имени/даты) ===
            # Капча может появиться здесь - проверяем и ждём ручного решения если нужно
            print("[CHECK] Проверяем наличие captcha...")

            captcha_here = False
            for _ in range(5):  # Быстрая проверка 5 секунд
                try:
                    # Проверяем #px-captcha
                    px = self.driver.find_elements(
                        By.CSS_SELECTOR, '#px-captcha')
                    if px and px[0].is_displayed() and px[0].size.get('height', 0) > 30:
                        captcha_here = True
                        break
                    # Проверяем iframe
                    iframes = self.driver.find_elements(
                        By.CSS_SELECTOR, 'iframe[src*="hsprotect"], iframe[title*="Human"]')
                    for iframe in iframes:
                        if iframe.is_displayed() and iframe.size.get('width', 0) > 50:
                            captcha_here = True
                            break
                except:
                    pass
                if captcha_here:
                    break
                time.sleep(1)

            if captcha_here:
                alert_user("CAPTCHA ОБНАРУЖЕНА! Решите вручную!")
                # Ждём решения (до 120 сек)
                for wait_sec in range(120):
                    time.sleep(1)
                    still_active = False
                    try:
                        px = self.driver.find_elements(
                            By.CSS_SELECTOR, '#px-captcha')
                        if px and px[0].is_displayed() and px[0].size.get('height', 0) > 30:
                            still_active = True
                        iframes = self.driver.find_elements(
                            By.CSS_SELECTOR, 'iframe[src*="hsprotect"], iframe[title*="Human"]')
                        for iframe in iframes:
                            if iframe.is_displayed() and iframe.size.get('width', 0) > 50:
                                still_active = True
                                break
                    except:
                        pass
                    if not still_active:
                        print("[CHECK] ✓ Captcha решена!")
                        break
                    if wait_sec % 15 == 0 and wait_sec > 0:
                        print(f"[CHECK] Ожидание решения... {wait_sec}сек")
                human_delay(500, 1000)
            else:
                print("[CHECK] Captcha не обнаружена, продолжаем")

            # === ШАГ 4: Дата рождения ===
            print("[STEP 4] Ввод даты рождения...")
            try:
                self._wait((By.CSS_SELECTOR,
                            'button#BirthMonthDropdown, button[name="BirthMonth"], [data-testid="birthdateControls"]'),
                           timeout=20)
                print("[STEP 4] Элементы даты найдены")

                self._fill_birth_date(identity)

                human_delay(500, 1000)

                if not self._click_next_button():
                    ActionChains(self.driver).send_keys(Keys.ENTER).perform()
                print("[STEP 4] Дата введена ✓")

            except Exception as e:
                print(f"[ERROR] Дата: {e}")
                self.driver.save_screenshot("error_birthdate.png")
                return None

            human_delay(700, 1200)

            # === ШАГ 5: Имя/Фамилия (если появились после даты) ===
            print("[STEP 5] Проверяем поля имени...")
            try:
                # Расширенные селекторы для полей имени (Fluent UI)
                first_name_selectors = [
                    '[data-testid="firstNameInput"] input',  # Fluent UI
                    'div[data-testid="firstNameInput"] input',
                    'input[name="FirstName"]',
                    'input#FirstName',
                    'input[placeholder="First name"]',
                    'input[aria-label="First name"]',
                    'input[autocomplete="given-name"]',
                    '.fui-Input input',  # Fallback Fluent
                ]
                last_name_selectors = [
                    '[data-testid="lastNameInput"] input',  # Fluent UI
                    'div[data-testid="lastNameInput"] input',
                    'input[name="LastName"]',
                    'input#LastName',
                    'input[placeholder="Last name"]',
                    'input[aria-label="Last name"]',
                    'input[autocomplete="family-name"]',
                ]
                all_name_selectors = ', '.join(
                    first_name_selectors + last_name_selectors)

                # Ждём до 15 секунд появления полей имени
                name_appeared = False
                for _ in range(15):
                    name_fields = self.driver.find_elements(
                        By.CSS_SELECTOR, all_name_selectors)
                    if name_fields:
                        name_appeared = True
                        print(
                            f"[STEP 5] Найдено {len(name_fields)} полей имени")
                        break
                    time.sleep(1)

                if name_appeared:
                    print("[STEP 5] Поля имени найдены, заполняем...")

                    # Заполняем First Name (пробуем разные селекторы)
                    first_filled = False
                    for sel in first_name_selectors:
                        try:
                            el = self.driver.find_element(By.CSS_SELECTOR, sel)
                            if el.is_displayed():
                                human_type(self.driver, sel,
                                           identity["first"], typo_rate=0.02)
                                first_filled = True
                                print(f"[STEP 5] First name введено: {sel}")
                                break
                        except Exception:
                            continue
                    human_delay(200, 500)

                    # Заполняем Last Name (пробуем разные селекторы)
                    last_filled = False
                    for sel in last_name_selectors:
                        try:
                            el = self.driver.find_element(By.CSS_SELECTOR, sel)
                            if el.is_displayed():
                                human_type(self.driver, sel,
                                           identity["last"], typo_rate=0.02)
                                last_filled = True
                                print(f"[STEP 5] Last name введено: {sel}")
                                break
                        except Exception:
                            continue
                    human_delay(300, 600)

                    # Нажимаем Next
                    if not self._click_next_button():
                        ActionChains(self.driver).send_keys(
                            Keys.ENTER).perform()
                    print("[STEP 5] Имя введено ✓")
                    human_delay(700, 1200)
                else:
                    print("[STEP 5] Поля имени не появились, пропускаем")

            except Exception as e:
                print(f"[STEP 5] Ошибка (не критично): {e}")

            human_delay(800, 1500)

            # === ШАГ 6: PerimeterX Captcha (Press and Hold) - РУЧНОЙ РЕЖИМ ===
            # PerimeterX v4+ с ML-моделью детектит Selenium с точностью 99.9%
            # Автоматическое решение невозможно - требуется ручное вмешательство
            print("\n" + "=" * 60)
            print("[STEP 6] ОЖИДАНИЕ РУЧНОГО РЕШЕНИЯ CAPTCHA")
            print("=" * 60)
            print("[INFO] PerimeterX v4+ невозможно решить автоматически.")
            print("[INFO] Если появится captcha 'Press and Hold' - решите её вручную.")
            print("[INFO] Скрипт автоматически продолжит после решения.")
            print("=" * 60 + "\n")

            # Ждём появления и затем исчезновения капчи (или успешного завершения)
            captcha_detected = False
            max_wait = 300  # 5 минут максимум

            for wait_sec in range(max_wait):
                time.sleep(1)

                # Проверяем наличие активной капчи
                captcha_visible = False

                # Способ 1: Проверяем #px-captcha
                try:
                    px_captcha = self.driver.find_element(
                        By.CSS_SELECTOR, '#px-captcha')
                    if px_captcha.is_displayed() and px_captcha.size.get('height', 0) > 30:
                        captcha_visible = True
                        if not captcha_detected:
                            captcha_detected = True
                            alert_user(
                                "CAPTCHA! Решите вручную (Press and Hold)")
                except:
                    pass

                # Способ 2: Проверяем iframe
                if not captcha_visible:
                    try:
                        iframes = self.driver.find_elements(
                            By.CSS_SELECTOR,
                            'iframe[src*="hsprotect"], iframe[title*="Human"], iframe[src*="captcha"]'
                        )
                        for iframe in iframes:
                            try:
                                if iframe.is_displayed() and iframe.size.get('width', 0) > 50:
                                    captcha_visible = True
                                    if not captcha_detected:
                                        captcha_detected = True
                                        alert_user("CAPTCHA! Решите вручную")
                                    break
                            except:
                                pass
                    except:
                        pass

                # Способ 3: Проверяем текст "Press and hold" на странице
                if not captcha_visible:
                    try:
                        body_text = self.driver.find_element(
                            By.TAG_NAME, 'body').text.lower()
                        if 'press and hold' in body_text or 'human challenge' in body_text:
                            captcha_visible = True
                            if not captcha_detected:
                                captcha_detected = True
                                alert_user("CAPTCHA! Решите вручную")
                    except:
                        pass

                # Если капча была, но исчезла - успех
                if captcha_detected and not captcha_visible:
                    print("[CAPTCHA] ✓ Captcha решена! Продолжаем...")
                    human_delay(1000, 2000)
                    break

                # Проверяем, не перешли ли мы на следующую страницу (успех без капчи)
                try:
                    current_url = self.driver.current_url.lower()
                    if 'outlook' in current_url or 'office' in current_url or 'welcome' in current_url:
                        print("[SUCCESS] Регистрация завершена!")
                        break
                except:
                    pass

                # Если капча не появилась за 15 секунд - пропускаем
                if not captcha_detected and wait_sec >= 15:
                    print("[STEP 6] Captcha не появилась, продолжаем...")
                    break

                # Периодический лог
                if captcha_visible and wait_sec % 10 == 0 and wait_sec > 0:
                    print(f"[CAPTCHA] Ожидание решения... {wait_sec}сек")

            human_delay(500, 1000)

            print("\n" + "=" * 60)
            print("[SUCCESS] Все шаги пройдены!")
            print("=" * 60)
            return identity

        except Exception as e:
            print(f"[FATAL] {e}")
            import traceback
            traceback.print_exc()
            return None

        finally:
            print("\n[WAIT] Браузер открыт — закройте вручную")
            try:
                while True:
                    time.sleep(1)
                    self.driver.current_url
            except Exception:
                print("[INFO] Браузер закрыт")
            finally:
                try:
                    self.driver.quit()
                except Exception:
                    pass

    def login_to_outlook(self, email, password):
        """
        Авторизуется в Outlook Web.

        Args:
            email: Email адрес
            password: Пароль

        Returns:
            True если успешно, False при ошибке
        """
        print(f"\n[LOGIN] Авторизация в Outlook: {email}")

        try:
            # Если драйвер не создан - создаём
            if not self.driver:
                self._build_stealth_driver()

            # Переходим на страницу входа
            self.driver.get("https://login.live.com/")
            human_delay(800, 1500)
            self._inject_stealth_scripts()

            # === ШАГ 1: Ввод email ===
            print("[LOGIN] Ввод email...")
            email_selectors = [
                'input[name="loginfmt"]',
                'input#i0116',
                'input[type="email"]',
                'input[placeholder*="email"]',
            ]

            email_field = None
            for sel in email_selectors:
                try:
                    email_field = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                    )
                    if email_field:
                        break
                except:
                    continue

            if not email_field:
                print("[LOGIN ERROR] Поле email не найдено")
                return False

            email_field.click()
            human_delay(100, 200)
            human_type(self.driver, email_selectors[0], email, typo_rate=0.01)
            print(f"[LOGIN] Email введён: {email}")

            # Нажимаем Next
            human_delay(300, 500)
            next_btn = self.driver.find_element(
                By.CSS_SELECTOR, '#idSIButton9, input[type="submit"]')
            self.driver.execute_script("arguments[0].click();", next_btn)
            print("[LOGIN] Нажата кнопка Next")

            human_delay(1500, 2500)

            # === ШАГ 2: Ввод пароля ===
            print("[LOGIN] Ввод пароля...")
            password_selectors = [
                'input[name="passwd"]',
                'input#i0118',
                'input[type="password"]',
            ]

            password_field = None
            for sel in password_selectors:
                try:
                    password_field = WebDriverWait(self.driver, 15).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                    )
                    if password_field:
                        break
                except:
                    continue

            if not password_field:
                print("[LOGIN ERROR] Поле пароля не найдено")
                self.driver.save_screenshot("login_error_password.png")
                return False

            password_field.click()
            human_delay(100, 200)
            human_type(
                self.driver, password_selectors[0], password, typo_rate=0.01)
            print("[LOGIN] Пароль введён")

            # Нажимаем Sign in
            human_delay(300, 500)
            signin_btn = self.driver.find_element(
                By.CSS_SELECTOR, '#idSIButton9, input[type="submit"]')
            self.driver.execute_script("arguments[0].click();", signin_btn)
            print("[LOGIN] Нажата кнопка Sign in")

            human_delay(2000, 3000)

            # === ШАГ 3: Обработка "Stay signed in?" ===
            try:
                stay_signed = self.driver.find_elements(
                    By.CSS_SELECTOR, '#idBtn_Back, #idSIButton9')
                if stay_signed:
                    # Нажимаем "No" или "Yes" - в зависимости от того что найдено
                    for btn in stay_signed:
                        if btn.is_displayed():
                            self.driver.execute_script(
                                "arguments[0].click();", btn)
                            print("[LOGIN] Обработан диалог 'Stay signed in'")
                            break
                    human_delay(1500, 2500)
            except:
                pass

            # Проверяем успешный вход
            current_url = self.driver.current_url.lower()
            if 'outlook' in current_url or 'mail' in current_url or 'live' in current_url:
                print("[LOGIN] ✓ Авторизация успешна!")
                return True
            else:
                print(f"[LOGIN] URL после входа: {current_url}")
                # Попробуем перейти напрямую в почту
                self.driver.get("https://outlook.live.com/mail/0/inbox")
                human_delay(2000, 3000)
                return True

        except Exception as e:
            print(f"[LOGIN ERROR] {e}")
            import traceback
            traceback.print_exc()
            self.driver.save_screenshot("login_error.png")
            return False

    def get_steam_verification_link(self, timeout=120, check_interval=10):
        """
        Ищет письмо от Steam и извлекает ссылку подтверждения.

        Args:
            timeout: Максимальное время ожидания письма (сек)
            check_interval: Интервал между проверками (сек)

        Returns:
            URL подтверждения или None
        """
        print(f"\n[MAIL] Поиск письма от Steam (таймаут: {timeout}сек)...")

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Переходим в inbox
                self.driver.get("https://outlook.live.com/mail/0/inbox")
                human_delay(2000, 3000)

                # Ищем письмо от Steam
                email_selectors = [
                    '[aria-label*="Steam"]',
                    '[aria-label*="steam"]',
                    'div[class*="hcptT"]:has-text("Steam")',
                    'span:contains("Steam")',
                    '[data-convid]',  # Любое письмо
                ]

                # Сначала ищем конкретно от Steam
                steam_email = None
                try:
                    # Ищем по тексту "Steam" в списке писем
                    emails = self.driver.find_elements(
                        By.CSS_SELECTOR, '[role="option"], [data-convid], .jGG6V')
                    for email_item in emails:
                        email_text = email_item.text.lower()
                        if 'steam' in email_text or 'steampowered' in email_text:
                            steam_email = email_item
                            print(f"[MAIL] Найдено письмо от Steam!")
                            break
                except:
                    pass

                if not steam_email:
                    # Альтернативный поиск через JavaScript
                    try:
                        steam_email = self.driver.execute_script("""
                            const items = document.querySelectorAll('[role="option"], [data-convid], .jGG6V, div[class*="EeHm"]');
                            for (let item of items) {
                                if (item.innerText.toLowerCase().includes('steam')) {
                                    return item;
                                }
                            }
                            return null;
                        """)
                    except:
                        pass

                if steam_email:
                    # Кликаем на письмо
                    self.driver.execute_script(
                        "arguments[0].click();", steam_email)
                    print("[MAIL] Открываем письмо...")
                    human_delay(2000, 3000)

                    # Ищем ссылку подтверждения
                    verification_link = self._extract_steam_link()
                    if verification_link:
                        return verification_link
                    else:
                        print("[MAIL] Ссылка не найдена в письме, ищем дальше...")

                # Ждём и повторяем
                elapsed = int(time.time() - start_time)
                print(
                    f"[MAIL] Письмо не найдено, ожидание... ({elapsed}/{timeout}сек)")

                # Обновляем inbox
                try:
                    refresh_btn = self.driver.find_element(
                        By.CSS_SELECTOR, '[aria-label*="Refresh"], [title*="Refresh"], button[name="Refresh"]')
                    self.driver.execute_script(
                        "arguments[0].click();", refresh_btn)
                except:
                    # Просто перезагрузим страницу
                    pass

                time.sleep(check_interval)

            except Exception as e:
                print(f"[MAIL] Ошибка поиска: {e}")
                time.sleep(check_interval)

        print(f"[MAIL] Таймаут {timeout}сек - письмо не найдено")
        return None

    def _extract_steam_link(self):
        """Извлекает ссылку подтверждения из открытого письма Steam"""
        try:
            # Ищем ссылки в теле письма
            links = self.driver.find_elements(
                By.CSS_SELECTOR, 'a[href*="store.steampowered.com"], a[href*="steampowered.com/account"]')

            for link in links:
                href = link.get_attribute('href') or ''
                # Ищем ссылку подтверждения (обычно содержит verify, confirm, newaccountverification)
                if any(kw in href.lower() for kw in ['verify', 'confirm', 'newaccount', 'stoken']):
                    print(f"[MAIL] ✓ Найдена ссылка подтверждения!")
                    print(f"[MAIL] URL: {href[:80]}...")
                    return href

            # Альтернативный поиск через JavaScript
            verification_link = self.driver.execute_script("""
                const links = document.querySelectorAll('a');
                for (let link of links) {
                    const href = link.href || '';
                    if (href.includes('steampowered.com') && 
                        (href.includes('verify') || href.includes('confirm') || 
                         href.includes('newaccount') || href.includes('stoken'))) {
                        return href;
                    }
                }
                return null;
            """)

            if verification_link:
                print(
                    f"[MAIL] ✓ Найдена ссылка (JS): {verification_link[:80]}...")
                return verification_link

            # Если не нашли конкретную ссылку, ищем любую от Steam
            all_steam_links = self.driver.execute_script("""
                const links = document.querySelectorAll('a[href*="steampowered.com"]');
                return Array.from(links).map(l => l.href);
            """)

            if all_steam_links:
                print(f"[MAIL] Найдено {len(all_steam_links)} ссылок от Steam")
                for link in all_steam_links:
                    print(f"  - {link[:60]}...")
                # Возвращаем первую подходящую
                for link in all_steam_links:
                    if 'verify' in link.lower() or 'confirm' in link.lower():
                        return link
                return all_steam_links[0] if all_steam_links else None

            print("[MAIL] Ссылки подтверждения не найдены")
            return None

        except Exception as e:
            print(f"[MAIL] Ошибка извлечения ссылки: {e}")
            return None

    def verify_steam_account(self, verification_link):
        """
        Переходит по ссылке подтверждения Steam.

        Args:
            verification_link: URL подтверждения

        Returns:
            True если успешно, False при ошибке
        """
        print(f"\n[VERIFY] Подтверждение аккаунта Steam...")
        print(f"[VERIFY] URL: {verification_link[:80]}...")

        try:
            self.driver.get(verification_link)
            human_delay(3000, 5000)

            # Проверяем успех
            page_text = self.driver.find_element(
                By.TAG_NAME, 'body').text.lower()

            success_indicators = ['verified', 'confirmed',
                                  'success', 'thank you', 'подтвержд', 'успешно']
            for indicator in success_indicators:
                if indicator in page_text:
                    print(f"[VERIFY] ✓ Аккаунт Steam подтверждён!")
                    return True

            print("[VERIFY] Страница подтверждения загружена")
            print(f"[VERIFY] URL: {self.driver.current_url}")
            return True

        except Exception as e:
            print(f"[VERIFY ERROR] {e}")
            return False


if __name__ == "__main__":
    headless = "--headless" in sys.argv
    proxy = None
    mode = "create"  # По умолчанию - создание аккаунта

    for arg in sys.argv:
        if arg.startswith("--proxy="):
            proxy = arg.split("=", 1)[1]
        elif arg == "--login":
            mode = "login"
        elif arg == "--verify":
            mode = "verify"

    creator = OutlookAccountCreator(proxy=proxy, headless=headless)

    if mode == "create":
        # Создание нового аккаунта
        result = creator.create_account()

        if result:
            print("\n" + "=" * 60)
            print("Созданные учётные данные:")
            print(f"  Email: {result['email']}")
            print(f"  Password: {result['password']}")
            print("=" * 60)

    elif mode == "login":
        # Только авторизация (нужно указать email/password)
        email = input("Email: ").strip()
        password = input("Password: ").strip()

        if creator.login_to_outlook(email, password):
            link = creator.get_steam_verification_link(timeout=120)
            if link:
                creator.verify_steam_account(link)

    elif mode == "verify":
        # Полный цикл: создать аккаунт + войти + получить письмо Steam
        result = creator.create_account()
        if result:
            print("\n[NEXT] Авторизация в почте для получения письма Steam...")
            if creator.login_to_outlook(result['email'], result['password']):
                link = creator.get_steam_verification_link(timeout=180)
                if link:
                    creator.verify_steam_account(link)
