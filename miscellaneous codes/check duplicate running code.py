import psutil
from time import sleep

code_name = 'Duplicate Code Check'
import ctypes
ctypes.windll.kernel32.SetConsoleTitleW(code_name)
print(code_name)

while True:
    pid_list = psutil.pids()

    scrip_list = []
    for pid in pid_list:
        try:
            p = psutil.Process(pid)
            if 'python.exe' in p.name():
                script_name = p.cmdline()[-1].split('\\')[-1]
                if script_name.endswith('py'):
                    scrip_list.append(script_name)
        except:
            pass

    dup = list({x for x in scrip_list if scrip_list.count(x) > 1})

    if len(dup) >= 1:
        print(dup)
    
    sleep(30)