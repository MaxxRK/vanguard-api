from datetime import datetime
from itertools import zip_longest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from .session import VanguardSession
from .urls import holdings_page


class AllAccount:
    """
    A class to manage all accounts associated with a VanguardSession.

    This class provides methods to retrieve and manage information about all accounts associated with a given session.

    Attributes:
        session (VanguardSession): The session associated with the accounts.
        as_of_time (datetime): The time at which the account information was retrieved.
        account_totals (dict): The total value of each account associated with the session.
        total_value (float): The total value of all accounts.
        account_numbers (list): The account numbers associated with the session.
        accounts_positions (dict): The positions of each account associated with the session.

    Methods:
        _get_account_id(selector): Retrieves the account ID from a given selector.
        _parse_rows(table_rows, account_id): Parses the rows of a table to extract holdings information.
        get_holdings(): Retrieves and sets the holdings information of the account.
    """

    def __init__(self, VanguardSession: VanguardSession):
        """
        Initializes a SymbolHoldings object with a given VanguardSession.

        Args:
        VanguardSession (VanguardSession): The session associated with the accounts.
        """
        self.session = VanguardSession
        self.as_of_time: datetime = None
        self.account_totals: dict = {}
        self.total_value = None
        self.account_numbers = []
        self.accounts_positions: dict = {}

    def _get_account_id(self, selector):
        """
        Retrieves the account ID from a given selector.

        Args:
            selector (ElementHandle): The selector from which to retrieve the account ID.

        Returns:
           string: account_id
        """
        account_id = selector.query_selector('span > span > span > span').inner_text()
        return account_id.split("—")[2].strip().replace("*", "")


    def _parse_rows(self, table_rows, account_id):
        """
        Parses the rows of a table to extract holdings information.

        Args:
            table_rows (ElementHandle): The rows of the table to parse.
            account_id (string): The account ID associated with the table.
        """
        (stocks, stock_symbols, stock_descriptions,
         stock_prices, dollar_changes,
         percent_changes, quantities) = [], [], [], [], [], [], []
        for i, row in enumerate(table_rows):
            if i == 0:
                type = row.query_selector("th")
                if type is not None:
                    type = type.inner_text().strip()
                    if account_id not in self.accounts_positions:
                        self.accounts_positions[account_id] = {}
                    if type not in self.accounts_positions[account_id]:
                        self.accounts_positions[account_id][type] = []   
            elif i >= 2:
                stock_names = row.query_selector_all('th')
                for j, info in enumerate(stock_names):
                    description = info.inner_text().strip()
                    if j == 1:
                        stock_symbols.append(description.strip())
                    if j == 2:
                        stock_descriptions.append(description.strip())
                stock_price_elements = row.query_selector_all("td")
                for k, price in enumerate(stock_price_elements):
                    if k == 0:
                        price_text = price.inner_text()
                        stock_prices.append(float(price_text.replace("$", "").replace(",", "").strip()))
                    elif k == 1:
                        dollar_changes.append(price.inner_text())
                    elif k == 2:
                        percent_changes.append(price.inner_text())
                    elif k == 3:
                        quantities.append(float(price.inner_text()))
            if i == len(table_rows) - 1:
                for (stock_symbol, stock_description, stock_price, dollar_change,
                                    percent_change, quantity) in zip_longest(stock_symbols, stock_descriptions,
                                                        stock_prices, dollar_changes,
                                                        percent_changes, quantities, fillvalue=None):
                    stocks.append({
                        "symbol": stock_symbol,
                        "description": stock_description,
                        "price": stock_price,
                        "dollar_change": dollar_change,
                        "percent_change": percent_change,
                        "quantity": quantity
                    })
                    self.accounts_positions[account_id][type] = stocks
                
    

    def get_holdings(self):
        """
        Retrieves and sets the holdings information of the account.

        This method navigates to the account holdings page, waits for the holdings information to load, and then retrieves the holdings information from the page.

        Returns:
            bool: True if the holdings information was successfully retrieved, False otherwise.
        """
        try:
            self.session.go_url(holdings_page())
            self.as_of_time = datetime.strftime(
                datetime.now(), "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            self.session.page.wait_for_selector(
                '//span[contains(text(), "Expand all accounts")]',
                timeout=120000
                ).click()
            total_element = self.session.page.wait_for_selector('//p[@class="c11n-text-xl-headline accordion-headline"]')
            self.total_value = float(total_element.inner_text().split()[-1].replace(",","").replace("$",""))
            self.session.page.wait_for_selector("#overflow-override")
            all_selectors = self.session.page.query_selector_all("#overflow-override")
            for i, selector in enumerate(all_selectors):
                account_id = self._get_account_id(selector)
                self.account_numbers.append(account_id)
                table_wrapper = selector.wait_for_selector(f'#self_managed_table_{i}')
                table_entries = table_wrapper.query_selector_all('tbody')
                for j,entry in enumerate(table_entries):
                    if j == len(table_entries) - 1:
                        total_row = entry.query_selector_all('tr')
                        for row in total_row:
                            totals = row.inner_text().split()
                            self.account_totals[account_id] = totals[-1].replace("$", "")
                    table_rows = entry.query_selector_all('tr')
                    self._parse_rows(table_rows, account_id)      
            return True
        except PlaywrightTimeoutError:
            return False