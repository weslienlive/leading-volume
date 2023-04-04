from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from time import sleep
import requests


options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--log-level=3')
options.add_experimental_option('excludeSwitches', ['enable-logging'])
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36")
driver_manager = ChromeDriverManager()
driver = webdriver.Chrome(service=Service(executable_path=driver_manager.install()), options=options)
url = 'https://www.coingecko.com/en/watchlists/high-volume'
driver.get(url)



def main():

    # initialize the previous lead_cex as empty
    previous_lead_cex = {}

    while True:
        pass
        try:
            # Check if the table element is present in the page's DOM
            table = driver.find_elements(By.XPATH, "//tbody[@data-target='currencies.contentBox']")

            # get all the divs with class tw-flex.center
            divs = table[0].find_elements(By.CLASS_NAME, 'tw-flex.center')
            print(f'Table found.')

            links = {}
            lead_cex = {}

            # loop through all the divs in divs list
            for div in divs:
                # get the link from the div
                link = BeautifulSoup(div.get_attribute('innerHTML'), 'html.parser').find('a')
                href = link['href']
                coin_name = link.text.split('\n')[2]

                # skip storing the href if the coin is in the given list
                if coin_name in ['Tether', 'Bitcoin', 'Ethereum', 'USD Coin', 'Binance USD', 'WETH', 'Dai', 'Wrapped BNB', 'Wrapped AVAX']:
                    continue
                
                links[coin_name] = href

            # loop through all the links in the links dictionary
            for coin_name, href in links.items():
                # navigate to the coin page
                driver.get(f'https://www.coingecko.com{href}')
                sleep(2)  # wait for the page to load
                
                # extract the required information from the page source
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                tbody = soup.find('tbody', {'data-target': 'gecko-table.paginatedShowMoreTbody'})
                Exchange = tbody.find('a').text
                Symbol = tbody.find_all('td')[2].find('a').text.strip()
                Volume = tbody.find_all('td')[8].text.strip()
                
                # store the extracted information if the exchange is one of the leading exchanges
                if Exchange in ['Upbit', 'Bithumb', 'Paribu', 'BtcTurk PRO']:
                    lead_cex[coin_name] = {'Exchange': Exchange, 'Symbol': Symbol, 'Volume' : Volume}

                
                # navigate back to the watchlist page
                driver.back()
                sleep(2)  # wait for the page to load


            # check if the new information stored in lead_cex is different from the previous_lead_cex
            if lead_cex != previous_lead_cex:

                # if the information is different, loop through each coin in lead_cex and update only the data points that are different
                for coin_name, data in lead_cex.items():

                    # use setdefault() to get the previous data or an empty dictionary if the coin is new
                    previous_data = previous_lead_cex.setdefault(coin_name, {})

                    # update the previous data with only the data points that are different
                    for key, value in data.items():

                        if previous_data.get(key) != value:
                            previous_data[key] = value

                            # send a telegram message with the updated data
                            telegram_message({coin_name: previous_data})

                # update previous_lead_cex with the new information
                previous_lead_cex = lead_cex


        except Exception as e:
            print('An error occurred:', e)

        finally:
            # close the driver
            driver.quit()

        sleep(3600)


def telegram_message(lead_cex):
    # send a telegram message
    bot_token = '6129356517:AAFYdtrko-9IizivM0IL0LOrMhzFozzbyVU'
    chat_id = '5710064724'

    for coin_name, data in lead_cex.items():
        exchange = data["Exchange"]
        symbol = data["Symbol"]
        volume = data["Volume"]
        message = f"Coin: {coin_name}\nExchange: {exchange}\nSymbol: {symbol}\nVolume: {volume}"
        send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&parse_mode=Markdown&text={message}'
        response = requests.get(send_text)
        print(response.content)

main()