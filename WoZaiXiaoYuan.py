import requests
import json
import yagmail
import yaml
import time
import re
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from base64 import b64encode


def encrypt(t, e):
    t = str(t)
    key = e.encode('utf-8')
    cipher = AES.new(key, AES.MODE_ECB)
    padded_text = pad(t.encode('utf-8'), AES.block_size)
    encrypted_text = cipher.encrypt(padded_text)
    return b64encode(encrypted_text).decode('utf-8')


def Login(headers, username, password):
    headers00 = {
        "accept": "application/json, text/plain, */*",
        "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1 Edg/119.0.0.0"}
    url00 = "https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/getSchoolList"
    response00 = requests.get(url00, headers=headers00)
    school_data = json.loads(response00.text)['data']
    def find_school_id(school_name, data):
        for school in data:
            if school['name'] == school_name:
                return school['id']
        return None
    school_id = find_school_id(school, school_data)
    key = (str(username) + "0000000000000000")[:16]
    encrypted_text = encrypt(password, key)
    login_url = 'https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/username'
    params = {
        "schoolId": school_id,
        "username": username,
        "password": encrypted_text
    }
    login_req = requests.post(login_url, params=params, headers=headers)
    print(login_req.text)
    text = json.loads(login_req.text)
    if text['code'] == 0:
        print(f"{username}账号登陆成功！")
        set_cookie = login_req.headers['Set-Cookie']
        jws = re.search(r'JWSESSION=(.*?);', str(set_cookie)).group(1)
        wzxySession = re.search(r'WZXYSESSION=(.*?);', str(set_cookie)).group(1)
        return jws, wzxySession
    else:
        print(f"{username}登陆失败，请检查账号密码！")
        return False

def testLoginStatus(headers, jws, wzxySession):
    # 用任意需要鉴权的接口即可，这里随便选了一个
    url = "https://gw.wozaixiaoyuan.com/health/mobile/health/getBatch"
    headers['Host'] = "gw.wozaixiaoyuan.com"
    headers['cookie'] = f'JWSESSION={jws}'
    headers['cookie'] = f'JWSESSION={jws}'
    headers['cookie'] = f'WZXYSESSION={wzxySession}'
    res = requests.get(url, headers=headers)
    text = json.loads(res.text)
    if text['code'] == 0:
        return True
    elif text['code'] == 103:
        return False
    else:
        return 0

def GetUnDo(headers, username):
    url = 'https://gw.wozaixiaoyuan.com/health/mobile/health/getBatch'
    res = requests.get(url, headers=headers)
    lists = json.loads(res.text)['data']
    for list in lists['list']:
        if list['state'] == 1 and list['type'] == 0:
            return list['id']
    print(f"{username}未找到未打卡项目！")
    return False


def GetAnswers(headers, username, batch):
    try:
        return users_data[str(username)]
    except Exception as e:
        print("未找到现存答案信息！", e)
    answers = {}
    url = 'https://gw.wozaixiaoyuan.com/health/mobile/health/getForm?batch='+batch
    res = requests.get(url, headers=headers)
    data = json.loads(res.text)
    locationType = data['data']['locationType']
    answers.update({"type": 0, "locationMode": 0, "locationType": locationType})
    print(f"获取{username}的参数成功！")
    return answers


def GetLocation(config_locations):
    location = config_locations['location']
    locations = []
    for _ in location:
        if _ == '省' or _ == '市' or _ == '州' or _ == '区' or _ == '县' or _ == '岛' or _ == '域' or _ == '道' or _ == '路' or _ == '乡' or _ == '镇':
            locations.append(location[:location.index(_) + 1])
            location = location[location.index(_) + 1:]
    locate = locations.copy()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'cache', 'location.json')
    with open(file_path, 'r', encoding='utf-8') as f:
        txt = json.loads(f.read())
    datas = []
    while len(locations) != 1:
        for i in txt:
            if i['label'] == locations[0]:
                datas.append(i['value'])
                locations.pop(0)
                try:
                    txt = i['children']
                except KeyError:
                    break
    location = {"location": f"中国/{locate[0]}/{locate[1]}/{locate[2]}/{locate[3]}/{locate[4]}/156/{datas[-2]}/156{datas[1]}/{datas[-1]}/{config_locations['longitude']}/{config_locations['latitude']}"
                }
    return location


def GetEachJws(config, headers):
    try:
        jws = jws_data[config['username']].split(',')[0]
        wzxySession = jws_data[config['username']].split(',')[1]
        return jws, wzxySession
    except:
        print(config['username'], "尝试登陆！")
        jws, wzxySession = Login(headers, config['username'], config['password'])
        if jws is False:
            mail.send(config['receive'], '登陆失败', '登陆失败，请检查账号密码')
            return False
        jws_data[str(config['username'])] = f"{jws},{wzxySession}"
        return jws, wzxySession


