import re
from enum import Enum
from time import sleep

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect

from .session import VanguardSession
from .urls import order_page


class PriceType(str, Enum):
    """This is an :class: 'enum.Enum' that contains the valid price types for an order."""

    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class Duration(str, Enum):
    """This is an :class:'~enum.Enum' that contains the valid durations for an order."""

    DAY = "DAY"
    GTC = "GOOD_TILL_CANCELLED"
    ON_OPEN = "ON_THE_OPEN"
    ON_CLOSE = "ON_THE_CLOSE"
    I_C = "IMMEDIATE_OR_CANCEL"


class OrderSide(str, Enum):
    """
    This is an :class:'~enum.Enum'
    that contains the valid order types for an order.
    """

    BUY = "BUY"
    SELL = "SELL"


class TypeCode(str, Enum):
    """
    This is an :class:'~enum.Enum'
    that contains the valid order types for an order.
    """

    CASH = "CASH"
    MARGIN = "MARGIN"


class Order:
    """
    This class contains information about an order.
    It also contains a method to place an order.
    """

    def __init__(self, session: VanguardSession):
        self.session = session
        self.order_number: str = ""

    def place_order(
        self,
        account_id,
        quantity: int,
        price_type: PriceType,
        symbol,
        duration: Duration,
        order_type: OrderSide,
        limit_price: float = 0.00,
        stop_price: float = 0.00,
        after_hours: bool = False,
        dry_run=True,
    ):
        """
        Builds and places an order.
        :attr: 'order_confirmation`
        contains the order confirmation data after order placement.

        Args:
            account_id (str): Account number of the account to place the order in.
            quantity (int): The number of shares to buy.
            price_type (PriceType): Price Type i.e. LIMIT, MARKET, STOP, etc.
            symbol (str): Ticker to place the order for.
            duration (Duration): Duration of the order i.e. DAY, GT90, etc.
            order_type (OrderSide): Type of order i.e. BUY, SELL, SELL_ALL.
            limit_price (float, optional): The price to buy the shares at. Defaults to 0.00.
            stop_price (float, optional): The price to buy the shares at. Defaults to 0.00.
            after_hours (bool, optional): Whether you want to place the order after hours. Defaults to True.
            dry_run (bool, optional): Whether you want the order to be placed or not.
                                      Defaults to True.

        Returns:
            Order:order_confirmation: Dictionary containing the order confirmation data.
        """
        order_messages = {
            "ORDER INVALID": "",
            "ORDER PREVIEW": "",
            "ORDER CONFIRMATION": "",
        }
        self.session.go_url(order_page())
        try:
            account_box = self.session.page.locator("#account-selector")
            account_box.wait_for(timeout=30000)
            account_box_interact = account_box.locator("..")
            account_box_interact.click()
            account_selectors = account_box.locator("option").all()
            for account in account_selectors:
                if account_id in account.text_content():
                    account_box.select_option(value=account.get_attribute("value"))
                    break
        except PlaywrightTimeoutError:
            pass
        quote_box = self.session.page.wait_for_selector(
            "//input[@placeholder='Get Quote']"
        )
        quote_box.click()
        quote_box.fill("")
        quote_box.fill(symbol)
        self.session.page.keyboard.press("Tab")
        for _ in range(12):
            quote_price = self.session.page.wait_for_selector(
                "(//div[@data-testid='txt-quote-value'])[2]", timeout=10000
            ).text_content()
            sleep(0.25)
            if quote_price != "$—":
                break
        if quote_price != "$—":
            order_messages["ORDER INVALID"] = "Order page loaded correctly."
        else:
            order_messages["ORDER INVALID"] = "Quote did not load correctly."

        if order_messages["ORDER INVALID"] != "Order page loaded correctly.":
            return order_messages
        try:
            self.session.page.wait_for_selector(
                "twe-trade-cannot-be-completed-modal tds-modal .modal__content",
                timeout=3000,
            )
            self.session.page.locator("xpath=//button[contains(text(), 'OK')]").click()
        except PlaywrightTimeoutError:
            pass
        if order_type == "BUY":
            buy_btn = self.session.page.wait_for_selector(
                "xpath=//label/span[text()='Buy']"
            )
            buy_btn.click()
        elif order_type == "SELL":
            sell_btn = self.session.page.wait_for_selector(
                "xpath=//label/span[text()='Sell']"
            )
            sell_btn.click()
        quantity_box = self.session.page.wait_for_selector(
            "//input[@placeholder='Enter Shares']"
        )
        quantity_box.fill("")
        quantity_box.type(str(quantity))
        try:
            if price_type == "MARKET":
                self.session.page.wait_for_selector(
                    "//label/span[text()='Market']",
                    timeout=3000,
                ).click()
            elif price_type == "LIMIT":
                if duration not in ["DAY", "GOOD_TILL_CANCELLED"]:
                    order_messages["ORDER INVALID"] = (
                        "Limit orders must be DAY or GOOD TILL CANCELLED."
                    )
                    return order_messages
                self.session.page.wait_for_selector(
                    "//label/span[text()='Limit']", timeout=3000
                ).click()
            elif price_type == "STOP":
                if duration not in ["DAY", "GOOD_TILL_CANCELLED"]:
                    order_messages["ORDER INVALID"] = (
                        "Stop orders must be DAY or GOOD TILL CANCELLED."
                    )
                    return order_messages
                self.session.page.wait_for_selector(
                    "//label/span[text()='Stop']", timeout=3000
                ).click()
            elif price_type == "STOP_LIMIT":
                if duration not in ["DAY", "GOOD_TILL_CANCELLED"]:
                    order_messages["ORDER INVALID"] = (
                        "Stop orders must be DAY or GOOD TILL CANCELLED."
                    )
                    return order_messages
                self.session.page.wait_for_selector(
                    "//label/span[text()='Stop Limit']", timeout=3000
                ).click()
            if price_type in ["LIMIT", "STOP_LIMIT"]:
                self.session.page.fill("#limitPrice", str(limit_price))
            if price_type in ["STOP", "STOP_LIMIT"]:
                self.session.page.fill("#stopPrice", str(stop_price))
        except PlaywrightTimeoutError:
            pass
        try:
            if duration == "DAY" and price_type != "MARKET":
                self.session.page.click("xpath=//label/span[text()='Day']")
            elif duration == "GOOD_TILL_CANCELLED":
                self.session.page.click("xpath=//label/span[text()='60-day (GTC)']")
            if order_type == "SELL":
                try:
                    ok_button = self.session.page.get_by_role("button", name="Ok")
                    expect(ok_button).to_be_visible(timeout=5000)
                    ok_button.click()
                except (AssertionError, PlaywrightTimeoutError):
                    pass
                cost_basis = self.session.page.locator(
                    "text=Choose a cost basis method"
                ).nth(0)
                cost_basis.wait_for(timeout=5000)
                check_box = self.session.page.locator(
                    "text=Set as the preferred cost basis method for this holding."
                ).nth(0)
                check_box.locator("..").click()
        except (PlaywrightTimeoutError, AssertionError):
            pass
        try:
            continue_button = self.session.page.get_by_role("button", name="Continue")
            expect(continue_button).to_be_visible(timeout=3000)
            continue_button.click()
        except (AssertionError, PlaywrightTimeoutError):
            pass
        try:
            self.session.page.wait_for_selector(
                "div.col-lg-6:nth-child(3) > twe-trade-detail:nth-child(2) > tds-card:nth-child(1) > div:nth-child(1) > tds-card-body:nth-child(1) > div:nth-child(3) > div:nth-child(1)",
                timeout=5000,
            )
            warning = self.session.page.get_by_text("errorBefore you can proceed").first
            warning_header = warning.text_content()
            warning_header = warning_header.replace("error", "").split(":")[0].strip()
            warning_items_locator = self.session.page.get_by_role("main")
            warning_items = warning_items_locator.locator("li").all()
            warning_text = {warning_header: []}
            for i, item in enumerate(warning_items):
                if i == 0:
                    warning_text[warning_header].append(item.text_content())
                if warning_text[warning_header][i - 1] != item.text_content():
                    warning_text[warning_header].append(item.text_content())
            order_messages["ORDER INVALID"] = warning_text
            return order_messages
        except PlaywrightTimeoutError:
            order_messages["ORDER INVALID"] = "No invalid order message found."
        try:
            preview = self.session.page.get_by_role("button", name="Preview Order")
            expect(preview).to_be_visible(timeout=10000)
            preview.click()
        except (AssertionError, PlaywrightTimeoutError):
            pass
        if after_hours:
            try:
                after_button = self.session.page.get_by_role("button", name="Continue")
                expect(after_button).to_be_visible(timeout=3000)
                after_button.click()
            except (AssertionError, PlaywrightTimeoutError):
                pass
        try:
            submit_button = self.session.page.get_by_role("button", name="Submit order")
            expect(submit_button).to_be_visible(timeout=5000)
            order_messages["ORDER PREVIEW"] = "Order preview loaded correctly."
            if dry_run:
                return order_messages
            submit_button.click()
        except (AssertionError, PlaywrightTimeoutError):
            raise Exception("No place order button found cannot continue.")
        try:
            survey_overlay = self.session.page.get_by_text("Help us improve")
            survey_overlay.wait_for(timeout=3000)
            survey_clear = self.session.page.get_by_text("Close")
            survey_clear.click()
        except PlaywrightTimeoutError:
            pass
        try:
            order_handle_one = self.session.page.get_by_text("Order #")
            order_handle_one.wait_for(timeout=5000)
            try:
                order_handle_two = self.session.page.get_by_text("Submitted at")
                order_handle_two.wait_for(timeout=5000)
            except PlaywrightTimeoutError:
                order_handle_two = self.session.page.get_by_text("Submitted on")
                order_handle_two.wait_for(timeout=5000)
            order_number_text = order_handle_one.text_content()
            order_match = re.search(r"Order #(\d+)", order_number_text)
            if order_match:
                order_number = order_match.group(1)
            else:
                order_number = "No order number found."
            order_date_text = order_handle_two.text_content()
            print(f"{order_date_text}")
            date_match = re.search(
                r"Submitted (at|on) (\d{1,2}:\d{2} [ap]\.m\., ET [A-Za-z]+ \d{1,2}, \d{4})",
                order_date_text,
            )
            if date_match:
                date_str = date_match.group(2)
                date_parts = date_str.split(", ET")
                order_date = (
                    date_parts[1].strip()
                    if len(date_parts) > 1
                    else "No order date found."
                )
                order_time = (
                    date_parts[0].replace(".", "")
                    if len(date_parts) > 1
                    else "No order time found."
                )
            else:
                order_date = "No order date found."
                order_time = "No order time found."
            order_confirm = {
                "Order Number": order_number,
                "Date": order_date,
                "Time": order_time,
            }
            order_messages["ORDER CONFIRMATION"] = order_confirm
            return order_messages
        except PlaywrightTimeoutError:
            order_messages["ORDER CONFIRMATION"] = (
                "No order confirmation page found. Order Failed."
            )
            return order_messages

    def get_quote(self, symbol):
        """
        Get a quote for a stock.

        Args:
            symbol (str): The ticker symbol of the stock.

        Returns:
            str: The price of the stock.
        """
        self.session.go_url(order_page())
        quote_box = self.session.page.wait_for_selector(
            "//input[@placeholder='Get Quote']"
        )
        quote_box.click()
        quote_box.fill("")
        quote_box.fill(symbol)
        self.session.page.keyboard.press("Tab")
        for _ in range(3):
            quote_price = self.session.page.wait_for_selector(
                "(//div[@data-testid='txt-quote-value'])[2]", timeout=10000
            ).text_content()
            sleep(1)
            if quote_price != "$—":
                quote_price = float(quote_price.replace("$", "").replace(",", ""))
            else:
                quote_price = None
        return quote_price
