#!/bin/python
#!coding:utf-8
'''
Q-UA2日志整理成设备属性json格式
'''

import os
import sys
import pdb
import json

if __name__ == "__main__":
    f = open('qua2.dat',"r")
    lines = f.readlines()
    f.close()
    d1 = {}#带分辨率大小的
    for line in lines:
        d = {}
        data = line.replace('Q-UA2: ','')
        elms = data.split("&")
        for elm in elms:
            kv = elm.split("=")
            if len(kv) != 2:
                continue
            d[kv[0].strip(" ")]=kv[1].strip(" ").replace("\r","").replace('\n',"")
        ret = {}
        if d.has_key("MO") and d.has_key("OS") and d.has_key("RL") and d.has_key("API"):
            ret["model"] = d["MO"]
            ret["version"] = d["OS"]
            ret["android_api"] = d["API"]
            ret["screan_rsn"] = d["RL"]
            model = d["MO"].replace(" ","").lower()
            os_v = d["OS"].replace(" ","")
            d1[model+"-"+os_v] = ret
        #if ret.has_key("model"):
        #    print ret
    
    d2 = {} #带build
    f = open("uas.txt","r")
    lines = f.readlines()
    f.close()
    for line in lines:
        line = line.replace("\r","").replace("\n","")
        ret = eval(line)
        model = ret["model"].replace(" ","").lower()
        os_v = ret["version"].replace(" ","")
        d2[model+"-"+os_v] = ret
    
    result = {}

    for k,v in d2.items():
        if d1.has_key(k):
            ret = d1[k]
            v["screan_rsn"] = ret["screan_rsn"]
            v["android_api"] = ret["android_api"]
            
            v["android_model"] = v["model"]
            v["os_build"] = v["build"]
            v["android_version"] = v["version"]
            
            del v["model"]
            del v["build"]
            del v["version"]

            print v

