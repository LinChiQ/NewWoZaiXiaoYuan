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
- [x] 2024.2.27 我在校园登陆功能更新，增加AES加密与学校选择，已同步更新。
- [x] 2024.5.2 由于依赖新增过多，代码新增Github Actions的使用，去除掉华为云函数部分的使用
- [x] 2024.8.20 重构代码，使用SQLite数据库对用户JWSESSION以及打卡数据进行存储，使用腾讯地图API对用户打卡地址进行解析处理，新增消息模块里的蓝牙签到（By Mudea661），同步更新README文件。
- [x] 2024.9.15 我在校园更新新打卡方式，已同步更新服务器代码与Github Action代码。


### 使用说明：
Python3.7版本及以上

`pip install -r requirements.txt`



#### 文件结构

```
- WoZaiXiaoYuan.py
- actionVersion.py
- blueTooth.py (Mudea661提供的蓝牙签到源码)
- requirements.txt
- README.md
- cache
  - config.yaml
  - userdata.db (服务器初运行时自动添加)
```



#### `config.yaml`文件填写

第一行填写

- 邮箱的地址以及邮箱申请的SMTP服务授权密码，邮箱SMTP服务器域名，**若不想使用邮箱推送则填空**

  下面以163邮箱为例：

正常登陆163邮箱后，点击上方的设置下拉栏，再点击POP3/SMTP/IMAP后，进入如下界面

