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

            # === ШАГ 1: Посещаем Microsoft.com ===
            print(f"\n[NAVIGATION] Шаг 1: Посещаем www.microsoft.com...")
            try:
                await self.browser_manager.page.goto(
                    "https://www.microsoft.com",
                    wait_until="domcontentloaded",
                    timeout=30000
                )
                print("[NAVIGATION] [+] Microsoft.com загружен")

                # Применяем storage
                await self.browser_manager.apply_storage()

                # Эмулируем человеческое поведение
                await human_delay(2000, 3500)
                await random_mouse_movement(self.browser_manager.page, random.randint(2, 4))

                # Легкий скроллинг
                await self.browser_manager.page.evaluate("window.scrollBy(0, 200)")
                await human_delay(800, 1500)

            except Exception as e:
                print(f"[NAVIGATION] Ошибка загрузки Microsoft.com: {e}")
                return None

            # === ШАГ 2: Кликаем "Войти" ===
            print("\n[NAVIGATION] Шаг 2: Нажимаем кнопку 'Войти'...")
            try:
                # Ищем кнопку входа (несколько вариантов локаторов)
                signin_locator = None

                # Попытка 1: По ID
                if await self.browser_manager.page.locator('#mectrl_main_trigger').count() > 0:
                    signin_locator = self.browser_manager.page.locator('#mectrl_main_trigger')
                # Попытка 2: По тексту (разные языки)
                elif await self.browser_manager.page.locator('a:has-text("Sign in")').count() > 0:
                    signin_locator = self.browser_manager.page.locator('a:has-text("Sign in")')
                elif await self.browser_manager.page.locator('a:has-text("Войти")').count() > 0:
                    signin_locator = self.browser_manager.page.locator('a:has-text("Войти")')
                elif await self.browser_manager.page.locator('a:has-text("Вхід")').count() > 0:
                    signin_locator = self.browser_manager.page.locator('a:has-text("Вхід")')

                if signin_locator:
                    # Движение мыши к кнопке перед кликом
                    await random_mouse_movement(self.browser_manager.page, 1)
                    await human_delay(500, 1000)

                    # Кликаем
                    await human_click(self.browser_manager.page, signin_locator)
                    print("[NAVIGATION] [+] Кнопка 'Войти' нажата")

                    # Ждем загрузки формы входа
                    await human_delay(2500, 4000)
                else:
                    print("[NAVIGATION] [!] Кнопка 'Войти' не найдена")
                    return None

            except Exception as e:
                print(f"[NAVIGATION] Ошибка при клике на 'Войти': {e}")
                return None

            # === ШАГ 3: Кликаем "Создать учетную запись" ===
            print("\n[NAVIGATION] Шаг 3: Нажимаем 'Создать учетную запись'...")
            try:
                # Ждем появления формы входа
                await self.browser_manager.page.wait_for_load_state("domcontentloaded", timeout=15000)

                # Эмулируем чтение страницы и изучение контента
                await human_delay(1500, 2500)
                await random_mouse_movement(self.browser_manager.page, random.randint(1, 3))

                # Легкий скроллинг (как будто пользователь смотрит на страницу)
                await self.browser_manager.page.evaluate("window.scrollBy(0, 100)")
                await human_delay(500, 1000)
                await self.browser_manager.page.evaluate("window.scrollBy(0, -50)")
                await human_delay(300, 700)

                # Ищем ссылку/кнопку "Create account" / "Створити обліковий запис"
                create_account_locator = None

                # Различные варианты локаторов (Fluent UI и стандартные)
                possible_selectors = [
                    # Родительские ссылки <a>, содержащие span с текстом (ПРИОРИТЕТ!)
                    'a:has(span:has-text("Створити обліковий запис"))',
                    'a:has(span:has-text("Create account"))',
                    'a:has(span:has-text("Создать"))',
                    'a:has(span.fui-Link:has-text("Створити"))',

                    # Fluent UI span/button с точным текстом на разных языках
                    'span.fui-Link:has-text("Створити обліковий запис")',
                    'span[role="button"]:has-text("Створити")',
                    'span.fui-Link:has-text("Create account")',
                    'span[role="button"]:has-text("Create")',
                    'span.fui-Link:has-text("Создать")',
                    'span[role="button"]:has-text("Создать")',

                    # Стандартные ссылки
                    'a:has-text("Create one")',
                    'a:has-text("Create account")',
                    'a:has-text("Sign up now")',
                    'a:has-text("Створити")',
                    'a:has-text("Создать")',
                    'a[href*="signup"]',
                    '#signup-link',
                ]

                for selector in possible_selectors:
                    try:
                        if await self.browser_manager.page.locator(selector).count() > 0:
                            create_account_locator = self.browser_manager.page.locator(selector).first
                            print(f"[NAVIGATION] Найден элемент с селектором: {selector}")
                            break
                    except Exception as e:
                        continue

                # Если не нашли точным селектором, пробуем универсальный поиск по role="button"
                if not create_account_locator:
                    print("[NAVIGATION] Пробуем универсальный поиск по role='button'...")
                    try:
                        all_buttons = await self.browser_manager.page.locator('span[role="button"], a[role="button"]').all()
                        for button in all_buttons:
                            text = await button.inner_text()
                            if any(keyword in text.lower() for keyword in ['створити', 'create', 'создать', 'sign up', 'signup']):
                                create_account_locator = button
                                print(f"[NAVIGATION] Найдена кнопка с текстом: {text}")
                                break
                    except Exception as e:
                        print(f"[NAVIGATION] Ошибка универсального поиска: {e}")

                if create_account_locator:
                    # Диагностика элемента
                    try:
                        is_visible = await create_account_locator.is_visible()
                        is_enabled = await create_account_locator.is_enabled()
                        text = await create_account_locator.inner_text()
                        tag_name = await create_account_locator.evaluate('el => el.tagName')
                        outer_html = await create_account_locator.evaluate('el => el.outerHTML')

                        print(f"[NAVIGATION] Элемент: visible={is_visible}, enabled={is_enabled}, text='{text}'")
                        print(f"[NAVIGATION] Tag: {tag_name}")
                        print(f"[NAVIGATION] HTML (первые 200 символов): {outer_html[:200]}")
                    except Exception as e:
                        print(f"[NAVIGATION] Ошибка диагностики элемента: {e}")

                    # Сохраняем URL до клика для проверки
                    url_before = self.browser_manager.page.url

                    # Движение мыши перед кликом
                    await random_mouse_movement(self.browser_manager.page, 1)
                    await human_delay(700, 1500)

                    # Пробуем несколько методов клика
                    clicked = False

                    # Метод 1: human_click (плавный с мышью)
                    try:
                        print("[NAVIGATION] Попытка 1: human_click...")
                        await human_click(self.browser_manager.page, create_account_locator)
                        await human_delay(1000, 1500)

                        # Проверяем, изменился ли URL
                        if self.browser_manager.page.url != url_before:
                            print("[NAVIGATION] [+] Клик сработал (URL изменился)")
                            clicked = True
                    except Exception as e:
                        print(f"[NAVIGATION] human_click не сработал: {e}")
                        # Проверяем URL даже при ошибке (навигация могла начаться)
                        await human_delay(1000, 1500)
                        if self.browser_manager.page.url != url_before:
                            print("[NAVIGATION] [+] human_click сработал (URL изменился несмотря на ошибку)")
                            clicked = True

                    # Метод 2: Обычный клик Playwright с no_wait_after (если первый не сработал)
                    if not clicked:
                        try:
                            print("[NAVIGATION] Попытка 2: Playwright click() с no_wait_after...")
                            await create_account_locator.click(timeout=10000, no_wait_after=True)
                            await human_delay(2000, 3000)

                            if self.browser_manager.page.url != url_before:
                                print("[NAVIGATION] [+] Playwright click сработал")
                                clicked = True
                        except Exception as e:
                            print(f"[NAVIGATION] Playwright click не сработал: {e}")
                            # Проверяем URL даже при ошибке
                            await human_delay(1000, 1500)
                            if self.browser_manager.page.url != url_before:
                                print("[NAVIGATION] [+] Playwright click сработал (URL изменился несмотря на ошибку)")
                                clicked = True

                    # Метод 3: JavaScript клик (для упрямых React/Fluent UI элементов)
                    if not clicked:
                        try:
                            print("[NAVIGATION] Попытка 3: JavaScript click()...")
                            await create_account_locator.evaluate('el => el.click()')
                            await human_delay(2000, 3000)

                            if self.browser_manager.page.url != url_before:
                                print("[NAVIGATION] [+] JavaScript click сработал")
                                clicked = True
                        except Exception as e:
                            print(f"[NAVIGATION] JavaScript click не сработал: {e}")
                            # Проверяем URL даже при ошибке
                            await human_delay(1000, 1500)
                            if self.browser_manager.page.url != url_before:
                                print("[NAVIGATION] [+] JavaScript click сработал (URL изменился несмотря на ошибку)")
                                clicked = True

                    # Метод 4: Клик на родительский элемент (иногда span внутри ссылки)
                    if not clicked:
                        try:
                            print("[NAVIGATION] Попытка 4: Клик на родительский элемент...")
                            parent = await create_account_locator.evaluate('el => el.parentElement')
                            if parent:
                                await create_account_locator.evaluate('el => el.parentElement.click()')
                                await human_delay(2000, 3000)

                                if self.browser_manager.page.url != url_before:
                                    print("[NAVIGATION] [+] Клик на родителя сработал")
                                    clicked = True
                        except Exception as e:
                            print(f"[NAVIGATION] Клик на родителя не сработал: {e}")
                            # Проверяем URL даже при ошибке
                            await human_delay(1000, 1500)
                            if self.browser_manager.page.url != url_before:
                                print("[NAVIGATION] [+] Клик на родителя сработал (URL изменился несмотря на ошибку)")
                                clicked = True

                    if not clicked:
                        print("[NAVIGATION] [!] Ни один метод клика не сработал!")
                        print(f"[NAVIGATION] URL до: {url_before}")
                        print(f"[NAVIGATION] URL после: {self.browser_manager.page.url}")

                        # Сохраняем скриншот для отладки
                        try:
                            await self.browser_manager.page.screenshot(path="C:\\projects\\outlook_click_failed.png")
                            print("[NAVIGATION] Скриншот сохранен: outlook_click_failed.png")
                        except:
                            pass

                        return None

                    # Эмулируем ожидание загрузки (человек двигает мышью во время ожидания)
                    await human_delay(1500, 2500)
                    await random_mouse_movement(self.browser_manager.page, random.randint(1, 2))
                    await human_delay(1500, 2500)
                else:
                    print("[NAVIGATION] [!] Кнопка 'Создать учетную запись' не найдена")
                    print(f"[NAVIGATION] Текущий URL: {self.browser_manager.page.url}")

                    # Дополнительная диагностика
                    try:
                        # Показываем все кнопки на странице
                        all_buttons = await self.browser_manager.page.locator('span[role="button"], a, button').all()
                        print(f"[NAVIGATION] Найдено элементов с role='button'/a/button: {len(all_buttons)}")

                        # Показываем первые 10 кнопок для отладки
                        for i, btn in enumerate(all_buttons[:10]):
                            try:
                                text = await btn.inner_text()
                                if text.strip():
                                    print(f"[NAVIGATION] Кнопка {i+1}: '{text.strip()[:50]}'")
                            except:
                                pass

                        # Сохраняем скриншот
                        await self.browser_manager.page.screenshot(path="C:\\projects\\outlook_create_button_not_found.png")
                        print("[NAVIGATION] Скриншот сохранен: outlook_create_button_not_found.png")
                    except Exception as e:
                        print(f"[NAVIGATION] Ошибка диагностики: {e}")

                    return None

            except Exception as e:
                print(f"[NAVIGATION] Ошибка при клике 'Создать учетную запись': {e}")
                import traceback
                traceback.print_exc()
                return None

            # === ШАГ 4: Проверяем что загрузилась форма регистрации ===

            # Эмулируем чтение страницы
            await human_delay(1000, 2000)
            await random_mouse_movement(self.browser_manager.page, random.randint(1, 2))

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

            # === ШАГ 5: Ждём появления формы регистрации ===
            print("\n[PAGE] Ожидание загрузки формы регистрации...")
            try:
                # Ждем появления поля email (Fluent UI + стандартные селекторы)
                email_form_selectors = [
                    'input.fui-Input__input[type="email"]',  # Fluent UI
                    'input[aria-label*="пошта" i]',  # украинский
                    'input[aria-label*="email" i]',  # английский
                    'input[name="Електронна пошта"]',  # украинский
                    'input[name="MemberName"]',  # стандартный
                    'input[type="email"]',  # универсальный
                ]

                # Пробуем найти хотя бы один из селекторов
                form_found = False
                for selector in email_form_selectors:
                    try:
                        await self.browser_manager.page.wait_for_selector(selector, timeout=5000)
                        print(f"[PAGE] [+] Форма регистрации найдена: {selector}")
                        form_found = True
                        break
                    except:
                        continue

                if not form_found:
                    raise Exception("Форма регистрации не найдена ни одним селектором")

                print("[PAGE] [+] Форма регистрации загружена")

                # Дополнительная задержка для полной загрузки всех элементов
                await human_delay(1500, 2500)

            except PlaywrightTimeout:
                print("[PAGE] [!] Форма регистрации не загрузилась - проверяем что показывается")
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

                    # Сохраняем скриншот для отладки
                    try:
                        await self.browser_manager.page.screenshot(path="C:\\projects\\outlook_form_not_found.png")
                        print("[PAGE] Скриншот сохранен: outlook_form_not_found.png")
                    except:
                        pass

                except Exception as e:
                    print(f"[PAGE] Ошибка получения текста: {e}")

                return None

            print(f"[PAGE] URL: {self.browser_manager.page.url}")

            # Финальная эмуляция человеческого поведения перед заполнением
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
            # print("\n[STEP 6] ПРОВЕРКА КАПЧИ")
            # await asyncio.sleep(2)
            # await self.captcha_solver.check_and_solve()

            try:
                await self.browser_manager.page.wait_for_selector('#px-captcha', state='hidden', timeout=300000)  # 5 минут
                # Или если элемент просто становится маленьким/скрытым:
                await self.browser_manager.page.wait_for_function("""() => {
                    const el = document.querySelector('#px-captcha');
                    return !el || el.offsetHeight < 20 || el.style.display === 'none';
                }""", timeout=300000)
                print("   CAPTCHA пройдена (элемент исчез) — продолжаем!\n")
            except Exception as e:
                print("   Таймаут ожидания CAPTCHA. Возможно, не пройдена.")
                # Можно добавить raise или продолжить с риском
                raise

            await asyncio.sleep(1)  # небольшая пауза для стабильности

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
                # await self.browser_manager.close()

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


