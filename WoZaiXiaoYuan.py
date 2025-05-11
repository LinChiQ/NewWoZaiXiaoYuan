import requests
import json
import yagmail
import yaml
import re
import os
import sqlite3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from base64 import b64encode
import urllib.parse


def InitDB():
    isUsers = 0
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    # 判断是否存在users表
    tables = cursor.fetchall()
    for table in tables:
        if table[0] == 'users':
            isUsers += 1
    # 不存在users表
    if isUsers <= 0:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                jws TEXT NOT NULL,
                punchData TEXT NOT NULL
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        return False
    cursor.close()
    conn.close()
    return True


def MsgSend(mails, message_title, message_info ,mail_receiver = False, sct_ftqq = False):
    if mails['mail_address']:
        mail = yagmail.SMTP(mails['mail_address'],
                            mails['password'], mails['host'])
        try:
            mail.send(mail_receiver, message_title, message_info)
        except Exception as e:
            print("推送出错！", str(e))
    if sct_ftqq:
        try:
            requests.get(f'https://sctapi.ftqq.com/{sct_ftqq}.send?{urllib.parse.urlencode({"title":message_title, "desp":message_info})}')
        except Exception as e:
            print("推送出错！", str(e))



# 登陆部分
def encrypt(t, e):
    t = str(t)
    key = e.encode('utf-8')
    cipher = AES.new(key, AES.MODE_ECB)
    padded_text = pad(t.encode('utf-8'), AES.block_size)
    encrypted_text = cipher.encrypt(padded_text)
    return b64encode(encrypted_text).decode('utf-8')


# 获取学校ID
def get_school_id(school_name):
    headers00 = {
    "accept": "application/json, text/plain, */*",
    "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1 Edg/119.0.0.0"}
    url00 = "https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/getSchoolList"
    response00 = requests.get(url00, headers=headers00)
    data = json.loads(response00.text)['data']
    for school in data:
        if school['name'] == school_name:
            return school['id']
    return None


def Login(headers, username, password):
    key = (str(username) + "0000000000000000")[:16]
    encrypted_text = encrypt(password, key)
    login_url = 'https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/username'
    params = {
        "schoolId": school_id,
        "username": username,
        "password": encrypted_text
    }
    login_req = requests.post(login_url, params=params, headers=headers)
    text = json.loads(login_req.text)
    if text['code'] == 0:
        print(f"{username}账号登陆成功！")
        set_cookie = login_req.headers['Set-Cookie']
        jws = re.search(r'JWSESSION=(.*?);', str(set_cookie)).group(1)
        return jws
    else:
        print(f"{username}登陆失败，请检查账号密码！")
        return False


def testLoginStatus(headers, jws):
    # 用任意需要鉴权的接口即可，这里随便选了一个
    url = 'https://gw.wozaixiaoyuan.com/sign/mobile/receive/getMySignLogs'
    params = {
        'page': 1,
        'size': 10
    }
    headers['Host'] = "gw.wozaixiaoyuan.com"
    headers['cookie'] = f'JWSESSION={jws}'
    headers['cookie'] = f'JWSESSION={jws}'
    headers['cookie'] = f'WZXYSESSION={jws}'
    res = requests.get(url, headers=headers, params=params)
    text = json.loads(res.text)
    print(text)
    if text['code'] == 0:
        return True
    elif text['code'] == 103:
        return False
    else:
        return 0


def GetUserJws(username):
    # 从sqlite中拿到用户对应jws
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT jws FROM users WHERE username = ?", (username,))
    # 获取并返回对应jws
    jws = cursor.fetchone()
    cursor.close()
    conn.close()
    if jws:
        return jws[0]
    return False


def updateJWS(username, newJWS):
    # update sqlite jws
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # 更新数据
    cursor.execute('''
        UPDATE users
        SET jws = ?
        WHERE username = ?
    ''', (newJWS, username))
    # 提交更改
    conn.commit()
    if cursor.rowcount == 0:
        # 更新失败
        print("更新失败！")
        return False
    print("更新成功！")
    cursor.close()
    conn.close()
    return True


