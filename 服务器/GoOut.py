import requests
import json
import time
import yaml
import yagmail
import re
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
jws_data_path = os.path.join(current_dir, 'cache', 'jws.txt')
config_path = os.path.join(current_dir, 'cache', 'config.yaml')

def Login(headers, username, password):
    login_url = 'https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/username'
    params = {
        'username': username,
        'password': password
    }
    login_req = requests.post(login_url, params=params, headers=headers)
    text = json.loads(login_req.text)
    if text['code'] == 0:
        print(f"{username}账号登陆成功！")
        set_cookie = login_req.headers['Set-Cookie']
        jws = re.search(r'JWSESSION=.*?;', str(set_cookie)).group(0)
        wzxy = re.search(r'WZXYSESSION=.*?;', str(set_cookie)).group(0)
        cookie = f'{jws} {wzxy}'
        return cookie
    else:
        print(f"{username}登陆失败，请检查账号密码！")
        return False


def testLoginStatus(headers, cookie):
    # 用任意需要鉴权的接口即可，这里随便选了一个
    url = "https://student.wozaixiaoyuan.com/heat/getTodayHeatList.json"
    headers['Host'] = "student.wozaixiaoyuan.com"
    headers['Cookie'] = cookie
    res = requests.post(url, headers=headers)
    text = json.loads(res.text)
    if text['code'] == 0:
        return True
    elif text['code'] == -10:
        return False
    else:
        return 0


def GetJWData():
    try:
        with open(jws_data_path, 'r' , encoding='utf-8') as f:
            jws_data = json.loads(f.read())
            print("读取现存jws文件成功！")
            return jws_data
    except FileNotFoundError:
        print("jws文件不存在，正在创建！")
        return {}
    except Exception as e:
        print("未知错误", e)
        exit(0)


def GetConfigs():
    with open(config_path, 'r', encoding='utf-8') as f:
        configs = yaml.safe_load_all(f.read())
    return configs


def ReturnMail(mails):
    mail = yagmail.SMTP(mails['mail_address'],
                        mails['password'], mails['host'])
    return mail


def GetPhoneNumber():
    url = 'https://api.uutool.cn/phone/generate_batch'
    headers = {
        'authority': 'api.uutool.cn',
        'method': 'POST',
        'path': '/phone/generate_batch',
        'scheme': 'https',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'content-length': '281',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://uutool.cn',
        'pragma': 'no-cache',
        'referer': 'https://uutool.cn/',
        'sec-ch-ua': '"Chromium";v="110", "Not A(Brand";v="24", "Microsoft Edge";v="110"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.63'
    }
    data = {'phone_num': '1',
            'area': '',
            'segment': '134,135,136,137,138,139,147,150,151,152,157,158,159,165,172,178,182,183,184,187,188,198,130,131,132,145,155,156,166,171,175,176,185,186,133,149,153,173,177,180,181,189,199'
    }
    req = requests.post(url , data= data, headers=headers)
    text = json.loads(req.text)
    number = text['data']['rows'][0]
    return number


def GetEachJws(config, headers):
    try:
        return jws_data[config['username']]
    except:
        print(config['username'], "尝试登陆！")
        cookie = Login(headers, config['username'], config['password'])
        if cookie is False:
            mail.send(config['receive'], '登陆失败', '登陆失败，请检查账号密码')
            return False
        jws_data[str(config['username'])] = cookie
        return cookie


def GoOut(headers , receive):
    get_one_url = 'https://gw.wozaixiaoyuan.com/out/mobile/out/getOne'
    req = requests.get(get_one_url, headers=headers)
    get_one = json.loads(req.text)
    state = get_one['data']['state']
    number = get_one['data']['number']
    if int(state) == 5:
        phone_number = GetPhoneNumber()
        out_url = 'https://gw.wozaixiaoyuan.com/out/mobile/out/save'
        out_json = {"number":number,"type":"其它","start":f"{time.localtime().tm_hour}:{time.localtime().tm_min}","end":"23:00","emergency":phone_number,"context":"事","outRoute":"事"}
        req = requests.post(out_url, json=out_json, headers=headers)
        if json.loads(req.text)['code'] == 0:
            print("请假成功！")
            mail.send(receive , "请假成功！" , "请假成功！")
            return True
        else:
            print("请假失败！")
            mail.send(receive, "请假失败！", "请假失败！")
            return False


def main():
    for config in configs:
        username = config['username']
        receive = config['receive']
        isOut = config['out']
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; WLZ-AN00 Build/HUAWEIWLZ-AN00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.99 XWEB/4343 MMWEBSDK/20220903 Mobile Safari/537.36 MMWEBID/4162 MicroMessenger/8.0.28.2240(0x28001C35) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 miniProgram/wxce6d08f781975d91'}
        cookie = GetEachJws(config, headers)
        if cookie:
            login_code = testLoginStatus(headers, cookie)
        else:
            continue
        if login_code is False:
            print(config['username'], "jws失效！")
            cookie = Login(headers, config['username'], config['password'])
            if cookie is False:
                continue
            print("jws文件更新成功")
            jws_data[config['username']] = cookie
        headers = {
            'Host': 'gw.wozaixiaoyuan.com',
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/plain, */*',
            'Cookie': cookie,
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
        if isOut:
            GoOut(headers , receive)
        else:
            continue


if __name__ == '__main__':
    configs = GetConfigs()
    mails = next(configs)
    mail = ReturnMail(mails)
    jws_data = GetJWData()
    main()
    with open(jws_data_path, 'w' , encoding='utf-8') as f:
        f.write(str(jws_data).replace("'", '"'))
