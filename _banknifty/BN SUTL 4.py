#!/usr/bin/env python
# coding: utf-8

# ### BN SUTL 4

# In[ ]:


code_name = 'BN SUTL 4'
import ctypes
ctypes.windll.kernel32.SetConsoleTitleW(code_name)
print(code_name)

index = 'BANKNIFTY'
scheme_no = 4


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
    caps_strategy = 'BN SUTL ' + str(scheme_no)
    BT_sheet, ts_ce_index, ts_pe_index = gsheet().get_sheet_and_index(gsheet.sheet_ids.bt_bn,caps_strategy)
    slipage = 0.0125
    
elif index == 'NIFTY':
    caps_strategy = 'NF SUTL ' + str(scheme_no)
    BT_sheet, ts_ce_index, ts_pe_index = gsheet().get_sheet_and_index(gsheet.sheet_ids.bt_nf,caps_strategy)
    slipage = 0.01
    
param = Parameter(index, caps_strategy)
entry_time = param.entry_time
sl = param.get('sl')
ut_sl = param.get('ut_sl')
ut_target = param.get('ut_target')
new_entry_time = datetime.time(13,1)
exit_time = param.exit_time

entry_time = datetime.datetime.combine(datetime.datetime.now().date() , entry_time) - datetime.timedelta(seconds=1)
new_entry_time = datetime.datetime.combine(entry_time.date() , new_entry_time) - datetime.timedelta(seconds=1)
check_time = entry_time

check_straddle_sl, modify_straddle_prices, check_ut_sl, modify_ut_prices = False, False, False, False
sell_flag = 0

