#!/usr/bin/env python
# coding: utf-8

# ### NF SUTW 2

# In[ ]:


code_name = 'NF SUTW 2'
import ctypes
ctypes.windll.kernel32.SetConsoleTitleW(code_name)
print(code_name)

index = 'NIFTY'
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
from play_sound import PlaySound
from holiday import *

if index == 'BANKNIFTY':
    caps_strategy = 'BN SUTW ' + str(scheme_no)
    BT_sheet, ts_ce_index, ts_pe_index = gsheet().get_sheet_and_index(gsheet.sheet_ids.weekly_bt_bn,caps_strategy)
    slipage = 0.0125
    
elif index == 'NIFTY':
    caps_strategy = 'NF SUTW ' + str(scheme_no)
    BT_sheet, ts_ce_index, ts_pe_index = gsheet().get_sheet_and_index(gsheet.sheet_ids.weekly_bt_nf,caps_strategy)
    slipage = 0.01
    
param = Parameter(index, caps_strategy)
entry_time = param.entry_time
sl = param.get('sl')
ut_sl = param.get('ut_sl')
ut_target = param.get('ut_target')
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

check_straddle_sl, modify_straddle_prices, check_ut_sl, modify_ut_prices = False, False, False, False
sell_flag = 0

straddle_live_pnl = 0
ut_live_pnl = 0
previous_day_pnl = 0
gsheet.Update_cell(BT_sheet, ts_pe_index, 11, f'= J{ts_ce_index} + J{ts_pe_index}')

