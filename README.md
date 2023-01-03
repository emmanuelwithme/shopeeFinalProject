# 蝦皮搶購站

## 功能
1. 蝦皮限時特賣預先取得未顯示價格
2. 通用型搶購程式(不只蝦皮可以搶)
3. 比價功能(爬蟲)
4. 會員系統


## Procfile
* web gunicorn app:app
* 第一個app為entry point is app.py，第二個app為app.py裡面Flask物件變數名稱為app