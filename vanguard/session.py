import json
import os
import random
import traceback
from time import sleep

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

from .urls import landing_page, login_page


class VanguardSession:
    """
    A class to manage a session with Vanguard.

    This class provides methods to initialize a WebDriver with the necessary options, log into Vanguard, and perform other actions on the Chase website.

    Attributes:
        title (str): Denotes the name of the profile and if populated will make the session persistent.
        headless (bool): Whether the WebDriver should run in headless mode.
        profile_path (str): The path to the user profile directory for the WebDriver.
        debug (bool): Whether to take a playwright trace.
        password (str): The user's password.
        context (BrowserContext): The browser context used to launch the browser.
        page (Page): The page instance used to interact with the browser.
        playwright (Playwright): The Playwright instance used to launch the browser.

    Methods:
        get_browser(): Initializes and returns a WebDriver with the necessary options.
        login(username, password, last_four): Logs into Vanguard with the provided credentials.
        login_two(code): Logs into Vanguard with the provided two-factor authentication code.
        save_storage_state(): Saves the storage state of the browser to a file.
        close_browser(): Closes the browser.
    """

    def __init__(self, title=None, headless=True, profile_path=".", debug=False):
        """
        Initializes a new instance of the VanguardSession class.

        Args:
            title (string): Denotes the name of the profile and if populated will make the session persistent.
            headless (bool, optional): Whether the WebDriver should run in headless mode. Defaults to True.
            docker (bool, optional): Whether the session is running in a Docker container. Defaults to False.
            profile_path (str, optional): The path to the user profile directory for the WebDriver. Defaults to None.
        """
        self.title: str = title
        self.headless: bool = headless
        self.profile_path: str = profile_path
        self.debug: bool = debug
        self.password: str = ""
        self.context = None
        self.page = None
        self.playwright = sync_playwright().start()
        self.get_browser()

    def get_browser(self):
        """
        Initializes and returns a browser instance.

        This method checks if a profile path exists, creates one if it doesn't,
        and then launches a new browser instance with the specified user agent,
        viewport, and storage state. It also creates a new page in the browser context and applies stealth settings to it.

        Returns:
            None

        Raises:
            FileNotFoundError: If the profile path does not exist and cannot be created.
            Error: If the browser cannot be launched or the page cannot be created.
        """
        self.profile_path = os.path.abspath(self.profile_path)
        if self.title is not None:
            self.profile_path = os.path.join(
                self.profile_path, f"Vanguard_{self.title}.json"
            )
        else:
            self.profile_path = os.path.join(self.profile_path, "Vanguard.json")
        if not os.path.exists(self.profile_path):
            os.makedirs(os.path.dirname(self.profile_path), exist_ok=True)
            with open(self.profile_path, "w") as f:
                json.dump({}, f)
        if self.headless:
            self.browser = self.playwright.firefox.launch(headless=True)
        else:
            self.browser = self.playwright.firefox.launch(headless=False)
        self.context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            storage_state=self.profile_path if self.title is not None else None,
        )
        self.page = self.context.new_page()
        # testing without playwright-stealth for a bit
        # stealth_sync(self.page)
        if self.debug:
            self.context.tracing.start(
                name="vanguard_trace", screenshots=True, snapshots=True
            )

    def save_storage_state(self):
        """
        Saves the storage state of the browser to a file.

        This method saves the storage state of the browser to a file so that it can be restored later.

        Args:
            filename (str): The name of the file to save the storage state to.
        """
        storage_state = self.page.context.storage_state()
        with open(self.profile_path, "w") as f:
            json.dump(storage_state, f)

    def close_browser(self):
        """Closes the browser."""
        if self.debug:
            self.context.tracing.stop(
                path=f'./vanguard_trace{self.title if self.title is not None else ""}.zip'
            )
        self.save_storage_state()
        self.browser.close()
        self.playwright.stop()

    def go_url(self, url):
        """Navigates to the specified URL."""
        try:
            self.page.goto(url)
        except Exception as e:
            if "NS_BINDING_ABORTED" not in str(e):
                raise e

    def find_login_state(self):
        for _ in range(120):
            try:
                if self.page.url == landing_page():
                    self.page.wait_for_selector(
                        "//h2[contains(text(), 'Accounts')]",
                        timeout=5000,
                    )
                    mode = 1
                    return mode
            except PlaywrightTimeoutError:
                pass
            try:
                self.page.wait_for_selector(
                    "#username-password-submit-btn-1", timeout=500
                )
                mode = 2
                return mode
            except PlaywrightTimeoutError:
                pass
            try:
                self.page.wait_for_selector(
                    "button.col-md:nth-child(2) > div:nth-child(1)", timeout=500
                )
                mode = 3
                return mode
            except PlaywrightTimeoutError:
                pass
            try:
                self.page.wait_for_selector(
                    "a:has-text('I don\\'t see this in my app')",
                    timeout=5000,
                )
                mode = 4
            except PlaywrightTimeoutError:
                pass
            try:
                self.page.wait_for_selector("#CODE", timeout=500)
                mode = 5
                return mode
            except PlaywrightTimeoutError:
                pass
            if "challenges.web.vanguard.com" in self.page.url:
                mode = 1
                return mode
        mode = 0
        return mode

    def login(self, username, password, last_four):
        """
        Logs into the website with the provided username and password.

        This method navigates to the login page, enters the provided username and password into the appropriate fields,
        and submits the form. If the login is successful, the WebDriver will be redirected to the user's account page.

        Args:
            username (str): The user's username.
            password (str): The user's password.
            last_four (int): The last four digits of the user's phone number.

        Raises:
            Exception: If there is an error during the login process in step one.
        """
        try:
            self.password = password
            self.go_url(login_page())
            login_state = self.find_login_state()
            if login_state == 0:
                raise Exception("Failed to find login state")
            elif login_state == 1:
                return False
            elif login_state == 2:
                try:
                    username_box = self.page.wait_for_selector("#USER", timeout=10000)
                    username_box.type(username, delay=random.randint(50, 500))
                    username_box.press("Tab")
                    password_box = self.page.query_selector("#PASSWORD-blocked")
                    password_box.type(password, delay=random.randint(50, 500))
                    sleep(random.uniform(1, 3))
                    self.page.query_selector("#username-password-submit-btn-1").click()
                except PlaywrightTimeoutError:
                    pass
            if login_state in [2, 3, 4]:
                try:
                    self.page.wait_for_selector(
                        "a:has-text('I don\\'t see this in my app')",
                        timeout=5000,
                    ).click()
                    self.page.wait_for_selector(
                        "button:has-text('Continue')",
                        timeout=5000,
                    ).click()
                except PlaywrightTimeoutError:
                    pass
                try:
                    self.page.wait_for_selector(
                        "button.col-md:nth-child(2) > div:nth-child(1)", timeout=5000
                    ).click()
                except PlaywrightTimeoutError:
                    pass
                try:
                    self.page.wait_for_selector(
                        "xpath=//div[contains(text(), '***-***-')]", timeout=5000
                    )
                    otp_cards = self.page.query_selector_all(
                        "xpath=//div[contains(text(), '***-***-')]"
                    )
                    for otp_card in otp_cards:
                        if otp_card.inner_text() == f"***-***-{last_four}":
                            otp_card.click()
                            break
                except PlaywrightTimeoutError:
                    pass
                try:
                    self.page.wait_for_selector(
                        "xpath=//div[contains(text(), 'Text')]", timeout=5000
                    ).click()
                    return True
                except PlaywrightTimeoutError:
                    if self.title is not None:
                        self.save_storage_state()
                    return False
            elif login_state == 5:
                return True
        except Exception as e:
            self.close_browser()
            traceback.print_exc()
            raise Exception(f"Error in first step of login into Vanguard: {e}")

    def login_two(self, code):
        """
        Performs the second step of login if 2fa needed.

        Args:
            code (str): 2fa code sent to users phone.

        Raises:
            Exception: Failed to login to chase.

        Returns:
            bool: True if login is successful, False otherwise.
        """
        try:
            code = str(code)
            self.page.wait_for_selector("#CODE", timeout=5000).fill(code)
            self.page.query_selector(
                "c11n-radio.c11n-radio:nth-child(2) > label:nth-child(2)"
            ).click()
            self.page.wait_for_selector(
                "#security-code-submit-btn", timeout=5000
            ).click()
            sleep(5)
            try:
                self.page.wait_for_url(
                    landing_page(), wait_until="domcontentloaded", timeout=5000
                )
                if self.title is not None:
                    self.save_storage_state()
                return True
            except TimeoutError:
                raise Exception("Failed to login to Vanguard")
        except Exception as e:
            self.close_browser()
            traceback.print_exc()
            print(f"Error logging into Chase: {e}")
            return False
