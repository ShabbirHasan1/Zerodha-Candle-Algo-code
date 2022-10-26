import pandas as pd
from time import sleep

data = pd.read_csv('https://api.kite.trade/instruments')
data.to_csv('../instrument_file.csv', index=False) 
print('Instrument downloaded')
sleep(300)
