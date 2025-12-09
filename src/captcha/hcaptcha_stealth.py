# src/stealth/hcaptcha_stealth.py
"""
Стелс-клик по чекбоксу hCaptcha (оптимизировано для Steam /join/ в 2025)
Подходит для стелс-ботов: минимум ожиданий, максимум человекоподобного поведения
"""

import random
import time

from scipy.interpolate import CubicSpline
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

from src.stealth import HumanTypist


def human_delay(min_ms=500, max_ms=1500):
    """Случайная задержка как у человека"""
    delay = random.uniform(min_ms, max_ms)
    time.sleep(delay / 1000)
    return int(delay)


class SeleniumHumanTypist:
    """Адаптер HumanTypist для Selenium"""

    def __init__(self, driver, speed_profile='normal', typo_rate=0.06, typo_correct_rate=0.9):
        self.driver = driver
        self.typist = HumanTypist(speed_profile=speed_profile, typo_rate=typo_rate)

    def type_text(self, element, text):
        """Печатает текст человекоподобно через Selenium"""
        total_length = len(text)
        for i, char in enumerate(text):
            # Проверяем опечатку (логика из HumanTypist)
            if self.typist._should_make_typo(i, total_length):
                typo_char = self.typist._get_typo_char(char)
                element.send_keys(typo_char)
                delay = self.typist._get_char_delay(typo_char, i, total_length)
                time.sleep(delay)
                time.sleep(random.uniform(0.1, 0.4))  # Пауза перед backspace
                element.send_keys(Keys.BACKSPACE)
                time.sleep(random.uniform(0.05, 0.15))

            # Правильный символ
            element.send_keys(char)
            delay = self.typist._get_char_delay(char, i, total_length)
            time.sleep(delay)


class SeleniumHumanMouse:
    """Адаптер HumanMouse для Selenium"""

    def __init__(self, driver):
        self.driver = driver
        self.actions = ActionChains(driver)

    def random_movement(self, movements=3):
        width = self.driver.execute_script("return window.innerWidth")
        height = self.driver.execute_script("return window.innerHeight")

        # Безопасные границы для движения мыши (отступ от краёв)
        margin = 50
        safe_width = max(200, width - margin * 2)
        safe_height = max(200, height - margin * 2)

        for _ in range(movements):
            # Генерируем координаты внутри безопасной зоны
            start_x = random.randint(margin, margin + safe_width)
            start_y = random.randint(margin, margin + safe_height)
            end_x = random.randint(margin, margin + safe_width)
            end_y = random.randint(margin, margin + safe_height)

            # Bézier: 4 control points for curve
            mid1_x = random.randint(min(start_x, end_x), max(start_x, end_x))
            mid1_y = random.randint(min(start_y, end_y), max(start_y, end_y))
            mid2_x = random.randint(min(start_x, end_x), max(start_x, end_x))
            mid2_y = random.randint(min(start_y, end_y), max(start_y, end_y))

            points = [(start_x, start_y), (mid1_x, mid1_y), (mid2_x, mid2_y), (end_x, end_y)]
            t = [0, 0.3, 0.7, 1]
            cs_x = CubicSpline(t, [p[0] for p in points])
            cs_y = CubicSpline(t, [p[1] for p in points])

            steps = 20
            current_x, current_y = start_x, start_y

            for i in range(steps):
                pos = i / steps
                new_x = int(cs_x(pos))
                new_y = int(cs_y(pos))

                # Вычисляем смещение относительно текущей позиции
                dx = new_x - current_x
                dy = new_y - current_y

                # Ограничиваем смещение чтобы не выйти за границы
                dx = max(-100, min(100, dx))
                dy = max(-100, min(100, dy))

                try:
                    self.actions.move_by_offset(dx, dy).perform()
                    current_x += dx
                    current_y += dy
                except Exception:
                    # Если движение невозможно - пропускаем
                    pass

                time.sleep(random.uniform(0.01, 0.05))

            self.actions.reset_actions()
            time.sleep(random.uniform(0.3, 0.8))


def human_type(driver, selector, text, speed_profile='normal', typo_rate=0.06):
    """
    Печатает текст РЕАЛИСТИЧНО как человек (версия для Selenium).

    Args:
        driver: Selenium WebDriver
        selector: CSS селектор поля ввода
        text: Текст для ввода
        speed_profile: 'slow', 'normal', 'fast', 'expert'
        typo_rate: Вероятность опечатки (0.0-1.0)
    """
    element = driver.find_element(By.CSS_SELECTOR, selector)

    # Человек сначала водит мышкой → фокус → клик
    mouse = SeleniumHumanMouse(driver)
    mouse.random_movement(movements=random.randint(2, 5))

    # 2. Плавное наведение на поле ( САМОЕ ВАЖНОЕ! )
    ActionChains(driver) \
        .move_to_element_with_offset(element, random.randint(-10, 10), random.randint(-5, 5)) \
        .pause(random.uniform(0.3, 1.1)) \
        .click() \
        .perform()

    # 3. Человек читает подсказку в поле (placeholder), думает...
    time.sleep(random.uniform(0.6, 2.1))

    # 4. Начинаем печатать — с настоящими burst'ами и опечатками
    typist = SeleniumHumanTypist(
        driver,
        speed_profile=speed_profile,
        typo_rate=typo_rate,
        typo_correct_rate=0.92
    )
    typist.type_text(element, text)

    # 5. После ввода — небольшая пауза (человек проверяет, что написал)
    time.sleep(random.uniform(0.7, 2.3))

    # 6. Иногда чуть подвигаем мышку после ввода (очень по-человечески)
    if random.random() < 0.4:
        ActionChains(driver).move_by_offset(
            random.randint(-80, 80), random.randint(-80, 80)
        ).pause(0.3).perform()


def random_mouse_movement(driver, movements=3):
    """
    Случайное движение мыши РЕАЛИСТИЧНО (версия для Selenium).

    Args:
        driver: Selenium WebDriver
        movements: Количество движений
    """
    mouse = SeleniumHumanMouse(driver)
    mouse.random_movement(movements=movements)

def stealth_checkbox_click(driver, checkbox_selector):
    """
    Максимально стелс-отметка чекбокса на Steam (или любой другой странице).
    Эмулирует реальное движение мыши + диспатч всех MouseEvent событий.
    Valve почти не ловит такой клик.

    Args:
        driver: Selenium WebDriver
        checkbox_selector: CSS селектор, например '#accept_ssa' или '#accept_ssa, [name="accept_ssa"]'
    """
    try:
        # Ищем чекбокс (с fallback селекторами)
        checkbox = driver.find_element(By.CSS_SELECTOR, checkbox_selector)

        # Если уже отмечен — выходим
        if checkbox.is_selected():
            print(f"[CHECKBOX] Уже отмечен: {checkbox_selector}")
            return True

        print(f"[CHECKBOX] Отмечаем чекбокс: {checkbox_selector}")

        # 1. Небольшое случайное движение мыши перед действием
        random_mouse_movement(driver, movements=random.randint(1, 3))
        human_delay(400, 900)  # 0.4–0.9 сек

        # 2. Плавно подводим курсор к чекбоксу с небольшим оффсетом (человек не попадает точно в центр)
        actions = ActionChains(driver)
        offset_x = random.randint(-8, 8)
        offset_y = random.randint(-8, 8)
        actions.move_to_element_with_offset(checkbox, offset_x, offset_y)
        actions.pause(random.uniform(0.2, 0.6))
        actions.perform()

        human_delay(200, 500)  # Короткая пауза перед кликом

        # 3. Диспатчим ВСЕ реальные события мыши через JS (самое важное для стелс)
        driver.execute_script("""
            const el = arguments[0];
            const events = ['mouseover', 'mousemove', 'mousedown', 'mouseup', 'click'];
            events.forEach(type => {
                const event = new MouseEvent(type, {
                    view: window,
                    bubbles: true,
                    cancelable: true,
                    buttons: 1,
                    clientX: el.getBoundingClientRect().x + el.clientWidth / 2,
                    clientY: el.getBoundingClientRect().y + el.clientHeight / 2
                });
                el.dispatchEvent(event);
            });
            // Принудительно отмечаем, если вдруг событие не сработало
            el.checked = true;
        """, checkbox)

        # Небольшая пауза после клика
        human_delay(300, 700)

        # Проверка результата
        if checkbox.is_selected():
            print(f"[CHECKBOX] ✓ Успешно отмечен: {checkbox_selector}")
            return True
        else:
            print(f"[CHECKBOX] ✗ Не отметился после JS — пробуем прямой клик (резерв)")
            checkbox.click()  # Крайний случай
            return checkbox.is_selected()

    except Exception as e:
        print(f"[CHECKBOX] Ошибка при отметке {checkbox_selector}: {str(e)[:120]}")
        return False

def stealth_hcaptcha_checkbox_click(driver, timeout_attempts=4):
    """
    Стелс-клик по чекбоксу hCaptcha на Steam (или других сайтах с hCaptcha в iframe)

    Args:
        driver: Selenium WebDriver
        timeout_attempts: Количество попыток поиска/клика (по умолчанию 4)

    Returns:
        bool: True если клик успешен
    """
    print(f"\n[HCAPTCHA] Starting stealth click on hCaptcha checkbox...")

    for attempt in range(1, timeout_attempts + 1):
        print(f"[HCAPTCHA] Attempt {attempt}/{timeout_attempts}")

        try:
            # === 1. Поиск iframe hCaptcha (много fallback-селекторов под 2025) ===
            iframe_selectors = [
                'iframe[src*="hcaptcha.com"]',
                'iframe[src*="newassets.hcaptcha.com"]',
                'iframe[title*="captcha"]',
                'iframe[title*="hCaptcha"]',
                'iframe[data-hcaptcha-widget-id]',
                'iframe[src*="captcha"]'
            ]

            iframe = None
            used_selector = None
            for sel in iframe_selectors:
                try:
                    candidates = driver.find_elements(By.CSS_SELECTOR, sel)
                    if candidates:
                        iframe = candidates[0]
                        used_selector = sel
                        print(f"[HCAPTCHA] Found iframe → {used_selector}")
                        break
                except:
                    continue

            if not iframe:
                print(f"[HCAPTCHA] ✗ iframe not found on attempt {attempt}")
                human_delay(2500, 4500)
                continue

            # Скролл к iframe
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", iframe)
            human_delay(600, 1200)

            # Имитация осмотра перед кликом
            random_mouse_movement(driver, movements=random.randint(2, 4))
            human_delay(1000, 2500)

            # === 2. Переход в iframe ===
            driver.switch_to.frame(iframe)
            print(f"[HCAPTCHA] Switched to iframe")

            # === 3. Поиск чекбокса внутри iframe ===
            checkbox_selectors = [
                '#checkbox',
                'span#checkbox',
                '[role="checkbox"]',
                '.checkbox',
                '.checkmark',
                '[id*="checkbox"]'
            ]

            checkbox = None
            checkbox_sel = None
            for sel in checkbox_selectors:
                try:
                    checkbox = driver.find_element(By.CSS_SELECTOR, sel)
                    checkbox_sel = sel
                    print(f"[HCAPTCHA] Checkbox found → {checkbox_sel}")
                    break
                except NoSuchElementException:
                    continue

            if not checkbox:
                print(f"[HCAPTCHA] ✗ Checkbox not found inside iframe")
                driver.switch_to.default_content()
                human_delay(2000, 4000)
                continue

            # Скролл внутри iframe
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
            human_delay(400, 800)

            # === 4. Человекоподобный клик с offset ===
            actions = ActionChains(driver)
            offset_x = random.randint(-15, 15)
            offset_y = random.randint(-15, 15)

            actions.move_to_element_with_offset(checkbox, offset_x, offset_y)
            actions.pause(random.uniform(0.5, 1.8))
            actions.click()
            actions.perform()

            print(f"[HCAPTCHA] ✓ Click performed (offset: {offset_x},{offset_y})")

            # Возврат в основной контекст
            driver.switch_to.default_content()
            print(f"[HCAPTCHA] Returned to main content")

            # Финальная пауза — ждём реакцию hCaptcha
            human_delay(2000, 5000)
            print(f"[HCAPTCHA] Stealth checkbox click SUCCESS!")
            return True

        except Exception as e:
            print(f"[HCAPTCHA] Error on attempt {attempt}: {str(e)[:150]}")
            try:
                driver.switch_to.default_content()
            except:
                pass
            human_delay(3000, 6000)

    # Все попытки провалились
    print(f"[HCAPTCHA] ✗ Failed after {timeout_attempts} attempts")
    try:
        driver.save_screenshot("hcaptcha_stealth_failed.png")
        print(f"[DEBUG] Screenshot saved: hcaptcha_stealth_failed.png")
    except:
        pass
    return False