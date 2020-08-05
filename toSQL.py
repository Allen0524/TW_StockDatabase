import sqlite3
import os
import datetime
import time
import pandas as pd
from dateutil.rrule import rrule, DAILY, MONTHLY



conn = sqlite3.connect('dataBase.db')

def month_range(start_date, end_date):
    return [dt.date() for dt in rrule(MONTHLY, dtstart=start_date, until=end_date)]

def date_range(start_date, end_date):
    return [dt.date() for dt in rrule(DAILY, dtstart=start_date, until=end_date)]


def update_table(conn, table_name, crawl_function, dates):
    
    df = pd.DataFrame()
    dfs = {}
    
    for d in dates:
        
        print('正在爬取: ', d)
        
        data = crawl_function(d)
        
        if data is None:
            print('失敗，可能是假日')
        else:
            df = df.append(data)
            print(d, '成功')
        
        if data is not None:
            add_to_sql(conn, table_name, df)
            df = pd.DataFrame()
            print(d, '儲存成功')
        
        time.sleep(15)

def add_to_sql(conn, name, df):
    
    exist = table_exist(conn, name)
    ret = pd.read_sql('select * from ' + name, conn, index_col=['stock_id', 'date'])if exist else pd.DataFrame()
    ret = ret.append(df)
    ret.reset_index(inplace=True)
    ret['stock_id'] = ret['stock_id'].astype(str)
    ret['date'] = pd.to_datetime(ret['date'])
    ret = ret.drop_duplicates(['stock_id', 'date'], keep='last')
    ret = ret.sort_values(['stock_id', 'date']).set_index(['stock_id', 'date'])
    
    
    ret.to_csv('backup.csv')
    
    try:
        ret.to_sql(name, conn, if_exists='replace')
        
    except:
        ret = pd.read_csv('backup.csv', parse_dates=['date'], dtype={'stock_id':str})
        ret['stock_id'] = ret['stock_id'].astype(str)
        ret.set_index(['stock_id', 'date'], inplace=True)
        ret.to_sql(name, conn, if_exists='replace')
        print("失敗")


def table_exist(conn, table):
    return list(conn.execute("SELECT count(*) from sqlite_master where type='table' and name='"+table+"'"))[0][0] == 1


