import requests
import json
import os
import time
from Crypto.Cipher import AES  # pycryptodome
from Crypto.Util.Padding import pad
from base64 import b64encode


class Logger:
    @staticmethod
    def w_log(text, mark):
        now_localtime = time.strftime("%H:%M:%S", time.localtime())
        text = text.encode('utf-8', 'ignore').decode('utf-8')
        print(f"{now_localtime}  By.mude | {mark} | {text}")


class Encryption:
    @staticmethod
    def encrypt(text, key):
        cipher = AES.new(key.encode('utf-8'), AES.MODE_ECB)
        padded_text = pad(text.encode('utf-8'), AES.block_size)
        return b64encode(cipher.encrypt(padded_text)).decode('utf-8')


class School:
    @staticmethod
    def find_school_id(school_name, data):
        for school in data:
            if school['name'] == school_name:
                return school['id']
        return None


class BlueDataUploader:
    @staticmethod
    def upload_blue_data(blue1, blue2, jwsession, mark, id, signid):
        headers = {
            "Content-Type": "application/json",
            "JWSESSION": jwsession
        }
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
                Logger.w_log(f"账号- {mark} -蓝牙签到成功", mark)
                return 0
            else:
                Logger.w_log(f"账号- {mark} -蓝牙签到失败: {response_data.get('message', '未知错误')}", mark)
                return 1
        else:
            Logger.w_log(f"账号- {mark} -网络请求失败, 请稍候再试", mark)
            return 1


class Signer:
    def __init__(self, username, password, school, mark, key):
        self.username = username
        self.password = password
        self.school = school
        self.mark = mark
        self.key = key
        self.session = requests.Session()

    def main_loop(self):
        encrypted_text = Encryption.encrypt(self.password, self.key)
        
        headers = {
            "accept": "application/json, text/plain, */*",
            "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1 Edg/119.0.0.0"
        }

        # 获取学校ID
        school_list_url = "https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/getSchoolList"
        school_data = self.session.get(school_list_url, headers=headers).json()['data']
        school_id = School.find_school_id(self.school, school_data)
        
        # 登录
        login_url = "https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/username"
        login_params = {
            "schoolId": school_id,
            "username": self.username,
            "password": encrypted_text
        }
        try:
            response = self.session.post(login_url, headers=headers, params=login_params)
            cookie = response.headers['Set-Cookie'].split(';')[0].split('=')[1]
        except:
            login_params["password"] = self.password
            response = self.session.post(login_url, headers=headers, params=login_params)
            cookie = response.headers['Set-Cookie'].split(';')[0].split('=')[1]

        # 获取签到日志
        sign_logs_url = "https://gw.wozaixiaoyuan.com/dormSign/mobile/receive/getMySignLogs"
        sign_logs_params = {
            "page": 1,
            "size": 10
        }
        try:
            response = self.session.get(sign_logs_url, headers={**headers, "jwsession": cookie}, params=sign_logs_params)
            data_ids = response.json()
            location_id = data_ids["data"][0]["locationId"]
            sign_id = data_ids["data"][0]["signId"]
            major = data_ids["data"][0]["deviceList"][0]["major"]
            uuid = data_ids["data"][0]["deviceList"][0]["uuid"]
            blue1 = [uuid.replace("-", "") + str(major)]
            blue2 = {"UUID1": uuid}
        except:
            Logger.w_log(f"账号- {self.mark} -获取签到列表出错！", self.mark)
            return 0

        return BlueDataUploader.upload_blue_data(blue1, blue2, cookie, self.mark, location_id, sign_id)


def main():
    try:
        configs = os.environ.get(f'wzxy')
        if not configs:
            exit()
        accounts_list = configs.split("&")    
    except Exception as e:
        Logger.w_log(f"账号密码等数据出现问题: {e}", mark)
    for configss in accounts_list:
        configs = configss.split("#")
        username = configs[0]
        password = configs[1]
        school = "昆明理工大学"
        mark = username
        key = (username + "0000000000000000")[:16]
        Logger.w_log(f"账号- {mark} -----------------", mark)
        Logger.w_log(f"账号- {mark} -开始打卡", mark)
        signer = Signer(username, password, school, mark, key)
        for attempt in range(3):
            try:
                code = signer.main_loop()
                if code == 0:
                    Logger.w_log(f"账号- {mark} -打卡成功", mark)
                    break
                elif code == 1:
                    continue
            except Exception as e:
                Logger.w_log(f"登录打卡部分出现问题: {e}", mark)

            Logger.w_log(f"账号- {mark} -尝试重新打卡", mark)
        else:
            Logger.w_log(f"账号- {mark} -尝试重新打卡三次失败", mark)


if __name__ == '__main__':
    main()
