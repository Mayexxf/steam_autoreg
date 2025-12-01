import pytest
from unittest.mock import Mock, MagicMock, patch, call
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

from steam_registration import SteamRegistration


class TestSteamRegistrationInit:
    """Тесты для инициализации класса SteamRegistration"""

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    def test_init_without_headless(self, mock_driver_manager, mock_chrome):
        """Тест инициализации без headless режима"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        registration = SteamRegistration(headless=False)

        assert registration.headless is False
        assert registration.driver is not None
        assert registration.human_mouse is not None
        assert registration.human_typing is not None

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    def test_init_with_headless(self, mock_driver_manager, mock_chrome):
        """Тест инициализации с headless режимом"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        registration = SteamRegistration(headless=True)

        assert registration.headless is True
        assert registration.driver is not None

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    def test_init_driver_failure(self, mock_driver_manager, mock_chrome):
        """Тест обработки ошибки при инициализации драйвера"""
        mock_chrome.side_effect = Exception("Driver initialization failed")

        with pytest.raises(Exception) as exc_info:
            SteamRegistration()

        assert "Driver initialization failed" in str(exc_info.value) or "Ошибка инициализации" in str(exc_info.value)


class TestSetupBrowser:
    """Тесты для настройки браузера"""

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    @patch('steam_registration.HumanMouse')
    @patch('steam_registration.HumanTypist')
    def test_setup_browser_success(self, mock_typist, mock_mouse, mock_driver_manager, mock_chrome):
        """Тест успешной настройки браузера"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        registration = SteamRegistration(headless=False)

        # Проверяем, что драйвер был создан и окно максимизировано
        mock_driver.maximize_window.assert_called()
        assert registration.driver == mock_driver

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    def test_setup_browser_with_headless_option(self, mock_driver_manager, mock_chrome):
        """Тест настройки браузера с headless опцией"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        registration = SteamRegistration(headless=True)

        # Проверяем, что Chrome был вызван с опциями
        assert mock_chrome.called


