#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Основной класс создания аккаунтов Outlook
"""

import random
import string
import asyncio
from typing import Optional, Dict

from playwright.async_api import TimeoutError as PlaywrightTimeout

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

            # Инициализируем компоненты
            self.captcha_solver = CaptchaSolver(self.browser_manager.page)
            self.form_filler = FormFiller(self.browser_manager.page)
            

            # Генерируем личность
            identity = self.generate_identity()
            print(f"\n[IDENTITY] Email: {identity['email']}")
            print(f"[IDENTITY] Password: {identity['password']}")
            print(f"[IDENTITY] Name: {identity['first']} {identity['last']}")
            print(f"[IDENTITY] Birth: {identity['birth_month']}/{identity['birth_day']}/{identity['birth_year']}")

            # # === ПРОГРЕВ БРАУЗЕРА: Посещаем нейтральную страницу ===
            # print(f"\n[WARMUP] Прогрев браузера - посещаем Bing.com...")
            # try:
            #     await self.browser_manager.page.goto(
            #         "https://www.bing.com",
            #         wait_until="domcontentloaded",
            #         timeout=30000
            #     )
            #     print("[WARMUP] [+] Bing.com загружен")
            #
            #     # Применяем storage на нейтральной странице
            #     await self.browser_manager.apply_storage()
            #
            #     # Естественное поведение: задержка, движения мыши, скроллинг
            #     await human_delay(1500, 2500)
            #     await random_mouse_movement(self.browser_manager.page, random.randint(2, 4))
            #
            #     # Скроллинг
            #     await self.browser_manager.page.evaluate("window.scrollBy(0, 300)")
            #     await human_delay(800, 1200)
            #     await self.browser_manager.page.evaluate("window.scrollBy(0, -150)")
            #     await human_delay(500, 800)
            #
            #     print("[WARMUP] [+] Прогрев завершен")
            # except Exception as e:
            #     print(f"[WARMUP] Ошибка прогрева: {e}")

            # === ПРОГРЕВ БРАУЗЕРА: Посещаем нейтральную страницу ===
            print(f"\n[WARMUP] Прогрев браузера - посещаем www.microsoft.com...")
            try:
                await self.browser_manager.page.goto(
                    "https://www.microsoft.com",
                    wait_until="domcontentloaded",
                    timeout=30000
                )
                print("[WARMUP] [+] Bing.com загружен")

                # Применяем storage на нейтральной странице
                await self.browser_manager.apply_storage()

                await human_delay(1500, 2500)

                # Надёжный локатор кнопки входа
                signin_locator = self.browser_manager.page.locator('#mectrl_main_trigger')  # по ID — самый стабильный
                # Резервные варианты
                if await signin_locator.count() == 0:
                    signin_locator = self.browser_manager.page.get_by_role("link", name="Вхід")
                if await signin_locator.count() == 0:
                    signin_locator = self.browser_manager.page.locator('a:has-text("Вхід")')

                await human_click(self.browser_manager.page, signin_locator)

                print("[WARMUP] [+] Прогрев завершен")
            except Exception as e:
                print(f"[WARMUP] Ошибка прогрева: {e}")

            await human_delay(25500, 35500)

            # Теперь переходим на страницу регистрации
            print(f"\n[PAGE] Загрузка signup.live.com...")
            try:
                await self.browser_manager.page.goto(
                    SIGNUP_URL,
                    wait_until="domcontentloaded",
                    timeout=60000
                )
            except PlaywrightTimeout:
                print("[PAGE] Таймаут загрузки, продолжаем...")

            # СРАЗУ проверяем что загрузилось
            print(f"[PAGE] URL после загрузки: {self.browser_manager.page.url}")

            try:
                page_title = await self.browser_manager.page.title()
                print(f"[PAGE] Заголовок: {page_title}")

                # Проверяем текст страницы на блокировку
                body_text = await self.browser_manager.page.inner_text('body')
                if 'suspicious' in body_text.lower() or 'unusual' in body_text.lower() or 'detected' in body_text.lower():
                    print(f"[PAGE] [!] ОБНАРУЖЕНА БЛОКИРОВКА!")
                    print(f"[PAGE] Текст: {body_text[:1000]}")

                    # Скриншот блокировки
                    try:
                        await self.browser_manager.page.screenshot(path="C:\\projects\\outlook_block_screenshot.png")
                        print("[PAGE] Скриншот блокировки сохранен: outlook_block_screenshot.png")
                    except:
                        pass

                    return None
                else:
                    print(f"[PAGE] Текст страницы выглядит нормально (первые 200 символов): {body_text[:200]}")
            except Exception as e:
                print(f"[PAGE] Ошибка проверки страницы: {e}")

            # Ждём форму
            try:
                await self.browser_manager.page.wait_for_selector(
                    'input[name="MemberName"], input[type="email"]',
                    timeout=130000
                )
            except PlaywrightTimeout:
                print("[PAGE] [!] Форма не загрузилась - проверяем что показывается")
                print(f"[PAGE] Текущий URL: {self.browser_manager.page.url}")

                # Проверяем заголовок страницы
                try:
                    title = await self.browser_manager.page.title()
                    print(f"[PAGE] Заголовок: {title}")
                except:
                    pass

                # Проверяем текст на странице
                try:
                    body_text = await self.browser_manager.page.inner_text('body')
                    if 'suspicious' in body_text.lower() or 'unusual' in body_text.lower():
                        print("[PAGE] [!] ОБНАРУЖЕНА БЛОКИРОВКА ПО ПОДОЗРИТЕЛЬНОЙ АКТИВНОСТИ!")
                        print(f"[PAGE] Текст: {body_text[:500]}")
                    elif 'captcha' in body_text.lower() or 'verify' in body_text.lower():
                        print("[PAGE] [!] Требуется капча/верификация")
                        print(f"[PAGE] Текст: {body_text[:500]}")
                    else:
                        print(f"[PAGE] Текст страницы (первые 300 символов): {body_text[:300]}")
                except Exception as e:
                    print(f"[PAGE] Ошибка получения текста: {e}")

                return None

            print(f"[PAGE] URL: {self.browser_manager.page.url}")
            await human_delay(PAGE_DELAY[0], PAGE_DELAY[1])
            await random_mouse_movement(self.browser_manager.page, random.randint(1, 4))

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
                await self.browser_manager.page.wait_for_selector(
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
            final_url = self.browser_manager.page.url.lower()
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
                    if not self.browser_manager.page or self.browser_manager.page.is_closed():
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


