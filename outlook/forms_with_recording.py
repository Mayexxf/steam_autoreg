#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Заполнение форм с поддержкой записанных движений мыши
Расширенная версия FormFiller
"""

import random
from typing import Dict, Optional
from pathlib import Path

from playwright.async_api import Page

from outlook.utils import human_type, human_click, human_delay, random_mouse_movement
from outlook.config import MONTH_NAMES

# Опциональный импорт mouse_player
try:
    from outlook.mouse_player import HumanBehavior
    MOUSE_RECORDING_AVAILABLE = True
except ImportError:
    MOUSE_RECORDING_AVAILABLE = False


class FormFillerWithRecording:
    """
    Заполнение форм с возможностью использования записанных движений мыши
    """

    def __init__(self, page: Page, recording_file: Optional[str] = None):
        """
        Args:
            page: Playwright Page
            recording_file: Путь к файлу с записью движений мыши (опционально)
        """
        self.page = page
        self.recording_file = recording_file
        self.use_recording = False

        # Проверяем доступность записанных движений
        if recording_file and Path(recording_file).exists() and MOUSE_RECORDING_AVAILABLE:
            self.human = HumanBehavior(page, recording_file)
            self.use_recording = True
            print(f"[FORM] 🎬 Используем записанные движения: {recording_file}")
        else:
            self.human = None
            if recording_file:
                print(f"[FORM] ⚠️  Файл записи не найден или mouse_player недоступен")
                print(f"[FORM] Используем стандартные Bezier движения")

    async def _type(self, selector: str, text: str, typo_rate: float = 0.02):
        """Печатает текст (с записанными движениями или стандартно)"""
        if self.use_recording and self.human:
            await self.human.type_like_human(selector, text)
        else:
            await human_type(self.page, selector, text, typo_rate=typo_rate)

    async def _click(self, selector: str, timeout: int = 10000):
        """Кликает (с записанными движениями или стандартно)"""
        if self.use_recording and self.human:
            await self.human.click_like_human(selector)
        else:
            await human_click(self.page, selector, timeout=timeout)

    async def _scroll(self, direction: str = 'down', amount: int = 300):
        """Скроллит (с записанными движениями или стандартно)"""
        if self.use_recording and self.human:
            await self.human.scroll_like_human(direction, amount)
        else:
            # Стандартный скролл
            delta = amount if direction == 'down' else -amount
            await self.page.mouse.wheel(0, delta)
            await human_delay(100, 300)

    async def fill_email(self, identity: Dict, generate_new_identity) -> bool:
        """Заполняет email с проверкой занятости"""
        max_attempts = 5

        for attempt in range(1, max_attempts + 1):
            try:
                email_selector = 'input[name="MemberName"], input#MemberName, input[type="email"]'
                await self.page.wait_for_selector(email_selector, timeout=15000)

                if attempt > 1:
                    await self.page.fill(email_selector, '')
                    await human_delay(200, 400)

                # Используем записанные движения или стандартный ввод
                await self._type(email_selector, identity["email"], typo_rate=0.05)
                await human_delay(300, 600)

                next_btn = 'button#iSignupAction, button[type="submit"]'
                await self._click(next_btn)
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
            await self._type('input[type="password"]', identity["password"], typo_rate=0.03)
            await human_delay(300, 600)

            await self._click('button#iSignupAction, button[type="submit"]')
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
            # Месяц
            await self.page.wait_for_selector(
                'select#BirthMonth, button#BirthMonthDropdown, #DateOfBirthMonth',
                timeout=15000
            )

            month_selector = await self.page.query_selector('select#BirthMonth')
            if month_selector:
                await self._click('select#BirthMonth')
                await human_delay(200, 400)
                await self.page.select_option('select#BirthMonth', value=str(month))
            else:
                await self._click('#BirthMonthDropdown, #DateOfBirthMonth')
                await human_delay(300, 500)
                await self._click(f'text="{month_name}"')

            await human_delay(200, 400)

            # День
            day_selector = await self.page.query_selector('input#BirthDay, input#DateOfBirthDay')
            if day_selector:
                await self._type('input#BirthDay, input#DateOfBirthDay', str(day))

            await human_delay(200, 400)

            # Год
            year_selector = await self.page.query_selector('input#BirthYear, input#DateOfBirthYear')
            if year_selector:
                await self._type('input#BirthYear, input#DateOfBirthYear', str(year))

            await human_delay(300, 600)

            # Кнопка Next
            await self._click('button#iSignupAction, button[type="submit"]')
            print("[BIRTH] ✓ Введена дата")
            return True

        except Exception as e:
            print(f"[BIRTH] Ошибка: {e}")
            return False

    async def handle_phone_verification(self) -> bool:
        """Обрабатывает верификацию по телефону (если требуется)"""
        try:
            # Проверяем наличие поля телефона
            phone_field = await self.page.query_selector(
                'input[type="tel"], input#Phone, input[name="PhoneNumber"]',
                timeout=3000
            )

            if phone_field and await phone_field.is_visible():
                print("[PHONE] Требуется верификация по телефону")
                print("[PHONE] ⚠️  Автоматическая обработка не реализована")
                return False

            return True

        except Exception:
            return True  # Нет поля телефона - продолжаем


# Пример использования
async def example_usage():
    """Пример использования FormFillerWithRecording"""
    from outlook.browser import BrowserManager

    browser = BrowserManager(
        proxy="MPzEefwWaIUi:tc6aWZqR@pool.proxy.market:10000",
        headless=False
    )

    try:
        await browser.setup()
        await browser.page.goto("https://signup.live.com/")

        # Вариант 1: Без записанных движений (стандартные Bezier)
        form_filler = FormFillerWithRecording(browser.page)

        # Вариант 2: С записанными движениями
        # form_filler = FormFillerWithRecording(
        #     browser.page,
        #     recording_file='outlook_signup_movements.json'
        # )

        identity = {
            "email": "test12345@outlook.com",
            "password": "TestPassword123!",
            "birth_month": 6,
            "birth_day": 15,
            "birth_year": 1990
        }

        await form_filler.fill_email(identity, lambda: identity)
        await form_filler.fill_password(identity)
        await form_filler.fill_birthdate(identity)

    finally:
        await browser.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
