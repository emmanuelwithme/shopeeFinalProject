import flask
import requests
import json
import math
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

ajax_bp = flask.Blueprint('ajax', __name__)


@ajax_bp.route('/get_promotionid', methods=["GET"])
def ajax_get_promotionid():
    # input none
    # output filtered_sessions_list( promotionid in it)
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }
    filtered_sessions_list = {}
    res = requests.get(
        "https://shopee.tw/api/v4/flash_sale/get_all_sessions", headers=headers)
    if res.json()['error'] == 0:
        sessions_list = res.json()['data']['sessions']
        filtered_sessions_list = {'sessions': []}
        for i in sessions_list:
            name = i['name']
            promotionid = i['promotionid']
            is_ongoing = i['is_ongoing']
            start_time = i['start_time']
            end_time = i['end_time']
            # Only want to keep "catid", "catname" fields.
            filtered_categories = [
                {'catid': cat['catid'], 'catname': cat['catname']} for cat in i['categories']]

            # Generate a sum up output.
            each_output = {'name': name, 'promotionid': promotionid, 'is_ongoing': is_ongoing,
                           'start_time': start_time, 'end_time': end_time, 'categories': filtered_categories}
            # append to filtered_sessions_list['sessions']
            filtered_sessions_list['sessions'].append(each_output)

            # start_datetime = datetime.datetime.fromtimestamp(start_time)
            # end_datetime = datetime.datetime.fromtimestamp(end_time)

            # len(sessions_list)代表限時特賣幾個時段 00:00 10:00 15:00 20:00 明日00:00 ->為5個時段
    else:
        print("https://shopee.tw/api/v4/flash_sale/get_all_sessions  request error!")
        # return error??
    res.close()

    json_string = json.dumps(filtered_sessions_list,
                             ensure_ascii=False).encode('utf8')
    json_object = json.loads(json_string.decode())
    return json_object


@ajax_bp.route('/get_all_items_detail', methods=["POST"])
def get_all_items_detail():
    promotionid = flask.request.form.get('promotionid')
    categoryid = flask.request.form.get('categoryid')

    promotionid = int(promotionid)
    categoryid = int(categoryid)
    

    print(f"promotionid={promotionid}, type={type(promotionid)}")
    print(f"categoryid={categoryid}, type={type(categoryid)}")

    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }

    item_brief_list = []
    itemids = []
    # res = requests.get("https://shopee.tw/api/v4/flash_sale/get_all_itemids?need_personalize=true&order_mode=1&promotionid=125132381343745&sort_soldout=true", headers=headers)
    res = requests.get(
        f"https://shopee.tw/api/v4/flash_sale/get_all_itemids?promotionid={promotionid}", headers=headers)
    # print(res.json())
    if res.json()['error'] == 0:
        promotionid = res.json()['data']['promotionid']
        item_brief_list = res.json()['data']['item_brief_list']
        # print(item_brief_list)

        # 取得符合categoryid的itemids陣列
        itemids = [i['itemid'] for i in item_brief_list if categoryid ==
                   0 or i['catid'] == categoryid]

        # 取得cookies, csrftoken
        options = webdriver.chrome.options.Options()
        options.add_argument("--disable-notifications")
        # 結束不會關閉瀏覽器
        # options.add_experimental_option("detach", True)
        # 全螢幕
        # options.add_argument("--start-maximized")

        service = Service('chromedriver_win32\chromedriver.exe')
        # Start a web browser
        driver = webdriver.Chrome(service=service, options=options)

        # Load the webpage
        driver.get('https://shopee.tw/flash_sale')

        raw_cookies = driver.get_cookies()
        # raw_cookies

        driver.close()

        arr = []
        csrftoken = ""
        for element in raw_cookies:
            if element.get('name') == 'csrftoken':
                csrftoken = element.get('value')
            arr.append('{}={}'.format(
                element.get('name'), element.get('value')))
        cookies = ';'.join(arr)
        print('cookies: ', cookies)
        print('csrftoken: ', csrftoken)

        # 取得
        headers = {
            "accept": "application/json",
            "x-api-source": "rweb",
            "x-kl-ajax-request": "Ajax_Request",
            "x-requested-with": "XMLHttpRequest",

            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "x-csrftoken": csrftoken,
            "referer": "https://shopee.tw/flash_sale",
            "content-type": "application/json",
            'cookie': cookies,
        }
        # print(f'''{{"promotionid":122990947930113,"categoryid":0,"itemids":{itemids},"limit":16,"with_dp_items":true}}''')
        items_list = []
        # math.ceil(len(itemids)/50) 為request的次數
        for i in range(math.ceil(len(itemids)/50)):
            item_start_index = 50*i
            item_end_index = len(itemids) if i == math.ceil(
                len(itemids)/50)-1 else 50*(i+1)
            # itemids list最多50個elements，"limit": 記得要改成itemids的elements數量。記得要分次request。
            # "promotionid":125132368760833是代表不同時間的限時搶購活動，如0:00-10:00為一個搶購時段，promotionid相同
            # "categoryid":0代表現正瘋搶

            payload = json.loads(
                f'''{{"promotionid":{promotionid}, "categoryid":{categoryid}, "itemids":{itemids[item_start_index:item_end_index]},"limit":{len(itemids[item_start_index:item_end_index])}, "with_dp_items":true}}''')
            res = requests.post(
                "https://shopee.tw/api/v4/flash_sale/flash_sale_batch_get_items", json=payload, headers=headers)
            # 將res.json()['data']['items']加到尾巴
            items_list.extend(res.json()['data']['items'])
            sleep_seconds = random.uniform(0.1, 0.3)
            time.sleep(sleep_seconds)
            res.close()
    else:
        print("https://shopee.tw/api/v4/flash_sale/get_all_itemids?promotionid=  \nrequest error! promotionid可能過期了，請重整網頁")
    res.close()

    json_string = json.dumps(
        items_list, ensure_ascii=False).encode('utf8')
    json_object = json.loads(json_string.decode())
    print(f"items_list={items_list}")
    return json_object

