#!/bin/python
#coding:utf8
'''
appium驱动监控，每个设备起一个服务
'''

import os
import sys
import time
import json
import redis
import datetime

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'../../config/'))
from cfg_db import *

def get_devices():
    rd = redis.Redis(host=cfg_redis["host"],port=cfg_redis["port"])
    devices = rd.hvals(cfg_rd_device)
    ret = []
    for dev in devices:
        dev = eval(dev)
        ret.append({"ip":dev["ip"],"dport":dev["driver_port"]})
    return ret

def check_driver(ip,dport):
    output = os.popen('ps aux | grep appium | grep {0} | grep {1} | grep -v grep'.format(ip,dport))
    cnt = output.read()
    if cnt.find(ip) != -1:
        return True
    return False

def start_driver(ip,dport):
    print "start driver for ip:{0}, port:{1}".format(ip,dport)
    os.system("nohup appium -p {0} --udid {1} 2>&1 &".format(ip,dport))



if __name__ == "__main__":
    while True:
        devs = get_devices()
        for dev in devs:
            ip = dev["ip"]
            dport = dev["dport"]
            if not check_driver(ip,dport):
                start_driver(ip,dport)
        time.sleep(3)
