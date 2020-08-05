import requests
from io import StringIO
import pandas as pd
import sqlite3
import os
import time
from toSQL import add_to_sql, table_exist


def crawlDividend(year):
    
    form_data = {
        'encodeURIComponent':1,
        'step':1,
        'firstin':1,
        'off':1,
        'co_id':2880,
        'year':year,
        'TYPEK':"all"
    }
    
    res = requests.post("https://mops.twse.com.tw/mops/web/t108sb27", data=form_data)
    df = pd.read_html(StringIO(res.text))
    #第九個才是
    ndf = df[9]
    
    collist = []
    for i in ndf.columns:
        collist.append(i[1])
    ndf.columns = collist
    
    #刪除錯誤列
    ndf = ndf[~(ndf['公司名稱']=='公司名稱')]
    
    ndf = ndf.rename(columns={'公司代號':'stock_id', '權利分派基準日':'date'})
    #ndf['date'] = ndf['date'].apply(modifyDate)  
    sdate = str(year+1911)+'01'+'01'
    ndf['date'] = sdate
    ndf['date'] = pd.to_datetime(ndf['date'], format="%Y%m%d")
    ndf.set_index(['stock_id', 'date'], inplace=True)
    
    return ndf


def update_dividend(conn, table_name, crawl_function, year):
    
    df = pd.DataFrame()
    dfs = {}
    print('正在爬取: ', year, "年度")
        
    data = crawl_function(year)
        
    if data is None:
        print('失敗，可能是假日')
    else:
        df = df.append(data)
        print(year, '年度成功')
        
    if data is not None:
        add_to_sql(conn, table_name, df)
        df = pd.DataFrame()
        print(year, '年度儲存成功')
        
    time.sleep(15)
    


conn = sqlite3.connect('dataBase.db')
#更新歷年股利
update_dividend(conn, 'dividend', crawlDividend, 108)