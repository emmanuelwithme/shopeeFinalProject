import flask
from ajax import ajax_bp
import json
from bs4 import BeautifulSoup
import pandas as pd
import requests


app = flask.Flask(__name__)
app.register_blueprint(ajax_bp, url_prefix='/ajax')


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

if __name__ == "__main__":
    app.run(debug=True)
