#!/usr/bin/env python
# coding: utf-8

# ### B120 OM W-3

# In[ ]:


code_name = 'B120 OM W-3'
import ctypes
ctypes.windll.kernel32.SetConsoleTitleW(code_name)
print(code_name)

index = 'BANKNIFTY'
scheme_no = 3


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
from parameter import Parameter
from holiday import *

if index == 'BANKNIFTY':
    caps_strategy = 'BN B120 OM W ' + str(scheme_no)
    BT_sheet, ts_ce_index, ts_pe_index = gsheet().get_sheet_and_index(gsheet.sheet_ids.weekly_bt_bn,caps_strategy)
    slipage = 0.0125
    
elif index == 'NIFTY':
    caps_strategy = 'NF B120 OM W ' + str(scheme_no)
    BT_sheet, ts_ce_index, ts_pe_index = gsheet().get_sheet_and_index(gsheet.sheet_ids.weekly_bt_nf,caps_strategy)
    slipage = 0.01

param = Parameter(index, caps_strategy)
entry_time = param.entry_time
sl = param.get('sl')
target = param.get('target')
trading_day = param.get('trading_day')
hedge_sd = 3

trading_day = set_trading_day(trading_day)

week_list = {'Friday':0, 'Saturday':1, 'Sunday':2, 'Monday':3, 'Tuesday':4, 'Wednesday':5, 'Thursday':6}
now = datetime.datetime.now().date()
parameter_day = now + datetime.timedelta(days = (week_list[trading_day] - week_list[datetime.datetime.today().strftime('%A')]))

entry_time = datetime.datetime.combine(parameter_day , entry_time) - datetime.timedelta(seconds=1)
entry_time = increment_if_holiday(entry_time)
check_time = entry_time

exit_time = datetime.time(15, 30)

check_ce_sl, modify_prices, check_pe_sl = False, False, False
sell_flag = 0

ce_check_time, pe_check_time = check_time, check_time

live_ce_pnl, live_pe_pnl, booked_ce_pnl, booked_pe_pnl = 0,0,0,0
previous_day_pnl = 0
gsheet.Update_cell(BT_sheet, ts_pe_index, 11, f'= J{ts_ce_index} + J{ts_pe_index}')

sleep_timedelta = ((entry_time - datetime.datetime.now()) - datetime.timedelta(seconds=60))
if sleep_timedelta.days == 0:
    sleep(sleep_timedelta.seconds)

