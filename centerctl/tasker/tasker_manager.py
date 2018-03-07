#!/bin/python
#coding:utf8
'''
任务管理类，实现管理功能模块
'''

import os
import sys
import pdb
import redis
import json
import time
import datetime
import logging
import logging.handlers

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'../../config'))
from cfg_db import *
from cfg_task import task_modules,task_conf

LOG = logging.getLogger(__name__)

class TaskerManager:

    def __init__(self):
        self._rd = redis.Redis(host=cfg_redis["host"],port=cfg_redis["port"])


    def findProcessingTask(self):
        task_keys = self._rd.hkeys(cfg_rd_task)
        for k in task_keys:
            task = self._rd.hget(cfg_rd_task,k)
            if not task: #task任务有可能被监控程序置空，如已经完成
                continue
            task = eval(task)
            status = task["status"]
            if status / 10 == 11: #状态为11x
                return task
        return None
    
    def findProcessingTasks(self):
        #获取所有正在运行的任务
        task_keys = self._rd.hkeys(cfg_rd_task)
        for k in task_keys:
            task = self._rd.hget(cfg_rd_task,k)
            if not task: #task任务有可能被监控程序置空，如已经完成
                continue
            task = eval(task)
            status = task["status"]
            if status / 10 == 11: #状态为11x
                yield task
        raise StopIteration()

    def findSpareTask(self):
        #找到一个还未开始的任务
        task_keys = self._rd.hkeys(cfg_rd_task)
        for k in task_keys:
            task = self._rd.hget(cfg_rd_task,k)
            if not task: #task任务有可能被监控程序删除，如已经完成
                continue
            task = eval(task)
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

def setup_logging(conf):
    """
    配置输出log格式等
    :param conf:全局变量，json格式全局配置
    :return:
    """
    root_logger = logging.getLogger()
    formatter = logging.Formatter(conf['logging']['format'])

    log_levels = [
        logging.ERROR,
        logging.WARNING,
        logging.INFO,
        logging.DEBUG
    ]
    loglevel = log_levels[conf['logging']['level']]
    root_logger.setLevel(loglevel)

    if not os.path.exists(os.path.dirname(conf['logging']['filename'])):
        os.makedirs(os.path.dirname(conf['logging']['filename']))
    
    if conf['logging']['type'] == 'file':
        log_out = logging.handlers.TimedRotatingFileHandler(
            conf['logging']['filename'],
            when=conf['logging']['rotationWhen'],
            interval=conf['logging']['rotationInterval'],
            backupCount=conf['logging']['rotationBackups']
        )
        print("Logging to %s." % conf['logging']['filename'])
    elif conf['logging']['type'] == 'stream':
        log_out = logging.StreamHandler()
    else:
        print("Logging type must be one of 'stream', or 'file', not "
              "'%s'." % conf['logging']['type'])
        sys.exit(1)

    log_out.setLevel(loglevel)
    log_out.setFormatter(formatter)
    root_logger.addHandler(log_out)
    return root_logger

if __name__ == "__main__":
    print 'ok'
    setup_logging(task_conf)
    mgr = TaskerManager()
    while True:
        #task = mgr.findProcessingTask() 
        for task in mgr.findProcessingTasks():
            #有进行中的任务
            print "TaskManager->Find processing task tid:{0}".format(task["tid"])
            mgr.executeTask(task)
            time.sleep(5)
            #continue
        task = mgr.findSpareTask()
        if task is not None:
            print "Find spare task tid:{0}".format(task["tid"])
            mgr.executeTask(task)
            time.sleep(5)
