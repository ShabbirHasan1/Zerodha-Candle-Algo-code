code_name = 'SET Target'
import ctypes
ctypes.windll.kernel32.SetConsoleTitleW(code_name)
print(code_name)

import sys
import os
sys.path.append(os.path.abspath('..') + '\\BT vs Actual\\inhouse_functions')
os.chdir(os.path.abspath('..') + '\\BT vs Actual\\inhouse_functions')

import requests
import pandas as pd
import datetime
from time import sleep
from Candle_Data import candle_data
from strike_selection import get_fno_data, get_scrip_trading_symbol, get_scrip_instrument_token
from telegram import telegram
from play_sound import PlaySound

index = ['BANKNIFTY', 'NIFTY'][int(input('BANKNIFTY : 0\nNIFTY     : 1  :'))]

if int(input('Option : 1\nFuture : 2  : ')) == 1:
    strike = input('Entre Strike : ')
    scrip = strike + 'CE' if int(input('CALL : 0 \nPut  : 1  :')) == 0 else 'PE'
    scrip_token = get_scrip_instrument_token(index, scrip)
    scrip = get_scrip_trading_symbol(index, scrip)
    print('\nScrip           : ', scrip)
    print('Current Price   : ', candle_data(scrip_token, datetime.datetime.now() - datetime.timedelta(minutes=1))[0])
else:
    scrip, scrip_token, data = get_fno_data(index)
    print('\nScrip           : ', scrip)
    print('Current Price   : ', candle_data(scrip_token, datetime.datetime.now() - datetime.timedelta(minutes=1))[0])
    
print('\nSET TARGET\n')

print('Notify Me If Price ')
mode = int(input('Greater than : 0' + '\n' 
                 'Less than    : 1  : '))

target_price = float(input('Entre Target Price : '))
current_time = datetime.datetime.strptime(datetime.datetime.strftime(datetime.datetime.now(), '%H:%M'), '%H:%M').time()
check_time = datetime.datetime.combine(datetime.datetime.now().date(), current_time) - datetime.timedelta(seconds = 1)

market_open = True
while market_open:
    
    if datetime.datetime.now() > check_time:
        sleep(5)
        current_close_price = candle_data(scrip_token, check_time)[0]
        print(check_time, current_close_price)
        
        if mode == 0:
            if current_close_price >= target_price:
                if scrip.endswith('FUT'):
                    PlaySound(f'{index} Future Price Greater Then Target Price {target_price}')
                else:
                    PlaySound(f"{index} {scrip[-7:-2]} {'CALL' if scrip.endswith('CE') else 'PUT'} Greater Then Target Price {target_price}")
                break
                
        elif mode == 1:
            if current_close_price <= target_price:
                if scrip.endswith('FUT'):
                    PlaySound(f'{index} Future Price Less Then Target Price {target_price}')
                else:
                    PlaySound(f"{index} {scrip[-7:-2]} {'CALL' if scrip.endswith('CE') else 'PUT'} Less Then Target Price {target_price}")
                break
                
        check_time += datetime.timedelta(minutes=1)
    
    if datetime.datetime.now().time() > datetime.time(15,29):
        market_open = False
        
print('Target Reach at ', check_time)
sleep(300)