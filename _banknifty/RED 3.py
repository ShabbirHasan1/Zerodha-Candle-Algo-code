#!/usr/bin/env python
# coding: utf-8

# ### RED 3

# In[ ]:


code_name = 'RED 3'
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

if index == 'BANKNIFTY':
    caps_strategy = 'BN RED ' + str(scheme_no)
    BT_sheet, ts_ce_index, ts_pe_index = gsheet().get_sheet_and_index(gsheet.sheet_ids.bt_bn,caps_strategy)
    
elif index == 'NIFTY':
    caps_strategy = 'NF RED ' + str(scheme_no)
    BT_sheet, ts_ce_index, ts_pe_index = gsheet().get_sheet_and_index(gsheet.sheet_ids.bt_nf,caps_strategy)

param = Parameter(index,caps_strategy)
entry_time = param.entry_time 
sl = param.get('sl')
decay = param.get('dt_trigger')
max_re = param.get('re_entries')
exit_time = param.exit_time
    
entry_time = datetime.datetime.combine(datetime.datetime.now().date() , entry_time) - datetime.timedelta(seconds=1)
check_time = entry_time

check_ce_sl, check_ce_re, modify_prices, check_pe_sl, check_pe_re = False, False, False, False, False
modify_ce_price, modify_pe_price = False, False
sell_flag = 0
ce_re_no, pe_re_no = 1,1

ce_check_time, pe_check_time = check_time, check_time

live_ce_pnl, live_pe_pnl, booked_ce_pnl, booked_pe_pnl = 0,0,0,0
gsheet.Update_cell(BT_sheet, ts_pe_index, 27, f'= Z{ts_ce_index} + Z{ts_pe_index}')

sleep_timedelta = ((entry_time - datetime.datetime.now()) - datetime.timedelta(seconds=60))
if sleep_timedelta.days == 0:
    sleep(sleep_timedelta.seconds)

