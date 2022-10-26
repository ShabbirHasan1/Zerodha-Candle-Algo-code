import sys
import os
sys.path.append(os.path.abspath('..') + '\\inhouse_functions')

code_name = 'Gsheet Pending Update'
import ctypes
ctypes.windll.kernel32.SetConsoleTitleW(code_name)
print(code_name)

import datetime
import pandas as pd
from time import sleep
from google_sheet import google_sheet
gsheet = google_sheet()
updated_row = 0

while True:
    sleep(2)
    
    if datetime.datetime.now().time() > datetime.time(16,30):
        break
    
    data = pd.read_csv(gsheet.pending_gsheet_path)
    data = data[updated_row:]

    if len(data) > 0:
        for idx, row in data.iterrows():
            print(idx)

            if not pd.isna(row['value']):

                if not pd.isna(row['cell']):
                    while True:
                        try:
                            sheet = gsheet.get_sheet(row['sheet_id'])
                            response = sheet.update_acell(str(row['cell']), row['value'])
                            break
                        except Exception as e:
                            print(e)
                            sleep(3)
                    print(updated_row, f" {sheet.title} Updated Cell {row['cell']} {row['value']}")

                else:
                    while True:
                        try:
                            sheet = gsheet.get_sheet(row['sheet_id'])
                            response = sheet.update_cell(int(row['row_no']), int(row['column_no']), row['value'])
                            break
                        except Exception as e:
                            print(e)
                            sleep(3)
                    print(updated_row, f" {sheet.title} Updated Row, Column {int(row['row_no'])} {int(row['column_no'])} {row['value']}")

            else:
                if not pd.isna(row['list_of_list']):
                
                    while True:
                        try:
                            sheet = gsheet.get_sheet(row['sheet_id'])
                            response = sheet.batch_update([{'range': row['range'], 'values':  eval(row['list_of_list'])}])
                            break
                        except Exception as e:
                            print(e)
                            sleep(3)
                    print(updated_row, f" {sheet.title} Updated Range {row['range']} {row['list_of_list']}")
                    
                else:
                    
                    while True:
                        try:
                            sheet = gsheet.get_sheet(row['sheet_id'])
                            response = sheet.format(row['range'], {"backgroundColor": {"red": 25.0, "green": 1.0, "blue": 25.0}})
                            break
                        except Exception as e:
                            print(e)
                            sleep(3)
                            
                    print(updated_row, f" {sheet.title} Updated Modified {row['range']}")

            updated_row +=1