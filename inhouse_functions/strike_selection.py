import datetime
import pandas as pd
import mysql.connector as sql
from time import sleep
from Candle_Data import strike_candle_data

insert_str = "INSERT IGNORE INTO tokens (token, scrip) VALUES (%s , %s)"

def insert_token_in_db(token_list):
    """
    token_list format = [(token, scrip), ....]
    
    """
    mydb = sql.connect(host="localhost", user="root", password="1988", database="candle_db" )
    mycursor = mydb.cursor()
    mycursor.executemany(insert_str, token_list)
    mydb.commit()
    mydb.close()

def get_fno_data(index):
    """
    return future tradingsymbol , future instrument_token , options_data
    """
    data = pd.read_csv('../instrument_file.csv')
    data = data[data.name.isin([index])]
    data.expiry = pd.to_datetime(data.expiry, format='%Y-%m-%d')
    data = data[data.expiry.dt.date >= datetime.datetime.today().date()]
    option_data = data[data.expiry == data.expiry.min()].reset_index(drop=True)
    future_data = data[data.segment.isin(['NFO-FUT'])]
    future_data = future_data[future_data.expiry == future_data.expiry.min()]
    
    return future_data.tradingsymbol.iloc[0], int(future_data.instrument_token.iloc[0]), option_data

def get_scrip_trading_symbol(index, scrip):
    future_trading_symbol, future_token, data = get_fno_data(index)
    return data[data['tradingsymbol'].str.endswith(scrip)]['tradingsymbol'].iloc[0]

def get_scrip_instrument_token(index, scrip):
    future_trading_symbol, future_token, data = get_fno_data(index)
    return data[data['tradingsymbol'].str.endswith(scrip)]['instrument_token'].iloc[0]

def select_strangle_strikes(index, target, entry_time):
    if (datetime.datetime.now() - entry_time) > datetime.timedelta(minutes=2):
        pass
    else:
        sleep(60)
        
    future_scrip, future_token, options_data = get_fno_data(index)

    o, h, l, c = strike_candle_data(future_token, entry_time)

    indices = ['BANKNIFTY', 'NIFTY']
    steps = [100, 50]
    limits = [2000, 800]

    limit = limits[indices.index(index)]
    step = steps[indices.index(index)]

    future_price = round(c/step)*step

    scrips_list, tokens_list = [], []

    for i in range(future_price-limit, future_price+limit+step, step):
        scrips_list.append(str(i) + 'CE')
        scrips_list.append(str(i) + 'PE')

    scrips_list.sort()

    for scrip in scrips_list.copy():
        try:
            tokens_list.append(options_data[options_data['tradingsymbol'].str.endswith(scrip)]['instrument_token'].iloc[0])
        except:
            scrips_list.remove(scrip)

    scrips_list.append(future_scrip)
    tokens_list.append(int(future_token))

    d = pd.DataFrame(columns=('scrip/token/price').split('/'))

    d['scrip'] = scrips_list
    d['token'] = tokens_list
    d['price'] = 0

    for idx, row in d.iterrows():
        o,h,l,c = strike_candle_data(row['token'], entry_time)
        d.loc[idx, 'price'] = c

    temp_d = d[d['price'] >= target].sort_values(by=['price'])

    ce_s = temp_d[temp_d['scrip'].str.endswith('CE')]['scrip'].iloc[0]
    pe_s = temp_d[temp_d['scrip'].str.endswith('PE')]['scrip'].iloc[0]

    ce_scrip_list = [ce_s, str(int(ce_s[:-2])-step) + 'CE', str(int(ce_s[:-2])+step) + 'CE']
    pe_scrip_list = [pe_s, str(int(pe_s[:-2])-step) + 'PE', str(int(pe_s[:-2])+step) + 'PE']

    call_price_list, put_price_list = [], []

    d.set_index('scrip', inplace=True)

    for i in range(3):
        call_price_list.append(d.loc[ce_scrip_list[i],'price'])
        put_price_list.append(d.loc[pe_scrip_list[i],'price'])

    init_call = call_price_list[0]
    init_put = put_price_list[0]
    target_2 = target*2
    min_diff = 999999
    diff = abs(init_put - init_call)
    if (init_call+init_put >= target_2) & (min_diff > diff):
        min_diff = diff
        ce_strike, pe_strike = ce_s, pe_s

    for i in range(1,3):
        if (min_diff  > abs(put_price_list[i]-init_call)) & (put_price_list[i]+init_call >= target_2):
            min_diff = abs(put_price_list[i] - init_call)
            ce_strike, pe_strike = ce_s, pe_scrip_list[i]

        if (min_diff  > abs(call_price_list[i]-init_put)) & (call_price_list[i]+init_put >= target_2):
            min_diff = abs(call_price_list[i] - init_put)
            ce_strike, pe_strike = ce_scrip_list[i], pe_s

    ce_scrip_token = d.loc[ce_strike,'token']
    pe_scrip_token = d.loc[pe_strike,'token']

    ce_scrip_price = d.loc[ce_strike,'price']
    pe_scrip_price = d.loc[pe_strike,'price']
    
    insert_token_in_db([(int(ce_scrip_token), str(ce_strike)), (int(pe_scrip_token), str(pe_strike))])
        
    return ce_strike, ce_scrip_token, ce_scrip_price, pe_strike, pe_scrip_token, pe_scrip_price

def select_straddle_strikes(index, entry_time):
    if (datetime.datetime.now() - entry_time) > datetime.timedelta(minutes=2):
        pass
    else:
        sleep(15)
        
    future_scrip, future_token, options_data = get_fno_data(index)
    options_data.sort_values(by=['tradingsymbol'], inplace=True)

    o, h, l, future_price = strike_candle_data(future_token, entry_time)

    indices = ['BANKNIFTY', 'NIFTY']
    steps = [100, 50]
    limits = [100, 50]

    limit = limits[indices.index(index)]
    step = steps[indices.index(index)]

    round_future_price = round(future_price/step)*step
    ce_scrip = str(round_future_price) + 'CE'
    pe_scrip = str(round_future_price) + 'PE'

    scrips_list = [ce_scrip, pe_scrip]

    scrips_tuple = tuple(scrips_list)
    instrument_tokens_list = list(options_data[options_data['tradingsymbol'].str.endswith(scrips_tuple)]['instrument_token'])
    tokens_list = instrument_tokens_list

    d = pd.DataFrame(columns=('scrip/token/price').split('/'))

    d['scrip'] = scrips_list
    d['token'] = tokens_list
    d['price'] = 0

    for idx, row in d.iterrows():
        o,h,l,c = strike_candle_data(row['token'], entry_time)
        d.loc[idx, 'price'] = c

    sync_future = round((d['price'].iloc[0] - d['price'].iloc[1] + round_future_price) / step) * step

    scrips_list,tokens_list = [],[]

    ce_scrip_list = [str(sync_future) + 'CE', str(sync_future+step) + 'CE', str(sync_future-step) + 'CE']
    pe_scrip_list = [str(sync_future) + 'PE', str(sync_future+step) + 'PE', str(sync_future-step) + 'PE']

    scrips_list = ce_scrip_list + pe_scrip_list
    scrips_list.sort()
    scrips_tuple = tuple(scrips_list)
    instrument_tokens_list = list(options_data[options_data['tradingsymbol'].str.endswith(scrips_tuple)]['instrument_token'])
    tokens_list = instrument_tokens_list

    d = pd.DataFrame(columns=('scrip/token/price').split('/'))

    d['scrip'] = scrips_list
    d['token'] = tokens_list
    d['price'] = 0

    for idx, row in d.iterrows():
        o,h,l,c = strike_candle_data(row['token'], entry_time)
        d.loc[idx, 'price'] = c

    d.set_index('scrip', inplace=True)

    difference = []
    for i in range(3):
        try:
            ce_price = d.loc[(ce_scrip_list[i]),'price']
            pe_price = d.loc[(pe_scrip_list[i]),'price']
            difference.append(abs(ce_price-pe_price))
        except:
            difference.append(-1)

    min_value = 999999
    for i in range(3):
        if ((min_value > difference[i]) & (difference[i] != -1)):
            min_value = difference[i]
            scrip_index = i

    # Required scrip and their price
    ce_scrip = ce_scrip_list[scrip_index]
    pe_scrip = pe_scrip_list[scrip_index]
    ce_price = d.loc[ce_scrip,'price']
    pe_price = d.loc[pe_scrip,'price']
    ce_token = d.loc[ce_scrip,'token']
    pe_token = d.loc[pe_scrip,'token']
    
    insert_token_in_db([(int(ce_token), str(ce_scrip)), (int(pe_token), str(pe_scrip))])

    return ce_scrip, ce_token, ce_price, pe_scrip, pe_token, pe_price, future_scrip, future_token, future_price

def find_ut_scrip(index, target, signal, future_price , entry_time):
    if (datetime.datetime.now() - entry_time) > datetime.timedelta(minutes=2):
        pass
    else:
        sleep(60)
  
    future_scrip, future_token, options_data = get_fno_data(index)
    options_data.sort_values(by=['tradingsymbol'], inplace=True)

    indices = ['BANKNIFTY', 'NIFTY']
    steps = [100, 50]
    limits = [2000, 600]

    limit = limits[indices.index(index)]
    step = steps[indices.index(index)]

    future_price = round(future_price/step)*step

    scrips_list, tokens_list = [], []
    
    for i in range(future_price-limit, future_price+limit+step, step):
        scrips_list.append(str(i) + signal)

    scrips_list.sort()

    for scrip in scrips_list.copy():
        try:
            tokens_list.append(options_data[options_data['tradingsymbol'].str.endswith(scrip)]['instrument_token'].iloc[0])
        except:
            scrips_list.remove(scrip)

    d = pd.DataFrame(columns=('scrip/token/price').split('/'))

    d['scrip'] = scrips_list
    d['token'] = tokens_list
    d['price'] = 0

    for idx, row in d.iterrows():
        o,h,l,c = strike_candle_data(row['token'], entry_time)
        d.loc[idx, 'price'] = c

    temp_d = d[d['price'] >= target].sort_values(by=['price'])

    s = temp_d['scrip'].iloc[0]
    s_token = temp_d['token'].iloc[0]
    s_price = temp_d['price'].iloc[0]
    
    insert_token_in_db([(int(s_token), str(s))])
    
    return s, s_token, s_price

def get_range_sl_prices(straddle_scrip, premium, range_sl):
    """
    straddle scrip either call Scrip or put Scrip i.e with CE/PE
    """
    limit = premium * (range_sl/100)
    lower_range = int(straddle_scrip[:-2]) - limit
    upper_range = int(straddle_scrip[:-2]) + limit
    return lower_range, upper_range
