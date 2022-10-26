code_name = 'Run Stop Code Message'
import ctypes
ctypes.windll.kernel32.SetConsoleTitleW(code_name)
print(code_name)

import sys
import os
sys.path.append(os.path.abspath('..') + '\\inhouse_functions')

import psutil
import datetime
from time import sleep
from telegram import telegram
from parameter import Parameter

if 'Expiry' in Parameter.Get_trading_day():
    exit_time = datetime.time(15,29)
else:
    exit_time = datetime.time(15,25)

market_open = True
previous_script = []
while market_open:
    pid_list = psutil.pids()

    script_list = []
    for pid in pid_list:
        try:
            p = psutil.Process(pid)
            if 'python.exe' in p.name():
                script_name = p.cmdline()[-1].split('\\')[-1]
                if script_name.endswith('py'):
                    script_list.append(script_name)
        except:
            pass
       
    t1 = list(set(previous_script) - set(script_list))
    t2 = list(set(script_list) - set(previous_script))
    
    if len(t1) > 0:
        for t in t1:
            telegram().send_message(telegram.group.BT_Vs_Actual_diff, f'*" {t[:-3]} "   Code Close ❌*')
        
    if len(t2) > 0:
        for t in t2:
            telegram().send_message(telegram.group.BT_Vs_Actual_diff, f'*" {t[:-3]} "   Code Start ✈️*')
        
    previous_script = script_list
    
    if datetime.datetime.now().time() > exit_time:
        if datetime.datetime.now() - datetime.datetime.combine(datetime.datetime.today().date(), datetime.time(15, 29)) < datetime.timedelta(minutes=5):
            market_open = False
        
    sleep(10)