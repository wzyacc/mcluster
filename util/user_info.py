#!/bin/python2.7
#coding:utf-8
'''
账号相关辅助函数
'''
import os
import sys
import pdb
import json
import time
import datetime
import MySQLdb
from MySQLdb import cursors

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'../config'))
from cfg_db import *




def get_db():
    mysql_host = cfg_mysql["host"]
    mysql_user = cfg_mysql["user"]
    mysql_passwd = cfg_mysql["pass"]
    mysql_db = cfg_mysql["db"]
    _mysql = MySQLdb.connect(host=mysql_host,user=mysql_user,passwd=mysql_passwd,db=mysql_db,charset='utf8',cursorclass=MySQLdb.cursors.DictCursor)
    return _mysql



def get_unlogin_user(platform,num=1):
    db = get_db()
    cursor = db.cursor()
    sql = "SELECT * FROM m_app_user WHERE platform='{0}' AND is_login=0 AND is_valid=1 LIMIT 0,{1}".format(platform,num)
    cursor.execute(sql)
    rets = cursor.fetchall()
    for ret in rets:
        if ret.has_key("ctime"):
            del ret["ctime"]
    return rets

