code_name = 'Hedge Calculate'
import ctypes
ctypes.windll.kernel32.SetConsoleTitleW(code_name)
print(code_name)

import sys
import os
sys.path.append(os.path.abspath('..') + '\\inhouse_functions')

import requests
import pandas as pd
import datetime
from Candle_Data import candle_data
from strike_selection import get_fno_data, get_scrip_trading_symbol, get_scrip_instrument_token
from telegram import telegram
import dataframe_image as dfi
import concurrent.futures
from play_sound import PlaySound

check_market_open = True
if datetime.datetime.now().time() > datetime.time(9,15):
    check_market_open = False

while True:
    
    if check_market_open:
        if datetime.datetime.now().time() > datetime.time(9,15):
            PlaySound('Market Open')
            check_market_open = False
            
    if datetime.datetime.now().time() > datetime.time(9,16,5):
        telegram().send_message(telegram.group.BT_Vs_Actual_diff, 'Hedge Benefit Calculate ...')
        break

hedge_time = (datetime.datetime.now() - datetime.timedelta(minutes=1)).time()

if datetime.datetime.now().time() > datetime.time(15,29):
    hedge_time = datetime.time(15,29)

bn_future_trading_symbol, bn_future_token, bdata = get_fno_data('BANKNIFTY')
future_ltp = candle_data(bn_future_token, datetime.datetime.combine(datetime.datetime.now().date(), hedge_time))[-1]
bn_straddle_strike = round(future_ltp/100) * 100

nf_future_trading_symbol, nf_future_token, ndata = get_fno_data('NIFTY')
future_ltp = candle_data(nf_future_token, datetime.datetime.combine(datetime.datetime.now().date(), hedge_time))[-1]
nf_straddle_strike = round(future_ltp/50) * 50

print('Time ', hedge_time)
print('BN Straddle Strike -', bn_straddle_strike)
print('NF Straddle Strike -', nf_straddle_strike)

def get_basket_result(index, straddle_strike, gap):
    while True:
        try:
            retrn = {}

            if index == 'BANKNIFTY':
                quantity = 25
            elif index == 'NIFTY':
                quantity = 50

            future_trading_symbol, future_token, data = get_fno_data(index)
            ce_scrip = data[data['tradingsymbol'].str.endswith(str(straddle_strike) + 'CE')]['tradingsymbol'].iloc[0]
            pe_scrip = data[data['tradingsymbol'].str.endswith(str(straddle_strike) + 'PE')]['tradingsymbol'].iloc[0]
            
            try:
                call_hedge_scrip = data[data['tradingsymbol'].str.endswith(str(int(straddle_strike) + gap) + 'CE')]['tradingsymbol'].iloc[0]
            except:
                call_hedge_scrip = ''
            
            try:
                put_hedge_scrip = data[data['tradingsymbol'].str.endswith(str(int(straddle_strike) - gap) + 'PE')]['tradingsymbol'].iloc[0]
            except:
                put_hedge_scrip = ''
                
            f = open("../zerodha_cookies.txt")
            cookies = f.read()
            f.close()

            headers = {
                'authorization': f'enctoken {cookies}',
            }

            json_data = [
                {'exchange': 'NFO', 'tradingsymbol': ce_scrip, 'transaction_type': 'SELL', 'variety': 'regular',
                    'product': 'MIS', 'order_type': 'MARKET', 'quantity': quantity,},
                {'exchange': 'NFO', 'tradingsymbol': pe_scrip, 'transaction_type': 'SELL', 'variety': 'regular',
                    'product': 'MIS', 'order_type': 'MARKET', 'quantity': quantity,},
            ]

            response = requests.post('https://kite.zerodha.com/oms/margins/basket?consider_positions=&mode=compact', headers=headers, json=json_data)
            st_required_margin = response.json()['data']['initial']['total']
            st_final_margin = response.json()['data']['final']['total']

            retrn['w/o_Hedge'] = {'required_margin': st_required_margin, 'final_margin':st_final_margin}
            
            # with hedge 
            ce_hedge_token = data[data['tradingsymbol'].str.endswith(str(int(straddle_strike) + gap) + 'CE')]['instrument_token'].iloc[0]
            pe_hedge_token = data[data['tradingsymbol'].str.endswith(str(int(straddle_strike) - gap) + 'PE')]['instrument_token'].iloc[0]
            
            ce_hedge_price = candle_data(ce_hedge_token, datetime.datetime.combine(datetime.datetime.now().date(), hedge_time))[-1]
            pe_hedge_price = candle_data(pe_hedge_token, datetime.datetime.combine(datetime.datetime.now().date(), hedge_time))[-1]
            hedge_price = ce_hedge_price + pe_hedge_price
            
            json_data += [
                {'exchange': 'NFO', 'tradingsymbol': call_hedge_scrip, 'transaction_type': 'BUY', 'variety': 'regular',
                    'product': 'MIS', 'order_type': 'MARKET', 'quantity': quantity,},
                {'exchange': 'NFO', 'tradingsymbol': put_hedge_scrip, 'transaction_type': 'BUY', 'variety': 'regular',
                    'product': 'MIS', 'order_type': 'MARKET', 'quantity': quantity,},
            ]

            response = requests.post('https://kite.zerodha.com/oms/margins/basket?consider_positions=&mode=compact', headers=headers, json=json_data)
            required_margin = response.json()['data']['initial']['total']
            final_margin = response.json()['data']['final']['total']

            retrn['hedge_scrip'] = {'call': call_hedge_scrip, 'put': put_hedge_scrip}
            retrn['with_Hedge'] = {'required_margin': required_margin, 'final_margin':final_margin}
            retrn['hedge_benefit'] = st_required_margin - final_margin
            retrn['hedge_price'] = hedge_price
            retrn['gap'] = gap
            return retrn
        except Exception as e:
            print(e, gap)
            retrn = {}
            retrn['w/o_Hedge'] = {'required_margin': 0, 'final_margin':0}
            retrn['hedge_scrip'] = {'call': call_hedge_scrip, 'put': put_hedge_scrip}
            retrn['with_Hedge'] = {'required_margin': 0, 'final_margin':0}
            retrn['hedge_benefit'] = 0
            retrn['hedge_price'] = 0
            retrn['gap'] = gap
            return retrn

