#!/bin/python
#coding:utf8
'''
手机设备参数相关函数
'''
import os
import sys
import pdb
import random
import json
import traceback

from pyimei import ImeiSupport

UAS = None

def random_dev():
    imei = random_imei()
    ssid = random_wifi_name()
    imsi = random_imsi()
    mac = random_mac()
    nettype = random_nettype()
    android_id = random_android_id()
    d = [
            {"imei":imei},
            {"ssid":ssid},
            {"imsi":imsi},
            {"mac":mac},
            {"nettype":nettype},
            {"android_id":android_id}
    ]
    ua = random_ua()
    if ua != None:
        for k,v in ua.iteritems():
            d.append({k:v})
    return d
    
def random_wifi_name():
    seed = '0123456789qwertyuiopasdfghjklzxcvbnm'
    len = random.randint(3,10)
    wifi_name = ""
    for i in range(len):
        wifi_name += random.choice(seed)
    return wifi_name

def random_imei():
    return ImeiSupport.generateNew()

def random_imsi():
    title = '4600'
    second = random.choice("0123567")
    r1 = 10000+random.randint(0,90000)
    r2 = 10000+random.randint(0,90000)
    return title+str(second)+str(r1)+str(r2)

def random_gps():
    return None

def random_mac():
    mac = [ 0x00, 0x16, 0x3e,random.randint(0x00, 0x7f),random.randint(0x00, 0xff),random.randint(0x00, 0xff)]
    return ':'.join(map(lambda x: "%02x" % x, mac))

def random_nettype():
    return random.choice(['wifi','4g','3g'])

def random_android_id():
    seed = '1234567890qwertyuiopasdfghjklzxcvbnm'
    aid = ""
    for i in range(16):
        aid += random.choice(seed)
    return aid

def random_ua():
    global UAS
    if not UAS:
        fp = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../data/uas.txt')
        f = open(fp,'r')
        UAS = []
        lines = f.readlines()
        for line in lines:
            try:
                UAS.append(eval(line.strip("\n")))
            except Exception as e:
                traceback.print_exc()
    n = len(UAS)
    if n == 0:
        return None
    return random.choice(UAS)


if __name__ == "__main__":
    print random_dev()
