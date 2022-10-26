import sys
import pandas as pd
import datetime
from time import sleep

holiday_data = pd.read_csv('../holidays.csv')
holiday_data.Date = pd.to_datetime(holiday_data.Date)

def is_holiday(date):
    if (pd.Timestamp(date.date()) in list(holiday_data.Date)) or (pd.Timestamp(date).weekday() == 5) or (
            pd.Timestamp(date).weekday() == 6):
        return True
    else:
        return False

def holiday_reason(date):
    if pd.Timestamp(date.date()) in list(holiday_data.Date):
        return holiday_data[holiday_data['Date'] == pd.Timestamp(date.date())]['Description'].iloc[0]
    elif pd.Timestamp(date).weekday() == 5:
        return 'Due to Saturday'
    elif pd.Timestamp(date).weekday() == 6:
        return 'Due to Sunday'
    else:
        return 'Not a Holiday'

def increment_if_holiday(date):
    while True:
        if is_holiday(date):
            date += datetime.timedelta(days=1)
        else:
            break
    return date

def set_trading_day(trading_day):
    week_list = {'Friday':0, 'Saturday':1, 'Sunday':2, 'Monday':3, 'Tuesday':4, 'Wednesday':5, 'Thursday':6}
    trading_day_no = {'Friday':5, 'Saturday':4, 'Sunday':4, 'Monday':4, 'Tuesday':3, 'Wednesday':2, 'Thursday':1}
    friday_date = (datetime.datetime.now() - datetime.timedelta(days = week_list[datetime.datetime.now().date().strftime('%A')])).date()
    thrusday_date = (datetime.datetime.now() + datetime.timedelta(days = week_list['Thursday'] - week_list[datetime.datetime.now().date().strftime('%A')])).date()
    week_date_list = list(pd.date_range(friday_date, thrusday_date))
    starting_date = [d for d in week_date_list if not is_holiday(d)][-trading_day_no[trading_day]:][0]
    
    if starting_date.date() > datetime.datetime.now().date():
        print('NO Trade Today :) ')
        sleep(5)
        sys.exit(0)
    else:
        return starting_date.strftime('%A')