#!/bin/python
#coding:utf8
'''
火山APP首次登录任务
'''
import os
import sys
import pdb
import json
import datetime
import logging
import random
import time


sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),"../"))
from tasker_base import TaskerBase

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'../../../config'))
from cfg_db import *

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),"../../../util/"))
import device_attrs
from user_info import get_unlogin_user

LOG = logging.getLogger(__name__)

class AppActiveHuoshan(TaskerBase):
    
    act = 'app-active-huoshan'
        
    def transfer_device(self):
        if self._task["status"] != 100:
            return False
        
        gid = self._task["gid"]
        devs = self._rd.hget(cfg_rd_rdg,gid)
        if not devs or len(devs) == 0:
            print '分组内没有设备...'
            self._task["status"] = -400
            self._rd.hset(cfg_rd_task,self._task["tid"],self._task)
            return False
        devs = eval(devs) 
        #如果组内设备有忙的，先等待
        if self.dev_has_busy(devs):
            print "AppActiveQQBrowser->Some devices busy!Wait..."
            return False

        #对所有设备，添加修改手机属性的本地任务
        for dev_info in devs:
            ip = dev_info["ip"]
            task_act_dev = {}#'{"tid":"{0}","action":"{1}","params":"{2}","p_tid":"{3}"}'
            tid = self._task["tid"]+"-"+ip
            task_act_dev["tid"]=tid
            task_act_dev["p_tid"]=self._task["tid"]
            task_act_dev["action"]=self._task["act_dev"]
            task_act_dev["params"]=device_attrs.random_dev()
            self._rd.hset(cfg_rd_act_dev,ip,json.dumps(task_act_dev))
       
        self.dev_set_busy(devs)
        self._task["status"] = 111
        self._rd.hset(cfg_rd_task,self._task["tid"],self._task)
        return True

    def transfer_net(self):
        if self._task["status"] != 111:
            return False
        
        gid = self._task["gid"]
        devs = eval(self._rd.hget(cfg_rd_rdg,gid))
        
        #对所有设备，检查本地任务有没未完成的
        for dev_info in devs:
            ip = dev_info["ip"]
            tid = self._task["tid"]+"-"+ip
            tast_act_dev = self._rd.hget(cfg_rd_act_dev,ip)
            if not tast_act_dev:
                print "Task->AppActiveQQBrowser:device task not finished,tid:{0}".format(tid)
                return False
            if tast_act_dev and tast_act_dev != '0': #有任务没有完成
                print "Task->AppActiveQQBrowser:device task not finished,tid:{0}".format(tid)
                return False
        
        for dev_info in devs:
            ip = dev_info["ip"]
            tast_act_net = {} #'{"tid":"{0},"cip":"{1}"}'.format(self._task["tid"]+"-"+dev,ip)
            tast_act_net["tid"]=self._task["tid"]+"-"+ip
            tast_act_net["cip"]=ip
            self._rd.hset(cfg_rd_act_net,ip,json.dumps(tast_act_net))
            #删除完成的device任务
            tast_act_dev = self._rd.hdel(cfg_rd_act_dev,ip)

        self._task["status"] = 113
        self._rd.hset(cfg_rd_task,self._task["tid"],self._task)
        return True
        

    def tansfer_do(self):
        if self._task["status"] != 113:
            return False
        
        gid = self._task["gid"]
        devs = self._rd.hget(cfg_rd_rdg,gid)
        if not devs:
            print "TaskManager->No devices for group gid:{0}".format(gid)
            return False
        devs = eval(devs) 
        
        #对所有设备，检查网络任务有没未完成的
        for dev_info in devs:
            ip = dev_info["ip"]
            tast_act_dev = self._rd.hget(cfg_rd_act_net,ip)
            if not tast_act_dev:
                print "TaskManager->Missing net task for ip:{0}".format(ip)
                return False
            if tast_act_dev and tast_act_dev != '0': #有任务没有完成,注意，这里统一认为vpn总是成功的!
                print "Task->AppActiveQQBrowser:net task not finished,ip:{0}".format(ip)
                return False
        
        #TODO:对net任务结果进行处理
        devices = []
        for dev_info in devs:
            ip = dev_info["ip"]
            utdid = dev_info["device_id"]
            driver = "http://127.0.0.1:{0}/wd/hub".format(dev_info["driver_port"])
            devices.append({"utdid":utdid,"driver":driver,"ip":ip})
            #删除已完成的网络任务
            self._rd.hdel(cfg_rd_act_net,ip)
        
        task_act_do = {}#'{"tid":"{0}","action":"{1}","devices":"{2}","prarams":[]}'.format(self._task["tid"],self._task["act_do"],devices)
        task_act_do = {"tid":self._task["tid"],"action":self._task["act_do"],"devices":devices,"cur_step":self._task["cur_step"]}
        
        #给任务添加登录账号信息
        users = get_unlogin_user('huoshan',len(devices))
        if not users or len(users) == 0:
            self._task["status"] = 200
            self._rd.hset(cfg_rd_task,self._task["tid"],self._task)
            LOG.error("DouyinYH->No unlogin user!We set task done for tid:{0}".format(self._task["tid"]))
            return False
        for i,user in enumerate(users):
            device = task_act_do["devices"][i]
            for k,v in user.iteritems():
                device[k] = v


        self._rd.hset(cfg_rd_act_do,self._task["tid"],json.dumps(task_act_do))
    
        self._task["status"] = 117
        self._task["devices"] = devices
        self._rd.hset(cfg_rd_task,self._task["tid"],self._task)
        return True

    def transfer_done(self):
        if self._task["status"] != 117:
            return False
       
        devs = self._task["devices"]
        for dev in devs:
            ip = dev["ip"]
            do_status = self._rd.hget(cfg_rd_act_do,ip)
            if do_status == None:
                print "Task->AppActiveQQBrowser:appium task not finished,ip:{0}".format(ip)
                return False
        #TODO:对do任务结果进行处理
        for dev in devs:
            ip = dev["ip"]
            do_status = self._rd.hget(cfg_rd_act_do,ip)
            self.report_task("act_do","(tid:{0},ip:{1},code:{2})".format(self._task["tid"],ip,do_status))

        for dev in devs:
            ip = dev["ip"]
            self._rd.hdel(cfg_rd_act_do,ip) #清除设备状态
            self._rd.hdel(cfg_rd_act_do,self._task["tid"])
        
        
        self._task["status"] = 200
        self._rd.hset(cfg_rd_task,self._task["tid"],self._task)
        return True

    def report_task(self,tag,info):
        LOG.info("AppAcitveQQBrowser->action:report_task,tag:{0},info:{1}".format(tag,info))
