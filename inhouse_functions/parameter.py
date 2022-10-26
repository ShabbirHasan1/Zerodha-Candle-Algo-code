import pandas as pd
from datetime import datetime as dt

class Parameter:
    pick_day = ''
    entry_time = ''
    exit_time = ''

    __parameter_data = ''
    __param = ''
    __today_day = pd.Timestamp(dt.today()).day_name()

    def __init__(self, index, strategy):

        self.__param = strategy.replace(' ', '_').lower()

        if index == 'BANKNIFTY':
            self.__parameter_data = pd.read_excel('../parameters.xlsx', 'bn_entry_time').set_index('Day')
        else:
            self.__parameter_data = pd.read_excel('../parameters.xlsx', 'nf_entry_time').set_index('Day')

        data = pd.read_csv('../instrument_file.csv')
        data = data[data.name.isin([index])]
        data.expiry = pd.to_datetime(data.expiry, format='%Y-%m-%d')
        data = data[data.expiry.dt.date >= dt.today().date()]
        expiry_day = data.expiry.min().day_name()

        if self.__today_day != expiry_day:
            self.pick_day = self.__today_day
        else:
            self.pick_day = 'Thursday'

        self.entry_time = self.__parameter_data.loc[self.pick_day, self.__param]
        self.exit_time = self.__parameter_data.loc[self.pick_day, 'exit_time']

    def get(self, required):
        return self.__parameter_data.loc[self.pick_day, self.__param + '_' + required]

    def get_all_param(self):
        column = []
        value = []
        for i in range(len(list(self.__parameter_data.columns))):
            if self.__param in list(self.__parameter_data.columns)[i]:
                column.append(list(self.__parameter_data.columns)[i])
                value.append(self.__parameter_data.loc[self.pick_day, self.__parameter_data.columns][i])

        return  pd.DataFrame(value, columns=[self.__param], index=column)
    
    def Get_trading_day():
        data = pd.read_csv('../instrument_file.csv')
        data = data[data.name.isin(['BANKNIFTY'])]
        data.expiry = pd.to_datetime(data.expiry, format='%Y-%m-%d')
        data = data[data.expiry.dt.date >= dt.today().date()]
        expiry_day = data.expiry.min().day_name()

        if pd.Timestamp(dt.today()).day_name() != expiry_day:
            return pd.Timestamp(dt.today()).day_name()
        else:
            return pd.Timestamp(dt.today()).day_name() + " Expiry"