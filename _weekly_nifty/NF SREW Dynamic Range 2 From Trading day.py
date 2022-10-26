#!/usr/bin/env python
# coding: utf-8

# In[ ]:


code_name = 'NF SREW Dynamic Range 2'
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
    caps_strategy = 'BN SREW ' + str(scheme_no)
    BT_sheet, ts_ce_index, ts_pe_index = gsheet().get_sheet_and_index(gsheet.sheet_ids.weekly_bt_bn,caps_strategy)
    slipage = 0.0125
    
elif index == 'NIFTY':
    caps_strategy = 'NF SREW ' + str(scheme_no)
    BT_sheet, ts_ce_index, ts_pe_index = gsheet().get_sheet_and_index(gsheet.sheet_ids.weekly_bt_nf,caps_strategy)
    slipage = 0.01

param = Parameter(index,caps_strategy)
entry_time = param.entry_time
range_sl = param.get('range_sl')
intra_sl = param.get('intra_sl')
trading_day = param.get('trading_day')
max_re = param.get('re_entries')
hedge_sd = 3

trading_day = set_trading_day(trading_day)

week_list = {'Friday':0, 'Saturday':1, 'Sunday':2, 'Monday':3, 'Tuesday':4, 'Wednesday':5, 'Thursday':6}
now = datetime.datetime.now().date()
parameter_day = now + datetime.timedelta(days = (week_list[trading_day] - week_list[datetime.datetime.today().strftime('%A')]))

entry_time = datetime.datetime.combine(parameter_day , entry_time) - datetime.timedelta(seconds=1)
entry_time = increment_if_holiday(entry_time)
check_time = entry_time

exit_time = datetime.time(15, 30)