@ajax_bp.route('/submit_item_buy_register_form', methods=["POST"])
def submit_item_buy_register_form():
    # 登入商城網站
    account = flask.request.form.get('account')
    password = flask.request.form.get('password')
    loginURL = flask.request.form.get('loginURL')
    loginAccountLocation = flask.request.form.get('loginAccountLocation')
    loginPasswordLocation = flask.request.form.get('loginPasswordLocation')
    flexSwitchCheckChecked = flask.request.form.get('flexSwitchCheckChecked')
    loginSubmitLocation = flask.request.form.get('loginSubmitLocation')

    # 商品
    itemURL = flask.request.form.get('itemURL')

    # 搶購步驟
    buy_time_str = flask.request.form.get('buyTime')
    buyTime = datetime.datetime.strptime(buy_time_str, '%Y-%m-%dT%H:%M')
    itemPriceLocation = flask.request.form.get('itemPriceLocation')
    inputValuesList = json.loads(flask.request.form.get('inputValues'))

    

    print(f"account={account} type={type(account)}")
    print(f"password={password} type={type(password)}")
    print(f"loginURL={loginURL} type={type(loginURL)}")
    print(f"loginAccountLocation={loginAccountLocation} type={type(loginAccountLocation)}")
    print(f"loginPasswordLocation={loginPasswordLocation} type={type(loginPasswordLocation)}")
    print(f"flexSwitchCheckChecked={flexSwitchCheckChecked} type={type(flexSwitchCheckChecked)}")
    print(f"loginSubmitLocation={loginSubmitLocation} type={type(loginSubmitLocation)}")

    print(f"itemURL={itemURL} type={type(itemURL)}")

    print(f"buyTime={buyTime} type={type(buyTime)}")
    print(f"itemPriceLocation={itemPriceLocation} type={type(itemPriceLocation)}")
    print(f"inputValuesList={inputValuesList} type={type(inputValuesList)}")


    # 開始用selenium登入
    options = webdriver.chrome.options.Options()
    options.add_argument("--disable-notifications")
    # 結束不會關閉瀏覽器
    options.add_experimental_option("detach", True)
    # 全螢幕
    options.add_argument("--start-maximized")

    service = Service('chromedriver_win32\chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=options)

    # 登入
    driver.get(loginURL)
    driver.find_element(By.XPATH, loginAccountLocation).send_keys(account)
    driver.find_element(By.XPATH,loginPasswordLocation).send_keys(password)
    if flexSwitchCheckChecked == 'on':
        driver.find_element(By.XPATH,loginPasswordLocation).send_keys(Keys.ENTER)
    elif flexSwitchCheckChecked == 'off':
        driver.find_element(By.XPATH,loginSubmitLocation).click()
    time.sleep(5)

    # 開始買
    current_time = datetime.datetime.now()
    goal_time = buyTime
    time_diff = goal_time - current_time

    # 以後可以改良成時間很靠近才取得最後價格
    driver.get(itemURL)
    # last_price = WebDriverWait(driver, 10,0.1).until(EC.presence_of_element_located((By.XPATH,itemPriceLocation)))
    
    while True:
        current_time = datetime.datetime.now()
        time_diff = goal_time - current_time
        print("current time: ",current_time)
        print("goal time: ",goal_time)
        print("time_diff: ",time_diff.seconds)
        # if time_diff.microseconds < 0:
        #     print("break time: ",current_time)
        #     break

        # if time_diff.seconds < -10:
        #     break
        # if time_diff.seconds < 20:
        if True:
            driver.get(itemURL)
            # current_price = WebDriverWait(driver, 10,0.1).until(EC.presence_of_element_located((By.XPATH,itemPriceLocation)))
            
            # if current_price.text != last_price.text: 和  # if True: 只能選一個執行
            # if current_price.text == last_price.text:
            if True:
                try:
                    for i in inputValuesList:
                        # 如果是滑鼠點擊事件，就點擊
                        if i['isClick']:
                            WebDriverWait(driver, 10,0.1).until(EC.element_to_be_clickable((By.XPATH,i['elementPosition']))).click()
                        # 不然就是鍵盤輸入事件，就輸入
                        else:
                            driver.find_element(By.XPATH,i['elementPosition']).send_keys(i['key'])
                except:
                    time.sleep(0.05)
                    continue
                break
            else:
                time.sleep(0.05)
        else:
            time.sleep(10)

    return {'massage':'success'}