def Punch(headers, batch, answers, receive, username):
    url = 'https://gw.wozaixiaoyuan.com/health/mobile/health/save?batch='+batch
    res = requests.post(url, json=answers, headers=headers)
    txt = json.loads(res.text)
    if txt['code'] == 0:
        print(f"{username}打卡成功！\n")
        mail.send(receive, "打卡成功！", "打卡成功！")
        return True
    else:
        print(f"{username}打卡失败！{str(txt)}\n")
        mail.send(receive, "打卡失败！", str(txt))
        return False


def ReturnMail(mails):
    mail = yagmail.SMTP(mails['mail_address'],
                        mails['password'], mails['host'])
    return mail


def GetConfigs():
    current_path = os.path.abspath(__file__)
    config_path = os.path.join(os.path.dirname(current_path), 'cache', 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        configs = yaml.safe_load_all(f.read())
    return configs



def GetUsers():
    try:
        current_path = os.path.abspath(__file__)
        users_path = os.path.join(os.path.dirname(current_path), 'cache', 'users.txt')
        with open(users_path, 'r', encoding='utf-8') as f:
            users_data = json.loads(f.read().replace("'", '"'))
            print("读取现存users文件成功！")
            return users_data
    except FileNotFoundError:
        print("users文件不存在，正在创建！")
        return {}
    except Exception as e:
        print("未知错误", e)
        exit(0)


def GetEachUser(username, headers, batch, config):
    try:
        return users_data[username]
    except:
        answers= GetAnswers(headers, username, batch)
        location = GetLocation(config['locations'])
        answers.update(location)
        users_data[str(username)] = answers
        return answers


def GetJWData():
    try:
        current_path = os.path.abspath(__file__)
        jws_path = os.path.join(os.path.dirname(current_path), 'cache', 'jws.txt')
        with open(jws_path, 'r', encoding='utf-8') as f:
            jws_data = json.loads(f.read())
            print("读取现存jws文件成功！")
            return jws_data
    except FileNotFoundError:
        print("jws文件不存在，正在创建！")
        return {}
    except Exception as e:
        print("未知错误", e)
        exit(0)



def DelayBackTime(id , headers):
    delay_url = 'https://gw.wozaixiaoyuan.com/out/mobile/out/saveDelay?' + id
    delay_json = {"endDate":f"{time.localtime().tm_hour + 1}:00","delayContent":"事"}
    req = requests.post(delay_url, json=delay_json, headers=headers)
    text = json.loads(req.text)
    if text['code'] == 0:
        print("延期成功！")
        return True
    else:
        print("延期失败！" , text)
        return False



def main():
    for config in configs:
        username = config['username']
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; WLZ-AN00 Build/HUAWEIWLZ-AN00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.99 XWEB/4343 MMWEBSDK/20220903 Mobile Safari/537.36 MMWEBID/4162 MicroMessenger/8.0.28.2240(0x28001C35) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 miniProgram/wxce6d08f781975d91'}
        jws, wzxySession = GetEachJws(config, headers)
        if jws:
            login_code = testLoginStatus(headers, jws, wzxySession)
        else:
            continue
        if login_code is False:
            print(config['username'], "jws失效！")
            jws, wzxySession = Login(headers, config['username'], config['password'])
            if jws is False:
                continue
            print("jws文件更新成功")
            jws_data[config['username']] = f"{jws},{wzxySession}"
        headers = {
            'Host': 'gw.wozaixiaoyuan.com',
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/plain, */*',
            'jwsession': jws,
            "cookie": f'JWSESSION={jws}',
            "cookie": f'JWSESSION={jws}',
            "cookie": f'WZXYSESSION={wzxySession}',
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
        batch = GetUnDo(headers, username)
        if not batch:
            continue
        answers = GetEachUser(username, headers, batch, config)
        Punch(headers, batch, answers, config['receive'], username)


if __name__ == "__main__":
    configs = GetConfigs()
    mails = next(configs)
    school = mails['school']
    mail = ReturnMail(mails)
    jws_data = GetJWData()
    users_data = GetUsers()
    main()
    jws_data_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'cache', 'jws.txt')
    users_data_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'cache', 'users.txt')
    with open(jws_data_path, 'w', encoding='utf-8') as f:
        f.write(str(jws_data).replace("'", '"'))
    with open(users_data_path, 'w', encoding='utf-8') as f:
        f.write(str(users_data).replace("'", '"'))


