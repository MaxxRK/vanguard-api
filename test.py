import traceback

from vanguard.account import AllAccount
from vanguard.order import Duration, Order, OrderSide, PriceType
from vanguard.session import VanguardSession

login_username = input("Input your username: ")
login_username = login_username.strip()
login_password = input("Input your password: ")
login_password = login_password.strip()
login_input = input("Input last four of your cell phone used to login on vanguard.com: ")
login_input = int(login_input.strip().upper())

profile = input("Input profile name: ")
profile = profile.strip().lower()
session = VanguardSession(title=profile, headless=True)
logged_in = session.login(login_username, login_password, login_input)
if logged_in:
    code = input("Enter 2fa code: ")
    session.login_two(code)
else:
    print("Vanguard logged in without 2fa!")

account_info = AllAccount(session)
account_info.get_account_ids()
account_info.get_holdings()

print(f"Total value: {account_info.total_value}")
print(f"Account numbers/totals: {account_info.account_totals}")
for account in account_info.accounts_positions.keys():
    print(f"Account: {account}")
    for type in account_info.accounts_positions[account].keys():
        print(f"Type: {type}")
        for stock in account_info.accounts_positions[account][type]:
            print(
                f'{stock["symbol"]} of price {stock["price"]} and quantity {stock["quantity"]}'
            )
order = Order(session)
price = order.get_quote("INTC")
print(f"Price of INTC: {price}")
for account in account_info.account_numbers:
    try:
        messages = order.place_order(
            account,
            1,
            PriceType.MARKET,
            "INTC",
            Duration.DAY,
            OrderSide.BUY,
            after_hours=True,
            dry_run=True,
        )
        if messages["ORDER INVALID"] == "" or messages["ORDER CONFIRMATION"] != "":
            print(f'Order confirmation: {messages["ORDER CONFIRMATION"]}')
        else:
            print(f'Order Invalid: {messages["ORDER INVALID"]}')
    except Exception as e:
        traceback.print_exc()
        print(f"Script exception: {e}")
        print(f'Error placing order for account {account}: {messages["ORDER INVALID"]}')
session.close_browser()