class TestInjectStorage:
    """Тесты для инъекции localStorage"""

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    def test_inject_storage_success(self, mock_driver_manager, mock_chrome):
        """Тест успешной инъекции storage"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        registration = SteamRegistration()
        registration.inject_storage()

        # Проверяем, что execute_script был вызван
        assert mock_driver.execute_script.called

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    def test_inject_storage_with_exception(self, mock_driver_manager, mock_chrome):
        """Тест обработки исключения при инъекции storage"""
        mock_driver = Mock()
        mock_driver.execute_script.side_effect = Exception("Script execution failed")
        mock_chrome.return_value = mock_driver

        registration = SteamRegistration()
        # Не должно вызывать исключение, только вывести сообщение
        registration.inject_storage()


class TestOpenRegistrationPage:
    """Тесты для открытия страницы регистрации"""

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    @patch('steam_registration.WebDriverWait')
    def test_open_registration_page_success(self, mock_wait, mock_driver_manager, mock_chrome):
        """Тест успешного открытия страницы регистрации"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        # Мокаем WebDriverWait
        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.return_value = Mock()

        registration = SteamRegistration()
        result = registration.open_registration_page()

        assert result is True
        mock_driver.get.assert_called_with("https://store.steampowered.com/join")

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    @patch('steam_registration.WebDriverWait')
    def test_open_registration_page_timeout(self, mock_wait, mock_driver_manager, mock_chrome):
        """Тест таймаута при открытии страницы регистрации"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        # Мокаем WebDriverWait с таймаутом
        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.side_effect = TimeoutException("Timeout waiting for element")

        registration = SteamRegistration()
        result = registration.open_registration_page()

        assert result is False


class TestFillEmailAddress:
    """Тесты для заполнения email"""

    @patch('steam_registration.ActionChains')
    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    @patch('steam_registration.time.sleep')  # Мокаем sleep для ускорения тестов
    def test_fill_email_success(self, mock_sleep, mock_driver_manager, mock_chrome, mock_action_chains):
        """Тест успешного заполнения email"""
        mock_driver = Mock()
        mock_element = Mock()
        mock_element.rect = {'x': 100, 'y': 100, 'width': 200, 'height': 30}
        mock_driver.find_element.return_value = mock_element
        mock_chrome.return_value = mock_driver

        # Мокаем ActionChains
        mock_actions = Mock()
        mock_actions.move_by_offset.return_value = mock_actions
        mock_actions.pause.return_value = mock_actions
        mock_actions.move_to_element.return_value = mock_actions
        mock_actions.click.return_value = mock_actions
        mock_actions.send_keys.return_value = mock_actions
        mock_action_chains.return_value = mock_actions

        registration = SteamRegistration()
        result = registration.fill_email_address("test@example.com")

        assert result is True
        mock_driver.find_element.assert_called_with(By.ID, "email")
        mock_element.clear.assert_called()

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    def test_fill_email_element_not_found(self, mock_driver_manager, mock_chrome):
        """Тест обработки отсутствующего элемента email"""
        mock_driver = Mock()
        mock_driver.find_element.side_effect = NoSuchElementException("Element not found")
        mock_chrome.return_value = mock_driver

        registration = SteamRegistration()
        result = registration.fill_email_address("test@example.com")

        assert result is False


class TestConfirmEmail:
    """Тесты для подтверждения email"""

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    @patch('steam_registration.time.sleep')
    def test_confirm_email_success(self, mock_sleep, mock_driver_manager, mock_chrome):
        """Тест успешного подтверждения email"""
        mock_driver = Mock()
        mock_element = Mock()
        mock_element.rect = {'x': 100, 'y': 100, 'width': 200, 'height': 30}
        mock_driver.find_element.return_value = mock_element
        mock_chrome.return_value = mock_driver

        registration = SteamRegistration()
        result = registration.confirm_email("test@example.com")

        assert result is True
        mock_driver.find_element.assert_called_with(By.ID, "reenter_email")

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    def test_confirm_email_failure(self, mock_driver_manager, mock_chrome):
        """Тест ошибки при подтверждении email"""
        mock_driver = Mock()
        mock_driver.find_element.side_effect = NoSuchElementException("Element not found")
        mock_chrome.return_value = mock_driver

        registration = SteamRegistration()
        result = registration.confirm_email("test@example.com")

        assert result is False


class TestAcceptAgreement:
    """Тесты для принятия соглашения"""

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    @patch('steam_registration.WebDriverWait')
    @patch('steam_registration.time.sleep')
    def test_accept_agreement_success(self, mock_sleep, mock_wait, mock_driver_manager, mock_chrome):
        """Тест успешного принятия соглашения"""
        mock_driver = Mock()
        mock_checkbox = Mock()
        mock_checkbox.is_selected.side_effect = [False, True]  # Сначала не выбран, потом выбран

        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.return_value = mock_checkbox

        mock_chrome.return_value = mock_driver

        registration = SteamRegistration()
        result = registration.accept_agreement()

        assert result is True
        mock_checkbox.click.assert_called()

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    @patch('steam_registration.WebDriverWait')
    def test_accept_agreement_element_not_found(self, mock_wait, mock_driver_manager, mock_chrome):
        """Тест обработки отсутствия чекбокса соглашения"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.side_effect = TimeoutException("Element not found")

        registration = SteamRegistration()
        result = registration.accept_agreement()

        assert result is False


