#!/usr/bin/env python
# coding: utf-8

# ### SRE OM 5

# In[ ]:


code_name = 'SRE OM 5'
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
from play_sound import PlaySound

if index == 'BANKNIFTY':
    caps_strategy = 'BN SRE OM ' + str(scheme_no)
    BT_sheet, ts_ce_index, ts_pe_index = gsheet().get_sheet_and_index(gsheet.sheet_ids.bt_bn, caps_strategy)
    slipage = 0.0125
    
elif index == 'NIFTY':
    caps_strategy = 'NF SRE OM ' + str(scheme_no)
    BT_sheet, ts_ce_index, ts_pe_index = gsheet().get_sheet_and_index(gsheet.sheet_ids.bt_nf, caps_strategy)
    slipage = 0.01

param = Parameter(index,caps_strategy)
entry_time = param.entry_time
sl = param.get('sl')
re_sl = 25
max_re = param.get('re_entries')
target = param.get('target')
intra_sl = 50
exit_time = param.exit_time

entry_time = datetime.datetime.combine(datetime.datetime.now().date() , entry_time) - datetime.timedelta(seconds=1)
check_time = entry_time

check_straddle_sl, modify_straddle_prices, check_intra_sl, sell_new_straddle = False, False, False, False
sell_flag = 0
re_no = 0
live_pnl, booked_pnl = 0, 0

sleep_timedelta = ((entry_time - datetime.datetime.now()) - datetime.timedelta(seconds=60))
if sleep_timedelta.days == 0:
    sleep(sleep_timedelta.seconds)

