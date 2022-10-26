code_name = 'Check Incomplete PNL Update'
import ctypes
ctypes.windll.kernel32.SetConsoleTitleW(code_name)
print(code_name)

import sys
import os
sys.path.append(os.path.abspath('..') + '\\inhouse_functions')

import difflib
import pandas as pd
import datetime
from glob import glob
from google_sheet import google_sheet
gsheet = google_sheet()

bn_codes_path = glob('..\\_banknifty\\*.py')
nf_codes_path = glob('..\\_nifty\\*.py')

bn_code = [file.split('\\')[-1].replace('-','_').replace('.py','').replace(' ', '_') for file in bn_codes_path]
nf_code = [file.split('\\')[-1].replace('-','_').replace('.py','').replace(' ', '_') for file in nf_codes_path]
sheet = gsheet.get_sheet(google_sheet.sheet_ids.BT_result_sheet)
pnl_series = google_sheet.get_sheet_df(sheet).set_index('Date').loc[str(datetime.datetime.now().date()), :]

for idx, value in pnl_series.items():
    try:
        if idx == 'SREW-1':
            break

        if value == '':
            if idx.startswith('NF_'):
                idx = idx.replace('NF_NRE', 'NRE')
                code_idx = nf_code.index(difflib.get_close_matches(idx, nf_code)[0])
                file_path = nf_codes_path[code_idx]
                os.system(f'python "{file_path}"')
            else:
                code_idx = bn_code.index(difflib.get_close_matches(idx, bn_code)[0])
                file_path = bn_codes_path[code_idx]
                os.system(f'python "{file_path}"')
        
    except Exception as e:
        print(idx, e)