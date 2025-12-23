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
                email_selector = self.page.get_by_role("textbox", name="Електронна пошта")
                await email_selector.wait_for(state="visible", timeout=20000)

                if attempt > 1:
                    print(f"[EMAIL] Повторный ввод")
                    await email_selector.fill("")
                    await human_delay(200, 400)

                await human_type(self.page, email_selector, identity["email"], typo_rate=0.05)
                await human_delay(300, 600)

                create_locator = self.page.get_by_role("button", name="Далі")
                await human_click(self.page, create_locator)
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

                error_selectors = ['#MemberNameError',
                                   '.alert-error', '[role="alert"]']
                for sel in error_selectors:
                    try:
                        error_el = await self.page.query_selector(sel)
                        if error_el and await error_el.is_visible():
                            error_text = await error_el.inner_text()
                            if error_text:
                                print(f"[EMAIL] Ошибка: {error_text[:60]}")
                                if any(kw in error_text.lower() for kw in ['taken', 'already', 'exist']):
                                    identity.update(generate_new_identity())
                                    print(
                                        f"[EMAIL] Новый: {identity['email']}")
                            break
                    except:
                        continue

            except Exception as e:
                print(f"[EMAIL] Ошибка попытки {attempt}: {e}")

        return False

    async def fill_password(self, identity: Dict) -> bool:
        """Заполняет пароль"""
        try:
            await self.page.wait_for_selector('input[type="password"]', timeout=15000)
            await human_type(self.page, 'input[type="password"]', identity["password"], typo_rate=0.03)
            await human_delay(300, 600)

            await human_click(self.page, 'button#iSignupAction, button[type="submit"]')
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
            await self.page.wait_for_selector(
                'select#BirthMonth, button#BirthMonthDropdown, #DateOfBirthMonth',
                timeout=15000
            )
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

            await human_click(self.page, 'button#iSignupAction, button[type="submit"]')
            print("[BIRTH] ✓ Дата введена")
            return True

        except Exception as e:
            print(f"[BIRTH] Ошибка: {e}")
            return False

    async def _select_month(self, month: int, month_name: str):
        """Выбирает месяц"""
        selectors = ['#BirthMonthDropdown',
                     'button#BirthMonthDropdown', 'select#BirthMonth']

        for sel in selectors:
            try:
                dropdown = await self.page.query_selector(sel)
                if not dropdown or not await dropdown.is_visible():
                    continue

                tag_name = await dropdown.evaluate("el => el.tagName.toLowerCase()")

                if tag_name == 'select':
                    await self.page.select_option(sel, value=str(month))
                    print(f"[BIRTH] Месяц: {month}")
                    return

                await dropdown.evaluate("el => el.click()")
                await human_delay(400, 700)

                options = await self.page.query_selector_all('[role="option"]')
                for opt in options:
                    try:
                        text = (await opt.inner_text()).strip()
                        if text == month_name or month_name.lower() in text.lower():
                            await opt.evaluate("el => el.click()")
                            print(f"[BIRTH] Месяц: {text}")
                            return
                    except:
                        continue

                await self.page.keyboard.press('Escape')
            except:
                continue

    async def _select_day(self, day: int):
        """Выбирает день"""
        selectors = ['#BirthDayDropdown',
                     'button#BirthDayDropdown', 'select#BirthDay']

        for sel in selectors:
            try:
                dropdown = await self.page.query_selector(sel)
                if not dropdown or not await dropdown.is_visible():
                    continue

                tag_name = await dropdown.evaluate("el => el.tagName.toLowerCase()")

                if tag_name == 'select':
                    await self.page.select_option(sel, value=str(day))
                    print(f"[BIRTH] День: {day}")
                    return

                await dropdown.evaluate("el => el.click()")
                await human_delay(400, 700)

                options = await self.page.query_selector_all('[role="option"]')
                for opt in options:
                    try:
                        text = (await opt.inner_text()).strip()
                        if text == str(day):
                            await opt.evaluate("el => el.click()")
                            print(f"[BIRTH] День: {day}")
                            return
                    except:
                        continue

                await self.page.keyboard.press('Escape')
            except:
                continue

    async def _enter_year(self, year: int):
        """Вводит год"""
        selectors = ['input#BirthYear',
                     'input[name="BirthYear"]', 'input#DateOfBirthYear']

        for sel in selectors:
            try:
                year_input = await self.page.query_selector(sel)
                if year_input and await year_input.is_visible():
                    await year_input.click()
                    await human_delay(100, 200)
                    await year_input.fill('')
                    for char in str(year):
                        await self.page.keyboard.type(char, delay=random.randint(50, 120))
                    print(f"[BIRTH] Год: {year}")
                    return
            except:
                continue

    async def fill_name(self, identity: Dict) -> bool:
        """Заполняет имя и фамилию"""
        try:
            first_selectors = [
                '[data-testid="firstNameInput"] input',
                'input[name="FirstName"]',
                'input#FirstName'
            ]
            last_selectors = [
                '[data-testid="lastNameInput"] input',
                'input[name="LastName"]',
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
            await human_click(self.page, 'button#iSignupAction, button[type="submit"]')
            print("[NAME] ✓ Имя введено")
            return True

        except Exception as e:
            print(f"[NAME] Ошибка: {e}")
            return False

