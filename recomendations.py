#!/usr/bin/python3
import yfinance as yf
import requests
import json
from tinkoff import TinkoffApi
from config import api_key
from bs4 import BeautifulSoup
import unicodedata


def get_file_data(filename):
    with open(filename, 'r') as file:
        data = file.readlines()
    return data


def append_data_to_file(file_name, string):
    with open(file_name, 'a') as file:
        file.write(string + '\n')


def company_open_price(companies_list):
    company_prices = {}
    for company in companies_list:
        clean_company_name = company.rstrip()
        recomendation_data = get_recomendation_data(clean_company_name)
        try:
            price = yf.Ticker(clean_company_name).info['open']
            recomendation = get_recomendation_result(recomendation_data)
            company_prices[clean_company_name] = {'price': price, 'recomendation': recomendation}
            if recomendation:
                # recomendation = f"{clean_company_name} - {company_prices[clean_company_name]['price']} - {company_prices[clean_company_name]['recomendation']}\n"
                recomended_company = clean_company_name
                append_data_to_file('recomendations.txt', recomended_company)
        except ValueError:
            print('Не удалось получить цену')
        except Exception as e:
            continue

    return company_prices


def get_recomendation_data(company_name):
    yahoo_finance_recommendation_url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{company_name}?modules=recommendationTrend"
    response = requests.get(url=yahoo_finance_recommendation_url).text
    json_data = json.loads(response)
    try:
        recomendation_period0 = json_data['quoteSummary']['result'][0]['recommendationTrend']['trend'][0]
    except Exception as error:
        print('Не удалось получить значения для рекомендуемого периода 0. Ошибка:')
        print(json_data)
        return False
    return recomendation_period0


def get_recomendation_result(recomendation_data):
    try:
        strong_buy = recomendation_data['strongBuy']
        buy = recomendation_data['buy']
        hold = recomendation_data['hold']
        sell = recomendation_data['sell']
        strong_sell = recomendation_data['strongSell']
        if (strong_buy + buy) > 20 and (hold + sell + strong_sell) < 10:
            return True
    except:
        print('Ошибка: получен некорректный формат данных')
        return False


def get_sp500_companies_names():
    url = "http://slickcharts.com/sp500"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"}

    response = requests.get(url, headers=headers)
    data = response.text
    soup = BeautifulSoup(data, "html5lib")

    table = soup.find_all('table')[0]
    rows = table.find_all('tr')[1:]

    companies = {}

    for row in rows:
        cols = row.find_all('td')
        company_position = cols[0].get_text()
        company_name = cols[1].get_text()
        company_short_name = cols[2].get_text()
        company_weight = float(cols[3].get_text())
        company_price = cols[4].get_text()
        companies[company_short_name] = {'position': company_position,
                                         'name': company_name,
                                         'weigh': company_weight,
                                         'price': unicodedata.normalize('NFKD', company_price).lstrip()
                                         }
    sp500_companies_names_list = []
    for company in companies.keys():
        if ',' not in companies[company]['price']:
            if float(companies[company]['price']) < 1000:
                sp500_companies_names_list.append(company)
    return sp500_companies_names_list


def get_intersection_companies(sp500, tinkof_companies):
    sp500_companies = set(sp500)
    tinkof_companies = set(tinkof_companies)
    intersection_companies = sp500_companies.intersection(tinkof_companies)
    return intersection_companies


def main():
    tinkof_api = TinkoffApi(api_key)
    tinkof_companies = tinkof_api.get_companies_list().keys()
    sp500_companies = get_sp500_companies_names()
    intersection_companies = get_intersection_companies(sp500_companies, tinkof_companies)
    company_open_price(intersection_companies)


if __name__ == '__main__':
    main()
