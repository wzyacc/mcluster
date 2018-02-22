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

task_modules = {
            "tuia-wap-click":TuiaWapCPC,
            "app-active-qqbrowser":AppActiveQQBrowser
        }


task_conf = {
    "logging": {
        "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
        "type": "file",
        "level": 2,
        "filename": "/data/log/mcluster/task_manager/task_manager",
        "rotationWhen": "M",
        "rotationInterval": 120,
        "rotationBackups": 0
    }
}