![avatar](https://img-blog.csdnimg.cn/aa3014630ebd4b5ea50bab59f9649070.png)
点击开启这两个服务，会提示用绑定手机号发送验证码，发送即可


开启后向下滑，找到新增授权密码，点击新增，手机发送验证码后，将所得的授权密码填入config.yaml文件之中

![avatar](https://img-blog.csdnimg.cn/29ee0dea2b7d4174b2b6ff61922e06d4.png)

找到下方SMTP服务器的host，填入config.yml文件之中

![avatar](https://img-blog.csdnimg.cn/0fb29040b4b24a6a9e9da93ed4aa42a2.png)

`school` 部分填写学校名称

`tencent_map` 处填写**腾讯地图API创建的应用的KEY值**，并分配该应用**地址解析与逆地址解析**的配额，操作如下：

1. 打开[腾讯地图开发平台](https://lbs.qq.com/map/)，点击右上角进行登陆/注册成为个人开发者，进入控制台，点击左侧的应用管理 -> 我的应用，创建一个新应用

![image-20240820092615089](https://gitee.com/lateyoung222/images/raw/master/imgs/image-20240820092615089.png)

2. 创建应用后在该应用中点击添加KEY，KEY名称随意，勾选下方的`WebServiceAPI`即可点击确定，**记录下显示出的KEY值填入config文件中的`tencent_map`处**

   ![image-20240820092851075](https://gitee.com/lateyoung222/images/raw/master/imgs/image-20240820092851075.png)

3. 为新增的KEY进行配额分配，点击左侧配额管理 -> 账户额度，接口类型选择地址，地点类，为**逆地址解析**与**地址解析**分配额度以及并发量

   ![image-20240820093252746](https://gitee.com/lateyoung222/images/raw/master/imgs/image-20240820093252746.png)

   ![image-20240820093312431](https://gitee.com/lateyoung222/images/raw/master/imgs/image-20240820093312431.png)




## 用户信息的填写：
`username` 处填入我在校园登陆账号，一般为手机号；

`password` 处填入登录密码；

`receive` 处填入接收邮箱地址，可以是打卡人的QQ邮箱，若不使用邮箱推送则填空

`sct_ftqq` 部分填写[Server酱](https://sct.ftqq.com)的<font color="red">SendKey</font>值，若为空则代表不使用

![image-20240517233108811](https://gitee.com/lateyoung222/images/raw/master/image-20240517233108811.png)

`location` 处填入打卡地址，请遵循省->市->区(市)->街道->路的五级划分填入

`blue_sign` 处填写是否进行蓝牙打卡，填写yes/no

`dorm_sign`  处填写是否进行归寝打卡，填写yes/no



#### 多用户打卡

多用户打卡在末尾新起一行，加上三个横线后(---)，在下一行复制粘贴上一用户配置格式，修改对应信息即可。



#### 登陆问题：

我在校园密码修改后，请点击清除缓存，等待页面跳转到未登录界面时，便可把修改后密码填入程序配置文件中，密码建议为字母加数字，否则程序登陆失败。在运行完程序并且程序将jws存入本地后，即可正常登录我在校园。



配置文件如下图：

![image-20240820094127279](https://gitee.com/lateyoung222/images/raw/master/imgs/image-20240820094127279.png)


## 代码使用

1. 服务器端配置：

​	从本仓库下载所有代码

​	`git clone https://github.com/LinChiQ/NewWoZaiXiaoYuan`

​	填写好cahche文件夹下的config.yaml文件以及相关配置，运行`python WoZaiXiaoYuan.py`

- 配置定时运行可在宝塔面板中直接使用计划任务配置为SHELL脚本命令: python/python3(Ubuntu系统) WoZaiXiaoYuan.py所在路径/WoZaiXiaoYuan.py
- 或者使用Linux自带的crontab命令运行：https://www.runoob.com/linux/linux-comm-crontab.html

2. Github Action的使用
   
   **Fork本仓库**

![image-20240502201050428](https://gitee.com/lateyoung222/images/raw/master/image-20240502201050428.png)

​	**配置打卡参数**

- 在Fork后的新仓库中，点击`Settings`，进入左侧栏目中的`Environments`，点击`New environment`，命名为`CONFIG_01`
  ![image-20240502201612262](https://gitee.com/lateyoung222/images/raw/master/image-20240502201612262.png)

- 在下方的`Environment secrets`中新增Secret，所需Secret有：

  ![image-20240502201702880](https://gitee.com/lateyoung222/images/raw/master/image-20240502201702880.png)

  - `school_name` 填写对应的学校名称，如昆明理工大学
  - `receive_mail` 填写所接受消息通知的邮件号
  - `mail_address` 填写**发送邮件通知**的邮件号，若为空则代表不使用
  - `mail_password` 填写**发送邮件通知**的邮件号的授权码
  - `mail_host` 填写**发送邮件通知**的邮件号所对应的SMTP服务器地址
  - `punch_location` 填写想要打卡地址，对应上方服务器端的location打卡地址
  - `dorm_sign` 是否进行归寝打卡，填写yes/no
  - `blue_sign` 是否进行蓝牙打卡，填写yes/no
  - `wzxy_username` 填写我在校园登录账号，通常为手机号
  - `wzxy_password` 填写我在校园登录密码
  - `sct_ftqq` 填写[Server酱](https://sct.ftqq.com)的<font color="red">SendKey</font>值，若为空则代表不使用
  - `tencentKey` 填写上方获取并已分配额度的腾讯地图KEY值

  ![填写参考](https://gitee.com/lateyoung222/images/raw/master/image-20240502202556250.png)

  

  **打卡测试**

- 所有参数填写完毕后，点击Actions按钮，点击左侧的**我在校园打卡**后，点击`Run workflow`，再点击绿色的`Run workflow`按钮进行测试，当Action中运行没有红色按钮即代表填写无误

  ![image-20240502202805383](https://gitee.com/lateyoung222/images/raw/master/image-20240502202805383.png)

- 点击开**执行打卡**中查看是否登录成功，如登录成功则可等待晚上10点自动打卡（Github Actions需要排队，可能推迟10分钟左右），如登录不成功请修改密码清楚缓存后重新填入。

  ![image-20240502203613949](https://gitee.com/lateyoung222/images/raw/master/image-20240502203613949.png)

  

​	**多用户打卡**

- 回到仓库首页，依次点击`.github/workflows/punch.yml`，将属于User02的部分取消注释后，在Environment中新增一个名为`CONFIG_02`的环境后，填入同样的Secert即可
- 如需要第三及以上个用户，请复制User01的所有代码，复制到yml文件后方，修改为User03，然后将`environment: CONFIG_02`修改为`environment: CONFIG_03`，再在Environment中新增一个叫`CONFIG_03`的环境后填写同样的Secert即可，更多用户相同步骤，请注意新增时的**yml文件缩进**



​	**Archive Fork后的仓库**

​	Github Action如果在仓库长期不更新代码的情况下，会在一个月内自动停止对Action的调用，所以在Fork仓	库后还需要对仓库Archive，点击`Settings`，往下找到`Danger Zone`，点击**Archive this repository**

![image-20240820095313803](https://gitee.com/lateyoung222/images/raw/master/imgs/image-20240820095313803.png)



