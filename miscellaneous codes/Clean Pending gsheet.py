import os
import sys
import ctypes
code_name = sys.argv[0].split('\\')[-1].replace('.py', '')
ctypes.windll.kernel32.SetConsoleTitleW(code_name)
print(code_name)

import pandas as pd
pending_gsheet_csv_path = "gsheet_pending.csv"
pending_gsheet_csv = pd.read_csv(pending_gsheet_csv_path)
pd.DataFrame(columns=pending_gsheet_csv.columns).to_csv(pending_gsheet_csv_path, index=False)