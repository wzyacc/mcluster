#!/bin/python
'''
任务管理类，实现管理功能模块
'''

import os
import sys
import redis

sys.path.append(sys.path.join(sys.path.dirname(sys.path.realpath(__file__)),'.../.../config'))
from cfg_db import *
from cfg_task import task_modules

class TaskerManager:

    def __init__(self):
        self._rd = redis.Redis(host=cfg_redis["host"],port=cfg_redis["port"])


    def findProcessingTask(self):
        task_keys = self._rd.hkeys(cfg_rd_task)
        for k in task_keys:
            task = self._rd.hget(k)
            if not task: #task任务有可能被监控程序置空，如已经完成
                continue
            status = task["status"]
            if status / 10 == 11: #状态为11x
                return task
        return None

    def findSpareTask(self):
        #找到一个还未开始的任务
        task_keys = self._rd.hkeys(cfg_rd_task)
        for k in task_keys:
            task = self._rd.hget(k)
            if not task: #task任务有可能被监控程序置空，如已经完成
                continue
            status = task["status"]
            if status == 100: #状态为100,任务准备好，需要执行
                return task
        return None

    def executeTask(self,task):
        module_name = task["act"]
        tasker = task_modules.get(module_name,None)
        if tasker is None:
            print "Tasker Module {0} not found!".format(module_name)
            return False
        ins = tasker(self._rd,task)
        ins.transfer_device()
        ins.transfer_net()
        ins.tansfer_do()
        ins.transfer_done()


if __name__ == "__main__":
    print 'ok'
    mgr = TaskerManager()
    while True:
        task = mgr.findProcessingTask() 
        if task is not None:
            #有进行中的任务，此处线简单处理，单任务推进策略
            print "Find processing task tid:{0}".format(task["tid"])
            mgr.executeTask(task)
            time.sleep(5)
            continue
        task = mgr.findSpareTask()
        if task is not None:
            print "Find spare task tid:{0}".format(task["tid"])
            mgr.executeTask(task)
            time.sleep(5)
