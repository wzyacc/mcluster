#!/bin/python
#coding:utf8
'''
各种任务控制基类,需要协调设备、网络和动作的工作。暂不考虑优先级问题。
'''
import os
import sys
import pdb
import datetime


sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),"../../config/"))
from cfg_db import *


class TaskerBase:
    def __init__(self,rd,task):
        self._task = task #任务信息，json数据
        self._rd = rd #redis客户端
    
    def dev_has_busy(self,devs):
        #单线程，无锁的问题
        for dev in devs:
            ip = dev["ip"]
            _dev = self._rd.hget(cfg_rd_device,ip)
            if not _dev:
                print "Task Base dev not found for ip:{0}".format(ip)
                continue
            busy = dev.get("busy",None)
            if busy and int(busy) == 1:#fix 是否繁忙字符串格式问题
                return True
        return False

    def dev_set_busy(self,devs):
        #单线程，无锁的问题
        for dev in devs:
            ip = dev["ip"]
            _dev = self._rd.hget(cfg_rd_device,ip)
            if not _dev:
                print "TaskManager->Device maybe offline for ip:"+ip
                continue
            _dev = eval(_dev)
            _dev["busy"]=1
            self._rd.hset(cfg_rd_device,ip,_dev)

    def transfer_device(self):
        #任务初始化到设备任务；或者本阶段任务状态迁移
        raise NotImplementedError

    def transfer_net(self):
        #若设备任务完成，初始化到网络任务；或者本阶段任务状态迁移
        raise NotImplementedError

    def tansfer_do(self):
        #若网络任务完成，初始化到动作任务；或者本阶段任务状态迁移
        raise NotImplementedError

    def transfer_done(self):
        #任务完成收尾清理工作;或者初始化新一轮任务
        raise NotImplementedError

    
