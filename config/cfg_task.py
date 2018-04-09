#!/bin/python
#coding:utf8
'''
任务配置文件
'''
import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),"../centerctl/tasker/plugins/"))

from tuia_wap_cpc import TuiaWapCPC
from app_activate_qqbrowser import AppActiveQQBrowser
from app_idle_qqbrowser import AppIdleQQBrowser
from app_activate_fztt import AppActiveFztt
from app_idle_fztt import AppIdleFztt
from app_activate_miaopai import AppActiveMiaopai
from app_idle_miaopai import AppIdleMiaopai
from app_yh_douyin import AppActiveDouyin
from app_yh_huajiao import AppActiveHuajiao
from app_yh_huoshan import AppActiveHuoshan
from app_yh_kuaishou import AppActiveKuaishou
from app_yh_xiongmao import AppActiveXiongmao

task_modules = {
            "tuia-wap-click":TuiaWapCPC,
            "app-active-qqbrowser":AppActiveQQBrowser,
            "app-idle-qqbrowser":AppIdleQQBrowser,
            "app-active-fztt":AppActiveQQBrowser,
            "app-idle-fztt":AppIdleQQBrowser,
            "app-active-miaopai":AppActiveMiaopai,
            "app-idle-miaopai":AppIdleMiaopai,
            "app-active-douyin":AppActiveDouyin,
            "app-active-huajiao":AppActiveHuajiao,
            "app-active-huoshan":AppActiveHuoshan,
            "app-active-kuaishou":AppActiveKuaishou,
            "app-active-xiongmao":AppActiveXiongmao,
        }


task_conf = {
    "logging": {
        "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
        "type":"stream",
        #"type": "file",
        "level": 2,
        "filename": "/data/log/mcluster/task_manager/task_manager",
        "rotationWhen": "M",
        "rotationInterval": 120,
        "rotationBackups": 0
    }
}
monitor_conf = {
    "logging": {
        "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
        "type":"stream",
        #"type": "file",
        "level": 2,
        "filename": "/data/log/mcluster/task_monitor/monitor_manager",
        "rotationWhen": "M",
        "rotationInterval": 120,
        "rotationBackups": 0
    }
}