try:
    while True:

        if (datetime.datetime.now() - check_time) > datetime.timedelta(minutes=2):
            sleep_time = 0.03
        else:
            sleep_time = 5
            sleep(2)

        if datetime.datetime.now() > check_time and sell_flag == 0:
            sleep(sleep_time)

            # getting strangle strike
            
            ce_scrip, ce_scrip_token, ce_price, pe_scrip, pe_scrip_token, pe_price = select_strangle_strikes(index, target, check_time)
            straddle_sl_price = int(round(((ce_price + pe_price) * (1+(sl/100))) * 100, -1) + 5)/100  
            intra_sl_price = int(round(((ce_price + pe_price) * (1+(intra_sl/100))) * 100, -1) + 5)/100  

            print(ce_scrip, ce_price)
            print(pe_scrip, pe_price)
            print('straddle SL ', straddle_sl_price)
            print('Intra SL ', intra_sl_price)
            
            straddle_slipage_price = (ce_price + pe_price) - ((ce_price + pe_price) * slipage)
            
            # update google sheet
            gsheet.Update_Batch(BT_sheet, f"{chr(65 + (re_no * 3))}{ts_ce_index}:{chr(67 + (re_no * 3))}{ts_pe_index + 1}", [[ce_scrip, ce_price, ''], [pe_scrip, pe_price, ''], ['', ce_price + pe_price, straddle_sl_price]])

            sell_flag, check_straddle_sl, modify_straddle_prices = 1, True, True
            check_time = check_time + datetime.timedelta(minutes=1)

        if check_straddle_sl:
            if datetime.datetime.now() > check_time:
                sleep(sleep_time)

                ce_o, ce_h, ce_l, ce_c = candle_data(ce_scrip_token, check_time)
                pe_o, pe_h, pe_l, pe_c = candle_data(pe_scrip_token, check_time)
                
                straddle_close = ce_c + pe_c
                straddle_high = max(ce_h + pe_l, ce_l + pe_h)

                print(check_time ,'Straddle Close, High ',straddle_close, straddle_high)
                
                live_pnl = booked_pnl + (straddle_slipage_price - straddle_close)
                gsheet.Update_PL_cell(BT_sheet, update='cell', row_no=ts_ce_index, column_no=20, value=live_pnl)

                if straddle_high >= intra_sl_price:
                    sl_time = check_time
                    print('\nStraddle SL HIT at Intra Minute', check_time.time())
                    sell_new_straddle = True
                    PlaySound(f'{index} S R E OM {scheme_no} SL Hit at Intra Minute')
                    
                    booked_pnl = booked_pnl + (straddle_slipage_price - intra_sl_price)
                    live_pnl = booked_pnl

                elif straddle_close >= straddle_sl_price:
                    sl_time = check_time
                    print('\nStraddle SL HIT at Close', check_time.time())
                    sell_new_straddle = True
                    PlaySound(f'{index} S R E OM {scheme_no} SL Hit at Candle Close')
                    
                    booked_pnl = booked_pnl + (straddle_slipage_price - straddle_close)
                    live_pnl = booked_pnl

                if sell_new_straddle:

                    if re_no < max_re:
                        pass
                    else:
                        gsheet.Update_cell(BT_sheet, ts_ce_index, ((re_no + 1) * 3) + 1, 'HIT')
                        break
                        
                    ce_scrip, ce_scrip_token, ce_price, pe_scrip, pe_scrip_token, pe_price = select_strangle_strikes(index, target, check_time)

                    if 'Expiry' in Parameter.Get_trading_day() and re_no == 0:
                        print(f'SL Change From {sl} to {re_sl}')
                        sl = re_sl
                    
                    straddle_sl_price = int(round(((ce_price + pe_price) * (1+(sl/100))) * 100, -1) + 5)/100  
                    intra_sl_price = int(round(((ce_price + pe_price) * (1+(intra_sl/100))) * 100, -1) + 5)/100
                    
                    straddle_slipage_price = (ce_price + pe_price) - ((ce_price + pe_price) * slipage)

                    re_no = re_no + 1
                    print('SL no.', re_no)
                    print(ce_scrip, ce_price)
                    print(pe_scrip, pe_price)
                    print('straddle SL ', straddle_sl_price)
                    print('Intra SL ', intra_sl_price)

                    # update google sheet
                    gsheet.Update_cell(BT_sheet, ts_ce_index, 20, live_pnl)
                    gsheet.Update_Batch(BT_sheet, f"{chr(65 + (re_no * 3))}{ts_ce_index}:{chr(67 + (re_no * 3))}{ts_pe_index + 1}", [[ce_scrip, ce_price, ''], [pe_scrip, pe_price, ''], ['', ce_price + pe_price, straddle_sl_price]])

                    entry_time = sl_time
                    sell_new_straddle, modify_straddle_prices = False, True

                check_time = check_time + datetime.timedelta(minutes=1)

        if modify_straddle_prices:
            if datetime.datetime.now() > entry_time + datetime.timedelta(minutes=2):
                ce_price = candle_data(ce_scrip_token, entry_time)[-1]
                pe_price = candle_data(pe_scrip_token, entry_time)[-1]
                
                straddle_sl_price = int(round(((ce_price + pe_price) * (1+(sl/100))) * 100, -1) + 5)/100  
                intra_sl_price = int(round(((ce_price + pe_price) * (1+(intra_sl/100))) * 100, -1) + 5)/100  
                
                straddle_slipage_price = (ce_price + pe_price) - ((ce_price + pe_price) * slipage)
                
                print('Modified Straddle SL ', straddle_sl_price)
                print('Modified Intra SL ', intra_sl_price)

                # update google sheet
                gsheet.Update_Batch(BT_sheet, f"{chr(66 + (re_no * 3))}{ts_ce_index}:{chr(67 + (re_no * 3))}{ts_pe_index + 1}", [[ce_price, ''], [pe_price, ''], [ce_price + pe_price, straddle_sl_price]])
                gsheet.cell_modified(BT_sheet, f"{chr(67 + (re_no * 3))}{ts_pe_index + 1}")
                modify_straddle_prices = False

        if check_straddle_sl == modify_straddle_prices == check_intra_sl == sell_new_straddle == False and sell_flag == 1:
            break 
        
        if check_time.time() > exit_time:
            break
            
    gsheet.Update_cell(BT_sheet, ts_ce_index, 20, live_pnl)
    total_pnl = live_pnl
    print('Total pnl : ',total_pnl)
    gsheet.Update_PNL_On_Sheet(caps_strategy, total_pnl)

except Exception as e:
    print(e)
    msg = "⚠️⚠️⚠️ Error !!! ⚠️⚠️⚠️ \n" + caps_strategy + " Code stop "
    telegram().send_message(telegram.group.BT_Vs_Actual_diff, msg + '\n' + str(e))


# In[ ]:




