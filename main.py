import requests
from bs4 import BeautifulSoup
from time import sleep
from dotenv import load_dotenv
import os
import streamlit as st
import pandas as pd



def configure():
    load_dotenv()

configure()


TOKEN_BOT = os.getenv('TOKEN_BOT')
CHAT_ID = os.getenv('CHAT_ID')
coingecko_url = 'https://www.coingecko.com/en/watchlists/high-volume'
exchanges = ['Upbit', 'Bithumb', 'Paribu', 'BtcTurk PRO']
prev_data = {}

def send_telegram_message(message):
    telegram_url = f'https://api.telegram.org/bot{TOKEN_BOT}/sendMessage'
    params = {'chat_id': CHAT_ID, 'text': message}
    response = requests.post(telegram_url, params=params)
    if response.status_code != 200:
        print(f'Failed to send message to Telegram. Error code: {response.status_code}')


try:
    while True:
        response = requests.get(coingecko_url)
        soup = BeautifulSoup(response.content, 'html.parser')

        tbody = soup.find('tbody', {'data-target': 'currencies.contentBox'})

        high_volume_coins = []

        for tr in tbody.find_all('tr'):
            td = tr.find('td', {'data-sort': True})
            if td:
                url = td.find('a')['href']  # get the URL from the anchor tag
                text = td.text.strip()
                coin_name, symbol = text.split('\n\n')
                coin = {}
                coin['coin_name'] = coin_name
                coin['url'] = url  # add the URL to the dictionary

                markets_url = f"https://www.coingecko.com{coin['url']}"
                response_markets = requests.get(markets_url)
                soup_markets = BeautifulSoup(response_markets.content, 'html.parser')
                tbody_markets = soup_markets.find('tbody', {'data-target': 'gecko-table.paginatedShowMoreTbody'})
                tr_markets = tbody_markets.find('tr')
                tds = tr_markets.find_all('td')
                exchange = tds[1].find('a').text.strip()

                pair = tds[2].find('a').text.strip()
                volume = tds[8].text.strip()
                coin['exchange'] = exchange
                coin['pair'] = pair
                coin['volume'] = volume
                key = f"{exchange}:{pair}:{volume}"

                if key not in prev_data and exchange in exchanges:
                    high_volume_coins.append(coin)
                    prev_data['markets'] = key
                    print(key)
                    send_telegram_message(key)

        sleep(4*60*60)

except Exception as e:
    send_telegram_message(e)