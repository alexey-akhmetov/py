#!/usr/bin/python3
import time
from tinkoff import TinkoffApi
from config import api_key, balance_min_level

'''
цикл:
    1. Найти акции в портфеле (ключ=figi) +
    2. Найти акции выставленные на продажу (ключи=figi) +
    3. Найти акции в портфеле(п1) не входящие в акции на продажу(п2)
    4. Проверить рекомендации для найденных в п3 списке позициях.
    5. Если компания рекомендована к продаже:
         продать акцию по формуле "цена покупки + 1,5%"
    time.sleep(n)
'''

pause = 15


def main():
        api = TinkoffApi(api_key)
        portfolio_companies = api.get_portfolio_positions(sort_figi=True)
        portfolio_sellings_list = api.get_sellings()
        companies_for_selling = [company for company in portfolio_companies
                                 if company not in portfolio_sellings_list]
        for company in companies_for_selling:
            print(f'Выставляем на продажу компанию {company}')
            sell_price = api.get_sell_price(company)
            api.sell_lot(company, price=sell_price)
            time.sleep(15)


if __name__ == '__main__':
    main()
