import json
import gspread
import datetime
import pandas as pd
from time import sleep
from oauth2client.service_account import ServiceAccountCredentials

class google_sheet:
    __sheets = ''
    pending_gsheet_path = f"..\\miscellaneous codes\\gsheet_pending.csv"

    def __init__(self):

        json_dict = json.loads(open("Gsheet_key.cred").read())

        __scope = ['https://spreadsheets.google.com/feeds',
                   'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']

        __crediential = ServiceAccountCredentials.from_json_keyfile_dict(json_dict, __scope)
        
        while True:
            try:
                __c = gspread.authorize(__crediential)
                self.__sheets = __c.open('Trades').worksheets()
                break
            except:
                sleep(2)

    def get_sheet_df(sheet_object):
        return pd.DataFrame(sheet_object.get_all_records())

    class sheet_ids:
        bt_bn = 1665571173
        bt_nf = 215834870
        si_bn = 421206330
        si_nf = 1438107960
        iifl_bn = 1768395367
        iifl_nf = 473512704
        z_bn = 1859405329
        z_nf = 425800770
        BT_result_sheet = 1584186431
        new_bn_z = 1780893234
        new_nf_z = 1590832227
        weekly_bt_bn = 972503522
        weekly_bt_nf = 1558494065

    def get_sheet(self, sheet_id):
        sheet = self.__sheets[self.__sheets.index([ele for ele in self.__sheets if ele.id == sheet_id][0])]
        return sheet

    def get_sheet_and_index(self, sheet_id, caps_strategy):
        
        while True:
            try:
                cs = caps_strategy.split(' ')
                sheet = self.get_sheet(sheet_id)
                d = pd.DataFrame(sheet.get_all_records())
                ts_index = d[d['1'] == f"{' '.join(cs[1:-1])}-{cs[-1]}"].index[0] + 2
                ts_ce_index = ts_index + 1
                ts_pe_index = ts_ce_index + 1
                return sheet, ts_ce_index, ts_pe_index
            except:
                sleep(2)

    def Update_a_cell(sheet, column_alphabet, row_no, value):

        if type(value) == float:
            value = '{0:.2f}'.format(value)

        try:
            return sheet.update_acell(column_alphabet + str(row_no), value)
        except:
            data = pd.DataFrame(columns=['sheet_id', 'row_no', 'column_no', 'cell', 'value', 'range', 'list_of_list'])
            data.loc[len(data)] = [sheet.id, '', '' , column_alphabet + str(row_no), value, '', '']
            try:
                data.to_csv(google_sheet.pending_gsheet_path, mode='a', index=False, header=False)
            except Exception as e:
                print(e)

    def Update_cell(sheet, row_no, column_no, value):

        if type(value) == float:
            value = '{0:.2f}'.format(value)

        try:
            return sheet.update_cell(row_no, column_no, value)
        except:
            data = pd.DataFrame(columns=['sheet_id', 'row_no', 'column_no', 'cell', 'value', 'range', 'list_of_list'])
            data.loc[len(data)] = [sheet.id, row_no, column_no, '', value, '', '']
            try:
                data.to_csv(google_sheet.pending_gsheet_path, mode='a', index=False, header=False)
            except Exception as e:
                print(e)
            
    def cell_modified(sheet, cell):
        try:
            return sheet.format(cell, {"backgroundColor": {"red": 25.0, "green": 1.0, "blue": 25.0}})
        except:
            data = pd.DataFrame(columns=['sheet_id', 'row_no', 'column_no', 'cell', 'value', 'range', 'list_of_list'])
            data.loc[len(data)] = [sheet.id, '', '', '', '', cell, '']
            try:
                data.to_csv(google_sheet.pending_gsheet_path, mode='a', index=False, header=False)
            except Exception as e:
                print(e)
            
    def Update_PL_cell(sheet, update='cell', row_no=None, column_no=None, value=None, Range=None, list_of_list=None):
        
        if datetime.datetime.combine(datetime.datetime.now().date(), datetime.time(15,30)) > datetime.datetime.now() > datetime.datetime.combine(datetime.datetime.now().date(), datetime.time(10)):
            if update == 'cell':
                try:
                    return sheet.update_cell(row_no, column_no, value)
                except:
                    pass

            elif update == 'batch':
                try:
                    return sheet.batch_update([{'range': Range, 'values':  list_of_list}])
                except:
                    pass

    def __change_float_value(list_var):
        for idx, value in enumerate(list_var):
            if type(value) == list:
                google_sheet.__change_float_value(value)
            else:
                if type(value) == float:
                    list_var[idx] = '{0:.2f}'.format(value)
                    list_var[idx] = round(value, 2)
                              

    def Update_Batch(sheet, Range, list_of_list):

        google_sheet.__change_float_value(list_of_list)

        try:
            return sheet.batch_update([{'range': Range, 'values':  list_of_list}])
        except:
            data = pd.DataFrame(columns=['sheet_id', 'row_no', 'column_no', 'cell', 'value', 'range', 'list_of_list'])
            data.loc[len(data)] = [sheet.id, '', '', '', '', Range, list_of_list]
            try:
                data.to_csv(google_sheet.pending_gsheet_path, mode='a', index=False, header=False)
            except Exception as e:
                print(e)

    def Update_PNL_On_Sheet(caps_Strategy, pnl_value):
        while True:
            try:
                BT_result = google_sheet().get_sheet(google_sheet.sheet_ids.BT_result_sheet)
                data = google_sheet.get_sheet_df(BT_result)
                break
            except:
                pass

        cs = caps_Strategy.split(' ')
        Strategy = ' '.join(cs[1:-1]) + '-' + cs[-1]

        if cs[0] == 'NF':
            Strategy = cs[0] + '_' + Strategy

        if type(pnl_value) == float:
            pnl_value = '{0:.2f}'.format(pnl_value)

        while True:
            try:
                return google_sheet.Update_cell(BT_result, list(data.Date).index(str(datetime.datetime.now().date())) + 2, list(data.columns).index(Strategy) + 1, pnl_value)
            except gspread.exceptions.APIError:
                sleep(2)