straddle_live_pnl = 0
ut_live_pnl = 0
gsheet.Update_cell(BT_sheet, ts_pe_index, 11, f'= J{ts_ce_index} + J{ts_pe_index}')
pnl_at_entry_time = 0
entry_time_slipage = 0

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
            ce_scrip, ce_scrip_token, ce_price, pe_scrip, pe_scrip_token, pe_price, futures_scrip, futures_token, futures = select_straddle_strikes(index, check_time)

            straddle_sl_price = int(round(((ce_price + pe_price) * (1+(sl/100))) * 100, -1) + 5)/100 
            
            straddle_slipage_price = (ce_price + pe_price) - ((ce_price + pe_price) * slipage)

            print(ce_scrip, ce_price)
            print(pe_scrip, pe_price)
            print('SL ', straddle_sl_price)
            
            # update google sheet
            gsheet.Update_Batch(BT_sheet, f"A{ts_ce_index}:C{ts_pe_index + 1}", [[ce_scrip, ce_price, ''], [pe_scrip, pe_price, ''], ['', ce_price + pe_price, straddle_sl_price]])

            sell_flag, check_straddle_sl, modify_straddle_prices = 1, True, True
            check_time = check_time + datetime.timedelta(minutes=1)

        if check_straddle_sl:
            if datetime.datetime.now() > check_time:
                sleep(sleep_time)

                ce_o, ce_h, ce_l, ce_c = candle_data(ce_scrip_token, check_time)
                pe_o, pe_h, pe_l, pe_c = candle_data(pe_scrip_token, check_time)
                straddle_high = max(ce_h + pe_l, ce_l + pe_h)
                straddle_close = (ce_c + pe_c)
                
                print(check_time ,'Straddle High ',straddle_high)
                
                straddle_live_pnl = straddle_slipage_price - straddle_close
                
                if check_time == new_entry_time:
                    
                    entry_time_slipage = straddle_close * slipage
                    pnl_at_entry_time = straddle_live_pnl
                    gsheet.Update_cell(BT_sheet, ts_pe_index, 13, pnl_at_entry_time)
                    gsheet.Update_cell(BT_sheet, ts_pe_index, 14, f'= k{ts_pe_index} - M{ts_pe_index}')
                
                gsheet.Update_PL_cell(BT_sheet, update='cell', row_no=ts_ce_index, column_no=10, value=straddle_live_pnl)

                if straddle_high >= straddle_sl_price:
                    sl_time = check_time
                    print('\nStraddle SL HIT', check_time.time())
                    PlaySound(f'{index} Late S U T {scheme_no} Straddle SL HIT')
                    
                    straddle_live_pnl = straddle_slipage_price - straddle_sl_price

                    #find UT
                    new_futures = candle_data(futures_token, check_time)[-1]
                    if new_futures > futures:
                        signal = 'PE'
                    else:
                        signal = 'CE'

                    ut_scrip, ut_token, ut_price = find_ut_scrip(index, ut_target, signal, new_futures, sl_time)
                    ut_sl_price = int((1 + (ut_sl/100)) * ut_price) + 1
                    print(f'UT is: {ut_scrip}  open: {ut_price}   UT Sl: {ut_sl_price}')
                    
                    ut_slipage_price = ut_price - (ut_price * slipage)
                    
                    # update google sheet
                    gsheet.Update_cell(BT_sheet, ts_ce_index, 10, straddle_live_pnl)
                    gsheet.Update_Batch(BT_sheet, f"D{ts_ce_index}:F{ts_ce_index}", [[ut_scrip[-7:], ut_price, ut_sl_price]])

                    modify_straddle_prices, check_straddle_sl, check_ut_sl, modify_ut_prices = False, False, True, True
                check_time = check_time + datetime.timedelta(minutes=1)

        if modify_straddle_prices:
            if datetime.datetime.now() > entry_time + datetime.timedelta(minutes=2):
                ce_price = candle_data(ce_scrip_token, entry_time)[-1]
                pe_price = candle_data(pe_scrip_token, entry_time)[-1]
                straddle_sl_price = int(round(((ce_price + pe_price) * (1+(sl/100))) * 100, -1) + 5)/100
                print('Modified SL ', straddle_sl_price)
                
                straddle_slipage_price = (ce_price + pe_price) - ((ce_price + pe_price) * slipage)
                
                # update google sheet
                gsheet.Update_Batch(BT_sheet, f"B{ts_ce_index}:C{ts_pe_index + 1}", [[ce_price, ''], [pe_price, ''], [ce_price + pe_price, straddle_sl_price]])
                gsheet.cell_modified(BT_sheet, f"C{ts_pe_index + 1}")
                modify_straddle_prices = False

        if check_ut_sl:
            if datetime.datetime.now() > check_time:
                sleep(sleep_time)
                
                ut_o, ut_h, ut_l, ut_c = candle_data(ut_token, check_time)
                
                ut_live_pnl = ut_slipage_price - ut_c
                
                if check_time == new_entry_time:
                    entry_time_slipage = ut_c * slipage
                    pnl_at_entry_time = straddle_live_pnl + ut_live_pnl
                    gsheet.Update_cell(BT_sheet, ts_pe_index, 13, pnl_at_entry_time)
                    gsheet.Update_cell(BT_sheet, ts_pe_index, 14, f'= k{ts_pe_index} - M{ts_pe_index}')
                
                gsheet.Update_PL_cell(BT_sheet, update='cell', row_no=ts_pe_index, column_no=10, value=ut_live_pnl)
                
                print(check_time ,'UT High: ',ut_h)

                if ut_h >= ut_sl_price:
                    print('\nUT SL Hit', check_time.time())
                    
                    ut_live_pnl = ut_slipage_price - ut_sl_price
                    
                    gsheet.Update_cell(BT_sheet, ts_pe_index, 10, ut_live_pnl)
                    gsheet.Update_cell(BT_sheet, ts_ce_index, 7, 'HIT')

                    check_ut_sl, modify_ut_prices = False, False
                check_time = check_time + datetime.timedelta(minutes=1)

        if modify_ut_prices:
            if datetime.datetime.now() > sl_time + datetime.timedelta(minutes=2):
                ut_price = candle_data(ut_token, sl_time)[-1]
                ut_sl_price = int((1 + (ut_sl/100)) * ut_price) + 1
                print('Modified UT Sl prices :',ut_sl_price)
                
                ut_slipage_price = ut_price - (ut_price * slipage)
                
                gsheet.Update_Batch(BT_sheet, f"E{ts_ce_index}:F{ts_ce_index}", [[ut_price, ut_sl_price]])
                gsheet.cell_modified(BT_sheet, f"F{ts_ce_index}")
                modify_ut_prices = False

        if check_straddle_sl == modify_straddle_prices == check_ut_sl == modify_ut_prices == False and sell_flag == 1:
            break
            
        if check_time.time() > exit_time:
            break
            
    gsheet.Update_Batch(BT_sheet, f"J{ts_ce_index}:J{ts_pe_index}", [[straddle_live_pnl],[ut_live_pnl]])
    total_pnl = (straddle_live_pnl + ut_live_pnl) - pnl_at_entry_time - entry_time_slipage
    print('Total pnl : ',total_pnl)
    gsheet.Update_PNL_On_Sheet(caps_strategy, total_pnl)
        
except Exception as e:
    msg = "⚠️⚠️⚠️ Error !!! ⚠️⚠️⚠️ \n" + caps_strategy + " Code stop "
    telegram().send_message(telegram.group.BT_Vs_Actual_diff, msg + '\n' + str(e))

