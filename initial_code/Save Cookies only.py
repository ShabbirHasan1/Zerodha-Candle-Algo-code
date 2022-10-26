print('Login ...')

import sys
import os
sys.path.append(os.path.abspath('..') + '\\inhouse_functions')
import pyotp
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Driver Path
webdriver_path = 'chromedriver.exe'

# Login
driver = webdriver.Chrome(service=Service(webdriver_path))
driver.implicitly_wait(3)
driver.get('https://kite.zerodha.com/')
driver.find_element(By.XPATH, "//input[@id='userid']").send_keys('OC5883')
driver.find_element(By.XPATH, "//input[@id='password']").send_keys('bn123456')
driver.find_element(By.XPATH, "//button[normalize-space()='Login']").click()
sleep(3)
driver.find_element(By.XPATH, "//input[@type='text']").send_keys(pyotp.TOTP('ZMIXODSMIXBPU2YQXKSN46YUYO3KORPY').now())
driver.find_element(By.XPATH, "//button[normalize-space()='Continue']").click()
sleep(2)

# get enctoken
raw_cookies = driver.get_cookies()
for cookie in raw_cookies:
    if cookie['name'] == 'enctoken':
        cookies = cookie['value']
        f = open("../zerodha_cookies.txt", "w")
        f.write(cookies)
        f.close()
        break

print('Cookies save Successfully')
sleep(300)
