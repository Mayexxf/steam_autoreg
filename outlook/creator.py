#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Основной класс создания аккаунтов Outlook
"""

import random
import re
import string
import asyncio
from typing import Optional, Dict

from playwright.async_api import TimeoutError as PlaywrightTimeout, expect

from src.utils.mouse_emulator import HumanMouseEmulator
from .config import (
    HARDCODED_PROXY, PAGE_DELAY, FIRST_NAMES, LAST_NAMES, MONTH_NAMES,
    SIGNUP_URL
)
from .utils import human_delay, random_mouse_movement, human_click
from .browser import BrowserManager
from .captcha import CaptchaSolver
from .forms import FormFiller

# Mobile proxy support
try:
    from src.proxy.mobileproxy_manager import MobileProxyManager
    MOBILEPROXY_AVAILABLE = True
except ImportError:
    MOBILEPROXY_AVAILABLE = False


class OutlookCreator:
    """Создание аккаунтов Outlook с полным stealth"""

    def __init__(self, proxy: str = None, headless: bool = False, rotate_ip: bool = False):
        self.proxy = proxy or HARDCODED_PROXY
        self.headless = headless
        self.rotate_ip = rotate_ip
        
        self.browser_manager: Optional[BrowserManager] = None
        self.captcha_solver: Optional[CaptchaSolver] = None
        self.form_filler: Optional[FormFiller] = None
        self.proxy_manager = None

        # Инициализируем MobileProxyManager если доступен
        if MOBILEPROXY_AVAILABLE and self.rotate_ip:
            try:
                self.proxy_manager = MobileProxyManager()
                print("[PROXY] [+] MobileProxyManager initialized")
            except Exception as e:
                print(f"[PROXY] MobileProxyManager failed: {e}")

    @staticmethod
    def generate_identity() -> Dict:
        """Генерирует случайную личность"""
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        suffix = random.randint(1000, 9999)
        username = f"{first.lower()}{last.lower()}{suffix}"

        password_chars = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(random.choices(password_chars, k=16))

        year = random.randint(1980, 2000)
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

    async def _rotate_ip(self) -> bool:
        """Ротирует IP мобильного прокси"""
        if not self.proxy_manager:
            return False

        print("\n" + "=" * 60)
        print("[PROXY] РОТАЦИЯ IP ПЕРЕД РЕГИСТРАЦИЕЙ")
        print("=" * 60)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.proxy_manager.change_ip_and_get_geo(wait_time=5)
        )

        if result.get('success'):
            new_ip = result.get('new_ip', 'unknown')
            geo = result.get('geo', {})
            print(f"[PROXY] [+] Новый IP: {new_ip}")
            if geo.get('country'):
                print(f"[PROXY] [+] Страна: {geo['country']}, {geo.get('city', '')}")
            
            if geo.get('success'):
                self.browser_manager.geo_config = geo
            return True
        else:
            print(f"[PROXY] ✗ Ротация не удалась: {result.get('message', 'unknown error')}")
            return False

    async def create_account(self) -> Optional[Dict]:
        """Основной метод создания аккаунта"""
        print("=" * 60)
        print("Outlook Account Creator (PLAYWRIGHT + STEALTH)")
        print("=" * 60)

        try:
            # Инициализируем браузер
            self.browser_manager = BrowserManager(
                proxy=self.proxy,
                headless=self.headless
            )

            # Ротация IP (если доступна)
            if self.rotate_ip and self.proxy_manager:
                await self._rotate_ip()

            # Настраиваем браузер
            await self.browser_manager.setup()
            page = self.browser_manager.page

            # Инициализируем компоненты
            self.captcha_solver = CaptchaSolver(page)
            self.form_filler = FormFiller(page)
            

            # Генерируем личность
            identity = self.generate_identity()
            print(f"\n[IDENTITY] Email: {identity['email']}")
            print(f"[IDENTITY] Password: {identity['password']}")
            print(f"[IDENTITY] Name: {identity['first']} {identity['last']}")
            print(f"[IDENTITY] Birth: {identity['birth_month']}/{identity['birth_day']}/{identity['birth_year']}")

            # === ПРОГРЕВ БРАУЗЕРА: Посещаем нейтральную страницу ===
            print(f"\n[WARMUP] Прогрев браузера - посещаем www.microsoft.com...")
            try:
                await page.goto(
                    "https://www.microsoft.com",
                    wait_until="domcontentloaded",
                    timeout=30000
                )
                print("[WARMUP] [+] Bing.com загружен")

                # Применяем storage на нейтральной странице
                await self.browser_manager.apply_storage()

                await human_delay(3500, 7500)

                # Надёжный локатор кнопки входа
                signin_locator = page.get_by_role("link", name="Увійдіть у свій обліковий запис")
                # Fallback 1: как button
                if await signin_locator.count() == 0:
                    signin_locator = page.get_by_role("link", name="Create free account")
                # Fallback 2: по уникальному href (актуальный linkid для signup 2025)
                if await signin_locator.count() == 0:
                    signin_locator = page.locator('a[href*="linkid=2125440"], a[href*="signup.live.com"]')

                # Чтобы избежать strict violation — берём первый видимый (или nth, если нужно)
                signin_locator = signin_locator.first  # <--- КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ!

                await human_delay(1500, 2500)
                await human_click(page, signin_locator)

                print("[WARMUP] [+] Прогрев завершен")
            except Exception as e:
                print(f"[WARMUP] Ошибка прогрева: {e}")

            # Теперь переходим на страницу регистрации
            print(f"\n[PAGE] Переходим на login.live.com...")
            await human_delay(3000, 5000)

            try:
                print(f"\n[PAGE] Поиск кнопки создания аккаунта")
                # Основной локатор: по полному тексту как link (самый частый вариант)
                create_account_locator = page.get_by_role("button", name="Створити обліковий запис")

                # Fallback 1: как button
                if await create_account_locator.count() == 0:
                    print(f"\n[ERROR] Fallback 1: Не удалось найти кнопку по имени")
                    create_account_locator = page.get_by_role(
                        "button",
                        name=re.compile(r"Створити.*обліковий запис|Create.*account", re.IGNORECASE)
                    )

                # Fallback 2: по частичному тексту (has-text)
                if await create_account_locator.count() == 0:
                    print(f"\n[ERROR] Fallback 2")
                    create_account_locator = page.get_by_text(
                        re.compile(r"Створити|Create", re.IGNORECASE)
                    ).filter(has_text=re.compile(r"обліковий запис|account|free", re.IGNORECASE))

                # Fallback 3: по известной ссылке (часто ведёт на signup)
                if await create_account_locator.count() == 0:
                    print(f"\n[ERROR] Fallback 3")
                    create_account_locator = page.locator(
                        'a[href*="signup.live.com"], a[href*="go.microsoft.com/fwlink"]')

                # Обязательная проверка + дебаг
                if await create_account_locator.count() == 0:
                    await page.screenshot(path="./screens/error_no_create_button.png", full_page=True)
                    print("[ERROR] Кнопка создания аккаунта НЕ НАЙДЕНА!")
                    title = await page.title()
                    print(f"[DEBUG] Title: {title}")
                    print(f"[DEBUG] URL: {page.url}")
                    raise Exception("Create account button not found")

                print("[WARMUP] [+] Кнопка создания аккаунта найдена")
            except Exception as e:
                print(f"[WARMUP] Ошибка поиска кнопки: {e}")

            # Ждём видимости и кликаем по-человечески
            await create_account_locator.first.wait_for(state="visible", timeout=20000)
            await human_click(page, create_account_locator)

            await human_delay(3000, 5000)  # Больше задержка — редирект и загрузка формы

            # Ждём форму
            # try:
            #     await page.wait_for_selector(
            #         'input[name="Електронна пошта"], input[type="email"]',
            #         timeout=130000
            #     )
            # except PlaywrightTimeout:
            #     print("[PAGE] [!] Форма не загрузилась - проверяем что показывается")
            #     print(f"[PAGE] Текущий URL: {page.url}")
            #
            #     # Проверяем заголовок страницы
            #     try:
            #         title = await page.title()
            #         print(f"[PAGE] Заголовок: {title}")
            #     except:
            #         pass
            #
            #     # Проверяем текст на странице
            #     try:
            #         body_text = await page.inner_text('body')
            #         if 'suspicious' in body_text.lower() or 'unusual' in body_text.lower():
            #             print("[PAGE] [!] ОБНАРУЖЕНА БЛОКИРОВКА ПО ПОДОЗРИТЕЛЬНОЙ АКТИВНОСТИ!")
            #             print(f"[PAGE] Текст: {body_text[:500]}")
            #         elif 'captcha' in body_text.lower() or 'verify' in body_text.lower():
            #             print("[PAGE] [!] Требуется капча/верификация")
            #             print(f"[PAGE] Текст: {body_text[:500]}")
            #         else:
            #             print(f"[PAGE] Текст страницы (первые 300 символов): {body_text[:300]}")
            #     except Exception as e:
            #         print(f"[PAGE] Ошибка получения текста: {e}")
            #
            #     return None
            #
            # print(f"[PAGE] URL: {page.url}")
            await human_delay(PAGE_DELAY[0], PAGE_DELAY[1])
            await random_mouse_movement(page, random.randint(1, 4))

            # === ШАГ 1: Email ===
            print("\n[STEP 1] Ввод email...")
            if not await self.form_filler.fill_email(identity, self.generate_identity):
                print("[ERROR] Не удалось ввести email")
                return None

            await human_delay(700, 1200)

            # === ШАГ 2: Password ===
            print("\n[STEP 2] Ввод пароля...")
            if not await self.form_filler.fill_password(identity):
                print("[ERROR] Не удалось ввести пароль")
                return None

            await human_delay(700, 1200)

            # === ШАГ 3: Определяем следующий шаг ===
            print("\n[STEP 3] Определяем следующий шаг...")
            await self._handle_next_step(identity)

            # === ШАГ 4: Дата рождения ===
            print("\n[STEP 4] Дата рождения...")
            try:
                await page.wait_for_selector(
                    'button#BirthMonthDropdown, select#BirthMonth',
                    timeout=15000
                )
                if not await self.form_filler.fill_birthdate(identity):
                    print("[ERROR] Не удалось ввести дату")
                    return None
            except PlaywrightTimeout:
                print("[STEP 4] Поля даты не найдены, пропускаем")

            await human_delay(700, 1200)

            # === ШАГ 5: Имя ===
            print("\n[STEP 5] Проверяем поля имени...")
            await self._handle_name_step(identity)

            await human_delay(500, 800)

            # === ШАГ 6: Капча ===
            print("\n[STEP 6] ПРОВЕРКА КАПЧИ")
            await asyncio.sleep(2)
            await self.captcha_solver.check_and_solve()

            # === ШАГ 7: Пост-регистрация ===
            print("\n[STEP 7] Обработка пост-регистрационных окон...")
            await self._handle_post_registration()

            # Проверяем результат
            final_url = page.url.lower()
            if 'outlook' in final_url or 'office' in final_url or 'mail' in final_url:
                print("\n" + "=" * 60)
                print("[SUCCESS] [+] Аккаунт создан!")
                print("=" * 60)

            return identity

        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()
            return None

        finally:
            # Ждём закрытия браузера пользователем
            print("\n" + "=" * 60)
            print("[INFO] Браузер остаётся открытым.")
            print("[INFO] Закройте окно браузера или нажмите Ctrl+C для выхода.")
            print("=" * 60)

            try:
                while True:
                    await asyncio.sleep(1)
                    if not page or page.is_closed():
                        print("[INFO] Окно браузера закрыто пользователем")
                        break
            except (KeyboardInterrupt, asyncio.CancelledError):
                print("\n[INFO] Получен сигнал завершения")
            finally:
                print("[INFO] Закрытие браузера...")
                await self.browser_manager.close()

    async def _handle_next_step(self, identity: Dict):
        """Определяет следующий шаг после пароля"""
        for _ in range(20):
            # Проверяем поля имени
            name_el = await self.browser_manager.page.query_selector(
                '[data-testid="firstNameInput"], input[name="FirstName"]'
            )
            if name_el and await name_el.is_visible():
                print("[STEP 3] Заполняем имя...")
                if not await self.form_filler.fill_name(identity):
                    return
                await human_delay(500, 800)

            # Проверяем поля даты
            birth_el = await self.browser_manager.page.query_selector(
                'button#BirthMonthDropdown, select#BirthMonth'
            )
            if birth_el and await birth_el.is_visible():
                print("[STEP 3] Сразу дата рождения")
                return

            await asyncio.sleep(0.5)

        print("[STEP 3] Неизвестный шаг")

    async def _handle_name_step(self, identity: Dict):
        """Обрабатывает шаг ввода имени"""
        for _ in range(10):
            name_el = await self.browser_manager.page.query_selector(
                '[data-testid="firstNameInput"], input[name="FirstName"]'
            )
            if name_el and await name_el.is_visible():
                print("[STEP 5] Заполняем имя...")
                await self.form_filler.fill_name(identity)

                # Проверяем блокировку
                await asyncio.sleep(2)
                block_error = await self.captcha_solver.check_block_error()
                if block_error:
                    print(f"\n[BLOCK] [!] {block_error}")
                    print("[BLOCK] Microsoft детектировал автоматизацию!")
                return
            await asyncio.sleep(1)

        print("[STEP 5] Поля имени не найдены")

    async def _handle_post_registration(self):
        """Обрабатывает пост-регистрационные диалоги"""
        print("\n[POST-REG] Обработка пост-регистрационных окон...")

        for _ in range(10):
            try:
                body_text = await self.browser_manager.page.inner_text('body')
                body_lower = body_text.lower()

                # Кнопки закрытия
                skip_selectors = [
                    'button:has-text("Skip")',
                    'button:has-text("No thanks")',
                    'button:has-text("Not now")',
                    'button:has-text("Maybe later")',
                    '[aria-label*="Close"]',
                    '[aria-label*="Dismiss"]',
                ]

                for sel in skip_selectors:
                    try:
                        btn = await self.browser_manager.page.query_selector(sel)
                        if btn and await btn.is_visible():
                            await btn.click()
                            await asyncio.sleep(1)
                            break
                    except:
                        continue

                await asyncio.sleep(1)

            except Exception as e:
                print(f"[POST-REG] Ошибка: {e}")

        print("[POST-REG] Диалоги обработаны")


