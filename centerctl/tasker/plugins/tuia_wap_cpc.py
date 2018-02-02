#!/bin/python
#coding:utf8
'''
推啊wap端cpc广告任务,总体任务调度不在这处理，只要考虑本任务即可
task原始任务格式
{
    'tid':"12344-1",
    'status':0, #任务状态,100准备中，11x进行中，200完成,具体参考任务状态码文档
    'group':'xiaomi-4a',
    'utime':1516949388,#任务更新时间戳
    'ctime':1516949388, #任务创建时间
    'name' : '推啊wap广告点击',#任务模块名称
    'remark':'刷10w次点击',#任务备注
    'act':'tuia-wap-click', #任务模块别名
    'act_dev':'modifyAttr', #手机本地任务模块别名
    'act_net':'nat-random', #网络任务模块别名,该任务只是随机ip，比如绑定ip许在任务迁移的时候处理
    'act_do':'tuia-wap-click',#动作任务模块别名，暂定appium执行动作
}
'''
import os
import sys
import json

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),"../"))
from tasker_base import TaskerBase

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'../../../config'))
from cfg_db import *

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),"../../../util/"))
import device_attrs

class TuiaWapCPC(TaskerBase):
    
    act = 'tuia-wap-click'
        
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
        
        #如果组内设备有忙的，先等待
        if self.dev_has_busy(devs):
            print "Some devices busy!Wait..."
            return False

        #对所有设备，添加修改手机属性的本地任务
        for dev_info in devs:
            dev = dev_info["ip"]
            task_act_dev = '{"tid":"{0}","action":"{1}","params":"{2}","p_tid":"{3}"}'
            tid = self._task["tid"]+"-"+dev
            task_act_dev = task_act_dev.format(tid,self._task["act_dev"],json.dumps(device_attrs.random_dev()),self._task["tid"])
            self._rd.hset(cfg_rd_actdev,tid,task_act_dev)
        
        self.dev_set_busy(devs)
        self._task["status"] = 111
        self._rd.hset(cfg_rd_task,self._task["tid"],self._task)
        return True

    def transfer_net(self):
        if self._task["status"] != 111:
            return False
        
        gname = self._task["group"]
        devs = json.loads(self._rd.hget(cfg_rd_rdg,gname))
        
        #对所有设备，检查本地任务有没未完成的
        for dev_info in devs:
            dev = dev_info["ip"]
            tid = self._task["tid"]+"-"+dev
            tast_act_dev = self._rd.hget(cfg_rd_actdev,tid,task_act_dev)
            if tast_act_dev and tast_act_dev != 'ok': #有任务没有完成
                return False
        
        for dev_info in devs:
            ip = dev_info["ip"]
            tid = self._task["tid"]+"-"+dev
            tast_act_net = '{"tid":"{0},"cip":"{1}"}'.format(self._task["tid"]+"-"+dev,ip)
            self._rd.hset(cfg_rd_actnet,ip,tast_act_net)

        self._task["status"] = 113
        self._rd.hset(cfg_rd_task,self._task["tid"],self._task)
        return True
        

    def tansfer_do(self):
        if self._task["status"] != 113:
            return False
        
        gname = self._task["group"]
        devs = json.loads(self._rd.hget(cfg_rd_rdg,gname))
        
        #对所有设备，检查网络任务有没未完成的
        for dev_info in devs:
            dev = dev_info["ip"]
            tid = self._task["tid"]+"-"+dev
            tast_act_dev = self._rd.hget(cfg_rd_actnet,tid,task_act_dev)
            if tast_act_dev and tast_act_dev != 'ok': #有任务没有完成
                return False
        #TODO:对net任务结果进行处理
        devices = []
        for dev_info in devs:
            ip = dev_info["ip"]
            utdid = dev_info["utdid"]
            driver = dev_info["driver"]
            devices.append({"utdid":utdid,"dirver":driver,"ip":ip})
        
        task_act_do = '{"tid":"{0}","action":"{1}","devices":"{2}","prarams":[]}'.format(self._task["tid"],self._task["act_do"],devices)
        self._rd.hset(cfg_rd_actdo,self._task["tid"],task_act_do)
    
        self._task["status"] = 117
        self._rd.hset(cfg_rd_task,self._task["tid"],self._task)
        return True

    def transfer_done(self):
        if self._task["status"] != 117:
            return False
        
        devs = self._task["devices"]
        for dev in devs:
            ip = dev["ip"]
            do_status = self._rd.hget(cfg_rd_actdo,ip)
            if do_status == None:
                return False
        #TODO:对do任务结果进行处理
        
        self._task["stutas"] = 200
        self._rd.hset(cfg_rd_task,self._task["tid"],self._task)
        return True