check_straddle_sl, modify_straddle_prices, sell_new_straddle = False, False, False
sell_flag = 0
re_no = 0
live_pnl, booked_pnl = 0, 0
previous_day_pnl = 0

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
            lower_range, upper_range = get_range_sl_prices(ce_scrip, ce_price + pe_price, range_sl) 
            intra_lower_range, intra_upper_range = get_range_sl_prices(ce_scrip, ce_price + pe_price, intra_sl)

            ce_hedge_limit = int(ce_scrip[:-2]) + ((ce_price + pe_price) * hedge_sd)
            pe_hedge_limit = int(pe_scrip[:-2]) - ((ce_price + pe_price) * hedge_sd)
            ce_hedge = str(int(ce_hedge_limit - (ce_hedge_limit % 100) + 100)) + 'CE'
            pe_hedge = str(int(pe_hedge_limit - (pe_hedge_limit % 100))) + 'PE'

            print(ce_scrip, ce_price)
            print(pe_scrip, pe_price)
            print('Premium ', ce_price + pe_price)
            print('Lower Range ', lower_range)
            print('Upper Range ', upper_range)
            print('Intra Lower Range ', intra_lower_range)
            print('Intra Upper Range ', intra_upper_range)
            print('CE Hedge ', ce_hedge)
            print('PE Hedge ', pe_hedge)
            print()

            straddle_slipage_price = (ce_price + pe_price) - ((ce_price + pe_price) * slipage)

            if datetime.datetime.today().date() == check_time.date():
                msg = f"*{caps_strategy}* Straddle Sell ✅ \n\n{ce_scrip[:-2]}  {round(ce_price + pe_price,2)} \n\nLower Range {lower_range} \nUpper Range {upper_range} \n\nTime {check_time.time()}"
                telegram().send_message(telegram.group.Weekly_trade, msg)

                # update google sheet
                gsheet.Update_Batch(BT_sheet, f"{chr(65 + (re_no * 3))}{ts_ce_index}:{chr(67 + (re_no * 3))}{ts_pe_index + 1}", [[ce_scrip, ce_price, f'({lower_range}, {upper_range})'], [pe_scrip, pe_price, f'({intra_lower_range}, {intra_upper_range})'], ['', ce_price + pe_price, '']])
                gsheet.Update_Batch(BT_sheet, f"AB{ts_ce_index}:AC{ts_ce_index}", [[ce_hedge, pe_hedge]])

            sell_flag, check_straddle_sl, modify_straddle_prices = 1, True, True
            check_time = check_time + datetime.timedelta(minutes=1)

        if check_straddle_sl:
            if datetime.datetime.now() > check_time:
                sleep(sleep_time)

                future_open, future_high, future_low, future_candle_close = candle_data(futures_token, check_time)

                ce_o, ce_h, ce_l, ce_c = candle_data(ce_scrip_token, check_time)
                pe_o, pe_h, pe_l, pe_c = candle_data(pe_scrip_token, check_time)
                straddle_close = ce_c + pe_c
                high_low_max = max(ce_h + pe_l, pe_h + ce_l)

                print(check_time ,'\tFuture Price', future_candle_close, '\tStraddle Price', straddle_close)

                live_pnl = booked_pnl + (straddle_slipage_price - straddle_close)
                print('pnl',live_pnl)

                if datetime.datetime.today().date() == check_time.date():
                    gsheet.Update_PL_cell(BT_sheet, update='cell', row_no=ts_ce_index, column_no=31, value=live_pnl)

                if (intra_upper_range < future_high or future_low < intra_lower_range) and check_time.time() != datetime.time(9,15,59):
                    sl_time = check_time

                    print(f'\nStraddle {re_no + 1} Swap at Intra SL', check_time.time())
                    sell_new_straddle = True

                    if datetime.datetime.today().date() == check_time.date():
                        telegram().send_message(telegram.group.Weekly_trade, f'🛑 *{caps_strategy}* Straddle Shift {re_no + 1} at Intra SL 🛑 \n\nTime {check_time.time()}')
                        PlaySound(f'{index} S R E Weekly {scheme_no} Straddle Shift {re_no + 1} at Intra SL')

                    booked_pnl = booked_pnl + (straddle_slipage_price - high_low_max)
                    live_pnl = booked_pnl

                elif upper_range < future_candle_close or future_candle_close < lower_range:
                    sl_time = check_time

                    print(f'\nStraddle {re_no + 1} Swap at Candle Close', check_time.time())
                    sell_new_straddle = True

                    if datetime.datetime.today().date() == check_time.date():
                        telegram().send_message(telegram.group.Weekly_trade, f'🛑 *{caps_strategy}* Straddle Shift {re_no + 1} at Candle close 🛑 \n\nTime {check_time.time()}')
                        PlaySound(f'{index} S R E Weekly {scheme_no} Straddle Shift {re_no + 1} at Candle close')

                    booked_pnl = booked_pnl + (straddle_slipage_price - straddle_close)
                    live_pnl = booked_pnl

                if sell_new_straddle:

                    if re_no < max_re:
                        pass
                    else:
                        print('\nStrategy Over\n')
                        print('\nTotal PNL : ', live_pnl)

                        today_pnl = live_pnl - previous_day_pnl
                        print('\nTODAY PNL : ',today_pnl)

                        if datetime.datetime.today().date() == check_time.date():

                            telegram().send_message(telegram.group.Weekly_trade, f'*{caps_strategy} \n\n🏳️ Strategy Over 🏳️*')
                            PlaySound(f'{index} S R E Weekly {scheme_no} Strategy Over')

                            gsheet.Update_cell(BT_sheet, ts_ce_index, ((re_no + 1) * 3) + 1, 'HIT')
                            gsheet.Update_cell(BT_sheet, ts_ce_index, 31, live_pnl)
                            gsheet.Update_PNL_On_Sheet(caps_strategy, today_pnl)

                        break

                    old_straddle = ce_scrip[:-2]
                    old_premium = ce_price + pe_price
                    ce_scrip, ce_scrip_token, ce_price, pe_scrip, pe_scrip_token, pe_price, futures_scrip, futures_token, futures = select_straddle_strikes(index, check_time)
                    lower_range, upper_range = get_range_sl_prices(ce_scrip, ce_price + pe_price, range_sl)
                    intra_lower_range, intra_upper_range = get_range_sl_prices(ce_scrip, ce_price + pe_price, intra_sl)

                    ce_hedge_limit = int(ce_scrip[:-2]) + ((ce_price + pe_price) * hedge_sd)
                    pe_hedge_limit = int(pe_scrip[:-2]) - ((ce_price + pe_price) * hedge_sd)
                    ce_hedge = str(int(ce_hedge_limit - (ce_hedge_limit % 100) + 100)) + 'CE'
                    pe_hedge = str(int(pe_hedge_limit - (pe_hedge_limit % 100))) + 'PE'

                    straddle_slipage_price = (ce_price + pe_price) - ((ce_price + pe_price) * slipage)

                    re_no = re_no + 1
                    print('SL no.', re_no)
                    print(ce_scrip, ce_price)
                    print(pe_scrip, pe_price)
                    print('Premium ', ce_price + pe_price)
                    print('Lower Range ', lower_range)
                    print('Upper Range ', upper_range)
                    print('Intra Lower Range ', intra_lower_range)
                    print('Intra Upper Range ', intra_upper_range)
                    print('CE Hedge ', ce_hedge)
                    print('PE Hedge ', pe_hedge)
                    print()

                    if datetime.datetime.today().date() == check_time.date():
                        msg = f"*{caps_strategy}* SELL New Straddle ✅ \n\nSL No {re_no} \n\nOLD\n{old_straddle}  {round(old_premium,2)} \n\nNew\n{ce_scrip[:-2]}  {round(ce_price + pe_price,2)} \n\nLower Range {lower_range} \nUpper Range {upper_range} \n\nTime {check_time.time()}"
                        telegram().send_message(telegram.group.Weekly_trade, msg)

                        # update google sheet
                        gsheet.Update_cell(BT_sheet, ts_ce_index, 31, live_pnl)
                        gsheet.Update_Batch(BT_sheet, f"{chr(65 + (re_no * 3))}{ts_ce_index}:{chr(67 + (re_no * 3))}{ts_pe_index + 1}", [[ce_scrip, ce_price, f'({lower_range}, {upper_range})'], [pe_scrip, pe_price, f'({intra_lower_range}, {intra_upper_range})'], ['', ce_price + pe_price, '']])
                        gsheet.Update_Batch(BT_sheet, f"AB{ts_ce_index}:AC{ts_ce_index}", [[ce_hedge, pe_hedge]])

                    entry_time = sl_time
                    sell_new_straddle, modify_straddle_prices = False, True

                check_time = check_time + datetime.timedelta(minutes=1)

        if modify_straddle_prices:
            if datetime.datetime.now() > entry_time + datetime.timedelta(minutes=2):

                ce_price = candle_data(ce_scrip_token, entry_time)[-1]
                pe_price = candle_data(pe_scrip_token, entry_time)[-1] 

                lower_range, upper_range = get_range_sl_prices(ce_scrip, ce_price + pe_price, range_sl) 
                intra_lower_range, intra_upper_range = get_range_sl_prices(ce_scrip, ce_price + pe_price, intra_sl)

                straddle_slipage_price = (ce_price + pe_price) - ((ce_price + pe_price) * slipage)

                print('\nModified Range ')
                print('Premium ', ce_price + pe_price)
                print('Lower Range ', lower_range)
                print('Upper Range ', upper_range)
                print('Intra Lower Range ', intra_lower_range)
                print('Intra Upper Range ', intra_upper_range)
                print()

                if datetime.datetime.today().date() == check_time.date():

                    # update google sheet
                    gsheet.Update_Batch(BT_sheet, f"{chr(66 + (re_no * 3))}{ts_ce_index}:{chr(67 + (re_no * 3))}{ts_pe_index + 1}", [[ce_price, f'({lower_range}, {upper_range})'], [pe_price, f'({intra_lower_range}, {intra_upper_range})'], [ce_price + pe_price, '']])
                    gsheet.cell_modified(BT_sheet, f"{chr(67 + (re_no * 3))}{ts_ce_index}:{chr(67 + (re_no * 3))}{ts_pe_index}")

                modify_straddle_prices = False

        if check_straddle_sl == modify_straddle_prices == sell_new_straddle == False and sell_flag == 1:
            break

        if check_time.time() > exit_time:
            check_time = check_time - datetime.timedelta(minutes=1)

            if 'Expiry' in Parameter.Get_trading_day() and datetime.datetime.today().date() == check_time.date():
                print('\nStrategy Over\n')
                print('\nTotal PNL : ', live_pnl)

                today_pnl = live_pnl - previous_day_pnl
                print('\nTODAY PNL : ',today_pnl)

                gsheet.Update_cell(BT_sheet, ts_ce_index, 31, live_pnl)
                gsheet.Update_PNL_On_Sheet(caps_strategy, today_pnl)

                break

            if (datetime.datetime.now() - check_time) > datetime.timedelta(minutes=10):
                pass
            else:
                sleep(240)

            t_ce_scrip, t_ce_scrip_token, t_ce_price, t_pe_scrip, t_pe_scrip_token, t_pe_price, t_futures_scrip, t_futures_token, t_futures = select_straddle_strikes(index, check_time)

            straddle_close = t_ce_price + t_pe_price

            lower_range, upper_range = get_range_sl_prices(ce_scrip, straddle_close, range_sl)
            intra_lower_range, intra_upper_range = get_range_sl_prices(ce_scrip, straddle_close, intra_sl)

            print('\nModified EOD Range ')
            print('Time ', check_time)
            print('Straddle', t_ce_scrip[:-2])
            print('Premium ', straddle_close)
            print('Lower Range ', lower_range)
            print('Upper Range ', upper_range)
            print('Intra Lower Range ', intra_lower_range)
            print('Intra Upper Range ', intra_upper_range)
            print()

            if datetime.datetime.today().date() == check_time.date():
                msg = f"*{caps_strategy}* Modified EOD Range 🟦 \n\nStraddle {t_ce_scrip[:-2]} \nPremium {round(straddle_close,2)} \n\nLower Range {lower_range} \nUpper Range {upper_range} \nIntra Lower Range {intra_lower_range} \nIntra Upper Range {intra_upper_range} \n\nTime {check_time.time()}"
                telegram().send_message(telegram.group.Weekly_trade, msg)
                
                gsheet.Update_Batch(BT_sheet, f"{chr(67 + (re_no * 3))}{ts_ce_index}:{chr(67 + (re_no * 3))}{ts_pe_index}", [[f'({lower_range}, {upper_range})'], [f'({intra_lower_range}, {intra_upper_range})']])

            check_time = datetime.datetime.combine(check_time + datetime.timedelta(days=1) , datetime.time(9,16)) - datetime.timedelta(seconds=1)
            check_time = increment_if_holiday(check_time)

            if datetime.datetime.today().date() < check_time.date():
                print('\nTotal PNL : ', live_pnl)

                today_pnl = live_pnl - previous_day_pnl
                print('\nTODAY PNL : ',today_pnl)

                gsheet.Update_cell(BT_sheet, ts_ce_index, 31, live_pnl)
                gsheet.Update_PNL_On_Sheet(caps_strategy, today_pnl)

                break
            else:
                print('\nTotal PNL : ', live_pnl)

                today_pnl = live_pnl - previous_day_pnl
                print('\nTODAY PNL : ',today_pnl)

                previous_day_pnl = live_pnl
                print(f'\nNext Day {check_time.strftime("%A")}\n\n')

except Exception as e:
    print(e)
    msg = "⚠️⚠️⚠️ Error !!! ⚠️⚠️⚠️ \n" + caps_strategy + " Code stop "
    telegram().send_message(telegram.group.BT_Vs_Actual_diff, msg + '\n' + str(e))