bn_range = [1000, 3100]
nf_range = [500, 1100]
hedge_data_frame = pd.DataFrame(columns='Straddle/Gap/ce_hedge/pe_hedge/hedge_price/Required Margin/Final Margin/Benefit'.split('/'))

bn_gap_list = []
for gap in range(bn_range[0], bn_range[1], 100):
    bn_gap_list.append(gap)
    
nf_gap_list = []
for gap in range(nf_range[0], nf_range[1], 50):
    nf_gap_list.append(gap)

# banknifty
bn_hedge_data = hedge_data_frame.copy()

with concurrent.futures.ThreadPoolExecutor() as executor:
    result = [executor.submit(get_basket_result, 'BANKNIFTY', bn_straddle_strike, gap) for gap in bn_gap_list]
for f in concurrent.futures.as_completed(result):
    response_dict = f.result()
    bn_hedge_data.loc[len(bn_hedge_data)] = [bn_straddle_strike, response_dict['gap'], response_dict['hedge_scrip']['call'][-7:], response_dict['hedge_scrip']['put'][-7:], response_dict['hedge_price'], int(response_dict['w/o_Hedge']['required_margin']), int(response_dict['with_Hedge']['final_margin']), int(response_dict['hedge_benefit'])]
bn_hedge_data.sort_values(by=['Gap'], inplace=True, ignore_index=True)

bn_hedge_data['Required Margin'] = bn_hedge_data.apply(lambda x: "{:,}".format(x['Required Margin']), axis=1)
bn_hedge_data['Final Margin'] = bn_hedge_data.apply(lambda x: "{:,}".format(x['Final Margin']), axis=1)
bn_hedge_data['Benefit'] = bn_hedge_data.apply(lambda x: "{:,}".format(x['Benefit']), axis=1)
dfi.export(bn_hedge_data,'bn_hedge.png')
telegram().send_image(telegram.group.BT_Vs_Actual_diff, 'bn_hedge.png', '*BANKNIFTY HEDGE*')

# nifty
nf_hedge_data = hedge_data_frame.copy()

with concurrent.futures.ThreadPoolExecutor() as executor:
    result = [executor.submit(get_basket_result, 'NIFTY', nf_straddle_strike, gap) for gap in nf_gap_list]
for f in concurrent.futures.as_completed(result):
    response_dict = f.result()
    nf_hedge_data.loc[len(nf_hedge_data)] = [nf_straddle_strike, response_dict['gap'], response_dict['hedge_scrip']['call'][-7:], response_dict['hedge_scrip']['put'][-7:], response_dict['hedge_price'], int(response_dict['w/o_Hedge']['required_margin']), int(response_dict['with_Hedge']['final_margin']), int(response_dict['hedge_benefit'])]
nf_hedge_data.sort_values(by=['Gap'], inplace=True, ignore_index=True)

nf_hedge_data['Required Margin'] = nf_hedge_data.apply(lambda x: "{:,}".format(x['Required Margin']), axis=1)
nf_hedge_data['Final Margin'] = nf_hedge_data.apply(lambda x: "{:,}".format(x['Final Margin']), axis=1)
nf_hedge_data['Benefit'] = nf_hedge_data.apply(lambda x: "{:,}".format(x['Benefit']), axis=1)
dfi.export(nf_hedge_data,'nf_hedge.png')
telegram().send_image(telegram.group.BT_Vs_Actual_diff, 'nf_hedge.png', '*NIFTY HEDGE*')

telegram().send_message(telegram.group.BT_Vs_Actual_diff, 'Hedge Benefit Calculate Code End !!!')