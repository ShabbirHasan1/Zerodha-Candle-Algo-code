print('\nClean Trades Sheet...')
import pandas as pd
from time import sleep
import datetime
from google_sheet import google_sheet
gsheet = google_sheet()

sheet_ids = [gsheet.sheet_ids.weekly_bt_bn, gsheet.sheet_ids.weekly_bt_nf]
clean = False
for sheet_id in sheet_ids:
    sheet = gsheet.get_sheet(sheet_id)
    d = pd.DataFrame(sheet.get_all_records())
    
    if datetime.datetime.now().weekday() == 4:
        for q in list(d[d['1'].str.contains('-')].index):
            sleep(2)
            ts_ce_index = q + 3
            ts_pe_index = ts_ce_index + 1
            sheet.batch_clear([f'A{ts_ce_index}:AF{ts_pe_index + 1}'])
            sheet.format(f'A{ts_ce_index}:AF{ts_pe_index + 1}', {"backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}})
        clean = True
        
if clean:
    print('cleaning done\n')
else:
    print('No Cleaning Today\n')