import requests
from bs4 import BeautifulSoup
from time import sleep
from dotenv import load_dotenv
import os

def configure():
    load_dotenv()

configure()


TOKEN_BOT = os.getenv('TOKEN_BOT')
CHAT_ID = os.getenv('CHAT_ID')
coingecko_url = 'https://www.coingecko.com/en/watchlists/high-volume'
high_volume_coins = []
upbit_vol = []
upbit_tickers_oi = []


def send_telegram_message(message):
    telegram_url = f'https://api.telegram.org/bot{TOKEN_BOT}/sendMessage'
    params = {'chat_id': CHAT_ID, 'text': message}
    response = requests.post(telegram_url, params=params)
    if response.status_code != 200:
        print(f'Failed to send message to Telegram. Error code: {response.status_code}')


def coingecko_hvc():
    print("Fetching coingecko high volume coins...")
    response = requests.get(coingecko_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    tbody = soup.find('tbody', {'data-target': 'currencies.contentBox'})

    for tr in tbody.find_all('tr'):
        td = tr.find('td', {'data-sort': True})
        if td:
            text = td.text.strip()
            coin_name, symbol = text.split('\n\n')
            symbol = symbol.strip()  # Remove leading/trailing whitespace
            high_volume_coins.append(symbol)


def upbit_hvc():
    print("Fetching upbit volume...") 
    api_url = 'https://api.coingecko.com/api/v3/exchanges/upbit/tickers'
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        tickers = data['tickers']
        sorted_tickers = sorted(tickers, key=lambda x: x['converted_volume']['usd'], reverse=True)
        bases_seen = set()  # To keep track of bases already added
        
        for ticker in sorted_tickers:
            base = ticker['base']
            volume = ticker['converted_volume']['usd']
            
            if base in high_volume_coins and base not in bases_seen:
                bases_seen.add(base)    
                upbit_vol.append({'base': base, 'volume': volume})


def ticker_oi():
    print("Fetching open interest...")
    
    for coin in upbit_vol:
        base = coin['base']
        open_interest_url = f"https://api.bybit.com/derivatives/v3/public/open-interest?category=linear&symbol={base}USDT&interval=5min"
        response = requests.get(open_interest_url)

        if response.status_code == 200:
            open_interest_data = response.json()
            if 'list' in open_interest_data['result']:
                open_interest = open_interest_data['result']['list']

                if len(open_interest) == 0:  # Check if the list is empty
                    continue  # Skip to the next iteration

                open_interest = open_interest_data['result']['list'][0]['openInterest']
                upbit_tickers_oi.append({'base': base, 'oi' : open_interest})


def aggr():
    print("Aggregating output...\n\n")
    message = ""  # Reset the message variable to an empty string
    
    data = []
    message += f"UPBIT VOLUME \n----------------------------------- \n"
    
    for coin in upbit_vol:
        base = coin['base']
        volume = int(coin['volume'])  # Convert volume to an integer
        
        for ticker in upbit_tickers_oi:
            if ticker['base'] == base:
                oi = float(ticker['oi'])
                entry = {'base': base, 'volume': volume, 'oi': oi}
                
                # Check if the entry already exists in the data list
                if entry not in data:
                    data.append(entry)
                
                break
    
    sorted_data = sorted(data, key=lambda x: x['volume'], reverse=True)
    
    for entry in sorted_data:
        base = entry['base']
        volume = entry['volume']
        oi = int(entry['oi'])
        oi_formatted = "{:,.0f}".format(oi)
        volume_formatted = "{:,.0f}".format(volume)
        
        if oi_formatted.count(",") == 1:
            oi_formatted = oi_formatted + "K"
        elif oi_formatted.count(",") == 2:
            oi_formatted = oi_formatted + "M"
            
        if volume_formatted.count(",") == 1:
            volume_formatted = volume_formatted + "K"
        elif volume_formatted.count(",") == 2:
            volume_formatted = volume_formatted + "M"
        
        message += f"{base} | Upbit Volume: {volume_formatted} | OI: {oi_formatted}\n"

    send_telegram_message(message)
    

   

while True:
    coingecko_hvc()
    upbit_hvc()
    ticker_oi()
    aggr()
    sleep(7200)

   

