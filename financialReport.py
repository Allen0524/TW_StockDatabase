import requests
from io import StringIO
import pandas as pd
import datetime
import time
import os
import re
import sqlite3
from monthRevenue import crawlMonthReport
from toSQL import add_to_sql

def crawlFinancialStatement(year, season):

    #所有公司清單
    allStockId = crawlMonthReport(datetime.date(year,season,1)).index.levels[0]
    
    allBalSheet = pd.DataFrame()
    allIncomSheet = pd.DataFrame()
    allCashSheet = pd.DataFrame()
    #650
    for stockId in allStockId[:10]:
        #if stockId == '1203':
            #break
        
        balSheet = pd.DataFrame()
        incomSheet = pd.DataFrame()
        cashSheet = pd.DataFrame()
        
        #有些是個別財報A或合併財報C，ETF沒有財報
        try:
            res = requests.get("https://mops.twse.com.tw/server-java/t164sb01?step=1&CO_ID="+stockId+"&SYEAR="+str(year)+"&SSEASON="+str(season)+"&REPORT_ID=C")
            if len(res.text) < 100:
                res = requests.get("https://mops.twse.com.tw/server-java/t164sb01?step=1&CO_ID="+stockId+"&SYEAR="+str(year)+"&SSEASON="+str(season)+"&REPORT_ID=A")
                res.encoding = 'big5'
                dfs = pd.read_html(StringIO(res.text))
            else:
                res.encoding = 'big5'
                dfs = pd.read_html(StringIO(res.text))
        except:
            continue

        
        print(stockId)
        #各公司的三張表
        
        folderpath = os.path.join('三大財務報表', str(year)+str(season), stockId)
        if not os.path.isdir(folderpath):
            os.makedirs(folderpath)
        
        #資產負債表  
        balSheet = pd.concat([balSheet, threeSheet(dfs, 0, stockId, year, season)])    
        fileName = stockId+'_bal.csv'
        path = os.path.join(folderpath, fileName)
        balSheet.to_csv(path, index=1)
        
        #損益表
        incomSheet = pd.concat([incomSheet, threeSheet(dfs, 1, stockId, year, season)])
        fileName = stockId+'_incom.csv'
        path = os.path.join(folderpath, fileName)
            
        incomSheet.to_csv(path, index=1)
        
        #現金流量表
        cashSheet = pd.concat([cashSheet, threeSheet(dfs, 2, stockId, year, season)])
        fileName = stockId+'_cash.csv'
        path = os.path.join(folderpath, fileName)

        cashSheet.to_csv(path, index=1)
        
        print(stockId,' 完成')
        time.sleep(10)
        
        allBalSheet = pd.concat([allBalSheet, pd.read_csv(os.path.join(folderpath, stockId+'_bal.csv'))])
        allIncomSheet = pd.concat([allIncomSheet, pd.read_csv(os.path.join(folderpath, stockId+'_incom.csv'))])
        allCashSheet = pd.concat([allCashSheet, pd.read_csv(os.path.join(folderpath, stockId+'_cash.csv'))])
        

    data = []
    data.append(allBalSheet.set_index(['stock_id', 'date']))
    data.append(allIncomSheet.set_index(['stock_id', 'date']))
    data.append(allCashSheet.set_index(['stock_id', 'date']))
    return data


def update_financialStatement(conn, crawlfun, year, season):
    
    #拿到長度為3的list，分別為: 資產負債、損益及現金流量表
    data = crawlfun(year, season)
    
    if data is not None:
        
        for i in range(3):
            #資產負債表
            if i == 0:
                add_to_sql(conn, 'balanceSheet', data[i])
            #損益表
            elif i == 1:
                add_to_sql(conn, 'incomeStatement', data[i])
            #現金流量表
            else:
                add_to_sql(conn, 'cashFlowsSheet', data[i])
            
    print(year,'第',season, '季', ' 更新完成')

def threeSheet(dfs, table, stockId, year, season):
    
    collist = []
    #取得column name
    for i in dfs[table].columns:
        collist.append(i[1])
            
    tempsheet = dfs[table]
    tempsheet.columns = collist
        
    #年度
    tit = collist[2]
    tempsheet = tempsheet[['會計項目Accounting Title', tit]]
        
    #刪除大部分英文
    jj = []
    for i in tempsheet['會計項目Accounting Title']:
        s = re.sub('[a-zA-Z]', '', i)
        s = s.replace(' ', '')
        s = s.replace(u'\u3000', '')
        s = s.replace('()', '')
        s = s.replace('-', '')
        s = s.replace(',', '')
        s = s.replace("'", '')
        jj.append(s)
        
    #行列轉換
    sheet = pd.DataFrame(columns = jj)
    sheet.loc[0] = tempsheet[tit].tolist()
    
    #因為各公司資產負債表均有些微不同，為了方便我們只看以下欄位，可依喜好更改
    if table == 0:
        try:
            sheet = sheet[['現金及約當現金', '資產總計', '負債總計', '普通股股本', '股本合計', '歸屬於母公司業主之權益合計', '權益總計']]
        except:
            try:
                sheet = sheet[['現金及約當現金', '資產總計', '負債總計', '普通股股本', '股本合計', '權益總計']]
            except KeyError as e:
                print(stockId, e)
                sheet = sheet[['現金及約當現金', '資產總計', '負債總計', '普通股股本', '股本合計', '權益總額']]
                #sheet2 = sheet.copy()
                #sheet2 = sheet2.rename(columns={'權益總額':'權益總計'})
                #sheet2['權益總計'] = sheet.loc[:,'權益總額']
                
        
    #新增股票代號及日期欄位
    sheet['stock_id'] = stockId
    if season == 1:
        sheet['date'] = datetime.date(year, 1, 1)
    elif season == 2:
        sheet['date'] = datetime.date(year, 4, 1)
    elif season == 3:
        sheet['date'] = datetime.date(year, 7, 1)
    else:
        sheet['date'] = datetime.date(year, 10, 1)
            
    sheet = sheet.set_index(['stock_id', 'date'])
    
    #sheet = sheet.apply(lambda s:pd.to_numeric(s, errors='coerce'))
    sheet = sheet.apply(lambda s: repl(s))
    sheet = sheet.apply(lambda s: toint(s))
    
    return sheet


def repl(s):
    try:
        t = str(s.values[0])
        s = s.replace(s.values[0], t).astype("string")
    except:
        s.values[0] = str(s.values[0])
        
    if s.values[0].find('(') != -1:
        s.values[0] = s.values[0].replace('(', '-')
        s.values[0] = s.values[0].replace(')', '')
    else:
        return s
    return s

def toint(s):
    try:
        s.values[0] = s.values[0].replace(',', '')
        s.values[0] = int(s.values[0])
    except:
        return s
    return s


conn = sqlite3.connect('dataBase.db')
#更新三大財務報表
#(conn, function, 年, 季)
update_financialStatement(conn, crawlFinancialStatement, 2019, 4)