import flask
from ajax import ajax_bp
import json
from bs4 import BeautifulSoup
import pandas as pd
import requests
import mysql.connector
from mysql.connector import Error
# hash密碼
import bcrypt


app = flask.Flask(__name__)
app.register_blueprint(ajax_bp, url_prefix='/ajax')

# 連接 MySQL/MariaDB 資料庫
connection = mysql.connector.connect(
    host='127.0.0.1',          # 主機名稱
    database='shopeefinalproject', # 資料庫名稱
    user='root',        # 帳號
    password='root',	# 密碼
	auth_plugin='mysql_native_password')  

@app.route("/")
def hello():
    return flask.render_template("home.html")

@app.route("/shopee_flash_sale")
def shopee_flash_sale():
    return flask.render_template("shopee_flash_sale.html")

@app.route("/itemBuyRegister/<shopid>/<itemid>",methods=['GET'])
def itemBuyRegister(shopid,itemid):
    return flask.render_template("itemBuyRegister.html",shopid=shopid,itemid=itemid)

@app.route('/compare_price',methods=['POST','GET'])
def getcompare_price():
	#偽裝header?
	headers = {'User-Agent': 'User-Agent:Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}
	if flask.request.method =='POST':
		if flask.request.values['send']=='送出':

			#key--想搜尋的關鍵字
			key=flask.request.form.get("sendkey_word")#想搜尋的商品
			sort=flask.request.form.get("sort_by")#排序(推薦/高低/低高)
			if sort !="":
				sort="sort="+sort+"&"

			high=flask.request.form.get("high")#價格區間
			low=flask.request.form.get("low")#價格區間

			if high=="" and low=="":
				pricerange=""
			elif high>low:
				pricerange="price="+low+"-"+high+"&"
			else:
				pricerange="price="+high+"-"+low+"&"

			#https://biggo.com.tw/s/  %E6%9A%96%E7%88%90%22  /?  sort=lp&  view=list
			print("key=", key)

			#GET資料
			url = "https://biggo.com.tw/s/"+key+"/?"+pricerange+sort+"view=list"
			print(url)
			response = requests.get(url,headers=headers)
			soup = BeautifulSoup(response.text, "html.parser")
			#將網頁資料以html.parser

			#篩選資料
			a_tags = soup.select('div.list-product-name.line-clamp-2 a')
			b_tags = soup.select('span.price')

			#set var
			temp=[] #暫存結果
			i=0 #計數 #索引

			#存成Dataframe
			df = pd.DataFrame()
			for t in a_tags:
				temp=t.text.split("\n")#分離每一筆資料
				df.at[i, "product"] = temp[1].strip()#刪除空格/取得資料/放入df
				i=i+1

			i=0
			for h in b_tags:
				temp=h.text.split("\n")
				if(len(temp)>1):
					df.at[i, "price"] = temp[1].strip().replace("$", " ")  #$符號會讓排版怪怪的 #取代
					i=i+1

			#url在a的標籤中 #使用soup.find_all('a') => print get
			i=0
			for link in soup.find_all('a'):
				if 'http' in str(link.get('data-href')):
					df.at[i, "url"] = link.get('data-href').strip()
					i=i+1


			#src=圖片
			i=0
			for link in soup.find_all('img'):
				if 'x16' in str(link.get('src')) or 'ap-south' in str(link.get('src')):
					i=i
				elif 'http' in str(link.get('src')) or 'shopee' in str(link.get('src')) or 'buy123' in str(link.get('src')) or 'img' in str(link.get('src')):
					df.at[i, "src"] = link.get('src').strip()
					#print(link.get('src').strip())
					i=i+1
			
			#df to json
			df_new = df.to_json(orient='records')
			df_new = json.loads(df_new)
			json.dumps(df_new, indent=4)

			if sort=="sort=lp&":
				sort="價格低到高"
			elif sort=="sort=hp&":
				sort="價格高到低"
			else:
				sort="推薦排序"

		return flask.render_template("show_compare_price.html",data=df_new,sort=sort,key=key,high=high,low=low)
	return flask.render_template("compare_price.html")

# 註冊頁面
@app.route('/register', methods=["GET", "POST"])
def register():
    if flask.request.method == 'GET':
        return flask.render_template("register.html")
    
    else:
        name = flask.request.form['name']
        email = flask.request.form['email']
        password = flask.request.form['password'].encode('utf-8')
        hash_password = bcrypt.hashpw(password, bcrypt.gensalt())
        
        cursor = connection.cursor()
        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s,%s,%s)",
            (name, email, hash_password))
        #sql = "INSERT INTO users (name, email, password) VALUES ({}, {}, {});"
        #new_data = (name, email, hash_password)
        #print(new_data)
        
        
        #cursor.execute(sql, new_data)
        connection.commit()
        flask.session['name'] = flask.request.form['name']
        flask.session['email'] = flask.request.form['email']

        return flask.redirect(flask.url_for('hello'))
        


# 登入頁面

@app.route('/login', methods=["GET", "POST"])
def login():
    if flask.request.method == 'POST':
        email = flask.request.form['email']
        
        password = flask.request.form['password'].encode('utf-8')

        cursor = connection.cursor(buffered=True)
        #cursor2 = mysql.connector.connect(buffered=True)

        cursor.execute("SELECT name, email, password FROM users;")

        # 列出查詢的資料
        #for ( email, password) in cursor:
            #print("email: %s, Password:%s" % (email,password))
        cursor.execute("SELECT * FROM users WHERE email=%s", [email])
        user = cursor.fetchone()
        print(user[3].encode('utf-8'))
        
        cursor.close()
        if user == None:
            return "沒有這個帳號"
        if len(user) != 0:
            if bcrypt.hashpw(password, user[3].encode('utf-8'))  == user[3].encode('utf-8') :
                flask.session['name'] = user[1]
                flask.session['email'] = user[2]
                return flask.render_template("home.html")
            else:
                return "您的密碼錯誤"
    else:
        return flask.render_template("login.html")
        


# 登出

@app.route('/logout')
def logout():
    flask.session.clear()
    return flask.render_template("home.html")

if __name__ == "__main__":
	app.secret_key = "This is a secret_key"
	app.run(debug=True)
