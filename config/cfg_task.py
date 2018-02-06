#!/bin/python
#coding:utf8
'''
任务配置文件
'''
import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),"../centerctl/tasker/plugins/"))

from tuia_wap_cpc import TuiaWapCPC

task_modules = {
            "tuia-wap-click":TuiaWapCPC
        }
