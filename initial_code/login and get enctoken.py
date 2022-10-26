print('Login ...')

import sys
import os
sys.path.append(os.path.abspath('..') + '\\inhouse_functions')

import pyotp
import datetime
import pandas as pd
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

from telegram import telegram
from parameter import Parameter
from google_sheet import google_sheet

import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

trading_day = Parameter.Get_trading_day()
teg = telegram()

teg.send_message(teg.group.BT_Vs_Actual_diff, '*Login Start ... ⏳*')

for idx, line in enumerate(open("login_cred.cred").readlines()):
    locals()[f'user_id_{idx}'], locals()[f'password_{idx}'], locals()[f'totp_{idx}'] = line.split(" ")

try:
    # Driver Path
    webdriver_path = 'chromedriver.exe'

    # Login
    driver = webdriver.Chrome(service=Service(webdriver_path))
    driver.implicitly_wait(3)
    driver.get('https://kite.zerodha.com/')
    driver.find_element(By.XPATH, "//input[@id='userid']").send_keys(user_id_0)
    driver.find_element(By.XPATH, "//input[@id='password']").send_keys(password_0)
    driver.find_element(By.XPATH, "//button[normalize-space()='Login']").click()
    sleep(3)
    driver.find_element(By.XPATH, "//input[@type='text']").send_keys(pyotp.TOTP(totp_0).now())
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

    print('Cookies 1 save Successfully')
    teg.send_message(teg.group.BT_Vs_Actual_diff, 'Cookies 1 save Successfully')
    
    driver.close()
    sleep(2)
            
    # Login
    driver = webdriver.Chrome(service=Service(webdriver_path))
    driver.implicitly_wait(3)
    driver.get('https://kite.zerodha.com/')
    driver.find_element(By.XPATH, "//input[@id='userid']").send_keys(user_id_1)
    driver.find_element(By.XPATH, "//input[@id='password']").send_keys(password_1)
    driver.find_element(By.XPATH, "//button[normalize-space()='Login']").click()
    sleep(3)
    driver.find_element(By.XPATH, "//input[@type='text']").send_keys(pyotp.TOTP(totp_1).now())
    driver.find_element(By.XPATH, "//button[normalize-space()='Continue']").click()
    sleep(2)

    # get enctoken
    raw_cookies = driver.get_cookies()
    for cookie in raw_cookies:
        if cookie['name'] == 'enctoken':
            cookies = cookie['value']
            f = open("zerodha_cookies.txt", "w")
            f.write(cookies)
            f.close()
            break

    print('Cookies 2 save Successfully')
    teg.send_message(teg.group.BT_Vs_Actual_diff, 'Cookies 2 save Successfully')

    # Download Instruments
    data = pd.read_csv('https://api.kite.trade/instruments')
    data.to_csv('../instrument_file.csv', index=False) 
    print('Instrument downloaded')
    teg.send_message(teg.group.BT_Vs_Actual_diff, 'Instrument downloaded')

    # clean trade sheet
    exec(open('../inhouse_functions/Clean Trade sheet.py').read())
    teg.send_message(teg.group.BT_Vs_Actual_diff, 'Trade Sheet Clean Done')

    # Update Date and day On PNL Sheet
    BT_result_sheet = google_sheet().get_sheet(google_sheet.sheet_ids.BT_result_sheet)
    row_no = len(google_sheet.get_sheet_df(BT_result_sheet)) + 2
    google_sheet.Update_cell(BT_result_sheet, row_no, 1, str(datetime.datetime.today().date()))
    google_sheet.Update_cell(BT_result_sheet, row_no, 2, trading_day)

    print('Date update success on BT Sheet    ', datetime.datetime.today().date(), trading_day, '\n')
    teg.send_message(teg.group.BT_Vs_Actual_diff, f'Date update success on BT Sheet \n_{datetime.datetime.today().date()} {trading_day}_')

    # all done
    print('Everything done successfully :)')
    teg.send_message(teg.group.BT_Vs_Actual_diff, '*Everything done successfully :) ✅*')
    sleep(30)
except Exception as e:
    msg = f"*⚠️⚠️⚠️ Error !!! ⚠️⚠️⚠️ \nLogin Code stop \n{e}*"
    print(msg)
    telegram().send_message(telegram.group.BT_Vs_Actual_diff, msg)
    sleep(30)