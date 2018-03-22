#!/bin/python
#coding:utf8
'''
任务监控程序，包括数据库任务状态的迁移，任务结束垃圾回收，异常状态监测等（哎，辛苦了）
'''
import os
import sys
import pdb
import time
import redis
import MySQLdb
from MySQLdb import cursors
import json
import datetime
import base64
import random

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),"../../config"))

from cfg_db import *



class TaskMonitor:
    def __init__(self):
        self._rd = redis.Redis(host=cfg_redis["host"],port=cfg_redis["port"])
        mysql_host = cfg_mysql["host"]
        mysql_user = cfg_mysql["user"]
        mysql_passwd = cfg_mysql["pass"]
        mysql_db = cfg_mysql["db"]
        self._mysql = MySQLdb.connect(host=mysql_host,user=mysql_user,passwd=mysql_passwd,db=mysql_db,charset='utf8',cursorclass=MySQLdb.cursors.DictCursor)
        self._cache_status = {} #任务状态更新缓存
    
    def group_transfer(self):
        #设备分组数据,忽略锁的问题，不存在严格同步问题
        #TODO:分组迁移存在问题，设备多分组问题
        #sql = 'SELECT * FROM m_group_dev LEFT JOIN `m_group` ON m_group_dev.gid=`m_group`.gid LEFT JOIN m_device ON m_group_dev.device_id=m_device.device_id' 
        sql = 'SELECT * FROM m_device'
        cursor = self._mysql.cursor()
        cursor.execute(sql);
        rets = cursor.fetchall()
        devs = {}
        for ret in rets:
            gid = ret["gid"]
            if devs.has_key(gid):
                devs[gid].append(ret)
            else:
                devs[gid] = [ret]

        for k,v in devs.iteritems():
            self._rd.hset(cfg_rd_rdg,k,v)


    def task_transfer(self):
        #将mysql数据中的任务放到redis中，将redis中的任务状态同步到mysql中
        

        #将新任务插入到redis中
        sql = "SELECT * FROM m_task_list LEFT JOIN m_task ON m_task_list.mid=m_task.mid"
        cursor = self._mysql.cursor()
        cursor.execute(sql)
        tasks = cursor.fetchall()
        for task in tasks:
            status = task["status"]
            if status != 0: #不是新任务
                continue
            rd_task = self._rd.hget(cfg_rd_task,task["tid"])
            if rd_task != None: #已经同步过了
                continue

            #新任务，qqbrowser需要数据准备
            if task["act"] == "app-idle-qqbrowser":
                status = self._prepare_app_idle_qqbrowser(task)
                if not status: #如果初始化失败，中止，这里考虑到设备繁忙的情况，oarea可能正在占用
                    continue
            
            #新任务，疯转头条需要数据准备
            if task["act"] == "app-idle-fztt":
                status = self._prepare_app_idle_fztt(task)
                if not status: #如果初始化失败，中止，这里考虑到设备繁忙的情况，oarea可能正在占用
                    continue
            
            #新任务，疯转头条需要数据准备
            if task["act"] == "app-idle-miaopai":
                status = self._prepare_app_idle_miaopai(task)
                if not status: #如果初始化失败，中止，这里考虑到设备繁忙的情况，oarea可能正在占用
                    continue

            #新任务，放入redis中
            task["status"] = 100
            self._rd.hset(cfg_rd_task,task["tid"],task)
            print "TaskMonitor->New task for tid:"+task["tid"]
        
        
        #将redis中的任务状态同步到mysql中
        task_keys = self._rd.hkeys(cfg_rd_task)
        for k in task_keys:
            tid = k
            task = self._rd.hget(cfg_rd_task,tid)
            if not task:
                print "Task is None for tid:{0}".format(tid)
            task = eval(task)
            status = task["status"]
            if status is not None and status == self._cache_status.get("status",None):#状态没变化
                continue
            sql = "UPDATE m_task_list SET status={0} WHERE tid='{1}'".format(status,tid)
            cursor.execute(sql)

    def task_recycle(self):
        #将新任务插入到redis中
        cursor = self._mysql.cursor()
        task_keys = self._rd.hkeys(cfg_rd_task)
        for k in task_keys:
            tid = k
            task = self._rd.hget(cfg_rd_task,tid)
            if not task:
                print "Task is None for tid:{0}".format(tid)
            task = eval(task)
            status = task["status"]
            if status >=0 and status < 200:
                continue
            if status < 0: #遇到错误了，跳过,由expt_handle处理
                continue
            
            #任务完成备份数据，如果有 
            self._backup_data()

            sql = "UPDATE m_task_list SET status={0} WHERE tid='{1}'".format(status,tid)
            cursor.execute(sql)
            print "Task recycle tid:{0},status:{1}".format(tid,status)
            #考虑轮次问题
            round_n = task["round_n"]
            if round_n <= task["cur_step"]+1:
                sql = "UPDATE m_task_list SET cur_step={0},status={1} WHERE tid='{2}'".format(round_n,status,tid)
                cursor.execute(sql)
                self._rd.hdel(cfg_rd_task,tid)
                #设置设备繁忙状态
                self._set_no_busy(task)
                continue
            #新一轮
            if task["act"] == "app-idle-qqbrowser":
                status = self._prepare_app_idle_qqbrowser(task,False)
                if not status: #如果初始化失败，中止，这里考虑到设备繁忙的情况
                    print "TaskMonitor->app_idle_qqbrowser prepare data error!"
                    continue

            task["cur_step"] += 1
            task["status"] = 100
            self._rd.hset(cfg_rd_task,tid,task)
            #更新当前轮次和状态
            sql = "UPDATE m_task_list SET cur_step={0},status={1} WHERE tid='{2}'".format(task["cur_step"],status,tid)
            cursor.execute(sql)

    def _set_no_busy(self,task):
        #释放设备
        devs = task["devices"]
        for dev in devs:
            cip = dev["ip"]
            dev_attr_str = self._rd.hget(cfg_rd_device,cip)
            if not dev_attr_str or dev_attr_str == "":
                continue
            dev_attr = eval(dev_attr_str)
            if dev_attr.get("busy",None) != 1:
                continue
            dev_attr["busy"] = 0
            self._rd.hset(cfg_rd_device,cip,json.dumps(dev_attr))

    def _backup_data(self):
        #备份数据，目前是刷app激活能用到，暂时先写在这
        cursor = self._mysql.cursor()
        backup_keys = self._rd.hkeys(cfg_rd_act_appbackup)
        for k in backup_keys:
            cip = k #备份主键为手机ip
            data = self._rd.hget(cfg_rd_act_appbackup,k)
            if not data:
                continue
            js = eval(data)
            if not js:
                print "TaskMonitor->backup data is not json:"+data
                continue
            s_m_attrs = self._rd.hget(cfg_rd_device,cip)
            while not s_m_attrs:
                print "TaskMonitor->cip({0}) attrs is not found,waiting...".format(cip)
                time.sleep(1)
            m_attrs = eval(s_m_attrs)
            fake_attrs = m_attrs["fake_attrs"]
            #此处约定的格式行如：[{"imei":"111"},{"mac":"fjsldfl"}]，修改接口文档需改正
            imei = None
            while not imei:
                for k in fake_attrs:
                    if k.get("imei",None) != None:
                        imei = k["imei"]
                        break
                print "TaskMonitor->Prase imei for cip:"+cip
                time.sleep(1)
            oarea = self._rd.hget(cfg_rd_act_net_oarea,cip)
            #先允许oarea为空
            if not oarea:
                oarea = ''
            '''
            while not oarea:
                oarea = self._rd.hget(cfg_rd_act_net_oarea,cip)
                print "TaskMonitor->oarea not found for cip:"+cip
                time.sleep(1)
            '''
            tid_info = js["tid"]
            tid_lun = tid_info.split(":")
            tid = tid_lun[0]
            task = eval(self._rd.hget(cfg_rd_task,tid))
            
            act = task["act"]
            b64_attrs = base64.b64encode(s_m_attrs)
            #账号信息
            user = js.get("user","")
            utype = js.get("utype",0)
            platform = js.get("platform","")
            sql = "INSERT INTO `m_appbackup`(imei,act,oarea,attrs,data,user,utype,platform) VALUES('{0}','{1}','{2}','{3}','{4}')".format(imei,act,oarea,b64_attrs,js["app_data"],user,utype,platform)
            cursor.execute(sql)
            self._mysql.commit()
            sql = "UPDATE `m_app_user` SET is_login=1 WHERE user='{0}',utype={1},platform='{2}'".format(user,utype,platform)
            cursor.execute(sql)
            self._mysql.commit()
            self._rd.hdel(cfg_rd_act_appbackup,cip) #删除redis中临时备份信息
            self._rd.hdel(cfg_rd_act_net_oarea,cip) #删除redis中临时区域信息
    
    def _prepare_app_idle_miaopai(self,task,first=True):
        #first:是否是初始化任务
        #为“秒拍”初始化数据，包括设备信息，出口ip
        #检测设备是否繁忙
        
        gid = task["gid"]
        devs = self._rd.hget(cfg_rd_rdg,gid)
        if not devs or len(devs) == 0:
            print '分组内没有设备...'
            return False
        devs = eval(devs) 

        for dev in devs:
            cip = dev["ip"]
            dev_info = self._rd.hget(cfg_rd_device,cip)
            if not dev_info or dev_info == "":
                print "TaskMonitor->Can not find dev for cip:"+cip
                return False

            dev_info = eval(dev_info)
            busy = dev_info.get("busy",None)
            if first and busy and dev_info["busy"] != 0:
                print "TaskMonitor->app_idle_miaopai device is busy of cip:"+cip
                return False
        
        n_dev = len(devs)
        cursor = self._mysql.cursor()
        sql = "SELECT count(DISTINCT(imei)) as n FROM `m_appbackup` WHERE act='app-active-miaopai'"
        cursor.execute(sql)
        ret = cursor.fetchall()
        n_imei = ret[0]["n"]
        if n_imei < n_dev:
            print "TaskMonitor->app-idle-miaopai imeis less for devices!"
            return False
        sql = "SELECT DISTINCT imei,id FROM `m_appbackup` WHERE act='app-active-miaopai' GROUP BY imei"
        cursor.execute(sql)
        ret = cursor.fetchall()
        ids = []
        for r in ret:
            ids.append(str(r["id"]))
        hits = random.sample(ids,n_dev)
        
        sql = "SELECT id,imei,oarea,attrs FROM m_appbackup WHERE id IN({0})".format(",".join(hits))
        cursor.execute(sql)
        rets = cursor.fetchall()
        lst_fake = [] #虚拟信息
        for r in rets:
            attrs_str = base64.b64decode(r["attrs"])
            if not attrs_str or attrs_str == "":
                print "TaskMonitor->app-idle-miaopai attrs is None for id:"+str(r[id])
                return False
            attrs = eval(attrs_str)
            fake = {}
            fake["fake_attrs"] = attrs["fake_attrs"]
            fake["oarea"] = r["oarea"]
            lst_fake.append(fake)
        for i in range(len(devs)):
            cip = devs[i]["ip"]
            self._rd.hset(cfg_rd_app_idle_oarea,cip,lst_fake[i]["oarea"])
            self._rd.hset(cfg_rd_app_idle_dev,cip,json.dumps(lst_fake[i]["fake_attrs"]))
        return True

    def _prepare_app_idle_fztt(self,task,first=True):
        #first:是否是初始化任务
        #为“疯转头条”初始化数据，包括设备信息，出口ip
        #检测设备是否繁忙
        
        gid = task["gid"]
        devs = self._rd.hget(cfg_rd_rdg,gid)
        if not devs or len(devs) == 0:
            print '分组内没有设备...'
            return False
        devs = eval(devs) 

        for dev in devs:
            cip = dev["ip"]
            dev_info = self._rd.hget(cfg_rd_device,cip)
            if not dev_info or dev_info == "":
                print "TaskMonitor->Can not find dev for cip:"+cip
                return False

            dev_info = eval(dev_info)
            busy = dev_info.get("busy",None)
            if first and busy and dev_info["busy"] != 0:
                print "TaskMonitor->app_idle_qqbrowser device is busy of cip:"+cip
                return False
        
        n_dev = len(devs)
        cursor = self._mysql.cursor()
        sql = "SELECT count(DISTINCT(imei)) as n FROM `m_appbackup` WHERE act='app-active-fztt'"
        cursor.execute(sql)
        ret = cursor.fetchall()
        n_imei = ret[0]["n"]
        if n_imei < n_dev:
            print "TaskMonitor->app-idle-qqbrowser imeis less for devices!"
            return False
        sql = "SELECT DISTINCT imei,id FROM `m_appbackup` WHERE act='app-active-fztt' GROUP BY imei"
        cursor.execute(sql)
        ret = cursor.fetchall()
        ids = []
        for r in ret:
            ids.append(str(r["id"]))
        hits = random.sample(ids,n_dev)
        
        sql = "SELECT id,imei,oarea,attrs FROM m_appbackup WHERE id IN({0})".format(",".join(hits))
        cursor.execute(sql)
        rets = cursor.fetchall()
        lst_fake = [] #虚拟信息
        for r in rets:
            attrs_str = base64.b64decode(r["attrs"])
            if not attrs_str or attrs_str == "":
                print "TaskMonitor->app-idle-qqbrowser attrs is None for id:"+str(r[id])
                return False
            attrs = eval(attrs_str)
            fake = {}
            fake["fake_attrs"] = attrs["fake_attrs"]
            fake["oarea"] = r["oarea"]
            lst_fake.append(fake)
        for i in range(len(devs)):
            cip = devs[i]["ip"]
            self._rd.hset(cfg_rd_app_idle_oarea,cip,lst_fake[i]["oarea"])
            self._rd.hset(cfg_rd_app_idle_dev,cip,json.dumps(lst_fake[i]["fake_attrs"]))
        return True


    def _prepare_app_idle_qqbrowser(self,task,first=True):
        #first:是否是初始化任务
        #为qq浏览器初始化数据，包括设备信息，出口ip
        #检测设备是否繁忙
        
        gid = task["gid"]
        devs = self._rd.hget(cfg_rd_rdg,gid)
        if not devs or len(devs) == 0:
            print '分组内没有设备...'
            return False
        devs = eval(devs) 

        for dev in devs:
            cip = dev["ip"]
            dev_info = self._rd.hget(cfg_rd_device,cip)
            if not dev_info or dev_info == "":
                print "TaskMonitor->Can not find dev for cip:"+cip
                return False

            dev_info = eval(dev_info)
            busy = dev_info.get("busy",None)
            if first and busy and dev_info["busy"] != 0:
                print "TaskMonitor->app_idle_qqbrowser device is busy of cip:"+cip
                return False
        
        n_dev = len(devs)
        cursor = self._mysql.cursor()
        sql = "SELECT count(DISTINCT(imei)) as n FROM `m_appbackup` WHERE act='app-active-qqbrowser'"
        cursor.execute(sql)
        ret = cursor.fetchall()
        n_imei = ret[0]["n"]
        if n_imei < n_dev:
            print "TaskMonitor->app-idle-qqbrowser imeis less for devices!"
            return False
        sql = "SELECT DISTINCT imei,id FROM `m_appbackup` WHERE act='app-active-qqbrowser' GROUP BY imei"
        cursor.execute(sql)
        ret = cursor.fetchall()
        ids = []
        for r in ret:
            ids.append(str(r["id"]))
        hits = random.sample(ids,n_dev)
        
        sql = "SELECT id,imei,oarea,attrs FROM m_appbackup WHERE id IN({0})".format(",".join(hits))
        cursor.execute(sql)
        rets = cursor.fetchall()
        lst_fake = [] #虚拟信息
        for r in rets:
            attrs_str = base64.b64decode(r["attrs"])
            if not attrs_str or attrs_str == "":
                print "TaskMonitor->app-idle-qqbrowser attrs is None for id:"+str(r[id])
                return False
            attrs = eval(attrs_str)
            fake = {}
            fake["fake_attrs"] = attrs["fake_attrs"]
            fake["oarea"] = r["oarea"]
            lst_fake.append(fake)
        for i in range(len(devs)):
            cip = devs[i]["ip"]
            self._rd.hset(cfg_rd_app_idle_oarea,cip,lst_fake[i]["oarea"])
            self._rd.hset(cfg_rd_app_idle_dev,cip,json.dumps(lst_fake[i]["fake_attrs"]))
        return True
            

    def expt_handle(self):
        pass




if __name__ == '__main__':
    print 'starting...'
    tm = TaskMonitor()
    while True:
        tm.group_transfer()
        tm.task_transfer()
        tm.task_recycle()
        tm.expt_handle()
        time.sleep(3)