def InsertOrUpdateUserData(username, jws, punchData):
    # 从sqlite中拿到用户对应jws
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user:
        cursor.execute("UPDATE users SET punchData = ? , jws = ? WHERE username = ?", (json.dumps(punchData), jws, username))
        conn.commit()
        if cursor.rowcount > 0:
            print("用户数据更新成功！")
            cursor.close()
            conn.close()
            return True
        cursor.close()
        conn.close()
        return False
    else:
        cursor.execute('''
            INSERT INTO users (username, jws, punchData) VALUES (?,?,?)
        ''', (username, jws, json.dumps(punchData)))
        conn.commit()
        if cursor.rowcount > 0:
            print("新增用户数据成功！")
            cursor.close()
            conn.close()
            return True
        cursor.close()
        conn.close()
        return False



def GetPunchData(username, location, tencentKey):
    # 从sqlite中拿到用户对应jws
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT punchData FROM users WHERE username = ?", (username,))
    # 尝试从数据库获取现存位置信息
    punchData = cursor.fetchone()
    if punchData:
        return json.loads(punchData[0])
    geocode = requests.get("https://apis.map.qq.com/ws/geocoder/v1", params={"address": location, "key": tencentKey})
    geocode_data = json.loads(geocode.text)
    if geocode_data['status'] == 0:
        reverseGeocode = requests.get("https://apis.map.qq.com/ws/geocoder/v1", params={"location": f"{geocode_data['result']['location']['lat']},{geocode_data['result']['location']['lng']}", "key": tencentKey})
        reverseGeocode_data = json.loads(reverseGeocode.text)
        if reverseGeocode_data['status'] == 0:
            location_data = reverseGeocode_data['result']
            PunchData = {
                "latitude": location_data['location']['lat'],
                "longitude": location_data['location']['lng'],
                "nationcode": "",
                "country": "中国",
                "province": location_data['ad_info']['province'],
                "citycode": "",
                "city": location_data['ad_info']['city'],
                "adcode": location_data['ad_info']['adcode'],
                "district": location_data['ad_info']['district'],
                "towncode": location_data['address_reference']['town']['id'],
                "township": location_data['address_reference']['town']['title'],
                "streetcode": "",
                "street": location_data['address_component']['street']
            }
            return PunchData


# 获取我的日志
def GetMySignLogs(headers):
    url = 'https://gw.wozaixiaoyuan.com/sign/mobile/receive/getMySignLogs'
    params = {
        'page': 1,
        'size': 10
    }
    data = requests.get(url, headers= headers, params=params).json()['data'][0]
    if int(data['signStatus']) != 1:
        print("用户已打过卡！")
        return False, False
    signId, id = data['signId'], data['id']
    return signId, id


def Punch(headers, punchData, username, id, signId, receive=False, sct_ftqq=False):
    headers['Referer'] = 'https://servicewechat.com/wxce6d08f781975d91/203/page-frame.html'
    url = 'https://gw.wozaixiaoyuan.com/sign/mobile/receive/doSignByLocation'
    params = {
        'id': id,
        'schoolId': school_id,
        'signId': signId
    }
    res = requests.post(url, data=json.dumps(punchData), headers=headers, params=params)
    txt = json.loads(res.text)
    if txt['code'] == 0:
        print(f"{username}打卡成功！\n")
        MsgSend(mails, "打卡成功！", f"{username}归寝打卡成功！", receive, sct_ftqq)
        return True
    else:
        print(f"{username}打卡失败！{str(txt)}\n")
        MsgSend(mails, "打卡失败！", f"{username}归寝打卡失败！{str(res.text)}", receive, sct_ftqq)
        return False


def GetConfigs():
    with open(config_path, 'r', encoding='utf-8') as f:
        configs = yaml.safe_load_all(f.read())
    return configs


