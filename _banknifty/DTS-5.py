#!/usr/bin/env python
# coding: utf-8

# In[ ]:


code_name = 'DTS 5'
import ctypes
ctypes.windll.kernel32.SetConsoleTitleW(code_name)
print(code_name)

index = 'BANKNIFTY'
scheme_no = 5


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

if index == 'BANKNIFTY':
    caps_strategy = 'BN DTS ' + str(scheme_no)
    BT_sheet, ts_ce_index, ts_pe_index = gsheet().get_sheet_and_index(gsheet.sheet_ids.bt_bn,caps_strategy)
    slipage = 0.0125
    
elif index == 'NIFTY':
    caps_strategy = 'NF DTS ' + str(scheme_no)
    BT_sheet, ts_ce_index, ts_pe_index = gsheet().get_sheet_and_index(gsheet.sheet_ids.bt_nf,caps_strategy)
    slipage = 0.01

param = Parameter(index,caps_strategy)
entry_time = param.entry_time 
sl = param.get('sl')
decay = param.get('dt_trigger')
target = param.get('target')
exit_time = param.exit_time

entry_time = datetime.datetime.combine(datetime.datetime.now().date() , entry_time) - datetime.timedelta(seconds=1)
check_time = entry_time

check_ce_sl, check_ce_re, modify_prices, check_pe_sl, check_pe_re = False, False, False, False, False
sell_flag = 0

ce_check_time, pe_check_time = check_time, check_time

live_ce_pnl, live_pe_pnl = 0,0
gsheet.Update_cell(BT_sheet, ts_pe_index, 7, f'= F{ts_ce_index} + F{ts_pe_index}')

sleep_timedelta = ((entry_time - datetime.datetime.now()) - datetime.timedelta(seconds=60))
if sleep_timedelta.days == 0:
    sleep(sleep_timedelta.seconds)

