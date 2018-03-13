#!/bin/python
#coding:utf8
'''
疯转头条app日活任务,总体任务调度不在这处理，只要考虑本任务即可
task原始任务格式
{
    'tid':"12344-1",
    'status':0, #任务状态,100准备中，11x进行中，200完成,具体参考任务状态码文档
    'group':'xiaomi-4a',
    'utime':1516949388,#任务更新时间戳
    'ctime':1516949388, #任务创建时间
    'name' : '推啊wap广告点击',#任务模块名称
    'remark':'刷10w次点击',#任务备注
    'act':'app-idle-fztt', #任务模块别名
    'act_dev':'modifyAttr', #手机本地任务模块别名
    'act_net':'nat-random', #网络任务模块别名,该任务只是随机ip，比如绑定ip在任务迁移的时候处理
    'act_do':'app-idel-fztt',#动作任务模块别名，暂定appium执行动作
}
'''
import os
import sys
import pdb
import json
import datetime
import logging


sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),"../"))
from tasker_base import TaskerBase

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'../../../config'))
from cfg_db import *

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),"../../../util/"))
import device_attrs

LOG = logging.getLogger(__name__)

class AppIdleFztt(TaskerBase):
    
    act = 'app-idle-fztt'
        
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
            print "AppActiveFztt->Some devices busy!Wait..."
            return False

        #对所有设备，添加修改手机属性的本地任务
        for dev_info in devs:
            ip = dev_info["ip"]
            task_act_dev = {}#'{"tid":"{0}","action":"{1}","params":"{2}","p_tid":"{3}"}'
            tid = self._task["tid"]+"-"+ip
            task_act_dev["tid"]=tid
            task_act_dev["p_tid"]=self._task["tid"]
            task_act_dev["action"]=self._task["act_dev"]
            
            #从redis中取设备的虚拟属性信息
            params = []
            fake_attr_str = self._rd.hget(cfg_rd_app_idle_dev,ip)
            if not fake_attr_str or fake_attr_str == "":
                print "AppIdleFztt->No fake device attribute for cip:"+ip
                return False
            fake_attr = eval(fake_attr_str)
            
            for fk in fake_attr:
                for k,v in fk.items():
                    params.append({k:v})

            task_act_dev["params"] = params
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
                print "Task->AppActiveFztt:device task not finished,tid:{0}".format(tid)
                return False
            if tast_act_dev and tast_act_dev != '0': #有任务没有完成
                print "Task->AppActiveFztt:device task not finished,tid:{0}".format(tid)
                return False
        
        for dev_info in devs:
            ip = dev_info["ip"]
            tast_act_net = {} #'{"tid":"{0},"cip":"{1}"}'.format(self._task["tid"]+"-"+dev,ip)
            tast_act_net["tid"]=self._task["tid"]+"-"+ip
            tast_act_net["cip"]=ip
            oarea = self._rd.hget(cfg_rd_app_idle_oarea,ip)
            if oarea:
                tast_act_net["oarea"]=oarea
            else:
                print "AppIdleFztt->oarea is None for cip:"+ip

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
                print "Task->AppActiveFztt:net task not finished,ip:{0}".format(ip)
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
                print "Task->AppActiveFztt:appium task not finished,ip:{0}".format(ip)
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
        LOG.info("AppAcitveFztt->action:report_task,tag:{0},info:{1}".format(tag,info))