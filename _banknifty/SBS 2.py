#!/usr/bin/env python
# coding: utf-8

# ### SBS 1

# In[ ]:


code_name = 'SBS 2'
import ctypes
ctypes.windll.kernel32.SetConsoleTitleW(code_name)
print(code_name)

index = 'BANKNIFTY'
scheme_no = 2


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
    caps_strategy = 'BN SBS ' + str(scheme_no)
    BT_sheet, ts_ce_index, ts_pe_index = gsheet().get_sheet_and_index(gsheet.sheet_ids.bt_bn, caps_strategy)
    slipage = 0.0125
    
elif index == 'NIFTY':
    caps_strategy = 'NF SBS ' + str(scheme_no)
    BT_sheet, ts_ce_index, ts_pe_index = gsheet().get_sheet_and_index(gsheet.sheet_ids.bt_nf, caps_strategy)
    slipage = 0.01

param = Parameter(index,caps_strategy)
entry_time = param.entry_time
sl = param.get('sl')
second_sell = param.get('second_sell')
target = param.get('target')
exit_time = param.exit_time

future_scrip, future_token, options_data = get_fno_data(index)

entry_time = datetime.datetime.combine(datetime.datetime.now().date() , entry_time) - datetime.timedelta(seconds=1)
check_time = entry_time

check_ce_sell_sl, check_ce_buy_sl, check_pe_sell_sl, check_pe_buy_sl, modify_ce_prices, modify_pe_prices = False, False, False, False, False, False
call_side, put_side = '', ''
sell_flag = 0
ce_first_sell, pe_first_sell = False, False

ce_check_time, pe_check_time = check_time, check_time

