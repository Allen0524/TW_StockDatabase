import sqlite3
import requests
from io import StringIO
import pandas as pd
import datetime
from toSQL import update_table, month_range


def crawlMonthReport(date):
    
    #date.year-1911 轉民國
    url = 'https://mops.twse.com.tw/nas/t21/sii/t21sc03_'+str(date.year-1911)+'_'+str(date.month)+'.html'
    r = requests.get(url)
    r.encoding = 'big5'
    dfs = pd.read_html(StringIO(r.text))
    
    #取得column name 
    #取df[6]只是舉例，因為它每個產業都有新的欄位名稱，[6]好像是塑膠產業
    collist = [] 
    for i in dfs[6].columns:
        collist.append(i[1])
        
    newdfs = []

    #在來開始找規律，和剛剛找欄為一樣，這個list的某些地方是存欄位或標題等名稱，因此只要看長度是否大於2就行
    for i in dfs:
        if len(i) > 2:
            newdfs.append(i)

    #把所有list合併成一DataFrame
    df = newdfs[0]
    for i in newdfs[1:]:
        df = pd.concat( [df, i], axis=0 )

    df.columns = collist
    
    #把合計刪掉
    df = df[~(df['公司代號'] == '合計')]
    
    #新增date欄位
    df['date'] = pd.to_datetime(datetime.date(date.year, date.month, 1))
    
    df = df.rename(columns={'公司代號':'stock_id'})
    df = df.set_index(['stock_id', 'date'])
    
    df = df.apply(lambda s:pd.to_numeric(s, errors='coerce'))
    
    #刪掉備註欄位
    df = df.drop(['公司名稱', '備註'], axis=1)
    
    return df



conn = sqlite3.connect('dataBase.db')
#更新月營收
fromdate = datetime.date(2017,1,1)
toDate = datetime.date(2017,1,1)
dates = month_range(fromdate, toDate)
update_table(conn, 'monthRevenue', crawlMonthReport, dates)