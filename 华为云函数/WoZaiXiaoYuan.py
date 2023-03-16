import requests
import json
import yagmail
import yaml
import time


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
        jws = login_req.headers['JWSESSION']
        return jws
    else:
        print(f"{username}登陆失败，请检查账号密码！")
        return False


def testLoginStatus(headers, jws):
    # 用任意需要鉴权的接口即可，这里随便选了一个
    url = "https://student.wozaixiaoyuan.com/heat/getTodayHeatList.json"
    headers['Host'] = "student.wozaixiaoyuan.com"
    headers['JWSESSION'] = jws
    res = requests.post(url, headers=headers)
    text = json.loads(res.text)
    if text['code'] == 0:
        return True
    elif text['code'] == -10:
        return False
    else:
        return 0


def GetUnDo(headers, username):
    url = 'https://gw.wozaixiaoyuan.com/health/mobile/health/getBatch'
    res = requests.get(url, headers=headers)
    lists = json.loads(res.text)['data']
    for list in lists['list']:
        if list['state'] == 1 and list['state'] == 0:
            return list['id']
    print(f"{username}未找到未打卡项目！")
    return False


def GetAnswers(headers, username, batch):
    start = 1
    answers = {}
    url = 'https://gw.wozaixiaoyuan.com/health/mobile/health/getForm?batch='+batch
    res = requests.get(url, headers=headers)
    data = json.loads(res.text)
    locationType = data['data']['locationType']
    options = data['data']['options']
    fields = data['data']['fields']
    for field in fields:
        optionId = field['optionId']
        if optionId in options and field['field'] == f't{start}' and field['required'] is True:
            for i in options[optionId]:
                if i['type'] == 0:
                    answers[field['field']] = i['value']
            start += 1
    answers.update({"type": 0, "locationMode": 0})
    print(f"获取{username}的参数成功！")
    return answers, locationType


def GetLocation(config_locations, locationType):
    location = config_locations['location']
    locations = []
    for _ in location:
        if _ == '省' or _ == '市' or _ == '州' or _ == '区' or _ == '县' or _ == '岛' or _ == '域' or _ == '道' or _ == '路' or _ == '乡' or _ == '镇':
            locations.append(location[:location.index(_) + 1])
            location = location[location.index(_) + 1:]
    locate = locations.copy()
    with open('code/cache/location.json', 'r', encoding='utf-8') as f:
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
    location = {"location": f"中国/{locate[0]}/{locate[1]}/{locate[2]}/{locate[3]}/{locate[4]}/156/{datas[-2]}/156{datas[1]}/{datas[-1]}/{config_locations['latitude']}/{config_locations['longitude']}",
                "locationType": locationType
                }
    return location



def Punch(headers, batch, answers, location, receive, username):
    url = 'https://gw.wozaixiaoyuan.com/health/mobile/health/save?batch='+batch
    data = answers.copy()
    data.update(location)
    res = requests.post(url, json=data, headers=headers)
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


def GetEachUser(username, headers, batch, config):
    answers, locationType = GetAnswers(headers, username, batch)
    location = GetLocation(config['locations'], locationType, username)
    return location, answers


def GetConfigs():
    with open('code/cache/config.yaml', 'r', encoding='utf-8') as f:
        configs = yaml.safe_load_all(f.read())
    return configs


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


def BackToSchool(headers_one , jws):
    get_one_url = 'https://gw.wozaixiaoyuan.com/out/mobile/out/getOne'
    req = requests.get(get_one_url, headers=headers_one)
    get_one = json.loads(req.text)
    id = get_one['data']['id']
    date = get_one['data']['end'].split(' ')[0].split('-')
    state = int(get_one['data']['state'])
    if time.localtime().tm_mday != int(date[-1]) or time.localtime().tm_mon != int(date[-2]) or time.localtime().tm_year!= int(date[0]):
        print("已超过一天逾期！")
        return False
    if state == 4:
        if not DelayBackTime(id , headers_one):
            return False
    if state == 5:
        print("已手动返校！")
        return True
    req = requests.get(get_one_url, headers=headers_one)
    get_second = json.loads(req.text)
    state = get_second['data']['state']
    id = get_second['data']['id']
    headers_two = {
        'Host': 'gw.wozaixiaoyuan.com',
        'accept': 'application/json, text/plain, */*',
        'jwsession': jws,
        'user-agent': 'Mozilla/5.0 (Linux; Android 8.1.0; OPPO R11st Build/OPM1.171019.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.99 XWEB/4425 MMWEBSDK/20230202 Mobile Safari/537.36 MMWEBID/4162 MicroMessenger/8.0.33.2320(0x28002137) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 miniProgram/wxce6d08f781975d91',
        'content-type': 'application/json;charset=UTF-8',
        'x-requested-with': 'com.tencent.mm',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': f'https://gw.wozaixiaoyuan.com/h5/mobile/out/index/out/back?id={id}',
        'accept-encoding': 'gzip, deflate',
        'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'cookie': f'JWSESSION={jws}',
        'cookie': f'JWSESSION={jws}'
    }
    if state == 2:
        back_url = 'https://gw.wozaixiaoyuan.com/out/mobile/out/back?id=' + id
        req = requests.get(back_url, headers=headers_two)
        text = json.loads(req.text)
        if text['code'] == 0:
            print("成功返校！")
            return True
        else:
            print("返校失败！", text)
            return False


def main():
    for config in configs:
        username = config['username']
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; WLZ-AN00 Build/HUAWEIWLZ-AN00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.99 XWEB/4343 MMWEBSDK/20220903 Mobile Safari/537.36 MMWEBID/4162 MicroMessenger/8.0.28.2240(0x28001C35) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 miniProgram/wxce6d08f781975d91'}
        jws = Login(headers , username , config['password'])
        if jws:
            login_code = testLoginStatus(headers, jws)
        else:
            continue
        if login_code:
            print(f"{username}登陆有效！")
        else:
            print(f"{username}登陆无效！")
            continue
        headers = {
            'Host': 'gw.wozaixiaoyuan.com',
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/plain, */*',
            'JWSESSION': jws,
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
        if config['back']:
            if BackToSchool(headers , jws):
                print(username , "返校成功！")
                mail.send(config['receive'] , '返校成功！' , '返校成功！')
            else:
                mail.send(config['receive'] , '返校失败！' , '返校失败！请查看！')
        batch = GetUnDo(headers, username)
        if not batch:
            continue
        location, answers = GetEachUser(username, headers, batch, config)
        Punch(headers, batch, answers, location, config['receive'], username)


def Start():
    global configs , mail
    configs = GetConfigs()
    mails = next(configs)
    mail = ReturnMail(mails)
    main()