try:
    while True:
        if (datetime.datetime.now() - ce_check_time) > datetime.timedelta(minutes=2) and (datetime.datetime.now() - pe_check_time) > datetime.timedelta(minutes=2):
            sleep_time = 0.03
        else:
            sleep_time = 7

        if datetime.datetime.now() > check_time and sell_flag == 0:
            sleep(sleep_time)

            ce_scrip, ce_scrip_token, ce_price, pe_scrip, pe_scrip_token, pe_price, futures_scrip, futures_token, futures = select_straddle_strikes(index, check_time)
            ce_decay_price, pe_decay_price = ce_price, pe_price

            ce_sl_price = int(round((ce_decay_price * (1+(sl/100))) * 100, -1) + 5)/100
            pe_sl_price = int(round((pe_decay_price * (1+(sl/100))) * 100, -1) + 5)/100   

            print(ce_scrip, ce_price, ce_sl_price)
            print(pe_scrip, pe_price, pe_sl_price)
            
            # slipage
            if index == 'BANKNIFTY':
                ce_slipage = ce_price * 0.0125
                pe_slipage = pe_price * 0.0125
            else:
                ce_slipage = ce_price * 0.01
                pe_slipage = pe_price * 0.01
                
            ce_slipage_price = ce_price - ce_slipage
            pe_slipage_price = pe_price - pe_slipage

            # update strike on google sheet
            gsheet.Update_a_cell(BT_sheet, 'A', ts_ce_index, ce_scrip)
            gsheet.Update_a_cell(BT_sheet, 'A', ts_pe_index, pe_scrip)
            gsheet.Update_a_cell(BT_sheet, 'B', ts_ce_index, ce_price)
            gsheet.Update_a_cell(BT_sheet, 'B', ts_pe_index, pe_price)
            gsheet.Update_a_cell(BT_sheet, 'C', ts_ce_index, ce_price)
            gsheet.Update_a_cell(BT_sheet, 'C', ts_pe_index, pe_price)
            gsheet.Update_a_cell(BT_sheet, 'D', ts_ce_index, ce_sl_price)
            gsheet.Update_a_cell(BT_sheet, 'D', ts_pe_index, pe_sl_price)

            sell_flag = 1
            check_ce_sl, check_pe_sl, modify_prices = True, True, True
            check_time = check_time + datetime.timedelta(minutes=1)
            ce_check_time, pe_check_time = check_time, check_time

        if check_ce_sl:
            if datetime.datetime.now() > ce_check_time:
                sleep(sleep_time)

                ce_o, ce_h, ce_l, ce_c = candle_data(ce_scrip_token, ce_check_time)
                print(ce_check_time ,'Call High ',ce_h)
                
                ce_pnl = ce_slipage_price - ce_c
                live_ce_pnl = booked_ce_pnl + ce_pnl
                
                try:
                    gsheet_res = BT_sheet.update_cell(ts_ce_index, 26, live_ce_pnl)
                except:
                    pass

                if ce_h >= ce_sl_price:
                    print('\nCall SL HIT', ce_re_no, ce_check_time.time())
                    
                    booked_ce_pnl = booked_ce_pnl + (ce_slipage_price - ce_sl_price)
                    live_ce_pnl = booked_ce_pnl

                    check_ce_sl = False
                    if ce_re_no > max_re:
                        gsheet.Update_cell(BT_sheet, ts_ce_index, (ce_re_no * 4) + 1, 'HIT')
                        pass
                    else:
                        ce_re_no = ce_re_no + 1

                        ce_scrip, ce_scrip_token, ce_price, temp_pe_scrip, temp_pe_scrip_token, temp_pe_price, futures_scrip, futures_token, futures = select_straddle_strikes(index, ce_check_time)
                        ce_decay_price, temp_pe_decay_price = int(round(ce_price * decay * 100, -1) - 5)/100, int(round(pe_price * decay * 100, -1) - 5)/100
                        ce_sl_price = int(round((ce_decay_price * (1+(sl/100))) * 100, -1) + 5)/100

                        print(ce_scrip, ce_price, ce_decay_price, '\n')
                        
                        # slipage
                        if index == 'BANKNIFTY':
                            ce_slipage = ce_decay_price * 0.0125
                        else:
                            ce_slipage = ce_decay_price * 0.01

                        ce_slipage_price = ce_decay_price - ce_slipage

                        # update google sheet
                        gsheet.Update_cell(BT_sheet, ts_ce_index, 26, live_ce_pnl)
                        gsheet.Update_cell(BT_sheet, ts_ce_index, (ce_re_no * 4) - 3, ce_scrip)
                        gsheet.Update_cell(BT_sheet, ts_ce_index, (ce_re_no * 4) - 2, ce_price)
                        gsheet.Update_cell(BT_sheet, ts_ce_index, (ce_re_no * 4) - 1, ce_decay_price)  
                        
                        check_ce_re, modify_ce_price = True, True
                        ce_entry_time = ce_check_time 

                ce_check_time += datetime.timedelta(minutes=1)         

        if check_pe_sl:
            if datetime.datetime.now() > pe_check_time:
                sleep(sleep_time)

                pe_o, pe_h, pe_l, pe_c = candle_data(pe_scrip_token, pe_check_time)
                print(pe_check_time ,'Put High ',pe_h)
                
                pe_pnl = pe_slipage_price - pe_c
                live_pe_pnl = booked_pe_pnl + pe_pnl
                
                try:
                    gsheet_res = BT_sheet.update_cell(ts_pe_index, 26, live_pe_pnl)
                except:
                    pass

                if pe_h >= pe_sl_price:
                    print('\nPut SL HIT', pe_re_no, pe_check_time.time())
                    
                    booked_pe_pnl = booked_pe_pnl + (pe_slipage_price - pe_sl_price)
                    live_pe_pnl = booked_pe_pnl                    

                    check_pe_sl = False
                    if pe_re_no > max_re:
                        gsheet.Update_cell(BT_sheet, ts_pe_index, (pe_re_no * 4) + 1, 'HIT')
                        pass
                    else:
                        pe_re_no = pe_re_no + 1

                        temp_ce_scrip, temp_ce_scrip_token, temp_ce_price, pe_scrip, pe_scrip_token, pe_price, futures_scrip, futures_token, futures = select_straddle_strikes(index, pe_check_time)
                        temp_ce_decay_price, pe_decay_price = int(round(ce_price * decay * 100, -1) - 5)/100, int(round(pe_price * decay * 100, -1) - 5)/100
                        pe_sl_price = int(round((pe_decay_price * (1+(sl/100))) * 100, -1) + 5)/100

                        print(pe_scrip, pe_price, pe_decay_price, '\n')
                        
                        # slipage
                        if index == 'BANKNIFTY':
                            pe_slipage = pe_decay_price * 0.0125
                        else:
                            pe_slipage = pe_decay_price * 0.01

                        pe_slipage_price = pe_decay_price - pe_slipage

                        # update google sheet
                        gsheet.Update_cell(BT_sheet, ts_pe_index, 26, live_pe_pnl)
                        gsheet.Update_cell(BT_sheet, ts_pe_index, (pe_re_no * 4) - 3, pe_scrip)
                        gsheet.Update_cell(BT_sheet, ts_pe_index, (pe_re_no * 4) - 2, pe_price)
                        gsheet.Update_cell(BT_sheet, ts_pe_index, (pe_re_no * 4) - 1, pe_decay_price)
                        
                        check_pe_re, modify_pe_price = True, True
                        pe_entry_time = pe_check_time 

                pe_check_time += datetime.timedelta(minutes=1)

        if check_ce_re:
            if datetime.datetime.now() > ce_check_time:
                sleep(sleep_time)

                ce_o, ce_h, ce_l, ce_c = candle_data(ce_scrip_token, ce_check_time)
                print(ce_check_time ,'Call Low ',ce_l)

                if ce_l <= ce_decay_price:
                    print('\nCALL RE entered',ce_re_no - 1, ce_check_time.time())
                    print(f'SL {ce_sl_price}\n')
                    gsheet.Update_cell(BT_sheet, ts_ce_index, (ce_re_no * 4) - 0, ce_sl_price)
                    check_ce_sl, check_ce_re, modify_ce_price = True, False, False
                ce_check_time += datetime.timedelta(minutes=1) 

        if check_pe_re:
            if datetime.datetime.now() > pe_check_time:
                sleep(sleep_time)
                pe_o, pe_h, pe_l, pe_c = candle_data(pe_scrip_token, pe_check_time)
                print(pe_check_time ,'Put Low ',pe_l)

                if pe_l <= pe_decay_price:
                    print('\nPut RE entered',pe_re_no, pe_check_time.time())
                    print(f'SL {pe_sl_price}\n')
                    gsheet.Update_cell(BT_sheet, ts_pe_index, (pe_re_no * 4) - 0, pe_sl_price)                
                    check_pe_sl, check_pe_re, modify_pe_price = True, False, False
                pe_check_time += datetime.timedelta(minutes=1)

        if modify_prices:
            if datetime.datetime.now() > entry_time + datetime.timedelta(minutes=2):
                ce_price = candle_data(ce_scrip_token, entry_time)[-1]
                pe_price = candle_data(pe_scrip_token, entry_time)[-1]
                ce_sl_price = int(round((ce_price * (1+(sl/100))) * 100, -1) + 5)/100
                pe_sl_price = int(round((pe_price * (1+(sl/100))) * 100, -1) + 5)/100

                print('\nPrices Modified')
                print(ce_price, ce_sl_price)
                print(pe_price, pe_sl_price)
                print()
                
                # slipage
                if index == 'BANKNIFTY':
                    ce_slipage = ce_price * 0.0125
                    pe_slipage = pe_price * 0.0125
                else:
                    ce_slipage = ce_price * 0.01
                    pe_slipage = pe_price * 0.01

                ce_slipage_price = ce_price - ce_slipage
                pe_slipage_price = pe_price - pe_slipage

                # compare with tradesheet and msg if difference 
                gsheet.Update_a_cell(BT_sheet, 'B', ts_ce_index, ce_price)
                gsheet.Update_a_cell(BT_sheet, 'B', ts_pe_index, pe_price)
                gsheet.Update_a_cell(BT_sheet, 'C', ts_ce_index, ce_price)
                gsheet.Update_a_cell(BT_sheet, 'C', ts_pe_index, pe_price)
                gsheet.Update_a_cell(BT_sheet, 'D', ts_ce_index, ce_sl_price)
                gsheet.Update_a_cell(BT_sheet, 'D', ts_pe_index, pe_sl_price)

                modify_prices = False
                
        if modify_ce_price:
            if datetime.datetime.now() > ce_entry_time + datetime.timedelta(minutes=2):
                
                ce_price = candle_data(ce_scrip_token, ce_entry_time)[-1]
                ce_decay_price = int(round(ce_price * decay * 100, -1) - 5)/100
                ce_sl_price = int(round((ce_decay_price * (1+(sl/100))) * 100, -1) + 5)/100
                
                print('\nCE Prices Modified')
                print(ce_scrip, ce_price, ce_decay_price, '\n')
                
                # slipage
                if index == 'BANKNIFTY':
                    ce_slipage = ce_decay_price * 0.0125
                else:
                    ce_slipage = ce_decay_price * 0.01

                ce_slipage_price = ce_decay_price - ce_slipage

                gsheet.Update_cell(BT_sheet, ts_ce_index, (ce_re_no * 4) - 2, ce_price)
                gsheet.Update_cell(BT_sheet, ts_ce_index, (ce_re_no * 4) - 1, ce_decay_price)

                modify_ce_price = False
                
            
        if modify_pe_price:
            if datetime.datetime.now() > pe_entry_time + datetime.timedelta(minutes=2):
                
                pe_price = candle_data(pe_scrip_token, pe_entry_time)[-1]
                pe_decay_price = int(round(pe_price * decay * 100, -1) - 5)/100
                pe_sl_price = int(round((pe_decay_price * (1+(sl/100))) * 100, -1) + 5)/100
                
                print('\nPE Prices Modified')
                print(pe_scrip, pe_price, pe_decay_price, '\n')
                
                # slipage
                if index == 'BANKNIFTY':
                    pe_slipage = pe_decay_price * 0.0125
                else:
                    pe_slipage = pe_decay_price * 0.01

                pe_slipage_price = pe_decay_price - pe_slipage
                
                gsheet.Update_cell(BT_sheet, ts_pe_index, (pe_re_no * 4) - 2, pe_price)
                gsheet.Update_cell(BT_sheet, ts_pe_index, (pe_re_no * 4) - 1, pe_decay_price)
                
                modify_pe_price = False

        if check_ce_sl == check_pe_sl == modify_prices == check_ce_re == check_pe_re == False and sell_flag == 1:
            break
        
        if ce_check_time.time() > exit_time or pe_check_time.time() > exit_time:
            break
    
    gsheet.Update_cell(BT_sheet, ts_ce_index, 26, live_ce_pnl)
    gsheet.Update_cell(BT_sheet, ts_pe_index, 26, live_pe_pnl)
    total_pnl = live_ce_pnl + live_pe_pnl
    print('Total pnl : ',total_pnl)
    gsheet.Update_PNL_On_Sheet(caps_strategy, total_pnl)
    
except Exception as e:
    print(e)
    msg = "⚠️⚠️⚠️ Error !!! ⚠️⚠️⚠️ \n" + caps_strategy + " Code stop "
    telegram().send_message(telegram.group.BT_Vs_Actual_diff, msg + '\n' + str(e))

