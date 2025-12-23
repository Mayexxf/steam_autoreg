#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Решение капчи PerimeterX (Press & Hold) для Microsoft
"""
import math
import random
import asyncio
import time
from typing import Optional, Any

from playwright.async_api import Page

from .utils import smooth_mouse_move, human_delay
from .config import CAPTCHA_MAX_ATTEMPTS

# PyAutoGUI для реальных системных кликов
try:
    import pyautogui
    pyautogui.FAILSAFE = False
    PYAUTOGUI_AVAILABLE = False
except ImportError:
    PYAUTOGUI_AVAILABLE = False


class CaptchaSolver:
    """Решатель капчи PerimeterX (Press & Hold)"""

    def __init__(self, page: Page):
        self.page = page
        self.captcha_frame = None
        self._iframe_logged = False
        self._debug_logged = False

    async def check_and_solve(self) -> bool:
        """Проверяет наличие капчи и решает её"""
        print("[CAPTCHA] Проверяем наличие капчи...")

        for attempt in range(10):
            is_present = await self._is_captcha_present()
            if is_present:
                print("[CAPTCHA] Капча обнаружена!")
                return await self._solve()
            await asyncio.sleep(0.5)

        print("[CAPTCHA] Капча не обнаружена после 10 проверок")
        return True

    async def _is_captcha_present(self) -> bool:
        """Проверяет наличие капчи на странице"""
        try:
            result = await self.page.evaluate("""() => {
                const body = document.body.innerText.toLowerCase();
                if (body.includes('press') && body.includes('hold')) return true;
                
                const px = document.querySelector('#px-captcha');
                if (px && px.offsetHeight > 30) return true;
                
                const iframes = document.querySelectorAll('iframe');
                for (let iframe of iframes) {
                    const title = (iframe.title || '').toLowerCase();
                    const src = iframe.src || '';
                    if (title.includes('human') || title.includes('verification') ||
                        src.includes('hsprotect') || src.includes('captcha')) {
                        if (iframe.offsetHeight > 30) return true;
                    }
                }
                
                return false;
            }""")
            return result
        except:
            return False

    async def _get_frame(self) -> Optional[Any]:
        """Находит iframe с капчей"""
        async def find_nested_frames(parent_frame, depth=0):
            frames_found = []
            try:
                iframes = await parent_frame.query_selector_all('iframe')
                for iframe in iframes:
                    try:
                        style = await iframe.get_attribute('style') or ''
                        if 'display: none' in style.lower():
                            continue
                        box = await iframe.bounding_box()
                        if not box or box['width'] < 50 or box['height'] < 20:
                            continue
                        child_frame = await iframe.content_frame()
                        if child_frame:
                            frames_found.append(child_frame)
                            deeper = await find_nested_frames(child_frame, depth + 1)
                            frames_found.extend(deeper)
                    except:
                        continue
            except:
                pass
            return frames_found

        iframes = await self.page.query_selector_all('iframe')
        for iframe in iframes:
            try:
                title = await iframe.get_attribute('title') or ''
                src = await iframe.get_attribute('src') or ''
                style = await iframe.get_attribute('style') or ''

                if ('human' in title.lower() or 'verification' in title.lower() or
                        'hsprotect' in src.lower() or 'captcha' in src.lower()):

                    if 'display: none' not in style.lower():
                        box = await iframe.bounding_box()
                        if box and box['width'] > 50 and box['height'] > 20:
                            if not self._iframe_logged:
                                print(
                                    f"[CAPTCHA] Найден iframe: title='{title}', size={box['width']}x{box['height']}")
                                self._iframe_logged = True

                            frame = await iframe.content_frame()
                            if frame:
                                nested = await find_nested_frames(frame)
                                if nested:
                                    return nested[-1]
                                return frame
            except:
                continue
        return None

    async def _find_button(self, frame=None) -> Optional[Any]:
        """Ищет кнопку Press & Hold"""
        target = frame if frame else self.page

        selectors = [
            '[aria-label*="Press"][aria-label*="Hold"]',
            '[aria-label*="Hold Human"]',
            '[aria-label*="hold" i][role="button"]',
            'div[role="button"][tabindex="0"]',
            '#px-captcha [role="button"]',
        ]

        for sel in selectors:
            try:
                elements = await target.query_selector_all(sel)
                for el in elements:
                    try:
                        visible = await el.is_visible()
                        if not visible:
                            continue
                        box = await el.bounding_box()
                        if not box or box['width'] < 50 or box['height'] < 20:
                            continue

                        aria = await el.get_attribute('aria-label') or ''
                        if 'completed' in aria.lower():
                            continue
                        if 'hold' in aria.lower():
                            return el
                    except:
                        continue
            except:
                continue
        return None

    async def _get_coordinates(self) -> Optional[tuple]:
        """Получает координаты для клика"""
        try:
            iframes = await self.page.query_selector_all('iframe')
            for iframe in iframes:
                title = await iframe.get_attribute('title') or ''
                src = await iframe.get_attribute('src') or ''
                style = await iframe.get_attribute('style') or ''

                if 'display: none' in style.lower():
                    continue

                if 'verification' in title.lower() or 'human' in title.lower() or 'hsprotect' in src.lower():
                    box = await iframe.bounding_box()
                    if box and box['width'] > 50 and box['height'] > 30:
                        x = box['x'] + box['width'] * 0.75
                        y = box['y'] + box['height'] * 0.5
                        return (x, y, box)
        except:
            pass

        try:
            px = await self.page.query_selector('#px-captcha')
            if px:
                box = await px.bounding_box()
                if box and box['width'] > 50:
                    x = box['x'] + box['width'] * 0.75
                    y = box['y'] + box['height'] * 0.5
                    return (x, y, box)
        except:
            pass

        return None

    async def _solve(self) -> bool:
        """Решает капчу"""
        print("[CAPTCHA] === Начало решения капчи ===")

        for retry in range(CAPTCHA_MAX_ATTEMPTS):
            print(f"\n[CAPTCHA] Попытка {retry + 1}/{CAPTCHA_MAX_ATTEMPTS}")

            frame = await self._get_frame()
            button = await self._find_button(frame)
            self.captcha_frame = frame

            if button:
                success = await self._hold_button(button, frame)
                if success:
                    print("[CAPTCHA] ✓ Капча пройдена!")
                    return True
            else:
                coords = await self._get_coordinates()
                if coords:
                    x, y, _ = coords
                    success = await self._hold_by_coordinates(x, y, frame)
                    if success:
                        print("[CAPTCHA] ✓ Капча пройдена!")
                        return True

            if await self._check_success():
                return True

            await asyncio.sleep(2)

        return False

    async def _hold_button(self, button, frame=None) -> bool:
        """Удерживает кнопку"""
        box = await button.bounding_box()
        if not box:
            return False

        x = box['x'] + box['width'] / 2 + random.uniform(-3, 3)
        y = box['y'] + box['height'] / 2 + random.uniform(-3, 3)

        return await self._hold_by_coordinates(x, y, frame)

    async def _hold_by_coordinates(self, x: float, y: float, frame=None) -> bool:
        """Удерживает по координатам"""
        if PYAUTOGUI_AVAILABLE:
            return await self._hold_pyautogui(x, y)
        else:
            return await self._hold_playwright(x, y)

    async def _hold_pyautogui(self, x: float, y: float) -> bool:
        """Удержание через PyAutoGUI"""
        try:
            window_info = await self.page.evaluate("""() => ({
                screenX: window.screenX,
                screenY: window.screenY,
                outerWidth: window.outerWidth,
                outerHeight: window.outerHeight,
                innerWidth: window.innerWidth,
                innerHeight: window.innerHeight
            })""")

            chrome_offset_x = (
                window_info['outerWidth'] - window_info['innerWidth']) // 2
            chrome_offset_y = window_info['outerHeight'] - \
                window_info['innerHeight'] - chrome_offset_x

            screen_x = int(window_info['screenX'] + chrome_offset_x + x)
            screen_y = int(window_info['screenY'] + chrome_offset_y + y)

            pyautogui.moveTo(screen_x, screen_y, duration=0.3)
            await asyncio.sleep(0.2)
            pyautogui.mouseDown()

            max_hold_time = 15000
            start_time = time.time()
            success = False

            while (time.time() - start_time) * 1000 < max_hold_time:
                await asyncio.sleep(0.03)
                elapsed_ms = int((time.time() - start_time) * 1000)

                dx = random.uniform(-2, 2)
                dy = random.uniform(-2, 2)
                pyautogui.moveTo(screen_x + dx, screen_y + dy, duration=0.01)

                if elapsed_ms % 100 < 30:
                    if await self._check_success():
                        success = True
                        break

            pyautogui.mouseUp()
            await asyncio.sleep(2)
            return success

        except Exception as e:
            print(f"[CAPTCHA] Ошибка PyAutoGUI: {e}")
            try:
                pyautogui.mouseUp()
            except:
                pass
            return False

    async def _hold_playwright(self, x: float, y: float) -> bool:
        """Удержание через Playwright"""
        try:
            await smooth_mouse_move(self.page, x, y)
            await human_delay(150, 350)  # чуть дольше пауза — естественнее
            await self.page.mouse.down()

            hold_duration = random.uniform(9.5, 14.0)  # вариативность
            start_time = time.time()
            last_correction = 0

            while (time.time() - start_time) < hold_duration:
                elapsed = time.time() - start_time

                # Основное дрожание — гауссово распределение (естественнее uniform)
                dx = random.gauss(0, 4.0)  # среднее отклонение ~4 px
                dy = random.gauss(0, 4.0)

                # Каждые 2–5 секунд — лёгкое круговое движение (человек поправляет кисть)
                if elapsed - last_correction > random.uniform(2.0, 5.0):
                    angle = elapsed * 1.5
                    radius = random.uniform(6, 14)
                    dx += math.cos(angle) * radius
                    dy += math.sin(angle) * radius
                    last_correction = elapsed

                # Редкий "сбой" — человек чуть отвлёкся
                if random.random() < 0.008:
                    dx += random.uniform(-18, 18)
                    dy += random.uniform(-12, 12)

                await self.page.mouse.move(x + dx, y + dy)
                await asyncio.sleep(random.uniform(0.04, 0.20))  # нерегулярный ритм

            await self.page.mouse.up()
            await human_delay(600, 1200)
            return await self._check_success()

        except Exception as e:
            print(f"[CAPTCHA] Ошибка Playwright: {e}")
            try:
                await self.page.mouse.up()
            except:
                pass
            return False

    async def _check_success(self) -> bool:
        """Проверяет успешность прохождения"""
        try:
            result = await self.page.evaluate("""() => {
                const body = document.body.innerText.toLowerCase();
                if (!body.includes('hold') && !body.includes('press')) return true;
                
                const px = document.querySelector('#px-captcha');
                if (!px || px.offsetHeight < 20) return true;
                
                return false;
            }""")
            return result
        except:
            return False

    async def check_block_error(self) -> Optional[str]:
        """Проверяет блокировку от Microsoft"""
        try:
            return await self.page.evaluate("""() => {
                const body = document.body.innerText.toLowerCase();
                
                if (body.includes("can't create your account")) 
                    return 'BLOCKED: Account creation blocked';
                if (body.includes('unusual activity'))
                    return 'BLOCKED: Unusual activity detected';
                if (body.includes('too many requests'))
                    return 'RATE_LIMIT: Too many requests';
                if (body.includes('verify your phone'))
                    return 'PHONE_REQUIRED: Phone verification needed';
                
                return null;
            }""")
        except:
            return None

