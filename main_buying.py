#!/usr/bin/python3
from tinkoff import TinkoffApi
from config import api_key, balance_min_level
import time
import random

'''
1. Проверять текущий баланс +
2. Проверять акции в портфеле +
3. Получать акции из рекомендаций, которых нет в портфеле. - 
'''

pause = 15


def get_portfolio_companies_names(api):
    companies_names = api.get_portfolio_positions().keys()
    return set(companies_names)


def read_file(file_name):
    with open(file_name, 'r') as file:
        file_strings_list = file.read().splitlines()
    return file_strings_list


def get_ticker_price(ticker_name, api):
    figi = api.get_figi_by_name(ticker_name)
    ticker_info = api.get_ticker_prices(figi)
    ticker_price = ticker_info['lastPrice']
    return ticker_price


def buying_random_company(companies_list, api):
    current_balance = api.balance_usd
    if companies_list is False:
        print('Список компаний пуст')
        return False
    shuffled_companies_list = sorted(companies_list, key=lambda *args: random.random())
    print('Компании к покупке', shuffled_companies_list)
    for company_name in shuffled_companies_list:
        ticker_price = get_ticker_price(company_name, api)
        if ticker_price <= current_balance:
            print(f'Покупаем акцию {company_name} !! :)')
            buying_result = api.buy_lot(company_name)
            time.sleep(5)
            current_balance = api.balance_usd
            print(f'Куплена акция компании {company_name}! ',
                  f'Текущий баланс: {current_balance} '
                  f'Результат покупки: {buying_result} ')
            return True


def main():
    api = TinkoffApi(api_key)
    current_balance = api.balance_usd
    print('Текущий баланс', current_balance)
    portfolio_companies_names = get_portfolio_companies_names(api)
    recomendations_companies = set(read_file('recomendations.txt'))
    companies_for_buying = [company for company in recomendations_companies
                            if company not in portfolio_companies_names]
    if current_balance >= balance_min_level:
        buying_random_company(companies_for_buying, api)
        time.sleep(pause)
    else:
        print(f'Покупка невозможна! На счету {current_balance}',
              f'Минимальный баланса: {balance_min_level}')
        time.sleep(pause)

        # print('Рекомендации', recomendations_companies_names)
        # print('Компании в портфеле', portfolio_companies_names)


if __name__ == '__main__':
    main()
