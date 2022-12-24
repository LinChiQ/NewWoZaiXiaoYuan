import requests
import json
import yagmail
import yaml


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
        if list['state'] == 1 and list['type'] == 0:
            return list['id']
    print(f"{username}未找到未打卡项目！")
    return False


def GetAnswers(headers, username, batch):
    try:
        return users_data[str(username)][1], 0
    except Exception as e:
        print("未找到现存答案信息！", e)
    start = 1
    answers = {}
    url = 'https://gw.wozaixiaoyuan.com/health/mobile/health/getForm?batch='+batch
    res = requests.get(url, headers=headers)
    data = json.loads(res.text)
    locationType = data['data']['locationType']
    options = data['data']['options']
    fields = data['data']['fields']
    for field in fields[1:]:
        optionId = field['optionId']
        if optionId in options and field['field'] == f't{start}' and field['required'] is True:
            for i in options[optionId]:
                if i['type'] == 0:
                    answers[field['field']] = i['value']
            start += 1
    answers.update({"type": 0, "locationMode": 0})
    print(f"获取{username}的参数成功！")
    return answers, locationType


def GetLocation(config_locations, locationType, username):
    try:
        return users_data[str(username)][0]
    except KeyError:
        print(f"{username}未找到现存位置信息！")
    location = config_locations['location']
    locations = []
    for _ in location:
        if _ == '省' or _ == '市' or _ == '州' or _ == '区' or _ == '县' or _ == '岛' or _ == '域' or _ == '道' or _ == '路' or _ == '乡' or _ == '镇':
            locations.append(location[:location.index(_) + 1])
            location = location[location.index(_) + 1:]
    locate = locations.copy()
    with open('./cache/location.json', 'r', encoding='utf-8') as f:
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


def GetEachJws(config, headers):
    try:
        return jws_data[config['username']]
    except:
        print(config['username'], "尝试登陆！")
        jws = Login(headers, config['username'], config['password'])
        if jws is False:
            mail.send(config['receive'], '登陆失败', '登陆失败，请检查账号密码')
            return False
        jws_data[str(config['username'])] = jws
        return jws


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


def GetConfigs():
    with open('./cache/config.yaml', 'r', encoding='utf-8') as f:
        configs = yaml.safe_load_all(f.read())
    return configs


def GetUsers():
    try:
        with open('./cache/users.txt', 'r') as f:
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
        return users_data[username][0], users_data[username][1]
    except:
        answers, locationType = GetAnswers(headers, username, batch)
        location = GetLocation(config['locations'], locationType, username)
        users_data[str(username)] = [location, answers]
        return location, answers


def GetJWData():
    try:
        with open('./cache/jws.txt', 'r') as f:
            jws_data = json.loads(f.read())
            print("读取现存jws文件成功！")
            return jws_data
    except FileNotFoundError:
        print("jws文件不存在，正在创建！")
        return {}
    except Exception as e:
        print("未知错误", e)
        exit(0)


def main():
    for config in configs:
        username = config['username']
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; WLZ-AN00 Build/HUAWEIWLZ-AN00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.99 XWEB/4343 MMWEBSDK/20220903 Mobile Safari/537.36 MMWEBID/4162 MicroMessenger/8.0.28.2240(0x28001C35) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 miniProgram/wxce6d08f781975d91'}
        jws = GetEachJws(config, headers)
        if jws:
            login_code = testLoginStatus(headers, jws)
        else:
            continue
        if login_code is False:
            print(config['username'], "jws失效！")
            jws = Login(headers, config['username'], config['password'])
            if jws is False:
                continue
            print("jws文件更新成功")
            jws_data[config['username']] = jws
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
        batch = GetUnDo(headers, username)
        if not batch:
            continue
        location, answers = GetEachUser(username, headers, batch, config)
        Punch(headers, batch, answers, location, config['receive'], username)


if __name__ == "__main__":
    configs = GetConfigs()
    mails = next(configs)
    mail = ReturnMail(mails)
    jws_data = GetJWData()
    users_data = GetUsers()
    main()
    with open('./cache/jws.txt', 'w') as f:
        f.write(str(jws_data).replace("'", '"'))
    with open('./cache/users.txt', 'w') as f:
        f.write(str(users_data).replace("'", '"'))
