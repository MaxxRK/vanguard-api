# vanguard-api
 A reverse-engineered python API to interact with the Vanguard Trading platform.

 This is not an official api! This api's functionality may change at any time.

 This api provides a means of buying and selling stocks through Vanguard. It uses playwright to scrape data and to interact with the website.

 ---

## Contribution
I am new to coding and new to open-source. I would love any help and suggestions!

## Disclaimer
I am not a financial advisor and not affiliated with Vanguard in any way. Use this tool at your own risk. I am not responsible for any losses or damages you may incur by using this project. This tool is provided as-is with no warranty.

## Setup
Install using pypi:
```
pip install vanguard-api
```
This package requires playwright. After installing vanguard-api, you will need to finish the install of playwright. You can do this in most cases by running the command:
```
playwright install
```
If you would like some more information on this, you can find it [here](https://playwright.dev/python/docs/intro).

You will also need to install the 'requirements.txt' file in this repository. You can do this by running the command:
```
pip install -r requirements.txt
```
This installs a custom version of playwright_stealth that will work with this library.

## Quickstart
Checkout `test.py` for a quickstart example it will: 
- Login and print account info.
- Print out Holdings.
- Place a dry run market order for 'INTC' on the first account in the `account_numbers` list
- Print out the order confirmation


---

 ## Implemented Features
 - [x] Login
 - [x] Login with MFA
 - [x] Get Account Data
 - [x] Place Market Orders
 - [x] Get Currently Held Positions
 - [x] Get Quotes
 - [x] Place Limit Orders

## TO DO
 - [ ] Get Order Status
 - [ ] Cancel placed orders
 - [ ] Options
 - [ ] Give me some Ideas!

## If you would like to support me, you can do so here:
[![GitHub Sponsors](https://img.shields.io/github/sponsors/maxxrk?style=social)](https://github.com/sponsors/maxxrk) 