try:
    while True:

        if (datetime.datetime.now() - ce_check_time) > datetime.timedelta(minutes=2) and (datetime.datetime.now() - pe_check_time) > datetime.timedelta(minutes=2):
            sleep_time = 0
        else:
            sleep_time = 5
            sleep(2)

        if datetime.datetime.now() > check_time and sell_flag == 0:
            sleep(sleep_time)

            # getting strangle strike
            ce_scrip, ce_scrip_token, ce_price, pe_scrip, pe_scrip_token, pe_price = select_strangle_strikes(index, target, check_time)

            ce_sl_price = int(round((ce_price * (1+(sl/100))) * 100, -1) + 5)/100
            pe_sl_price = int(round((pe_price * (1+(sl/100))) * 100, -1) + 5)/100 
            
            ce_hedge_limit = int(ce_scrip[:-2]) + ((ce_price + pe_price) * hedge_sd)
            pe_hedge_limit = int(pe_scrip[:-2]) - ((ce_price + pe_price) * hedge_sd)
            ce_hedge = str(int(ce_hedge_limit - (ce_hedge_limit % 100) + 100)) + 'CE'
            pe_hedge = str(int(pe_hedge_limit - (pe_hedge_limit % 100))) + 'PE'

            print(ce_scrip, ce_price, ce_sl_price)
            print(pe_scrip, pe_price, pe_sl_price)

            # slipage
            ce_slipage_price = ce_price - (ce_price * slipage)
            pe_slipage_price = pe_price - (pe_price * slipage)

            if datetime.datetime.today().date() == check_time.date():
                # update strike on google sheet
                gsheet.Update_Batch(BT_sheet, f"A{ts_ce_index}:C{ts_pe_index}", [[ce_scrip, ce_price, ce_sl_price], [pe_scrip, pe_price, pe_sl_price]])
                gsheet.Update_Batch(BT_sheet, f"D{ts_ce_index}:E{ts_ce_index}", [[ce_hedge, pe_hedge]])

            sell_flag, check_ce_sl, check_pe_sl, modify_prices = 1, True, True, True
            check_time = check_time + datetime.timedelta(minutes=1)
            ce_check_time, pe_check_time = check_time, check_time

        if check_ce_sl:
            if datetime.datetime.now() > ce_check_time:
                sleep(sleep_time)
                
                ce_o, ce_h, ce_l, ce_c = candle_data(ce_scrip_token, ce_check_time)                
                print(ce_check_time ,f'Call High : {ce_h}')
                
                ce_pnl = ce_slipage_price - ce_c
                live_ce_pnl = booked_ce_pnl + ce_pnl

                if datetime.datetime.today().date() == ce_check_time.date():
                    gsheet.Update_PL_cell(BT_sheet, update='cell', row_no=ts_ce_index, column_no=10, value=live_ce_pnl)
                
                if ce_h >= ce_sl_price:
                    print('\nCall SL HIT ', ce_check_time.time())
                    
                    if check_time.time() != datetime.time(9,15,59):
                        booked_ce_pnl = booked_ce_pnl + (ce_slipage_price - ce_sl_price)
                        live_ce_pnl = booked_ce_pnl
                    else:
                        booked_ce_pnl = booked_ce_pnl + ce_pnl
                        live_ce_pnl = booked_ce_pnl
                    
                    #update on google sheet
                    gsheet.Update_cell(BT_sheet, ts_ce_index, 10, live_ce_pnl)
                    gsheet.Update_a_cell(BT_sheet, 'F', ts_ce_index, 'HIT')

                    check_ce_sl = False

                ce_check_time = ce_check_time + datetime.timedelta(minutes=1)
                
        if check_pe_sl:
            if datetime.datetime.now() > pe_check_time:
                sleep(sleep_time)

                pe_o, pe_h, pe_l, pe_c = candle_data(pe_scrip_token, pe_check_time)
                print(pe_check_time, f'Put High : {pe_h}')
                
                pe_pnl = pe_slipage_price - pe_c
                live_pe_pnl = booked_pe_pnl + pe_pnl
                
                if datetime.datetime.today().date() == pe_check_time.date():
                    gsheet.Update_PL_cell(BT_sheet, update='cell', row_no=ts_pe_index, column_no=10, value=live_pe_pnl)

                if pe_h >= pe_sl_price:
                    print('\nPut SL HIT ', pe_check_time.time())
                    
                    if check_time.time() != datetime.time(9,15,59):
                        booked_pe_pnl = booked_pe_pnl + (pe_slipage_price - pe_sl_price)
                        live_pe_pnl = booked_pe_pnl
                    else:
                        booked_pe_pnl = booked_pe_pnl + pe_pnl
                        live_pe_pnl = booked_pe_pnl
                    
                    # update google sheet
                    gsheet.Update_cell(BT_sheet, ts_pe_index, 10, live_pe_pnl)
                    gsheet.Update_a_cell(BT_sheet, 'F', ts_pe_index, 'HIT')

                    check_pe_sl = False
        
                pe_check_time = pe_check_time + datetime.timedelta(minutes=1)

        if modify_prices:
            if datetime.datetime.now() > entry_time + datetime.timedelta(minutes=2):
                ce_price = candle_data(ce_scrip_token, entry_time)[-1]
                pe_price = candle_data(pe_scrip_token, entry_time)[-1]
                ce_sl_price = int(round((ce_price * (1+(sl/100))) * 100, -1) + 5)/100
                pe_sl_price = int(round((pe_price * (1+(sl/100))) * 100, -1) + 5)/100
                
                print('Modified sl prices  call:',ce_sl_price ," Put:",pe_sl_price)
                
                ce_slipage_price = ce_price - (ce_price * slipage)
                pe_slipage_price = pe_price - (pe_price * slipage)
                
                gsheet.Update_Batch(BT_sheet, f"B{ts_ce_index}:C{ts_pe_index}", [[ce_price, ce_sl_price], [pe_price, pe_sl_price]])
                gsheet.cell_modified(BT_sheet, f"C{ts_ce_index}:C{ts_pe_index}")
                modify_prices = False

        if check_ce_sl == check_pe_sl == modify_prices == False and sell_flag == 1:
            
            total_pnl = live_ce_pnl + live_pe_pnl
            print('\nStrategy Over\n')
            print('\nTotal PNL : ', total_pnl)

            today_pnl = total_pnl - previous_day_pnl
            print('\nTODAY PNL : ',today_pnl)
            
            if datetime.datetime.today().date() == pe_check_time.date() or datetime.datetime.today().date() == ce_check_time.date():
                gsheet.Update_Batch(BT_sheet, f"J{ts_ce_index}:J{ts_pe_index}", [[live_ce_pnl],[live_pe_pnl]])
                gsheet.Update_PNL_On_Sheet(caps_strategy, today_pnl)
            
            break

        if ce_check_time.time() > exit_time or pe_check_time.time() > exit_time:
            check_time = max(ce_check_time, pe_check_time)
            check_time = check_time - datetime.timedelta(minutes=1)
            
            if 'Expiry' in Parameter.Get_trading_day() and datetime.datetime.today().date() == check_time.date():
                
                total_pnl = live_ce_pnl + live_pe_pnl
                print('\nStrategy Over\n')
                print('\nTotal PNL : ', total_pnl)
                
                today_pnl = total_pnl - previous_day_pnl
                print('\nTODAY PNL : ',today_pnl)
                
                gsheet.Update_Batch(BT_sheet, f"J{ts_ce_index}:J{ts_pe_index}", [[live_ce_pnl],[live_pe_pnl]])
                gsheet.Update_PNL_On_Sheet(caps_strategy, today_pnl)  
                
                break

            check_time = datetime.datetime.combine(check_time + datetime.timedelta(days=1) , datetime.time(9,16)) - datetime.timedelta(seconds=1)
            check_time = increment_if_holiday(check_time)
            ce_check_time, pe_check_time = check_time, check_time

            if datetime.datetime.today().date() < check_time.date():
                
                total_pnl = live_ce_pnl + live_pe_pnl
                print('\nTotal PNL', total_pnl)
                
                today_pnl = total_pnl - previous_day_pnl
                print('\nTODAY PNL : ',today_pnl)
                
                gsheet.Update_Batch(BT_sheet, f"J{ts_ce_index}:J{ts_pe_index}", [[live_ce_pnl],[live_pe_pnl]])
                gsheet.Update_PNL_On_Sheet(caps_strategy, today_pnl)  
                
                break
            else:
                total_pnl = live_ce_pnl + live_pe_pnl
                print('\nTotal PNL', total_pnl)
                
                today_pnl = total_pnl - previous_day_pnl
                print('\nTODAY PNL : ',today_pnl)
                
                previous_day_pnl = live_ce_pnl + live_pe_pnl
                print(f'\nNext Day {check_time.strftime("%A")}\n\n')
    
except Exception as e:
    msg = "⚠️⚠️⚠️ Error !!! ⚠️⚠️⚠️ \n" + caps_strategy + " Code stop "
    telegram().send_message(telegram.group.BT_Vs_Actual_diff, msg + '\n' + str(e))

