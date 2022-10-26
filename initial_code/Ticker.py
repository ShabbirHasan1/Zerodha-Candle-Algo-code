code_name = 'Ticker'
import ctypes
ctypes.windll.kernel32.SetConsoleTitleW(code_name)
print(code_name)

import requests
import datetime
import pandas as pd
from time import sleep
import mysql.connector as sql
import warnings
warnings.filterwarnings('ignore')

import sys
import os
sys.path.append(os.path.abspath('..') + '\\inhouse_functions')
from telegram import telegram

teg = telegram()
teg.send_message(teg.group.BT_Vs_Actual_diff, '*Ticker Start ... *')

def tokens_list():
    tokens_data = pd.read_sql("SELECT * FROM tokens", mydb)
    return tokens_data['token'].to_list()

def create_table(name):
    cmd =  f"create table {name} ( date_time datetime not null primary key, open double, high double, low double, close double );"
    mycursor.execute(cmd)
    mydb.commit()

def check_table(name):
    cmd = f"show tables like '{name}';"
    mycursor.execute(cmd)
    try:
        mycursor.fetchone()[0]
        return True
    except:
        return False

def insert_data(name, data_list):
    cmd = f"replace into {name}(date_time, open, high, low, close) values(%s, %s, %s, %s, %s)"
    mycursor.executemany(cmd, data_list)
    mydb.commit()

def get_candle_data(token):
    try:
        start_date = datetime.datetime(2022,10,21).date().strftime('%Y-%m-%d')
        end_date = datetime.datetime.now().date().strftime('%Y-%m-%d')
        #open and read the file after the appending:
        f = open("zerodha_cookies.txt", "r")
        cookies = f.read()
        f.close()

        url = 'https://kite.zerodha.com/oms/instruments/historical/'+ str(token) +'/minute?user_id=BI3179&oi=1&from=' + start_date + '&to=' + end_date + '&ciqrandom=1597949155770'
        headers = {
            'authorization': 'enctoken ' + cookies
        }

        x = requests.get(url, headers=headers)

        df = pd.DataFrame(x.json()['data']['candles']).iloc[:,0:5]
        df[0]= df[0].str.replace('T', ' ').str.split('+').str[0]

        li = []
        for i in df.values:
            li.append(tuple(i))

        return li
    except:
        sleep(10)

start_time = datetime.datetime.combine(datetime.datetime.now().date(), datetime.time(9, 15))
end_time = datetime.datetime.combine(datetime.datetime.now().date(), datetime.time(15, 30))
interval_in_sec = 1

check_time = datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M')

while True:
    
    if start_time < datetime.datetime.now() < end_time:
        
        if datetime.datetime.now() > check_time:
            sleep(interval_in_sec)
            print(check_time)

            mydb = sql.connect( host="localhost", user="root", password="1988", database="candle_db", consume_results=True)
            mycursor = mydb.cursor()

            data = pd.read_sql('select * from tokens', con=mydb)
            token_list = data['token'].to_list() 

            for token in token_list:
                if check_table(f"t_{token}"):
                    """update price"""
                    insert_data(f"t_{token}", get_candle_data(token))
                else:
                    print(f"New Table Created t_{token}")
                    create_table(f"t_{token}")
                    insert_data(f"t_{token}", get_candle_data(token))

            mydb.close()
            check_time += datetime.timedelta(minutes=1)