live_ce_pnl, live_pe_pnl, booked_ce_pnl, booked_pe_pnl = 0,0,0,0
gsheet.Update_cell(BT_sheet, ts_pe_index, 13, f'= L{ts_ce_index} + L{ts_pe_index}')

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

            # getting strangle strike
            ce_scrip, ce_scrip_token, ce_price, pe_scrip, pe_scrip_token, pe_price = select_strangle_strikes(index, target, check_time)

            ce_sl_price = int(round((ce_price * (1+(sl/100))) * 100, -1) + 5)/100
            pe_sl_price = int(round((pe_price * (1+(sl/100))) * 100, -1) + 5)/100   

            print(ce_scrip, ce_price, ce_sl_price)
            print(pe_scrip, pe_price, pe_sl_price)

            # slipage
            ce_slipage_price = ce_price - (ce_price * slipage)
            pe_slipage_price = pe_price - (pe_price * slipage)

            # update strike on google sheet
            gsheet.Update_a_cell(BT_sheet, 'A', ts_ce_index, ce_scrip)
            gsheet.Update_a_cell(BT_sheet, 'A', ts_pe_index, pe_scrip)
            gsheet.Update_a_cell(BT_sheet, 'B', ts_ce_index, ce_price)
            gsheet.Update_a_cell(BT_sheet, 'B', ts_pe_index, pe_price)
            gsheet.Update_a_cell(BT_sheet, 'C', ts_ce_index, ce_sl_price)
            gsheet.Update_a_cell(BT_sheet, 'C', ts_pe_index, pe_sl_price)

            sell_flag = 1
            ce_first_sell, pe_first_sell, call_side, put_side = True, True, 'SELL', 'SELL'
            check_ce_sell_sl, check_pe_sell_sl, modify_ce_prices, modify_pe_prices = True, True, True, True
            mod_ce_time, mod_pe_time = check_time, check_time
            check_time = check_time + datetime.timedelta(minutes=1)
            ce_check_time, pe_check_time = check_time, check_time

        if modify_ce_prices:
            if datetime.datetime.now() > mod_ce_time + datetime.timedelta(minutes=2):
                ce_price = candle_data(ce_scrip_token, mod_ce_time)[-1]

                if call_side == 'SELL':
                    ce_sl_price = int(round((ce_price * (1+(sl/100))) * 100, -1) + 5)/100

                    if ce_first_sell:
                        gsheet.Update_a_cell(BT_sheet, 'B', ts_ce_index, ce_price)
                        gsheet.Update_a_cell(BT_sheet, 'C', ts_ce_index, ce_sl_price)
                    else:
                        gsheet.Update_a_cell(BT_sheet, 'H', ts_ce_index, ce_price)
                        gsheet.Update_a_cell(BT_sheet, 'I', ts_ce_index, ce_sl_price)
                else:
                    ce_sl_price = int(round((ce_price * (1-(sl/100))) * 100, -1) + 5)/100
                    gsheet.Update_a_cell(BT_sheet, 'E', ts_ce_index, ce_price)
                    gsheet.Update_a_cell(BT_sheet, 'F', ts_ce_index, ce_sl_price)

                print('Modified call sl prices :', ce_sl_price)
                ce_slipage_price = ce_price - (ce_price * slipage)
                modify_ce_prices = False


        if modify_pe_prices:
            if datetime.datetime.now() > mod_pe_time + datetime.timedelta(minutes=2):
                pe_price = candle_data(pe_scrip_token, mod_pe_time)[-1]

                if put_side == 'SELL':
                    pe_sl_price = int(round((pe_price * (1+(sl/100))) * 100, -1) + 5)/100

                    if pe_first_sell:
                        gsheet.Update_a_cell(BT_sheet, 'B', ts_pe_index, pe_price)
                        gsheet.Update_a_cell(BT_sheet, 'C', ts_pe_index, pe_sl_price)
                    else:
                        gsheet.Update_a_cell(BT_sheet, 'H', ts_pe_index, pe_price)
                        gsheet.Update_a_cell(BT_sheet, 'I', ts_pe_index, pe_sl_price)
                else:
                    pe_sl_price = int(round((pe_price * (1-(sl/100))) * 100, -1) + 5)/100
                    gsheet.Update_a_cell(BT_sheet, 'E', ts_pe_index, pe_price)
                    gsheet.Update_a_cell(BT_sheet, 'F', ts_pe_index, pe_sl_price)

                print('Modified Put sl prices :', pe_sl_price)
                pe_slipage_price = pe_price - (pe_price * slipage)
                modify_pe_prices = False

        if check_ce_sell_sl:
            if datetime.datetime.now() > ce_check_time:
                sleep(sleep_time)

                ce_o, ce_h, ce_l, ce_c = candle_data(ce_scrip_token, ce_check_time)
                print(ce_check_time ,f'Call High : {ce_h}')

                ce_pnl = ce_slipage_price - ce_c
                live_ce_pnl = booked_ce_pnl + ce_pnl

                try:
                    gsheet_res = BT_sheet.update_cell(ts_ce_index, 12, live_ce_pnl)
                except:
                    pass

                if ce_h >= ce_sl_price:
                    print(f"\nCall {'first'if ce_first_sell else '2nd'} Sell SL HIT ", ce_check_time.time())

                    booked_ce_pnl = booked_ce_pnl + (ce_slipage_price - ce_sl_price)
                    live_ce_pnl = booked_ce_pnl

                    #update on google sheet
                    gsheet.Update_cell(BT_sheet, ts_ce_index, 12, live_ce_pnl)

                    if ce_first_sell:

                        print('\nBUY CALL')

                        new_futures = candle_data(future_token, ce_check_time)[-1]
                        ce_scrip, ce_scrip_token, ce_price = find_ut_scrip(index, target, 'CE', new_futures, ce_check_time)
                        ce_sl_price = int(round((ce_price * (1-(sl/100))) * 100, -1) + 5)/100

                        print(ce_scrip, ce_price, ce_sl_price)
                        print()

                        # update strike on google sheet
                        gsheet.Update_a_cell(BT_sheet, 'D', ts_ce_index, ce_scrip)
                        gsheet.Update_a_cell(BT_sheet, 'E', ts_ce_index, ce_price)
                        gsheet.Update_a_cell(BT_sheet, 'F', ts_ce_index, ce_sl_price)

                        # slipage
                        ce_slipage_price = ce_price - (ce_price * slipage)

                        ce_first_sell, call_side = False, 'BUY'
                        check_ce_buy_sl, modify_ce_prices = True, True
                        mod_ce_time = ce_check_time
                    else:
                        gsheet.Update_a_cell(BT_sheet, 'J', ts_ce_index, 'HIT')

                    check_ce_sell_sl = False
                ce_check_time = ce_check_time + datetime.timedelta(minutes=1)

        if check_pe_sell_sl:
            if datetime.datetime.now() > pe_check_time:
                sleep(sleep_time)

                pe_o, pe_h, pe_l, pe_c = candle_data(pe_scrip_token, pe_check_time)
                print(pe_check_time, f'Put High : {pe_h}')

                pe_pnl = pe_slipage_price - pe_c
                live_pe_pnl = booked_pe_pnl + pe_pnl

                try:
                    gsheet_res = BT_sheet.update_cell(ts_pe_index, 12, live_pe_pnl)
                except:
                    pass

                if pe_h >= pe_sl_price:
                    print(f"\nPut {'first'if ce_first_sell else '2nd'} Sell SL HIT ", pe_check_time.time())

                    booked_pe_pnl = booked_pe_pnl + (pe_slipage_price - pe_sl_price)
                    live_pe_pnl = booked_pe_pnl

                    # update google sheet
                    gsheet.Update_cell(BT_sheet, ts_pe_index, 12, live_pe_pnl)

                    if pe_first_sell:
                        print('\nBUY PUT')

                        new_futures = candle_data(future_token, pe_check_time)[-1]
                        pe_scrip, pe_scrip_token, pe_price = find_ut_scrip(index, target, 'PE', new_futures, pe_check_time)
                        pe_sl_price = int(round((pe_price * (1-(sl/100))) * 100, -1) + 5)/100

                        print(pe_scrip, pe_price, pe_sl_price)
                        print()

                        # update strike on google sheet
                        gsheet.Update_a_cell(BT_sheet, 'D', ts_pe_index, pe_scrip)
                        gsheet.Update_a_cell(BT_sheet, 'E', ts_pe_index, pe_price)
                        gsheet.Update_a_cell(BT_sheet, 'F', ts_pe_index, pe_sl_price)

                        # slipage
                        pe_slipage_price = pe_price - (pe_price * slipage)

                        pe_first_sell, put_side = False, 'BUY'
                        check_pe_buy_sl, modify_pe_prices = True, True
                        mod_pe_time = pe_check_time
                    else:
                        gsheet.Update_a_cell(BT_sheet, 'J', ts_pe_index, 'HIT')

                    check_pe_sell_sl = False
                pe_check_time = pe_check_time + datetime.timedelta(minutes=1)

        if check_ce_buy_sl:
            if datetime.datetime.now() > ce_check_time:
                sleep(sleep_time)

                ce_o, ce_h, ce_l, ce_c = candle_data(ce_scrip_token, ce_check_time)                
                print(ce_check_time ,f'Call Low : {ce_l}')

                ce_pnl = ce_c - ce_slipage_price
                live_ce_pnl = booked_ce_pnl + ce_pnl

                try:
                    gsheet_res = BT_sheet.update_cell(ts_ce_index, 12, live_ce_pnl)
                except:
                    pass

                if ce_l <= ce_sl_price:
                    print('\nCall Buy SL HIT ', ce_check_time.time())

                    booked_ce_pnl = booked_ce_pnl + (ce_sl_price - ce_slipage_price)
                    live_ce_pnl = booked_ce_pnl

                    #update on google sheet
                    gsheet.Update_cell(BT_sheet, ts_ce_index, 12, live_ce_pnl)

                    if second_sell:
                        print('\nSELL CALL')

                        new_futures = candle_data(future_token, ce_check_time)[-1]
                        ce_scrip, ce_scrip_token, ce_price = find_ut_scrip(index, target, 'CE', new_futures, ce_check_time)
                        ce_sl_price = int(round((ce_price * (1+(sl/100))) * 100, -1) + 5)/100

                        print(ce_scrip, ce_price, ce_sl_price)
                        print()

                        # update strike on google sheet
                        gsheet.Update_a_cell(BT_sheet, 'G', ts_ce_index, ce_scrip)
                        gsheet.Update_a_cell(BT_sheet, 'H', ts_ce_index, ce_price)
                        gsheet.Update_a_cell(BT_sheet, 'I', ts_ce_index, ce_sl_price)

                        # slipage
                        ce_slipage_price = ce_price - (ce_price * slipage)

                        ce_first_sell, call_side = False, 'SELL'
                        check_ce_sell_sl, modify_ce_prices = True, True
                        mod_ce_time = ce_check_time
                    else:
                        gsheet.Update_a_cell(BT_sheet, 'J', ts_ce_index, 'HIT')

                    check_ce_buy_sl = False
                ce_check_time = ce_check_time + datetime.timedelta(minutes=1) 

        if check_pe_buy_sl:
            if datetime.datetime.now() > pe_check_time:
                sleep(sleep_time)

                pe_o, pe_h, pe_l, pe_c = candle_data(pe_scrip_token, pe_check_time)                
                print(pe_check_time ,f'Put Low : {pe_l}')

                pe_pnl = pe_c - pe_slipage_price
                live_pe_pnl = booked_pe_pnl + pe_pnl

                try:
                    gsheet_res = BT_sheet.update_cell(ts_pe_index, 12, live_pe_pnl)
                except:
                    pass

                if pe_l <= pe_sl_price:
                    print('\nPut Buy SL HIT ', pe_check_time.time())

                    booked_pe_pnl = booked_pe_pnl + (pe_sl_price - pe_slipage_price)
                    live_pe_pnl = booked_pe_pnl

                    #update on google sheet
                    gsheet.Update_cell(BT_sheet, ts_pe_index, 12, live_pe_pnl)

                    if second_sell:
                        print('\nSELL Put')

                        new_futures = candle_data(future_token, pe_check_time)[-1]
                        pe_scrip, pe_scrip_token, pe_price = find_ut_scrip(index, target, 'PE', new_futures, pe_check_time)
                        pe_sl_price = int(round((pe_price * (1+(sl/100))) * 100, -1) + 5)/100

                        print(pe_scrip, pe_price, pe_sl_price)
                        print()

                        # update strike on google sheet
                        gsheet.Update_a_cell(BT_sheet, 'G', ts_pe_index, pe_scrip)
                        gsheet.Update_a_cell(BT_sheet, 'H', ts_pe_index, pe_price)
                        gsheet.Update_a_cell(BT_sheet, 'I', ts_pe_index, pe_sl_price)

                        # slipage
                        pe_slipage_price = pe_price - (pe_price * slipage)

                        pe_first_sell, put_side = False, 'SELL'
                        check_pe_sell_sl, modify_pe_prices = True, True
                        mod_pe_time = pe_check_time
                    else:
                        gsheet.Update_a_cell(BT_sheet, 'J', ts_pe_index, 'HIT')

                    check_pe_buy_sl = False
                pe_check_time = pe_check_time + datetime.timedelta(minutes=1)    

        if (check_ce_sell_sl == check_ce_buy_sl == check_pe_sell_sl == check_pe_buy_sl == modify_ce_prices == modify_pe_prices == False) and (sell_flag == 1):
            break

        if ce_check_time.time() > exit_time or pe_check_time.time() > exit_time:
            break 
              
    gsheet.Update_cell(BT_sheet, ts_ce_index, 12, live_ce_pnl)
    gsheet.Update_cell(BT_sheet, ts_pe_index, 12, live_pe_pnl)
    total_pnl = live_ce_pnl + live_pe_pnl
    print('Total pnl : ',total_pnl)
    gsheet.Update_PNL_On_Sheet(caps_strategy, total_pnl)
                
except Exception as e:
    msg = "⚠️⚠️⚠️ Error !!! ⚠️⚠️⚠️ \n" + caps_strategy + " Code stop "
    telegram().send_message(telegram.group.BT_Vs_Actual_diff, msg + '\n' + str(e))


# In[ ]:




