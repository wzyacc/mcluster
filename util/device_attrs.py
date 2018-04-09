#!/bin/python
#coding:utf8
'''
手机设备参数相关函数
'''
import os
import sys
import pdb
import time
import random
import json
import traceback

from pyimei import ImeiSupport

UAS = None

def random_dev():
    #获取随机设备信息
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
    
    build_probs = None
    
    while not build_probs:
        builds = random_builds()
        brand = builds["build_brand"]
        model = builds["build_model"]

        uas = get_brand_uas(brand,model)
        if not uas:
            print "Not found target ua for:"
            print builds
            pdb.set_trace()
        build_probs = gen_build_probs(builds,uas)

    packages = random_brand_packages(brand)
    
    for k,v in build_probs.iteritems():
        d.append({k:v})
    d.append({"packages":packages})

    #sd信息
    sd = random_sd(brand,model)
    for k,v in sd.iteritems():
        d.append({k:v})
    
    #固定屏幕大小
    for item in d:
        if item.has_key("screan_rsn"):
            item["screan_rsn"] = "720*1280"


    return d


def random_sd(brand=None,model=None):
    wds = "0123456789qwertyuiopasdfghjklzxcvbnm"
    if brand.lower().find("leeco") != -1:
        if model.lower().find("le x620") != -1:
            sd_name = 'HBG4a2'
            sd_cid = '90014a484247346132a'
            for i in range(13):
                sd_cid += random.choice(wds)
            return {"sd_type":"MMC","sd_name":sd_name,"sd_cid":sd_cid}
        if model.lower().find("lex651") != -1:
            sd_name = 'BJNB4R'
            sd_cid = '150100424a4e4234520'
            for i in range(13):
                sd_cid += random.choice(wds)
            return {"sd_type":"MMC","sd_name":sd_name,"sd_cid":sd_cid}
    
    if brand.lower().find("360") != -1:
        if model.lower().find("1501_m02") != -1:
            sd_name = 'DF4016'
            sd_cid = '4501004446343031360'
            for i in range(13):
                sd_cid += random.choice(wds)
            return {"sd_type":"MMC","sd_name":sd_name,"sd_cid":sd_cid}
    
    if brand.lower().find("oppo") != -1:
        if model.lower().find("a37m") != -1:
            sd_name = 'Q2J96R'
            sd_cid = '13014e51324a3936521'
            for i in range(13):
                sd_cid += random.choice(wds)
            return {"sd_type":"MMC","sd_name":sd_name,"sd_cid":sd_cid}
    
    if brand.lower().find("vivo") != -1:
        if model.lower().find("y55") != -1:
            sd_name = 'QE13MB'
            sd_cid = '150100514531334d420'
            for i in range(13):
                sd_cid += random.choice(wds)
            return {"sd_type":"MMC","sd_name":sd_name,"sd_cid":sd_cid}

    return {"sd_type":"","sd_name":"","sd_cid":""}


def gen_build_probs(builds,uas):
    bf = builds["build_fingerprint"]
    android_version = bf.split("/")[2].split(":")[1]
    good_ua = None
    for ua in uas:
        if ua["android_version"] == android_version:
            good_ua = ua
            break
    if not good_ua:
        return None
   

    for k,v in good_ua.iteritems():
        if builds.has_key(k):
            continue
        builds[k] = v
    builds["os_build"] = builds["build_id"]
    return builds

def random_builds():
    #随机生成builds信息
    ret = {}
    
    fp = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../data/builds.txt')
    d_builds = {}
    with open(fp,'r') as f:
        d_builds = json.load(f)
    builds = []
    for k,v in d_builds.iteritems():
        if k == "unkown":
            continue

        for k1,v1 in v.iteritems():
            for item in v1:
                builds.append(item)
    return random.choice(builds)


def random_brand_packages(brand):
    #随机生成指定品牌的包列表
    ret = {}
    ret["sys"] = []
    ret["brand"] = []
    ret["third"] = []
    fp = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../data/packages.txt')
    d_packages = {}
    with open(fp,'r') as f:
        cnt = f.read()
        d_packages = eval(cnt)
    #手机出厂时间生成
    t_area = random.randint(0,100)
    if t_area < 30:
        t_create = int(time.time()-random.randint(20*24*3600,6*30*24*3600))*1000
    if t_area >= 30 and t_area < 60:
        t_create = int(time.time()-random.randint(6*30*24*3600,12*30*24*3600))*1000
    if t_area >= 60 and t_area < 80:
        t_create = int(time.time()-random.randint(12*30*24*3600,2*12*30*24*3600))*1000
    if t_area >= 80:
        t_create = int(time.time()-random.randint(2*12*30*24*3600,5*12*30*24*3600))*1000
    
    pk_sys = d_packages["sys"][brand]
    for k in pk_sys.keys():
        pk_box = pk_sys[k]
        rd = random.randint(0,100)
        if rd < 80:
            pk = random.choice(pk_box)
            pk["packageName"] = k
            pk["firstInstallTime"] = '%d' % t_create
            pk["lastUpdateTime"] = '%d' % t_create
            ret["sys"].append(pk)
    
    pk_brand = d_packages["brand"][brand]
    for k in pk_brand:
        pk_box = pk_brand[k]
        rd = random.randint(0,100)
        if rd < 80:
            t_dis = random.randint(2*24*3600,12*30*24*3600)
            t_install = (time.time()-t_dis)*1000 
            t_up = random.randint(0,100)
            if t_up < 5:
                t_update = (time.time()-random.randint(2*24*3600,10*24*3600))*1000
            else:
                t_update = t_install
            t_update = max(t_create,t_update)
            pk = random.choice(pk_box)
            pk["packageName"] = k
            pk["firstInstallTime"] = '%d' % t_install
            pk["lastUpdateTime"] = '%d' % t_update
            ret["brand"].append(pk)
    
    rd = random.randint(0,100)
    if rd < 5:
        app_c = random.randint(1,10)
    elif rd <30:
        app_c = random.randint(10,15)
    elif rd<55:
        app_c = random.randint(15,20)
    elif rd<90:
        app_c = random.randint(20,25)
    else:
        app_c = random.randint(25,40)
    hit_p = app_c*100/40
    
    pk_third = d_packages["third"]
    for k in pk_third:
        lst_pk = pk_third[k]
        rd_hit = random.randint(0,100)
        if rd_hit < hit_p:
            t_dis = random.randint(2*24*3600,12*30*24*3600)
            t_install = (time.time()-t_dis)*1000 
            t_up = random.randint(0,100)
            if t_up < 10:
                t_update = (time.time()-random.randint(2*24*3600,10*24*3600))*1000
                t_update = max(t_create,t_update)
            else:
                t_update = t_install
            pk = random.choice(lst_pk)
            pk["packageName"] = k
            pk["firstInstallTime"] = '%d' % t_install
            pk["lastUpdateTime"] = '%d' % t_update
            ret["third"].append(pk)

    return ret
    
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
    return random.choice(['4g','3g'])
    rd = random.randint(0,100)
    if rd < 5:
        return '3g'
    elif rd < 20:
        return '4g'
    return 'wifi'

def random_android_id():
    seed = '1234567890qwertyuiopasdfghjklzxcvbnm'
    aid = ""
    for i in range(16):
        aid += random.choice(seed)
    return aid

def random_ua():
    global UAS
    #if not UAS:
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

def get_brand_uas(brand,model):
    fp = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../data/uas.txt')
    f = open(fp,'r')
    uas = []
    lines = f.readlines()
    for line in lines:
        try:
            uas.append(eval(line.strip("\n")))
        except Exception as e:
            traceback.print_exc()
    lst_dev = []
    for dev in uas:
        if dev["android_model"].lower() == model.lower():
            lst_dev.append(dev)
    if len(lst_dev) == 0:
        return None
    return lst_dev

    '''
    if len(lst_dev) > 0:
        print "Warning->get_brand_ua:Not uique device selected!"
        print lst_dev
    return random.choice(lst_dev)
    '''

if __name__ == "__main__":
    print random_dev()
