import requests
import pandas as pd
from io import StringIO
import datetime
import sqlite3
from toSQL import date_range, update_table

#爬股價
def crawlPrice(date):
    
    #strftime可以把日期格式轉換成各種字串例如20200621
    datestr = date.strftime('%Y%m%d')
    try:
        response = requests.get("https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=" + datestr + "&type=ALLBUT0999&_=1592808180378")
    except Exception as e:
        print("更新" + datestr + "股票資料時 發生錯誤")
        print(e)
        return None
    
    newlines = []
    lines = response.text.split('\n')
    for line in lines:
        if len(line.split('",')) == 17:
            newlines.append(line)
    
    try:
        df = pd.read_csv(StringIO("\n".join(newlines).replace('=', '')))
    except:
        print("失敗，可能是假日")
        return None
    
    df = df.astype(str)
    df = df.apply(lambda s: s.str.replace(',', ""))
    df['date'] = pd.to_datetime(date)
    df = df.rename(columns={'證券代號':'stock_id'})
    df = df.set_index(['stock_id', 'date'])
    df = df.apply(lambda s:pd.to_numeric(s, errors='coerce'))
    df = df.dropna(axis=1, how='all')
   
    return df



conn = sqlite3.connect('dataBase.db')
#更新股價
fromdate = datetime.date(2020,7,28)
toDate = datetime.date(2020,8,4)
dates = date_range(fromdate, toDate)
update_table(conn, 'price', crawlPrice, dates)