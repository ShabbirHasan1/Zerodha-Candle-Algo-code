import requests
import pandas as pd
from time import sleep
import mysql.connector as sql

import warnings
warnings.filterwarnings('ignore')

def strike_candle_data(token, check_time):
    while True:
        try:
            o,h,l,c = 0,0,0,0
            today = check_time.date().strftime('%Y-%m-%d')
            #open and read the file after the appending:
            f = open("../zerodha_cookies.txt", "r")
            cookies = f.read()
            f.close()

            time = check_time.time().strftime('%H:%M')
            url = 'https://kite.zerodha.com/oms/instruments/historical/'+ str(token) +'/minute?user_id=BI3179&oi=1&from=' + today + '&to=' + today + '&ciqrandom=1597949155770'
            headers = {
                'authorization': 'enctoken ' + cookies
            }
            x = requests.get(url, headers=headers)

            if x.status_code == 429:
                sleep(30)
                raise Exception('To Many Request')

            for i in range(len(x.json()['data']['candles'])):
                if x.json()['data']['candles'][i][0][11:16] == time:
                    cd = x.json()['data']['candles'][i]
                    o, h, l, c =  cd[1], cd[2], cd[3], cd[4]
            return o, h, l, c
        except Exception as e:
            print(e)
            sleep(2)
            
def candle_data(token, check_time):
    try:
        t_check_time = check_time.strftime('%Y-%m-%d %H:%M') + ':00'
        mydb = sql.connect(host="localhost", user="root", password="1988", database="candle_db", consume_results=True)
        ohlc = pd.read_sql_query(f"SELECT * FROM t_{token} WHERE date_time = '{t_check_time}';", con=mydb).iloc[0].to_list()[1:]
        mydb.close()
        return ohlc
    except:
        mydb.close()
        print('except')
        return strike_candle_data(token, check_time)      