try:
    while True:
        if (datetime.datetime.now() - ce_check_time) > datetime.timedelta(minutes=2) and (datetime.datetime.now() - pe_check_time) > datetime.timedelta(minutes=2):
            sleep_time = 0.03
        else:
            sleep_time = 5
            sleep(2)

        if datetime.datetime.now() > check_time and sell_flag == 0:
            sleep(sleep_time)

            ce_scrip, ce_scrip_token, ce_price, pe_scrip, pe_scrip_token, pe_price = select_strangle_strikes(index, target, check_time)
            
            ce_decay_price, pe_decay_price = int(round(ce_price * decay * 100, -1) - 5)/100, int(round(pe_price * decay * 100, -1) - 5)/100
            
            ce_sl_price = int(round((ce_decay_price * (1+(sl/100))) * 100, -1) + 5)/100
            pe_sl_price = int(round((pe_decay_price * (1+(sl/100))) * 100, -1) + 5)/100   

            print(ce_scrip, ce_price,', decay =', ce_decay_price)
            print(pe_scrip, pe_price,', decay =', pe_decay_price)
            
            # slipage                
            ce_slipage_price = ce_decay_price - (ce_decay_price * slipage)
            pe_slipage_price = pe_decay_price - (pe_decay_price * slipage)

            # update strike on google sheet
            gsheet.Update_Batch(BT_sheet, f"A{ts_ce_index}:C{ts_pe_index}", [[ce_scrip, ce_price, ce_decay_price], [pe_scrip, pe_price, pe_decay_price]])

            sell_flag, check_ce_re, check_pe_re, modify_prices = 1, True, True, True
            check_time = check_time + datetime.timedelta(minutes=1)
            ce_check_time, pe_check_time = check_time, check_time
            
        if check_ce_re:
            if datetime.datetime.now() > ce_check_time:
                sleep(sleep_time)

                ce_o, ce_h, ce_l, ce_c = candle_data(ce_scrip_token, ce_check_time)
                print(ce_check_time ,'Call Low ',ce_l)

                if ce_l <= ce_decay_price:
                    print('\nCALL Sell At ', ce_check_time.time())
                    print(f'SL Price {ce_sl_price}\n')
                    gsheet.Update_a_cell(BT_sheet, 'D', ts_ce_index, ce_sl_price)
                    check_ce_sl, check_ce_re = True, False
                ce_check_time += datetime.timedelta(minutes=1) 

        if check_pe_re:
            if datetime.datetime.now() > pe_check_time:
                sleep(sleep_time)
                pe_o, pe_h, pe_l, pe_c = candle_data(pe_scrip_token, pe_check_time)
                print(pe_check_time ,'Put Low ',pe_l)

                if pe_l <= pe_decay_price:
                    print('\nPut Sell At ', pe_check_time.time())
                    print(f'SL Price {pe_sl_price}\n')
                    gsheet.Update_a_cell(BT_sheet, 'D', ts_pe_index, pe_sl_price)                
                    check_pe_sl, check_pe_re = True, False
                pe_check_time += datetime.timedelta(minutes=1)      

        if check_ce_sl:
            if datetime.datetime.now() > ce_check_time:
                sleep(sleep_time)

                ce_o, ce_h, ce_l, ce_c = candle_data(ce_scrip_token, ce_check_time)
                print(ce_check_time ,'Call High ',ce_h)
                
                live_ce_pnl = ce_slipage_price - ce_c
                gsheet.Update_PL_cell(BT_sheet, update='cell', row_no=ts_ce_index, column_no=6, value=live_ce_pnl)

                if ce_h >= ce_sl_price:
                    print('\nCall SL HIT', ce_check_time.time())
                    live_ce_pnl = ce_slipage_price - ce_sl_price
                    gsheet.Update_cell(BT_sheet, ts_ce_index, 5, 'HIT')
                    gsheet.Update_cell(BT_sheet, ts_ce_index, 6, live_ce_pnl)
                    check_ce_sl = False   

                ce_check_time += datetime.timedelta(minutes=1)         

        if check_pe_sl:
            if datetime.datetime.now() > pe_check_time:
                sleep(sleep_time)

                pe_o, pe_h, pe_l, pe_c = candle_data(pe_scrip_token, pe_check_time)
                print(pe_check_time ,'Put High ',pe_h)
                
                live_pe_pnl = pe_slipage_price - pe_c
                gsheet.Update_PL_cell(BT_sheet, update='cell', row_no=ts_pe_index, column_no=6, value=live_pe_pnl)

                if pe_h >= pe_sl_price:
                    print('\nPut SL HIT', pe_check_time.time())
                    live_pe_pnl = pe_slipage_price - pe_sl_price
                    gsheet.Update_cell(BT_sheet, ts_pe_index, 5, 'HIT')
                    gsheet.Update_cell(BT_sheet, ts_pe_index, 6, live_pe_pnl)
                    check_pe_sl = False

                pe_check_time += datetime.timedelta(minutes=1)

        if modify_prices:
            if datetime.datetime.now() > entry_time + datetime.timedelta(minutes=2):
                ce_price = candle_data(ce_scrip_token, entry_time)[-1]
                pe_price = candle_data(pe_scrip_token, entry_time)[-1]
                
                ce_decay_price, pe_decay_price = int(round(ce_price * decay * 100, -1) - 5)/100, int(round(pe_price * decay * 100, -1) - 5)/100

                ce_sl_price = int(round((ce_decay_price * (1+(sl/100))) * 100, -1) + 5)/100
                pe_sl_price = int(round((pe_decay_price * (1+(sl/100))) * 100, -1) + 5)/100 

                print('\nPrices Modified')
                print(ce_price,', decay =', ce_decay_price)
                print(pe_price,', decay =', pe_decay_price)
                print()
                
                # slipage
                ce_slipage_price = ce_decay_price - (ce_decay_price * slipage)
                pe_slipage_price = pe_decay_price - (pe_decay_price * slipage)

                # compare with tradesheet and msg if difference
                gsheet.Update_Batch(BT_sheet, f"B{ts_ce_index}:C{ts_pe_index}", [[ce_price, ce_decay_price], [pe_price, pe_decay_price]])
                gsheet.cell_modified(BT_sheet, f"C{ts_ce_index}:C{ts_pe_index}")

                modify_prices = False

        if check_ce_sl == check_pe_sl == modify_prices == check_ce_re == check_pe_re == False and sell_flag == 1:
            break   
        
        if ce_check_time.time() > exit_time or pe_check_time.time() > exit_time:
            break
    
    gsheet.Update_Batch(BT_sheet, f"F{ts_ce_index}:F{ts_pe_index}", [[live_ce_pnl],[live_pe_pnl]])
    total_pnl = live_ce_pnl + live_pe_pnl
    print('Total pnl : ',total_pnl)
    gsheet.Update_PNL_On_Sheet(caps_strategy, total_pnl)
    
except Exception as e:
    print(e)
    msg = "⚠️⚠️⚠️ Error !!! ⚠️⚠️⚠️ \n" + caps_strategy + " Code stop "
    telegram().send_message(telegram.group.BT_Vs_Actual_diff, msg + '\n' + str(e))

