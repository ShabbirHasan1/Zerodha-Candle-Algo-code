#!/usr/bin/env python
# coding: utf-8

# ### B120S 7

# In[ ]:


code_name = 'B120S 7'
import ctypes
ctypes.windll.kernel32.SetConsoleTitleW(code_name)
print(code_name)

index = 'BANKNIFTY'
scheme_no = 7


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
    caps_strategy = 'BN B120S ' + str(scheme_no)
    BT_sheet, ts_ce_index, ts_pe_index = gsheet().get_sheet_and_index(gsheet.sheet_ids.bt_bn,caps_strategy)
    slipage = 0.0125

elif index == 'NIFTY':
    caps_strategy = 'NF B120S ' + str(scheme_no)
    BT_sheet, ts_ce_index, ts_pe_index = gsheet().get_sheet_and_index(gsheet.sheet_ids.bt_nf,caps_strategy)
    slipage = 0.01

param = Parameter(index, caps_strategy)
entry_time = param.entry_time
sl = param.get('sl')
ut_sl = param.get('ut_sl')
target = param.get('target')
exit_time = param.exit_time

entry_time = datetime.datetime.combine(datetime.datetime.now().date() , entry_time) - datetime.timedelta(seconds=1)
check_time = entry_time

check_ce_pe_sl, check_ut_sl, modify_prices, modify_ut_prices, trade_check = False, False, False, False, False
sell_flag = 0

