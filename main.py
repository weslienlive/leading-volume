from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from time import sleep
from tqdm import tqdm

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


try:
    # Check if the table element is present in the page's DOM
    table = driver.find_elements(By.XPATH, "//tbody[@data-target='currencies.contentBox']")

    # get all the divs with class tw-flex.center
    divs = table[0].find_elements(By.CLASS_NAME, 'tw-flex.center')
    print(f'Table found.')

    links = {}
    lead_cex = {}

    # loop through all the divs in divs list
    for div in tqdm(divs, desc="looping through all the divs"):
        # get the link from the div
        link = BeautifulSoup(div.get_attribute('innerHTML'), 'html.parser').find('a')
        href = link['href']
        coin_name = link.text.split('\n')[2]

        # skip storing the href if the coin is in the given list
        if coin_name in ['Tether', 'Bitcoin', 'Ethereum', 'USD Coin', 'Binance USD', 'WETH', 'Dai', 'Wrapped BNB', 'Wrapped AVAX']:
            continue
        
        links[coin_name] = href

    # loop through all the links in the links dictionary
    for coin_name, href in tqdm(links.items(), desc="looping through all links in links dict"):
        # navigate to the coin page
        driver.get(f'https://www.coingecko.com{href}')
        sleep(5)  # wait for the page to load
        
        # extract the required information from the page source
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        tbody = soup.find('tbody', {'data-target': 'gecko-table.paginatedShowMoreTbody'})
        Exchange = tbody.find('a').text
        Symbol = tbody.find_all('td')[2].find('a').text
        
        # store the extracted information if the exchange is one of the leading exchanges
        if Exchange in ['Upbit', 'Bithumb', 'Paribu', 'BtcTurk PRO']:
            lead_cex[coin_name] = {'Exchange': Exchange, 'Symbol': Symbol}
        
        # navigate back to the watchlist page
        driver.back()
        sleep(5)  # wait for the page to load


    # print the extracted information for leading exchanges
    print(lead_cex)

except Exception as e:
    print('An error occurred:', e)

finally:
    # close the driver
    driver.quit()
