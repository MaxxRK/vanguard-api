import re
from enum import Enum
from time import sleep

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

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
            self.session.page.wait_for_selector(
                "//div[text()=' Select Account ']", timeout=10000
            ).click()
            account_box = self.session.page.wait_for_selector(
                ".c11n-modal-dialog-open",
                timeout=10000,
            )
            account_selectors = account_box.query_selector_all("tds-list-option")
            for account in account_selectors:
                if account_id in account.text_content():
                    account.click()
                    break
        except PlaywrightTimeoutError:
            pass
        quote_box = self.session.page.wait_for_selector(
            "//input[@placeholder='Get Quote']"
        )
        quote_box.click()
        quote_box.fill("")
        quote_box.fill(symbol)
        self.session.page.press(
            "//input[@placeholder='Get Quote']",
            "Enter",
        )
        for _ in range(3):
            quote_price = self.session.page.wait_for_selector(
                "(//div[@data-testid='txt-quote-value'])[2]", timeout=10000
            ).text_content()
            sleep(1)
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
            buy_btn = self.session.page.wait_for_selector("xpath=//label[text()='Buy']")
            buy_btn.click()
        elif order_type == "SELL":
            sell_btn = self.session.page.wait_for_selector(
                "xpath=//label[text()='Sell']"
            )
            sell_btn.click()
        quantity_box = self.session.page.wait_for_selector(
            "//input[@placeholder='Enter Shares']"
        )
        quantity_box.fill("")
        quantity_box.type(str(quantity))
        if price_type == "MARKET":
            self.session.page.wait_for_selector("//label[text()='Market']").click()
        elif price_type == "LIMIT":
            if duration not in ["DAY", "GOOD_TILL_CANCELLED"]:
                order_messages["ORDER INVALID"] = (
                    "Limit orders must be DAY or GOOD TILL CANCELLED."
                )
                return order_messages
            self.session.page.wait_for_selector("//label[text()='Limit']").click()
        elif price_type == "STOP":
            if duration not in ["DAY", "GOOD_TILL_CANCELLED"]:
                order_messages["ORDER INVALID"] = (
                    "Stop orders must be DAY or GOOD TILL CANCELLED."
                )
                return order_messages
            self.session.page.wait_for_selector("//label[text()='Stop']").click()
        elif price_type == "STOP_LIMIT":
            if duration not in ["DAY", "GOOD_TILL_CANCELLED"]:
                order_messages["ORDER INVALID"] = (
                    "Stop orders must be DAY or GOOD TILL CANCELLED."
                )
                return order_messages
            self.session.page.wait_for_selector("//label[text()='Stop Limit']").click()
        try:
            if price_type in ["LIMIT", "STOP_LIMIT"]:
                self.session.page.fill("#limitPrice", str(limit_price))
            if price_type in ["STOP", "STOP_LIMIT"]:
                self.session.page.fill("#stopPrice", str(stop_price))
        except PlaywrightTimeoutError:
            pass
        try:
            if duration == "DAY":
                self.session.page.click("xpath=//label[text()='Day']")
            elif duration == "GOOD_TILL_CANCELLED":
                self.session.page.click("xpath=//label[text()='60-day (GTC)']")
            if order_type == "SELL":
                self.session.page.wait_for_selector(
                    "twe-cost-basis-modal tds-checkbox .tds-checkbox__indicator.tds-checkbox--blue",
                    timeout=3000,
                ).click()
                self.session.page.wait_for_selector(
                    "//button[contains(text(), ' Continue ')]",
                    timeout=10000,
                ).click()
                self.session.page.wait_for_selector(
                    "body > twe-root > main > twe-trade > form > div > div.row > div:nth-child(1) > twe-cost-basis-control > twe-cost-basis-modal > tds-modal > div.modal.visible > div > div.modal__content",
                    timeout=10000,
                )
        except PlaywrightTimeoutError:
            pass
        try:
            self.session.page.wait_for_selector(
                "body > twe-root > vg-vgn-nav > div > main > twe-trade > form > div > div.row > div.col-lg-6.col-xxl-4.tds-mb-9.d-none.d-xxl-block > twe-trade-detail > tds-card > div > tds-card-body > div.twe-flex-button-wrap > button:nth-child(2)",
                timeout=5000,
            ).click()
        except PlaywrightTimeoutError:
            pass
        if after_hours:
            try:
                sleep(2)
                self.session.page.wait_for_selector(
                    "//button[text()='Continue']",
                    timeout=5000,
                ).click()
            except PlaywrightTimeoutError:
                pass

        try:
            warning = self.session.page.wait_for_selector(
                "div.col-lg-6:nth-child(3) > twe-trade-detail:nth-child(2) > tds-card:nth-child(1) > div:nth-child(1) > tds-card-body:nth-child(1) > div:nth-child(3)",
                timeout=5000,
            )
            warning_header_selector = warning.query_selector("p")
            warning_header = warning_header_selector.text_content()
            warning_items = warning.query_selector_all("li")
            warning_text = {warning_header: []}
            for item in warning_items:
                warning_text[warning_header].append(item.text_content())
            order_messages["ORDER INVALID"] = warning_text
            return order_messages
        except PlaywrightTimeoutError:
            order_messages["ORDER INVALID"] = "No invalid order message found."

        try:
            order_preview = self.session.page.wait_for_selector(
                ".col-lg-7 > tds-card:nth-child(1) > div:nth-child(1) > tds-card-body:nth-child(1)",
                timeout=5000,
            )
            order_preview_text = order_preview.text_content()
            preview_parts = re.split(
                r"(Account|Transaction|Shares|Security|Order type|Duration|Commission|Estimated amount|\*)",
                order_preview_text,
            )
            order_preview = {
                "Account": preview_parts[2],
                "Transaction": preview_parts[4],
                "Shares": preview_parts[6],
                "Security": preview_parts[8],
                "Order type": preview_parts[10],
                "Duration": preview_parts[12],
                "Commission": preview_parts[14],
                "Estimated amount": preview_parts[18],
                "Note": preview_parts[20],
            }
            order_messages["ORDER PREVIEW"] = order_preview
            if dry_run:
                return order_messages
            try:
                self.session.page.click(
                    "//button[text()=' Submit Order ']", timeout=10000
                )
            except PlaywrightTimeoutError:
                raise Exception("No place order button found cannot continue.")
        except PlaywrightTimeoutError:
            order_messages["ORDER PREVIEW"] = "No order preview page found."

        try:
            order_handle_one = self.session.page.wait_for_selector(
                "body > twe-root > vg-vgn-nav > div > main > twe-confirm > div > div > div.col-lg-7.order-first.order-lg-last.tds-mb-4.tds-mb-m-9 > h2",
                timeout=5000,
            )
            order_handle_two = self.session.page.wait_for_selector(
                "body > twe-root > vg-vgn-nav > div > main > twe-confirm > div > div > div.col-lg-7.order-first.order-lg-last.tds-mb-4.tds-mb-m-9 > div.page-heading.tds-mb-7 > p",
                timeout=5000,
            )
            order_number_text = order_handle_one.text_content()
            order_match = re.search(r"Received order #(\d+)", order_number_text)
            if order_match:
                order_number = order_match.group(1)
            else:
                order_number = "No order number found."
            order_date_text = order_handle_two.text_content()
            date_match = re.search(
                r"Submitted on (\d{2}/\d{2}/\d{4}) at (\d{1,2}:\d{2} [AP]\.M\. ET)",
                order_date_text,
            )
            if date_match:
                date_str = date_match.group(1)
                time_str = date_match.group(2).replace(".", "")
                order_date = date_str
                order_time = time_str
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
        self.session.page.press(
            "//input[@placeholder='Get Quote']",
            "Enter",
        )
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