live_ce_pnl, live_pe_pnl, live_ut_pnl = 0, 0, 0
gsheet.Update_cell(BT_sheet, ts_pe_index, 11, f'= J{ts_ce_index} + J{ts_pe_index}')
SL_hit = False

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

            ce_sl_price = int(round((ce_price * (1+(sl/100))) * 100, -1) + 5)/100
            pe_sl_price = int(round((pe_price * (1+(sl/100))) * 100, -1) + 5)/100

            print(ce_scrip, ce_price, ce_sl_price)
            print(pe_scrip, pe_price, pe_sl_price)

            ce_slipage_price = ce_price - (ce_price * slipage)
            pe_slipage_price = pe_price - (pe_price * slipage)

            # update strike on google sheet
            gsheet.Update_Batch(BT_sheet, f"A{ts_ce_index}:C{ts_pe_index}", [[ce_scrip, ce_price, ce_sl_price], [pe_scrip, pe_price, pe_sl_price]])

            sell_flag, check_ce_pe_sl, modify_prices = 1, True, True
            check_time = check_time + datetime.timedelta(minutes=1)

        if check_ce_pe_sl:
            if datetime.datetime.now() > check_time:
                sleep(sleep_time)

                ce_o, ce_h, ce_l, ce_c = candle_data(ce_scrip_token, check_time)
                pe_o, pe_h, pe_l, pe_c = candle_data(pe_scrip_token, check_time)
                print(check_time ,'Call High,Close:',ce_h,ce_c,'  ', 'Put high,Close:', pe_h,pe_c)

                live_ce_pnl = ce_slipage_price - ce_c
                live_pe_pnl = pe_slipage_price - pe_c
                gsheet.Update_PL_cell(BT_sheet, update='batch', Range=f"J{ts_ce_index}:J{ts_pe_index}", list_of_list=[[live_ce_pnl],[live_pe_pnl]])

                if ce_h >= ce_sl_price:
                    print('\nCALL SL HIT', check_time.time())
                    SL_hit = True

                    ut_scrip, ut_token, ut_price, ut_sl_price = pe_scrip, pe_scrip_token, pe_c, int(round((pe_c * (1+(ut_sl/100))) * 100, -1) + 5)/100
                    ut_slipage_price = pe_slipage_price
                    ts_ut_index = ts_pe_index

                    live_ce_pnl = (ce_slipage_price - ce_sl_price)

                    print('pnl : ',live_ce_pnl)
                    print('UT PUT  Close',ut_price ,'UT SL', ut_sl_price)

                    # update google sheet
                    gsheet.Update_cell(BT_sheet, ts_ce_index, 10, live_ce_pnl)

                elif pe_h >= pe_sl_price:
                    print('\nPUT SL HIT', check_time.time())
                    SL_hit = True

                    ut_scrip, ut_token, ut_price, ut_sl_price = ce_scrip, ce_scrip_token, ce_c, int(round((ce_c * (1+(ut_sl/100))) * 100, -1) + 5)/100
                    ut_slipage_price = ce_slipage_price
                    ts_ut_index = ts_ce_index

                    live_pe_pnl = (pe_slipage_price - pe_sl_price)

                    print('pnl : ',live_pe_pnl)
                    print(f'UT Call {ut_price}   UT SL {ut_sl_price}')

                    # update google sheet
                    gsheet.Update_cell(BT_sheet, ts_pe_index, 10, live_pe_pnl)

                if SL_hit == True:
                    check_ce_pe_sl, modify_prices, check_ut_sl, modify_ut_prices = False, False, True, True
                    ut_sl_time = check_time
                    gsheet.Update_Batch(BT_sheet, f"D{ts_ce_index}:F{ts_ce_index}", [[ut_scrip[-2:], ut_price, ut_sl_price]])

                check_time = check_time + datetime.timedelta(minutes=1)

        if modify_prices:
            if datetime.datetime.now() > entry_time + datetime.timedelta(minutes=2):
                ce_price = candle_data(ce_scrip_token, entry_time)[-1]
                pe_price = candle_data(pe_scrip_token, entry_time)[-1]
                ce_sl_price = int(round((ce_price * (1+(sl/100))) * 100, -1) + 5)/100
                pe_sl_price = int(round((pe_price * (1+(sl/100))) * 100, -1) + 5)/100
                print('Modified sl prices  call:',ce_sl_price ," Put:",pe_sl_price)

                ce_slipage_price = ce_price - (ce_price * slipage)
                pe_slipage_price = pe_price - (pe_price * slipage)

                # update google sheet
                gsheet.Update_Batch(BT_sheet, f"B{ts_ce_index}:C{ts_pe_index}", [[ce_price, ce_sl_price], [pe_price, pe_sl_price]])
                gsheet.cell_modified(BT_sheet, f"C{ts_ce_index}:C{ts_pe_index}")
                modify_prices = False

        if check_ut_sl:
            if datetime.datetime.now() > check_time:
                sleep(sleep_time)

                ut_o, ut_h, ut_l, ut_c = candle_data(ut_token, check_time)
                print(check_time, f'UT  High:{ut_h}   Close:{ut_c}')

                live_ut_pnl = ut_slipage_price - ut_c
                gsheet.Update_PL_cell(BT_sheet, update='cell', row_no=ts_ut_index, column_no=10, value=live_ut_pnl)

                if ut_h >= ut_sl_price:
                    print('UT SL HIT', check_time.time())

                    live_ut_pnl = ut_slipage_price - ut_sl_price

                    #update google sheet
                    gsheet.Update_cell(BT_sheet, ts_ut_index, 10, live_ut_pnl)
                    gsheet.Update_a_cell(BT_sheet, 'G', ts_ce_index, 'HIT')
                    check_ut_sl, modify_ut_prices = False, False

                check_time = check_time + datetime.timedelta(minutes=1)

        if modify_ut_prices:
            if datetime.datetime.now() > ut_sl_time + datetime.timedelta(minutes=2):
                sleep(sleep_time)
                ut_price = candle_data(ut_token, ut_sl_time)[-1]
                ut_sl_price = int(round((ut_price * (1+(ut_sl/100))) * 100, -1) + 5)/100

                print('Modified UT Sl prices :',ut_sl_price)

                # update google sheet
                gsheet.Update_Batch(BT_sheet, f"E{ts_ce_index}:F{ts_ce_index}", [[ut_price, ut_sl_price]])
                gsheet.cell_modified(BT_sheet, f"F{ts_ce_index}")
                modify_ut_prices = False

        if check_ce_pe_sl == check_ut_sl == modify_prices == modify_ut_prices == False and sell_flag == 1:
            break

        if check_time.time() > exit_time:
            break

    if SL_hit == True:
        if ut_scrip == ce_scrip:
            gsheet.Update_Batch(BT_sheet, f"J{ts_ce_index}:J{ts_pe_index}", [[live_ut_pnl],[live_pe_pnl]])
            total_pnl = live_pe_pnl + live_ut_pnl

        elif ut_scrip == pe_scrip:
            gsheet.Update_Batch(BT_sheet, f"J{ts_ce_index}:J{ts_pe_index}", [[live_ce_pnl],[live_ut_pnl]])
            total_pnl = live_ce_pnl + live_ut_pnl
    else:
        total_pnl = live_ce_pnl + live_pe_pnl

    print('Total pnl : ',total_pnl)
    gsheet.Update_PNL_On_Sheet(caps_strategy, total_pnl)

except Exception as e:
    msg = "⚠️⚠️⚠️ Error !!! ⚠️⚠️⚠️ \n" + caps_strategy + " Code stop "
    telegram().send_message(telegram.group.BT_Vs_Actual_diff, msg + '\n' + str(e))