class TestSolveCaptcha:
    """Тесты для решения капчи"""

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    @patch('steam_registration.TwoCaptcha')
    @patch('steam_registration.time.sleep')
    def test_solve_captcha_success(self, mock_sleep, mock_two_captcha, mock_driver_manager, mock_chrome):
        """Тест успешного решения капчи"""
        mock_driver = Mock()
        mock_driver.current_url = "https://store.steampowered.com/join"

        # Мокаем iframe с hCaptcha
        mock_iframe = Mock()
        mock_iframe.get_attribute.return_value = "https://hcaptcha.com/captcha?sitekey=test-key"
        mock_driver.find_elements.return_value = [mock_iframe]

        # Мокаем элемент для ответа капчи
        mock_response_elem = Mock()
        mock_driver.find_element.return_value = mock_response_elem

        # Мокаем решатель капчи
        mock_solver = Mock()
        mock_solver.solve.return_value = "test-captcha-response-token"
        mock_two_captcha.return_value = mock_solver

        mock_chrome.return_value = mock_driver

        registration = SteamRegistration()
        result = registration.solve_captcha()

        assert result is True
        mock_solver.solve.assert_called()

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    @patch('steam_registration.TwoCaptcha')
    def test_solve_captcha_failure(self, mock_two_captcha, mock_driver_manager, mock_chrome):
        """Тест обработки ошибки при решении капчи"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        # Мокаем ошибку решения капчи
        mock_solver = Mock()
        mock_solver.solve.side_effect = Exception("Captcha solving failed")
        mock_two_captcha.return_value = mock_solver

        registration = SteamRegistration()
        result = registration.solve_captcha()

        assert result is False


class TestContinueRegistration:
    """Тесты для продолжения регистрации"""

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    @patch('steam_registration.WebDriverWait')
    @patch('steam_registration.time.sleep')
    def test_continue_registration_success(self, mock_sleep, mock_wait, mock_driver_manager, mock_chrome):
        """Тест успешного продолжения регистрации"""
        mock_driver = Mock()
        mock_driver.current_url = "https://store.steampowered.com/verify"

        mock_button = Mock()
        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.return_value = mock_button

        mock_chrome.return_value = mock_driver

        registration = SteamRegistration()
        result = registration.continue_registration()

        assert result is True

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    @patch('steam_registration.WebDriverWait')
    @patch('steam_registration.time.sleep')
    def test_continue_registration_button_not_found(self, mock_sleep, mock_wait, mock_driver_manager, mock_chrome):
        """Тест обработки отсутствия кнопки продолжения"""
        mock_driver = Mock()
        mock_driver.current_url = "https://store.steampowered.com/join"
        mock_driver.find_element.side_effect = NoSuchElementException("Button not found")

        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.side_effect = TimeoutException("Button not found")

        mock_chrome.return_value = mock_driver

        registration = SteamRegistration()
        result = registration.continue_registration()

        assert result is False


class TestSetAccountDetails:
    """Тесты для установки деталей аккаунта"""

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    @patch('steam_registration.time.sleep')
    def test_set_account_details_success(self, mock_sleep, mock_driver_manager, mock_chrome):
        """Тест успешной установки деталей аккаунта"""
        mock_driver = Mock()

        # Мокаем элементы формы
        mock_username = Mock()
        mock_password = Mock()
        mock_confirm_password = Mock()

        def mock_find_element(by, value):
            if value == "accountname":
                return mock_username
            elif value == "password":
                return mock_password
            elif value == "reenter_password":
                return mock_confirm_password

        mock_driver.find_element.side_effect = mock_find_element
        mock_chrome.return_value = mock_driver

        registration = SteamRegistration()
        result = registration.set_account_details("testuser", "testpass123")

        assert result is True
        mock_username.clear.assert_called()
        mock_password.clear.assert_called()
        mock_confirm_password.clear.assert_called()

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    def test_set_account_details_element_not_found(self, mock_driver_manager, mock_chrome):
        """Тест обработки отсутствующих элементов формы"""
        mock_driver = Mock()
        mock_driver.find_element.side_effect = NoSuchElementException("Element not found")
        mock_chrome.return_value = mock_driver

        registration = SteamRegistration()
        result = registration.set_account_details("testuser", "testpass123")

        assert result is False


class TestCompleteRegistration:
    """Тесты для завершения регистрации"""

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    @patch('steam_registration.WebDriverWait')
    @patch('steam_registration.time.sleep')
    def test_complete_registration_success(self, mock_sleep, mock_wait, mock_driver_manager, mock_chrome):
        """Тест успешного завершения регистрации"""
        mock_driver = Mock()
        mock_button = Mock()
        mock_driver.find_element.return_value = mock_button

        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.return_value = Mock()

        mock_chrome.return_value = mock_driver

        registration = SteamRegistration()
        result = registration.complete_registration()

        assert result is True
        mock_button.click.assert_called()

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    def test_complete_registration_button_not_found(self, mock_driver_manager, mock_chrome):
        """Тест обработки отсутствия кнопки завершения"""
        mock_driver = Mock()
        mock_driver.find_element.side_effect = NoSuchElementException("Button not found")
        mock_chrome.return_value = mock_driver

        registration = SteamRegistration()
        result = registration.complete_registration()

        assert result is False


class TestRegisterAccount:
    """Интеграционные тесты для полного процесса регистрации"""

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    def test_register_account_with_provided_data(self, mock_driver_manager, mock_chrome):
        """Тест регистрации с предоставленными данными"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        registration = SteamRegistration()

        # Мокаем все методы для успешного выполнения
        registration.open_registration_page = Mock(return_value=True)
        registration.fill_email_address = Mock(return_value=True)
        registration.confirm_email = Mock(return_value=True)
        registration.accept_agreement = Mock(return_value=True)
        registration.solve_captcha = Mock(return_value=True)
        registration.continue_registration = Mock(return_value=True)
        registration.verify_email = Mock(return_value=True)
        registration.set_account_details = Mock(return_value=True)
        registration.complete_registration = Mock(return_value=True)

        result = registration.register_account(
            email="test@example.com",
            username="testuser",
            password="testpass123"
        )

        assert result is True
        registration.open_registration_page.assert_called_once()
        registration.fill_email_address.assert_called_once_with("test@example.com")
        registration.confirm_email.assert_called_once_with("test@example.com")

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    def test_register_account_failure_at_email(self, mock_driver_manager, mock_chrome):
        """Тест обработки ошибки при заполнении email"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        registration = SteamRegistration()

        # Мокаем ошибку при заполнении email
        registration.open_registration_page = Mock(return_value=True)
        registration.fill_email_address = Mock(return_value=False)

        result = registration.register_account(
            email="test@example.com",
            username="testuser",
            password="testpass123"
        )

        assert result is False

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    def test_register_account_with_generated_data(self, mock_driver_manager, mock_chrome):
        """Тест регистрации с автогенерированными данными"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        registration = SteamRegistration()

        # Мокаем генерацию данных
        registration.storage_gen.generate_email = Mock(return_value="generated@example.com")
        registration.storage_gen.generate_username = Mock(return_value="generateduser")
        registration.storage_gen.generate_password = Mock(return_value="generatedpass123")

        # Мокаем все методы для успешного выполнения
        registration.open_registration_page = Mock(return_value=True)
        registration.fill_email_address = Mock(return_value=True)
        registration.confirm_email = Mock(return_value=True)
        registration.accept_agreement = Mock(return_value=True)
        registration.solve_captcha = Mock(return_value=True)
        registration.continue_registration = Mock(return_value=True)
        registration.verify_email = Mock(return_value=True)
        registration.set_account_details = Mock(return_value=True)
        registration.complete_registration = Mock(return_value=True)

        result = registration.register_account()

        assert result is True
        registration.storage_gen.generate_email.assert_called_once()
        registration.storage_gen.generate_username.assert_called_once()
        registration.storage_gen.generate_password.assert_called_once()


class TestGetButtonInfo:
    """Тесты для получения информации о кнопках"""

    @patch('steam_registration.webdriver.Chrome')
    @patch('steam_registration.ChromeDriverManager')
    def test_get_button_info(self, mock_driver_manager, mock_chrome):
        """Тест получения информации о кнопках"""
        mock_driver = Mock()

        # Создаем мок кнопок
        mock_button1 = Mock()
        mock_button1.text = "Continue"
        mock_button1.get_attribute.side_effect = lambda attr: {
            "id": "continue_btn",
            "class": "btn_blue",
            "type": "submit"
        }.get(attr)
        mock_button1.is_displayed.return_value = True
        mock_button1.is_enabled.return_value = True

        mock_driver.find_elements.return_value = [mock_button1]
        mock_chrome.return_value = mock_driver

        registration = SteamRegistration()
        buttons_info = registration.get_button_info()

        assert len(buttons_info) == 1
        assert buttons_info[0]["text"] == "Continue"
        assert buttons_info[0]["id"] == "continue_btn"
        assert buttons_info[0]["is_displayed"] is True
        assert buttons_info[0]["is_enabled"] is True