# 蓝牙签到模块开始 By Mudea661
def upload_blue_data(blue1, blue2, headers, id, signid, mails, config):
    data = {
        "blue1": blue1,
        "blue2": list(blue2.values())
    }
    response = requests.post(
        url=f"https://gw.wozaixiaoyuan.com/dormSign/mobile/receive/doSignByDevice?id={id}&signId={signid}",
        headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        response_data = response.json()
        if response_data.get("code") == 0:
            MsgSend(mails,f"账号- {config['username']} -蓝牙打卡成功！", f"账号- {config['username']} -蓝牙打卡成功！", config['receive'], config['sct_ftqq'])
            return 0
        else:
            MsgSend(mails,f"账号- {config['username']} -蓝牙打卡失败！", f"账号- {config['username']} -蓝牙打卡失败！", config['receive'], config['sct_ftqq'])
            return 1
    else:
        return 1


def doBluePunch(headers, username, config, mails):
    # 获取签到日志
    sign_logs_url = "https://gw.wozaixiaoyuan.com/dormSign/mobile/receive/getMySignLogs"
    sign_logs_params = {
        "page": 1,
        "size": 10
    }
    try:
        response = requests.get(sign_logs_url, headers=headers, params=sign_logs_params)
        data_ids = response.json()
        location_id = data_ids["data"][0]["locationId"]
        sign_id = data_ids["data"][0]["signId"]
        major = data_ids["data"][0]["deviceList"][0]["major"]
        uuid = data_ids["data"][0]["deviceList"][0]["uuid"]
        blue1 = [uuid.replace("-", "") + str(major)]
        blue2 = {"UUID1": uuid}
    except:
        MsgSend(mails,f"账号- {username} -获取签到列表出错！", f"账号- {username} -获取签到列表出错！", config['receive'], config['sct_ftqq'])
        return 0
    return upload_blue_data(blue1, blue2, headers, location_id, sign_id, mails, config)

# 蓝牙模块结束

def main():
    for config in configs:
        global school_id
        username = config['username']
        school_id = get_school_id(school)
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; WLZ-AN00 Build/HUAWEIWLZ-AN00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.99 XWEB/4343 MMWEBSDK/20220903 Mobile Safari/537.36 MMWEBID/4162 MicroMessenger/8.0.28.2240(0x28001C35) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 miniProgram/wxce6d08f781975d91'}
        jws = GetUserJws(username)
        if jws:
            print(username, "尝试使用上次登陆jws。")
            login_code = testLoginStatus(headers, jws)
            if not login_code:
                print(username, "jws失效！尝试重新登录。")
                jws = Login(headers, config['username'], config['password'])
                if not jws:
                    print(username, "尝试登陆失败，请检查帐号密码！")
                    MsgSend(mails, "登陆失败！", "账号或密码错误，请检查！", config['receive'], config['sct_ftqq'])
                    continue
                print(username, "重新登录成功，正在更新对应jws！")
                updateJWS(username, jws)
        else:
            print(username, "未存在JWS，进行首次登陆。")
            jws = Login(headers, config['username'], config['password'])
            if not jws:
                print(username, "尝试登陆失败，请检查帐号密码！")
                MsgSend(mails, "登陆失败！", "账号或密码错误，请检查！", config['receive'], config['sct_ftqq'])
                continue
        headers = {
            'Host': 'gw.wozaixiaoyuan.com',
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/plain, */*',
            'jwsession': jws,
            "cookie": f'JWSESSION={jws}',
            "cookie": f'JWSESSION={jws}',
            "cookie": f'WZXYSESSION={jws}',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; WLZ-AN00 Build/HUAWEIWLZ-AN00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.99 XWEB/4343 MMWEBSDK/20220903 Mobile Safari/537.36 MMWEBID/4162 MicroMessenger/8.0.28.2240(0x28001C35) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 miniProgram/wxce6d08f781975d91',
            'Content-Type': 'application/json;charset=UTF-8',
            'X-Requested-With': 'com.tencent.mm',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://gw.wozaixiaoyuan.com/h5/mobile/health/0.3.7/health',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        if config['dorm_sign']:
            signId, id = GetMySignLogs(headers)
            if not signId:
                continue
            punchData = GetPunchData(username, config['location'], tencentKey)
            Punch(headers, punchData, username, id, signId, config['receive'], config['sct_ftqq'])
            InsertOrUpdateUserData(username, jws, punchData)
        if config['blue_sign']:
            # 蓝牙打卡
            doBluePunch(headers, username, config, mails)


if __name__ == "__main__":
    current_path = os.path.abspath(__file__)
    config_path = os.path.join(os.path.dirname(current_path), 'cache', 'config.yaml')
    db_path = os.path.join(os.path.dirname(current_path), 'cache', 'userdata.db')
    configs = GetConfigs()
    mails = next(configs)
    school = mails['school']
    tencentKey = mails['tencent_map']
    InitDB()
    main()



