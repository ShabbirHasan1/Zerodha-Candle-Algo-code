import os
import sys
import ctypes
code_name = sys.argv[0].split('\\')[-1].replace('.py', '')
ctypes.windll.kernel32.SetConsoleTitleW(code_name)
print(code_name)

sys.path.append(os.path.abspath('..') + '\\inhouse_functions')
import requests
import datetime
from time import sleep
from play_sound import PlaySound

while True:
    sleep(5)
    
    if datetime.datetime.now().time() > datetime.time(16,30):
        break
    
    try:
        requests.get('https://www.google.com/')
    except:
        PlaySound('Internet Issue')