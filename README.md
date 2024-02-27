# NewWoZaiXiaoYuan
新版我在校园（合并后）的自动打卡+外出报备+自动返校程序，测试于昆明理工大学，其他学校应该也能用。



## 支持功能：

1. 多用户打卡

2. 获取JWS存储本地，避免多次登录可能问题

3. 根据用户输入地址获取配置参数，不再需要抓包获取

4. 自动获取打卡答案，无需手动填入

5. 每日自动外出报备

6. 每日自动返校

### 更新日志

- [x] 2023.11.20 修改代码中的检查登陆URL
- [x] 2023.11.1 我在校园取消JWSESSION，修改为Cookie，已同步更新
- [x] 2023.5.24 取消问题答案选项，修改为返寝打卡
- [x] 2024.2.27 我在校园登陆功能更新，增加AES加密与学校选择，已同步更新，登陆部分参考[mudea661-daily仓库](https://github.com/mudea661/daily/)


### 使用说明：
Python3.7版本及以上

- pip install requests

- pip install yagmail

- pip install pycryptodome

---

## 配置文件的使用：
### 邮箱配置：
请将配置文件夹cache与程序本体放在同一路径下。

```
- WoZaiXiaoYuan.py
- cache
  - config.yaml
  - location.json
```

第一行填写邮箱的地址以及邮箱申请的SMTP服务授权密码，邮箱SMTP服务器域名，下面以163邮箱为例：

正常登陆163邮箱后，点击上方的设置下拉栏，再点击POP3/SMTP/IMAP后，进入如下界面

![avatar](https://img-blog.csdnimg.cn/aa3014630ebd4b5ea50bab59f9649070.png)
点击开启这两个服务，会提示用绑定手机号发送验证码，发送即可


开启后向下滑，找到新增授权密码，点击新增，手机发送验证码后，将所得的授权密码填入config.yml文件之中

![avatar](https://img-blog.csdnimg.cn/29ee0dea2b7d4174b2b6ff61922e06d4.png)

找到下方SMTP服务器的host，填入config.yml文件之中

![avatar](https://img-blog.csdnimg.cn/0fb29040b4b24a6a9e9da93ed4aa42a2.png)


## 用户信息的填写：
在username处填入我在校园登陆账号，一般为手机号；

password处填入登录密码；

receive处填入接收邮箱地址，可以是打卡人的QQ邮箱

back处填写yes或no，表示是否自动返校

out处填写yes或no，表示是否每天自动外出报备


location处填入打卡地址，请遵循省->市->区(市)->街道->路的五级划分填入

longitude填入打卡经度

latitude填入打卡纬度


## 多用户打卡
多用户打卡在末尾新起一行，加上三个横线后(---)，在下一行复制粘贴上一用户配置格式，修改对应信息即可。


坐标以及地点获取可用腾讯地图的坐标拾取器：https://lbs.qq.com/tool/getpoint/ ，但腾讯地图获取到的地址并不含有街道，请手动在路段前添加上街道。



在获取街道时，可按F12打开开发者工具，点击网络后刷新，输入你所需地址后找到?key=XXXXX 的数据包，依次点开result，address_reference，town中的值便是街道名称。



登陆问题：
> 我在校园密码修改后，请点击清除缓存，等待页面跳转到未登录界面时，便可把修改后密码填入程序配置文件中，密码建议为字母加数字，否则程序登陆失败。在运行完程序并且程序将jws存入本地后，即可正常登录我在校园。



配置文件如下图：

![avatar](https://img-blog.csdnimg.cn/bd053620e86a418d9d2be5b34a396bdc.png)


## 代码使用

1. 服务器端配置：

- 将服务器端的cache文件夹中的config.yaml文件填写好后，使用scp命令或者下载filezilla后将WoZaiXiaoYuan.py，GoOut.py以及cache文件夹上传到服务器中。

- filezilla下载地址：https://pc.qq.com/detail/6/detail_22246.html

- 配置定时运行可在宝塔面板中直接使用计划任务配置为SHELL脚本命令: python/python3(Ubuntu系统) WoZaiXiaoYuan.py所在路径/WoZaiXiaoYuan.py

- python/python3(Ubuntu系统) GoOut.py所在路径/GoOut.py，几点运行便会几点自动提交外出报备

- 或者使用Linux自带的crontab命令运行：https://www.runoob.com/linux/linux-comm-crontab.html


2.华为云函数运行


- python版本选择>=Python3.7

> 具体可见这篇文章：https://blog.csdn.net/qq_28778001/article/details/124891438

将config文件填写好后，将WoZaiXiaoYuan.py，index.py，GoOut.py，cache文件夹统一打包为zip文件上传至函数云中

华为云函数中自动判断当前时间，若为晚上8点之前运行，则执行外出报备，8点后执行为运行打卡，具体时间可修改index.py中的时间

将依赖文件按照文章中的方式添加至依赖包中，再在函数页面的最下面添加上依赖即可运行。
