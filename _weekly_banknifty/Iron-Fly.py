#!/usr/bin/env python
# coding: utf-8

# In[ ]:


code_name = 'BN Iron_Fly 1 to 10'
import ctypes
ctypes.windll.kernel32.SetConsoleTitleW(code_name)
print(code_name)

index = 'BANKNIFTY'


# In[ ]:


import sys
import os
sys.path.append(os.path.abspath('..') + '\\inhouse_functions')
import pandas as pd
import datetime
from time import sleep
from Candle_Data import candle_data
from strike_selection import *
from telegram import telegram
from google_sheet import google_sheet as gsheet
from play_sound import PlaySound

entry_times = [datetime.time(9, 19), datetime.time(9, 21), datetime.time(9, 26), datetime.time(9, 31), datetime.time(9, 36),
               datetime.time(9, 41), datetime.time(9, 46), datetime.time(9, 51), datetime.time(9, 56), datetime.time(10, 1)]

if index == 'BANKNIFTY':
    caps_strategy = 'BN IFW ' + str(1)
    BT_sheet, ts_ce_index, ts_pe_index = gsheet().get_sheet_and_index(gsheet.sheet_ids.bt_bn,caps_strategy)
    
elif index == 'NIFTY':
    caps_strategy = 'NF IFW ' + str(1)
    BT_sheet, ts_ce_index, ts_pe_index = gsheet().get_sheet_and_index(gsheet.sheet_ids.bt_nf,caps_strategy)

entry_time = datetime.datetime.combine(datetime.datetime.now().date() , entry_times[0]) - datetime.timedelta(seconds=1)
check_time = entry_time
hedge_sd = 2
entry_times = entry_times[1:]
sell_flag = 0
sheet_col = 1

try: 
    while True:

        if (datetime.datetime.now() - check_time) > datetime.timedelta(minutes=2):
            sleep_time = 0.03
        else:
            sleep_time = 7

        if datetime.datetime.now() > check_time and sell_flag == 0:
            sleep(sleep_time)
            print(f'Straddle {10 - len(entry_times)}   Sell at {check_time}')
            PlaySound(f'IRON FLY {10 - len(entry_times)}')

            # getting strangle strike
            ce_scrip, ce_scrip_token, ce_price, pe_scrip, pe_scrip_token, pe_price, futures_scrip, futures_token, futures = select_straddle_strikes(index, check_time)

            ce_hedge_limit = int(ce_scrip[:-2]) + ((ce_price + pe_price) * hedge_sd)
            pe_hedge_limit = int(pe_scrip[:-2]) - ((ce_price + pe_price) * hedge_sd)
            ce_hedge = str(int(ce_hedge_limit - (ce_hedge_limit % 100) + 100)) + 'CE'
            pe_hedge = str(int(pe_hedge_limit - (pe_hedge_limit % 100))) + 'PE'

            print('scrip\tprice\thedge')
            print(ce_scrip, ce_price, ce_hedge)
            print(pe_scrip, pe_price, pe_hedge)
            print()

            # update google sheet 
            gsheet.Update_cell(BT_sheet, ts_ce_index, sheet_col, ce_scrip)
            gsheet.Update_cell(BT_sheet, ts_pe_index, sheet_col, pe_scrip)
            gsheet.Update_cell(BT_sheet, ts_ce_index, sheet_col + 1, ce_price)
            gsheet.Update_cell(BT_sheet, ts_pe_index, sheet_col + 1, pe_price)
            gsheet.Update_cell(BT_sheet, ts_ce_index, sheet_col + 2, ce_hedge)
            gsheet.Update_cell(BT_sheet, ts_pe_index, sheet_col + 2, pe_hedge)
            
            if len(entry_times) == 0:
                break
            
            sheet_col += 3
            entry_time = datetime.datetime.combine(datetime.datetime.now().date() , entry_times[0]) - datetime.timedelta(seconds=1)
            check_time = entry_time
            entry_times = entry_times[1:]

            if len(entry_times) == 4:
                sheet_col = 1
                if index == 'BANKNIFTY':
                    caps_strategy = 'BN IFW ' + str(6)
                    BT_sheet, ts_ce_index, ts_pe_index = gsheet().get_sheet_and_index(gsheet.sheet_ids.bt_bn,caps_strategy)

                elif index == 'NIFTY':
                    caps_strategy = 'NF IFW ' + str(6)
                    BT_sheet, ts_ce_index, ts_pe_index = gsheet().get_sheet_and_index(gsheet.sheet_ids.bt_nf,caps_strategy)

except Exception as e:
    msg = "⚠️⚠️⚠️ Error !!! ⚠️⚠️⚠️ \n" + caps_strategy[:-2] + " Code stop "
    telegram().send_message(telegram.group.BT_Vs_Actual_diff, msg + '\n' + str(e))


# In[ ]:




