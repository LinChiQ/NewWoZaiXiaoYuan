# NewWoZaiXiaoYuan
新版我在校园（合并后）的自动打卡程序

# 使用说明：
Python3.7版本及以上

pip install requests

pip install yagmail



# 配置文件的使用：
# 邮箱配置：
请将配置文件夹cache与程序本体放在同一路径下。


第一行填写邮箱的地址以及邮箱申请的SMTP服务授权密码，邮箱SMTP服务器域名，下面以163邮箱为例：

正常登陆163邮箱后，点击上方的设置下拉栏，再点击POP3/SMTP/IMAP后，进入如下界面

![avatar](https://img-blog.csdnimg.cn/aa3014630ebd4b5ea50bab59f9649070.png)
点击开启这两个服务，会提示用绑定手机号发送验证码，发送即可


开启后向下滑，找到新增授权密码，点击新增，手机发送验证码后，将所得的授权密码填入config.yml文件之中

![avatar](https://img-blog.csdnimg.cn/29ee0dea2b7d4174b2b6ff61922e06d4.png)

找到下方SMTP服务器的host，填入config.yml文件之中

![avatar](https://img-blog.csdnimg.cn/0fb29040b4b24a6a9e9da93ed4aa42a2.png)


# 用户信息的填写：
在username处填入我在校园登陆账号，一般为手机号；

password处填入登录密码；

receive处填入接收邮箱地址，可以是打卡人的QQ邮箱

location处填入打卡地址，请遵循省->市->区(市)->街道->路的五级划分填入

longitude填入打卡经度

latitude填入打卡纬度


# 多用户打卡
多用户打卡在末尾新起一行，加上三个横线后(---)，在下一行复制粘贴上一用户配置格式，修改对应信息即可。

配置文件如下图：

![avatar](https://img-blog.csdnimg.cn/3900ac81640b45fbb0afe0f04796d5aa.png)


# 代码使用
所有配置填写完成后，将WoZaiXiaoYuan.py和cache文件夹一并上传到服务器或云函数之上，按照要求自定义打卡时间。

具体可见这篇文章：https://blog.csdn.net/qq_28778001/article/details/124891438
在这不再赘述。
