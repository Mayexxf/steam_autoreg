#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Заполнение форм регистрации Microsoft
"""

import random
from typing import Dict

from playwright.async_api import Page

from src.utils.mouse_emulator import HumanMouseEmulator
from .utils import human_type, human_click, human_delay, random_mouse_movement
from .config import MONTH_NAMES


class FormFiller:
    """Заполнение форм регистрации"""

    def __init__(self, page: Page):
        self.page = page
        self.emulation = None


    async def fill_email(self, identity: Dict, generate_new_identity) -> bool:
        """Заполняет email с проверкой занятости"""
        max_attempts = 5

        for attempt in range(1, max_attempts + 1):
            try:
                # Fluent UI селекторы (приоритет) + стандартные
                email_selectors = [
                    'input.fui-Input__input[type="email"]',  # Fluent UI
                    'input[aria-label*="пошта" i]',  # украинский "Електронна пошта"
                    'input[aria-label*="email" i]',  # английский
                    'input[aria-label*="почта" i]',  # русский
                    'input[name="Електронна пошта"]',  # украинский name
                    'input[name="MemberName"]',  # стандартный
                    'input#MemberName',
                    'input[type="email"]',
                ]

                email_selector = None
                for selector in email_selectors:
                    try:
                        if await self.page.locator(selector).count() > 0:
                            email_selector = selector
                            print(f"[EMAIL] Найдено поле с селектором: {selector}")
                            break
                    except:
                        continue

                if not email_selector:
                    print("[EMAIL] Поле email не найдено ни одним селектором!")
                    # Ждем и пробуем снова вместо немедленного выхода
                    await human_delay(2000, 3000)
                    continue  # Продолжаем цикл попыток

                await self.page.wait_for_selector(email_selector, timeout=15000)

                if attempt > 1:
                    # Очищаем поле перед новой попыткой
                    try:
                        await self.page.fill(email_selector, '')
                        await human_delay(200, 400)
                    except:
                        pass

                await human_type(self.page, email_selector, identity["email"], typo_rate=0.05)
                await human_delay(300, 600)

                # Fluent UI кнопки + стандартные (специфичные селекторы!)
                next_btn_selectors = [
                    'button[data-testid="primaryButton"]',  # Fluent UI primary button
                    'button.fui-Button[type="submit"]',  # Fluent UI submit
                    'button[type="submit"]',
                    'button#iSignupAction',
                    'button:has-text("Далі")',  # украинский
                    'button:has-text("Next")',  # английский
                    'button:has-text("Далее")',  # русский
                ]

                next_btn = None
                for selector in next_btn_selectors:
                    try:
                        if await self.page.locator(selector).count() > 0:
                            next_btn = selector
                            break
                    except:
                        continue

                if not next_btn:
                    next_btn = 'button[type="submit"]'  # fallback

                # Создаем локатор из селектора
                next_btn_locator = self.page.locator(next_btn)
                await human_click(self.page, next_btn_locator)
                await human_delay(1500, 2500)

                try:
                    password_field = await self.page.wait_for_selector(
                        'input[type="password"]', timeout=3000
                    )
                    if password_field and await password_field.is_visible():
                        print(f"[EMAIL] ✓ Принят: {identity['email']}")
                        return True
                except:
                    pass

                # Проверяем ошибки (включая Fluent UI и украинский текст)
                error_selectors = [
                    '#MemberNameError',
                    '.alert-error',
                    '[role="alert"]',
                    '[data-testid="errorMessage"]',  # Fluent UI
                    '.fui-MessageBar',  # Fluent UI message bar
                ]

                for sel in error_selectors:
                    try:
                        error_el = await self.page.query_selector(sel)
                        if error_el and await error_el.is_visible():
                            error_text = await error_el.inner_text()
                            if error_text:
                                print(f"[EMAIL] Ошибка: {error_text[:80]}")
                                # Украинские, английские, русские ключевые слова
                                taken_keywords = [
                                    'taken', 'already', 'exist',  # английский
                                    'використовується', 'зайнято', 'зайнятий',  # украинский
                                    'используется', 'занято', 'занят',  # русский
                                ]
                                if any(kw in error_text.lower() for kw in taken_keywords):
                                    # Генерируем новый email
                                    new_identity = generate_new_identity()
                                    identity.update(new_identity)
                                    print(f"[EMAIL] Новый email: {identity['email']}")

                                    # Задержка перед повтором
                                    await human_delay(1000, 2000)
                            break
                    except:
                        continue

            except Exception as e:
                print(f"[EMAIL] Ошибка попытки {attempt}: {e}")

        return False

    async def fill_password(self, identity: Dict) -> bool:
        """Заполняет пароль"""
        try:
            # Fluent UI селекторы для пароля
            password_selectors = [
                'input.fui-Input__input[type="password"]',  # Fluent UI
                'input[aria-label*="пароль" i]',  # украинский/русский
                'input[aria-label*="password" i]',  # английский
                'input[name="Пароль"]',  # украинский
                'input[name="Password"]',  # английский
                'input[type="password"]',  # универсальный
            ]

            password_selector = None
            for selector in password_selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        password_selector = selector
                        print(f"[PASSWORD] Найдено поле с селектором: {selector}")
                        break
                except:
                    continue

            if not password_selector:
                password_selector = 'input[type="password"]'  # fallback

            await self.page.wait_for_selector(password_selector, timeout=15000)
            await human_type(self.page, password_selector, identity["password"], typo_rate=0.03)
            await human_delay(300, 600)

            # Кнопка submit (специфичные селекторы!)
            submit_btn_selectors = [
                'button[data-testid="primaryButton"]',  # Fluent UI primary button
                'button.fui-Button[type="submit"]',
                'button#iSignupAction',
                'button[type="submit"]',
                'button:has-text("Далі")',
                'button:has-text("Next")',
            ]

            submit_btn = None
            for selector in submit_btn_selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        submit_btn = selector
                        break
                except:
                    continue

            if not submit_btn:
                submit_btn = 'button[type="submit"]'

            # Создаем локатор из селектора
            submit_btn_locator = self.page.locator(submit_btn)
            await human_click(self.page, submit_btn_locator)
            print("[PASSWORD] ✓ Введён")
            return True
        except Exception as e:
            print(f"[PASSWORD] Ошибка: {e}")
            return False

    async def fill_birthdate(self, identity: Dict) -> bool:
        """Заполняет дату рождения"""
        month = identity["birth_month"]
        day = identity["birth_day"]
        year = identity["birth_year"]
        month_name = MONTH_NAMES[month] if 1 <= month <= 12 else "January"

        print(f"[BIRTH] Заполняем: {month_name} {day}, {year}")

        try:
            # Fluent UI и стандартные селекторы для месяца
            month_selectors = [
                'button.fui-Button[aria-label*="місяць" i]',  # украинский
                'button.fui-Button[aria-label*="month" i]',  # английский
                'button.fui-Combobox__button',  # Fluent UI combobox
                'select#BirthMonth',
                'button#BirthMonthDropdown',
                '#DateOfBirthMonth',
            ]

            month_selector = None
            for selector in month_selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        month_selector = selector
                        break
                except:
                    continue

            if not month_selector:
                print("[BIRTH] Поле месяца не найдено!")
                return False

            await self.page.wait_for_selector(month_selector, timeout=15000)
            await human_delay(300, 500)

            # Месяц
            await self._select_month(month, month_name)
            await human_delay(200, 400)

            # День
            await self._select_day(day)
            await human_delay(200, 400)

            # Год
            await self._enter_year(year)
            await human_delay(300, 600)

            # Кнопка submit для даты рождения (специфичные селекторы!)
            submit_btn_selectors = [
                'button[data-testid="primaryButton"]',  # Fluent UI primary button
                'button.fui-Button[type="submit"]',
                'button#iSignupAction',
                'button[type="submit"]',
            ]

            submit_btn = None
            for selector in submit_btn_selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        submit_btn = selector
                        break
                except:
                    continue

            if not submit_btn:
                submit_btn = 'button[type="submit"]'

            submit_btn_locator = self.page.locator(submit_btn)
            await human_click(self.page, submit_btn_locator)
            print("[BIRTH] ✓ Дата введена")
            return True

        except Exception as e:
            print(f"[BIRTH] Ошибка: {e}")
            return False

    async def _select_month(self, month: int, month_name: str, month_name_ua: str = None):
        """Выбор месяца с расширенным поиском и дебагом текста опций"""
        print(f"[BIRTH] Выбор месяца: {month} ({month_name})")

        button_selectors = [
            'button#BirthMonthDropdown',
            '#BirthMonthDropdown',
            'button[aria-label*="місяць" i]',
            'button[aria-label*="month" i]',
        ]

        for btn_sel in button_selectors:
            try:
                button = await self.page.query_selector(btn_sel)
                if not button or not await button.is_visible():
                    continue

                print(f"[BIRTH] Найден dropdown: {btn_sel}")

                await button.focus()
                await button.click(delay=150, force=True)
                print(f"[BIRTH] Открываем dropdown")

                # Ждём popup
                await self.page.wait_for_selector('[role="listbox"], [role="option"]:visible', state="visible",
                                                  timeout=10000)
                print(f"[BIRTH] Popup открыт")

                await human_delay(500, 800)

                # Собираем ВСЕ опции и печатаем их текст для дебага
                options = await self.page.query_selector_all('[role="option"]')
                print(f"[BIRTH] Найдено {len(options)} опций. Тексты:")
                option_texts = []
                for opt in options:
                    text = await opt.text_content()  # Лучше inner_text — text_content игнорирует скрытые
                    clean_text = text.strip() if text else ""
                    option_texts.append(clean_text)
                    print(f"   - '{clean_text}'")

                if not options:
                    print("[BIRTH] Опции не найдены совсем!")
                    await self.page.keyboard.press('Escape')
                    continue

                # Ищем по точному совпадению, частичному, case-insensitive, и альтернативному названию (ua)
                target_names = [month_name]
                if month_name_ua:
                    target_names.append(month_name_ua)

                found_opt = None
                for opt in options:
                    text = await opt.text_content()
                    clean_text = text.strip().lower() if text else ""
                    for target in target_names:
                        if target.lower() == clean_text or target.lower() in clean_text:
                            found_opt = opt
                            print(f"[BIRTH] Найдена опция: '{text.strip()}' (цель: {target})")
                            break
                    if found_opt:
                        break

                if not found_opt:
                    print(f"[BIRTH] Опция не найдена среди: {option_texts}")
                    await self.page.keyboard.press('Escape')
                    continue

                # Кликаем надёжно
                await found_opt.scroll_into_view_if_needed()
                await found_opt.focus()
                await human_delay(100, 200)
                await found_opt.click(delay=150, force=True)
                print(f"[BIRTH] ✓ Месяц выбран: {await found_opt.text_content()}")

                # Закрываем popup на всякий случай
                try:
                    await self.page.wait_for_selector('[role="listbox"]', state="hidden", timeout=5000)
                except:
                    await self.page.keyboard.press('Escape')

                return

            except Exception as e:
                print(f"[BIRTH] Ошибка с селектором {btn_sel}: {e}")
                await self.page.keyboard.press('Escape')
                continue

        raise Exception("Не удалось выбрать месяц — опции не совпадают с ожидаемым текстом")

    async def _select_day(self, day: int):
        """Выбирает день"""
        print(f"[BIRTH] Выбор дня: {day}")

        selectors = [
            'button.fui-Button[aria-label*="день" i]',  # украинский Fluent UI
            'button.fui-Button[aria-label*="day" i]',  # английский Fluent UI
            'button.fui-Combobox__button:not([aria-label*="місяць" i]):not([aria-label*="month" i])',  # Fluent UI
            '#BirthDayDropdown',
            'button#BirthDayDropdown',
            'select#BirthDay'
        ]

        for sel in selectors:
            try:
                dropdown = await self.page.query_selector(sel)
                if not dropdown or not await dropdown.is_visible():
                    continue

                print(f"[BIRTH] Найден dropdown дня с селектором: {sel}")
                tag_name = await dropdown.evaluate("el => el.tagName.toLowerCase()")
                print(f"[BIRTH] Tag: {tag_name}")

                if tag_name == 'select':
                    await self.page.select_option(sel, value=str(day))
                    print(f"[BIRTH] День: {day} (через select)")
                    return

                # Открываем dropdown с разными методами
                try:
                    await dropdown.click(timeout=5000)
                    print(f"[BIRTH] Dropdown дня открыт (Playwright click)")
                except:
                    await dropdown.evaluate("el => el.click()")
                    print(f"[BIRTH] Dropdown дня открыт (JS click)")

                await human_delay(400, 700)

                # Пробуем разные селекторы для опций
                option_selectors = [
                    '[role="option"]',
                    '.fui-Option',
                    'li[role="option"]',
                    '[data-testid*="option"]',
                ]

                options = []
                for opt_sel in option_selectors:
                    options = await self.page.query_selector_all(opt_sel)
                    if options:
                        print(f"[BIRTH] Найдено {len(options)} опций дня с селектором: {opt_sel}")
                        break

                if not options:
                    print(f"[BIRTH] Опции дня не найдены!")
                    await self.page.keyboard.press('Escape')
                    continue

                for opt in options:
                    try:
                        text = (await opt.inner_text()).strip()
                        if text == str(day):
                            await opt.evaluate("el => el.click()")
                            print(f"[BIRTH] День: {day}")
                            return
                    except:
                        continue

                print(f"[BIRTH] День {day} не найден среди опций")
                await self.page.keyboard.press('Escape')
            except Exception as e:
                print(f"[BIRTH] Ошибка при выборе дня: {e}")
                continue

    async def _enter_year(self, year: int):
        """Вводит год"""
        print(f"[BIRTH] Ввод года: {year}")

        selectors = [
            'input.fui-Input__input[aria-label*="рік" i]',  # украинский Fluent UI
            'input.fui-Input__input[aria-label*="year" i]',  # английский Fluent UI
            'input.fui-Input__input[aria-label*="год" i]',  # русский Fluent UI
            'input[name="Рік"]',  # украинский
            'input[name="Year"]',  # английский
            'input#BirthYear',
            'input[name="BirthYear"]',
            'input#DateOfBirthYear'
        ]

        for sel in selectors:
            try:
                year_input = await self.page.query_selector(sel)
                if year_input and await year_input.is_visible():
                    print(f"[BIRTH] Найдено поле года с селектором: {sel}")
                    await year_input.click()
                    await human_delay(100, 200)
                    await year_input.fill('')
                    print(f"[BIRTH] Поле года очищено")

                    for char in str(year):
                        await self.page.keyboard.type(char, delay=random.randint(50, 120))

                    print(f"[BIRTH] Год: {year}")
                    return
            except Exception as e:
                print(f"[BIRTH] Ошибка при вводе года: {e}")
                continue

        print(f"[BIRTH] Поле года не найдено!")

    async def fill_name(self, identity: Dict) -> bool:
        """Заполняет имя и фамилию"""
        try:
            # Fluent UI селекторы для имени
            first_selectors = [
                'input.fui-Input__input[aria-label*="ім\'я" i]',  # украинский
                'input.fui-Input__input[aria-label*="first" i]',  # английский
                'input.fui-Input__input[aria-label*="имя" i]',  # русский
                'input[name="Ім\'я"]',  # украинский
                'input[name="FirstName"]',  # английский
                '[data-testid="firstNameInput"] input',
                'input#FirstName'
            ]

            # Fluent UI селекторы для фамилии
            last_selectors = [
                'input.fui-Input__input[aria-label*="прізвище" i]',  # украинский
                'input.fui-Input__input[aria-label*="last" i]',  # английский
                'input.fui-Input__input[aria-label*="фамилия" i]',  # русский
                'input[name="Прізвище"]',  # украинский
                'input[name="LastName"]',  # английский
                '[data-testid="lastNameInput"] input',
                'input#LastName'
            ]

            await random_mouse_movement(self.page, random.randint(1, 3))
            await human_delay(300, 700)

            # First name
            for sel in first_selectors:
                try:
                    el = await self.page.query_selector(sel)
                    if el and await el.is_visible():
                        await human_type(self.page, sel, identity["first"], typo_rate=0.05)
                        print(f"[NAME] First: {identity['first']}")
                        break
                except:
                    continue

            await human_delay(400, 800)
            await random_mouse_movement(self.page, random.randint(1, 2))

            # Last name
            for sel in last_selectors:
                try:
                    el = await self.page.query_selector(sel)
                    if el and await el.is_visible():
                        await human_type(self.page, sel, identity["last"], typo_rate=0.05)
                        print(f"[NAME] Last: {identity['last']}")
                        break
                except:
                    continue

            await human_delay(600, 1200)

            # Кнопка submit для имени (специфичные селекторы!)
            submit_btn_selectors = [
                'button[data-testid="primaryButton"]',  # Fluent UI primary button
                'button.fui-Button[type="submit"]',
                'button#iSignupAction',
                'button[type="submit"]',
                'button:has-text("Далі")',
                'button:has-text("Next")',
            ]

            submit_btn = None
            for selector in submit_btn_selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        submit_btn = selector
                        break
                except:
                    continue

            if not submit_btn:
                submit_btn = 'button[type="submit"]'

            # Создаем локатор из селектора
            submit_btn_locator = self.page.locator(submit_btn)
            await human_click(self.page, submit_btn_locator)
            print("[NAME] ✓ Имя введено")
            return True

        except Exception as e:
            print(f"[NAME] Ошибка: {e}")
            return False

