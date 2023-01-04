# 蝦皮搶購站

[影片(PPT 介紹及程式Demo)](https://youtu.be/xbPyQ8AdZyQ)

## 功能

 1. 蝦皮限時特賣預先取得未顯示價格
 2. 通用型搶購程式(不只蝦皮可以搶)
 3. 比價功能(爬蟲)
 4. 會員系統

## 連接MySQL資料庫

> 在app.py裡面:
> 
    connection = mysql.connector.connect(
	    host='127.0.0.1', # 主機名稱
	    database='shopeefinalproject', # 資料庫名稱
	    user='root', # 帳號
	    password='root', # 密碼
	    auth_plugin='mysql_native_password')
> 記得執行app.py前:
> 

 1. 先開啟MySQL server
 2. 然後create database 名稱: shopeefinalproject
 3. 然後在該database執行以下SQL創建users table
 

    create  table  IF  NOT  EXISTS users (
        id int  not  null auto_increment,
        name  varchar(20) not  null,
        email varchar(20) not  null,
        password  char(80) not  null,
        primary  key (id)
    );
        
## Procfile

* web gunicorn app:app
* 第一個app為entry point is app.py，第二個app為app.py裡面Flask物件變數名稱為app

## 登記搶購

 - Xpath 可以用chrome右鍵檢查，找到HTML element按右鍵Copy Xpath