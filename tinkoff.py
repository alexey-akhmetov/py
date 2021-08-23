#!/usr/bin/python3
import requests
from config import api_key, profit_percent


class TinkoffApi:
    BASE_API_URL = 'https://api-invest.tinkoff.ru/openapi'

    def __init__(self, api_key, sell_percent=profit_percent):
        self.api_key = api_key
        self.profit_sell_percent = sell_percent
        self.headers = {
                'accept': 'application/json',
                'Authorization': self.api_key,
            }
        self.default_account_id = self.accounts[0]
        self.balance = self.__get_balance()

    def __get_response(self, url, params=None):
        response = requests.get(url,
                                headers=self.headers,
                                params=params)
        return response

    def __post_response(self, url, params, json):
        response = requests.post(url,
                                 params=params,
                                 headers=self.headers,
                                 json=json)
        return response

    def __get_balance(self):
        response = self.__get_response(TinkoffApi.BASE_API_URL + '/portfolio/currencies')
        raw_balance = response.json()
        balance = {elem['currency']: elem['balance'] for elem in raw_balance['payload']['currencies']}
        return balance

    def __get_portfolio(self):
        raw_portfolio = self.__get_response(TinkoffApi.BASE_API_URL + '/portfolio')
        raw_portfolio_positions_list = raw_portfolio.json()['payload']['positions']
        portfolio_positions_list = filter(lambda elem: elem['instrumentType']=='Stock', raw_portfolio_positions_list)
        return portfolio_positions_list

    def __get_ticker_info(self, ticker_name):
        params = {'ticker': ticker_name}
        raw_ticker_info = self.__get_response(TinkoffApi.BASE_API_URL + '/market/search/by-ticker',
                                              params=params)
        ticker_info = raw_ticker_info.json()['payload']['instruments']
        return ticker_info

    def __get_ticker_prices(self, figi):
        params = {'figi': figi,
                  'depth': 1}
        raw_ticker_prices = self.__get_response(TinkoffApi.BASE_API_URL + '/market/orderbook',
                                                params=params)
        ticker_info = raw_ticker_prices.json()['payload']
        return ticker_info

    def __get_companies_list(self):
        raw_companies_list = self.__get_response(TinkoffApi.BASE_API_URL + "/market/stocks")
        companies_list = raw_companies_list.json()['payload']['instruments']
        return companies_list

    def __get_sellings(self):
        params = (
            ('brokerAccountId', self.default_account_id),
        )
        raw_sellings_list = self.__get_response(TinkoffApi.BASE_API_URL + "/orders", params=params)
        sellings_list = raw_sellings_list.json()['payload']
        return sellings_list

    def get_ticker_prices(self, figi):
        company_info = self.__get_ticker_prices(figi)
        return company_info

    def get_sellings(self):
        sellings_list = self.__get_sellings()
        sellings_list = {company['figi']: company for company in
                         sellings_list}
        return sellings_list

    def get_companies_list(self, sort_figi=False):
        raw_companies_list = self.__get_companies_list()
        if sort_figi:
            key = 'figi'
        else:
            key = 'ticker'
        companies_list = {company[key]: company for company in raw_companies_list}
        return companies_list

    def get_figi_by_name(self, ticker_name):
        ticker_info = self.__get_ticker_info(ticker_name)
        figi_code = ticker_info[0]['figi']
        return figi_code

    def buy_lot(self, lot_name=None, lots=1, figi=False):
        if not figi:
            figi_name = self.get_figi_by_name(lot_name)
        else:
            figi_name = lot_name
        params = {'figi': figi_name,
                  'brokerAccountId': self.default_account_id}
        data = {"lots": lots,
                "operation": "Buy"}
        url = TinkoffApi.BASE_API_URL + "/orders/market-order"
        response = self.__post_response(url,
                                        params=params,
                                        json=data)

        return response.text

    def sell_lot(self, lot_figi, lots=1, price=None, account_id=None):
        if account_id is None:
            account_id = self.default_account_id
        if price is None:
            price = self.get_ticker_prices(lot_figi)['lastPrice']
        params = {'figi': lot_figi,
                  'brokerAccountId': account_id}
        data = {"lots": lots,
                "operation": "Sell",
                "price": price}
        url = TinkoffApi.BASE_API_URL + "/orders/limit-order"
        response = self.__post_response(url,
                                        params=params,
                                        json=data)
        return response.text

    def get_sell_recomendation(self, expected_yield, lot_price, lots_num, sell_percent=None):
        if sell_percent is None:
            sell_percent = self.profit_sell_percent / 100
        percent = sell_percent / 100
        current_price = lot_price * lots_num
        profit_balance = lot_price * lots_num * percent
        if expected_yield >= profit_balance:
            return True
        else:
            return False

    def get_ticker_info(self, ticker_name):
        ticker_info = self.__get_ticker_info(ticker_name)
        return ticker_info

    @property
    def portfolio_companies_expected_yield(self):
        portfolio_companies = self.__get_portfolio()
        portfolio_companies_expected_yield = {company['ticker']: company['expectedYield']['value']
                                              for company in portfolio_companies}
        return portfolio_companies_expected_yield

    def get_sell_recomendations(self, portfolio_companies=None, figi=False, profit_only=False):
        portfolio_companies_expected_yield = {}
        if portfolio_companies is None:
            portfolio_companies = self.__get_portfolio()
        for company in portfolio_companies:
            if figi:
                company_name = company['figi']
            else:
                company_name = company['ticker']
            expected_yield = company['expectedYield']['value']
            lot_price = company['averagePositionPrice']['value']
            lot_balance = company['balance']
            sell_percent = self.profit_sell_percent
            sell_recomendation = self.get_sell_recomendation(expected_yield, lot_price, lot_balance,
                                                             sell_percent=sell_percent)
            portfolio_companies_expected_yield[company_name] = sell_recomendation
            if profit_only:
                portfolio_companies_expected_yield = {key: value for key, value in portfolio_companies_expected_yield.items() if value is True}
        return portfolio_companies_expected_yield

    def get_sell_price(self, lot):
        portfolio_companies = self.get_portfolio_positions(sort_figi=True)
        lot_price = float(portfolio_companies[lot]['averagePositionPrice']['value'])
        profit = lot_price / 100 * self.profit_sell_percent
        lot_sell_price = round(lot_price + profit, 2)
        print('Цена покупки:', lot_price)
        print('Цена продажи:', lot_sell_price)
        print('Profit:', lot_sell_price - lot_price)

        return lot_sell_price

    def get_portfolio_positions(self, sort_figi=False):
        raw_portfolio_positions = self.__get_portfolio()
        if sort_figi:
            key = 'figi'
        else:
            key = 'ticker'
        portfolio_positions = {position[key]: position for position in raw_portfolio_positions
                               if position['instrumentType'] == 'Stock'}
        return portfolio_positions

    @property
    def balance_rub(self):
        raw_balance = self.__get_balance()
        if 'RUB' in raw_balance.keys():
            return raw_balance['RUB']
        else:
            return None

    @property
    def balance_usd(self):
        raw_balance = self.__get_balance()
        if 'USD' in raw_balance.keys():
            return raw_balance['USD']
        else:
            return None

    @property
    def balance_eur(self):
        raw_balance = self.__get_balance()
        if 'EUR' in raw_balance.keys():
            return raw_balance['EUR']
        else:
            return None

    @property
    def accounts(self):
        response = self.__get_response(TinkoffApi.BASE_API_URL + '/user/accounts')
        accounts_info = response.json()['payload']['accounts']
        brokers_accounts = [account['brokerAccountId'] for account in accounts_info]
        return brokers_accounts

    def __repr__(self):
        info = f'ID аккаунта: {self.default_account_id}'
        return info


if __name__ == '__main__':
    api = TinkoffApi(api_key, sell_percent=profit_percent)
    print('Информация:', api)
    print('Портфолио:', api.get_portfolio_positions())
    print('USD на счету: ', api.balance_usd)
    print('get_ticker_info', api.get_figi_by_name('BAC'))
    print('Предполагаемая доходность', api.portfolio_companies_expected_yield)
    print('Рекомендации к продаже', api.get_sell_recomendations(figi=False))
    print('get_sellings', api.get_sellings())
    print('get_companies_list', api.get_companies_list(sort_figi=True))
    print('Информация о тикере', api.get_ticker_info('MSFT'))
    print('Цена акции', api.get_ticker_prices('BBG000BPH459')['lastPrice'])
    # print('Купить: ', api.buy_lot('APPL', lots=3))
    # print('Продать: ', api.sell_lot('BBG000BCTLF6')) # если цена не указана, то продажа по текущей цене


# продажа ответ: Продать:  {"trackingId":"9d11967209a86772","payload":{"orderId":"179028517530","operation":"Sell","status":"New","requestedLots":1,"executedLots":0,"commission":{"currency":"USD","value":0}},"status":"Ok"}


