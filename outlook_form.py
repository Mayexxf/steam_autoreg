#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Заполнение форм регистрации Microsoft (Selenium версия)
"""

import random
from typing import Dict

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from src.utils.mouse_emulator import HumanMouseEmulator  # если используете
from outlook.utils import human_type, human_click, human_delay, random_mouse_movement
from outlook.config import MONTH_NAMES


class FormFiller:
    """Заполнение форм регистрации Microsoft на Selenium"""

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)
        self.actions = ActionChains(driver)
        self.emulation = None  # если нужно — можно инициализировать HumanMouseEmulator(driver)


    def fill_email(self, identity: Dict, generate_new_identity) -> bool:
        """Заполняет email с проверкой занятости (до 5 попыток)"""
        max_attempts = 5

        for attempt in range(1, max_attempts + 1):
            try:
                print(f"[EMAIL] Попытка {attempt}/{max_attempts}")

                # Ждём поле ввода email
                email_field = self.wait.until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='MemberName'], input#i0319"))
                )

                if attempt > 1:
                    print(f"[EMAIL] Очищаем поле для новой попытки")
                    email_field.clear()
                    human_delay(200, 400)

                # Вводим email по-человечески
                human_type(self.driver, selector, identity["email"], typo_rate=0.05)
                human_delay(300, 600)

                # Кнопка "Далі" / "Next"
                next_btn = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'], button#idSIButton9, input#iSignupAction"))
                )
                human_click(self.driver, next_btn)
                human_delay(1500, 2500)

                # Проверяем, перешли ли на шаг с паролем
                try:
                    password_field = WebDriverWait(self.driver, 4).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
                    )
                    if password_field.is_displayed():
                        print(f"[EMAIL] ✓ Принят: {identity['email']}")
                        return True
                except:
                    pass

                # Проверяем наличие ошибки (email занят)
                error_selectors = [
                    "#MemberNameError",
                    ".alert-error",
                    "[role='alert']",
                    ".error-text",
                    "#usernameError"
                ]
                error_found = False
                for sel in error_selectors:
                    try:
                        error_el = self.driver.find_element(By.CSS_SELECTOR, sel)
                        if error_el.is_displayed():
                            error_text = error_el.text.strip()
                            if error_text:
                                print(f"[EMAIL] Ошибка: {error_text[:60]}")
                                if any(kw in error_text.lower() for kw in ['taken', 'already', 'exist', 'занят', 'используется']):
                                    identity.update(generate_new_identity())
                                    print(f"[EMAIL] Генерируем новый: {identity['email']}")
                                    error_found = True
                                    break
                    except:
                        continue

                if not error_found:
                    print("[EMAIL] Неизвестная ошибка или таймаут")
                    break

            except Exception as e:
                print(f"[EMAIL] Ошибка попытки {attempt}: {e}")

        print("[EMAIL] ✗ Все попытки исчерпаны")
        return False


    def fill_password(self, identity: Dict) -> bool:
        """Заполняет пароль"""
        try:
            password_field = self.wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='password'], input#iPassword"))
            )

            human_type(self.driver, password_field, identity["password"], typo_rate=0.03)
            human_delay(300, 600)

            next_btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'], button#iSignupAction"))
            )
            human_click(self.driver, next_btn)

            print("[PASSWORD] ✓ Введён")
            return True

        except Exception as e:
            print(f"[PASSWORD] Ошибка: {e}")
            return False


    def fill_birthdate(self, identity: Dict) -> bool:
        """Заполняет дату рождения"""
        month = identity["birth_month"]
        day = identity["birth_day"]
        year = identity["birth_year"]
        month_name = MONTH_NAMES.get(month, "January")

        print(f"[BIRTH] Заполняем: {month_name} {day}, {year}")

        try:
            # Ждём появления любого из полей даты
            self.wait.until(
                EC.presence_of_any_elements_located([
                    (By.CSS_SELECTOR, "select#BirthMonth"),
                    (By.CSS_SELECTOR, "button#BirthMonthDropdown"),
                    (By.ID, "BirthMonth")
                ])
            )
            human_delay(300, 500)

            self._select_month(month, month_name)
            human_delay(200, 400)

            self._select_day(day)
            human_delay(200, 400)

            self._enter_year(year)
            human_delay(300, 600)

            next_btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'], button#iSignupAction"))
            )
            human_click(self.driver, next_btn)

            print("[BIRTH] ✓ Дата введена")
            return True

        except Exception as e:
            print(f"[BIRTH] Ошибка: {e}")
            return False


    def _select_month(self, month: int, month_name: str):
        """Выбирает месяц (поддержка select и dropdown)"""
        selectors = ["#BirthMonthDropdown", "button#BirthMonthDropdown", "select#BirthMonth", "#DateOfBirthMonth"]

        for sel in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, sel)
                if not element.is_displayed():
                    continue

                tag = element.tag_name.lower()

                if tag == "select":
                    from selenium.webdriver.support.ui import Select
                    Select(element).select_by_value(str(month))
                    print(f"[BIRTH] Месяц (select): {month}")
                    return

                # Кликаем по dropdown-кнопке
                element.click()
                human_delay(400, 700)

                # Ищем опцию по тексту
                option = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, f"//div[@role='option' and contains(., '{month_name}')]"))
                )
                option.click()
                print(f"[BIRTH] Месяц (dropdown): {month_name}")
                return

            except Exception:
                continue

        # Fallback: нажать Escape, если открыто
        try:
            self.actions.send_keys("\u001b").perform()  # ESC
        except:
            pass


    def _select_day(self, day: int):
        """Выбирает день"""
        selectors = ["#BirthDayDropdown", "button#BirthDayDropdown", "select#BirthDay"]

        for sel in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, sel)
                if not element.is_displayed():
                    continue

                tag = element.tag_name.lower()

                if tag == "select":
                    from selenium.webdriver.support.ui import Select
                    Select(element).select_by_value(str(day))
                    print(f"[BIRTH] День (select): {day}")
                    return

                element.click()
                human_delay(400, 700)

                option = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, f"//div[@role='option' and text()='{day}']"))
                )
                option.click()
                print(f"[BIRTH] День (dropdown): {day}")
                return

            except Exception:
                continue


    def _enter_year(self, year: int):
        """Вводит год"""
        selectors = ["input#BirthYear", "input[name='BirthYear']", "input#DateOfBirthYear"]

        for sel in selectors:
            try:
                year_input = self.driver.find_element(By.CSS_SELECTOR, sel)
                if year_input.is_displayed():
                    year_input.click()
                    human_delay(100, 200)
                    year_input.clear()
                    human_type(self.driver, year_input, str(year), delay_range=(50, 120))
                    print(f"[BIRTH] Год: {year}")
                    return
            except Exception:
                continue


    def fill_name(self, identity: Dict) -> bool:
        """Заполняет имя и фамилию"""
        try:
            await random_mouse_movement(self.driver, random.randint(1, 3))
            human_delay(300, 700)

            first_selectors = [
                "[data-testid='firstNameInput'] input",
                "input[name='FirstName']",
                "input#FirstName",
                "input#iFirstName"
            ]

            last_selectors = [
                "[data-testid='lastNameInput'] input",
                "input[name='LastName']",
                "input#LastName",
                "input#iLastName"
            ]

            # Имя
            first_field = None
            for sel in first_selectors:
                try:
                    first_field = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if first_field.is_displayed():
                        human_type(self.driver, first_field, identity["first"], typo_rate=0.05)
                        print(f"[NAME] First: {identity['first']}")
                        break
                except:
                    continue

            human_delay(400, 800)
            random_mouse_movement(self.driver, random.randint(1, 2))

            # Фамилия
            for sel in last_selectors:
                try:
                    last_field = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if last_field.is_displayed():
                        human_type(self.driver, last_field, identity["last"], typo_rate=0.05)
                        print(f"[NAME] Last: {identity['last']}")
                        break
                except:
                    continue

            human_delay(600, 1200)

            next_btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'], button#iSignupAction"))
            )
            human_click(self.driver, next_btn)

            print("[NAME] ✓ Имя введено")
            return True

        except Exception as e:
            print(f"[NAME] Ошибка: {e}")
            return False