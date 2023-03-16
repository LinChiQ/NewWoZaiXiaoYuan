from WoZaiXiaoYuan import Start
from GoOut import go_out
from time import localtime

def handler(event , context):
    if localtime().tm_hour == 22:
        Start()
    else:
        go_out()