try: 
    while True:

        if (datetime.datetime.now() - check_time) > datetime.timedelta(minutes=2):
            sleep_time = 0
        else:
            sleep_time = 5
            sleep(2)

        if datetime.datetime.now() > check_time and sell_flag == 0:
            sleep(sleep_time)

            # getting strangle strike
            ce_scrip, ce_scrip_token, ce_price, pe_scrip, pe_scrip_token, pe_price, futures_scrip, futures_token, futures = select_straddle_strikes(index, check_time)

            straddle_sl_price = int(round(((ce_price + pe_price) * (1+(sl/100))) * 100, -1) + 5)/100 
            
            ce_hedge_limit = int(ce_scrip[:-2]) + ((ce_price + pe_price) * hedge_sd)
            pe_hedge_limit = int(pe_scrip[:-2]) - ((ce_price + pe_price) * hedge_sd)
            ce_hedge = str(int(ce_hedge_limit - (ce_hedge_limit % 100) + 100)) + 'CE'
            pe_hedge = str(int(pe_hedge_limit - (pe_hedge_limit % 100))) + 'PE'

            straddle_slipage_price = (ce_price + pe_price) - ((ce_price + pe_price) * slipage)

            print(ce_scrip, ce_price)
            print(pe_scrip, pe_price)
            print('SL ', straddle_sl_price)
            print()
            
            if datetime.datetime.today().date() == check_time.date():
                msg = f"*{caps_strategy}* Straddle SELL ✅\n\n{ce_scrip} {ce_price} \n{pe_scrip} {pe_price} \n\nSL {straddle_sl_price} \nTime {check_time.time()}"
                telegram().send_message(telegram.group.Weekly_trade, msg)
            
                # update google sheet
                gsheet.Update_Batch(BT_sheet, f"A{ts_ce_index}:C{ts_pe_index + 1}", [[ce_scrip, ce_price, ''], [pe_scrip, pe_price, ''], ['', ce_price + pe_price, straddle_sl_price]])
                gsheet.Update_Batch(BT_sheet, f"G{ts_ce_index}:H{ts_ce_index}", [[ce_hedge, pe_hedge]])

            sell_flag, check_straddle_sl, modify_straddle_prices = 1, True, True
            check_time = check_time + datetime.timedelta(minutes=1)

        if check_straddle_sl:
            if datetime.datetime.now() > check_time:
                sleep(sleep_time)

                ce_o, ce_h, ce_l, ce_c = candle_data(ce_scrip_token, check_time)
                pe_o, pe_h, pe_l, pe_c = candle_data(pe_scrip_token, check_time)
                straddle_high = max(ce_h + pe_l, ce_l + pe_h)
                straddle_close = (ce_c + pe_c)

                print(check_time ,'\tStraddle High ',straddle_high)

                straddle_live_pnl = straddle_slipage_price - straddle_close
                print('pnl ',  straddle_live_pnl)
                
                if datetime.datetime.today().date() == check_time.date():
                    gsheet.Update_PL_cell(BT_sheet, update='cell', row_no=ts_ce_index, column_no=10, value=straddle_live_pnl)

                if straddle_high >= straddle_sl_price:
                    sl_time = check_time
                    print('\nStraddle SL HIT', check_time.time())

                    if datetime.datetime.today().date() == check_time.date():
                        telegram().send_message(telegram.group.Weekly_trade, f"*{caps_strategy}* Straddle SL HIT 🛑 \nSL Time {check_time.time()}")
                        PlaySound(f'{index} S U T Weekly {scheme_no} Straddle SL HIT')

                    if sl_time.time() != datetime.time(9,15,59):
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
                    
                    if datetime.datetime.today().date() == check_time.date():
                        telegram().send_message(telegram.group.Weekly_trade, f"*{caps_strategy}* UT SELL 🟦\n\nUT Scrip {ut_scrip} \nPrice {ut_price} \nUT SL {ut_sl_price} \nTime {check_time.time()}")

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
                print(f'\nModified SL {straddle_sl_price} \n')
                
                straddle_slipage_price = (ce_price + pe_price) - ((ce_price + pe_price) * slipage)
                
                if datetime.datetime.today().date() == check_time.date():
                    
                    # update google sheet
                    gsheet.Update_Batch(BT_sheet, f"B{ts_ce_index}:C{ts_pe_index + 1}", [[ce_price, ''], [pe_price, ''], [ce_price + pe_price, straddle_sl_price]])
                    gsheet.cell_modified(BT_sheet, f"C{ts_pe_index + 1}")

                modify_straddle_prices = False

        if check_ut_sl:
            if datetime.datetime.now() > check_time:
                sleep(sleep_time)

                ut_o, ut_h, ut_l, ut_c = candle_data(ut_token, check_time)

                ut_live_pnl = ut_slipage_price - ut_c
                print('pnl ', ut_live_pnl + straddle_live_pnl)

                if datetime.datetime.today().date() == check_time.date():
                    gsheet.Update_PL_cell(BT_sheet, update='cell', row_no=ts_pe_index, column_no=10, value=ut_live_pnl)

                print(check_time ,'\tUT High: ',ut_h)

                if ut_h >= ut_sl_price:
                    print('\nUT SL Hit', check_time.time())

                    if check_time.time() != datetime.time(9,15,59):
                        ut_live_pnl = ut_slipage_price - ut_sl_price

                    total_pnl = straddle_live_pnl + ut_live_pnl
                    print('\nStrategy Over\n')
                    print('\nTotal PNL : ', total_pnl)

                    today_pnl = total_pnl - previous_day_pnl
                    print('\nTODAY PNL : ',today_pnl)
                    
                    if datetime.datetime.today().date() == check_time.date():
                        telegram().send_message(telegram.group.Weekly_trade, f"*{caps_strategy}* UT SL HIT 🛑 \nSL Time {check_time.time()} \n\n🏳️ Strategy Over 🏳️")
                        PlaySound(f'{index} S U T Weekly {scheme_no} Strategy Over')
                    
                        gsheet.Update_cell(BT_sheet, ts_pe_index, 10, ut_live_pnl)
                        gsheet.Update_cell(BT_sheet, ts_ce_index, 9, 'HIT')
                        gsheet.Update_PNL_On_Sheet(caps_strategy, today_pnl)
                    
                    check_ut_sl, modify_ut_prices = False, False
                check_time = check_time + datetime.timedelta(minutes=1)

        if modify_ut_prices:
            if datetime.datetime.now() > sl_time + datetime.timedelta(minutes=2):
                ut_price = candle_data(ut_token, sl_time)[-1]
                ut_sl_price = int((1 + (ut_sl/100)) * ut_price) + 1
                print(f'\nModified UT Sl prices : {ut_sl_price} \n')

                ut_slipage_price = ut_price - (ut_price * slipage)
                
                if datetime.datetime.today().date() == check_time.date():
                    gsheet.Update_Batch(BT_sheet, f"E{ts_ce_index}:F{ts_ce_index}", [[ut_price, ut_sl_price]])
                    gsheet.cell_modified(BT_sheet, f"F{ts_ce_index}")

                modify_ut_prices = False

        if check_straddle_sl == modify_straddle_prices == check_ut_sl == modify_ut_prices == False and sell_flag == 1:
            break

        if check_time.time() > exit_time:
            check_time = check_time - datetime.timedelta(minutes=1)

            if 'Expiry' in Parameter.Get_trading_day() and datetime.datetime.today().date() == check_time.date():
                
                total_pnl = straddle_live_pnl + ut_live_pnl
                print('\nStrategy Over\n')
                print('\nTotal PNL : ', total_pnl)
                
                today_pnl = total_pnl - previous_day_pnl
                print('\nTODAY PNL : ',today_pnl)
                
                gsheet.Update_Batch(BT_sheet, f"J{ts_ce_index}:J{ts_pe_index}", [[straddle_live_pnl],[ut_live_pnl]])
                gsheet.Update_PNL_On_Sheet(caps_strategy, today_pnl)  
                
                break

            check_time = datetime.datetime.combine(check_time + datetime.timedelta(days=1) , datetime.time(9,16)) - datetime.timedelta(seconds=1)
            check_time = increment_if_holiday(check_time)

            if datetime.datetime.today().date() < check_time.date():
                
                total_pnl = straddle_live_pnl + ut_live_pnl
                print('\nTotal PNL', total_pnl)
                
                today_pnl = total_pnl - previous_day_pnl
                print('\nTODAY PNL : ',today_pnl)
                
                gsheet.Update_Batch(BT_sheet, f"J{ts_ce_index}:J{ts_pe_index}", [[straddle_live_pnl],[ut_live_pnl]])
                gsheet.Update_PNL_On_Sheet(caps_strategy, today_pnl)  
                
                break
            else:
                total_pnl = straddle_live_pnl + ut_live_pnl
                print('\nTotal PNL', total_pnl)
                
                today_pnl = total_pnl - previous_day_pnl
                print('\nTODAY PNL : ',today_pnl)
                
                previous_day_pnl = straddle_live_pnl + ut_live_pnl
                print(f'\nNext Day {check_time.strftime("%A")}\n\n')   

except Exception as e:
    msg = "⚠️⚠️⚠️ Error !!! ⚠️⚠️⚠️ \n" + caps_strategy + " Code stop "
    telegram().send_message(telegram.group.BT_Vs_Actual_diff, msg + '\n' + str(e))


# In[ ]:




