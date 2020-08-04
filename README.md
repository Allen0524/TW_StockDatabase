# TW_StockDatabased

建立台灣上市公司股票的資料庫，其中包含:
* 月營收資料
* 股價資訊
* 三大財務報表(簡化版)

## 資料來源
* [月營收資料](https://mops.twse.com.tw/nas/t21/sii/t21sc03_109_1_0.html)
* [股價](https://www.twse.com.tw/zh/page/trading/exchange/MI_INDEX.html)
* [三大財務報表](https://mops.twse.com.tw/server-java/t164sb01?step=1&CO_ID=2330&SYEAR=2019&SSEASON=1&REPORT_ID=C)

## 環境需求
* python 3.6
* DB Browser for SQLite

## 檔案說明
#### 1. month_revenue.ipynb 
>此檔案為月營收爬蟲
#### 2. price.ipynb 
>此檔案為股價資訊爬蟲
#### 3. financialReport.ipynb 
>此檔案為三大財務報表爬蟲



