#!/bin/python2.7
#coding:utf-8
'''
将待养账号导入数据库中
'''

import os
import sys
import MySQLdb
from MySQLdb import cursors
import argparse
import traceback

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'../config'))
from cfg_db import *



def get_db():
    mysql_host = cfg_mysql["host"]
    mysql_user = cfg_mysql["user"]
    mysql_passwd = cfg_mysql["pass"]
    mysql_db = cfg_mysql["db"]
    _mysql = MySQLdb.connect(host=mysql_host,user=mysql_user,passwd=mysql_passwd,db=mysql_db,charset='utf8',cursorclass=MySQLdb.cursors.DictCursor)
    return _mysql


def user_insert(cursor, platform, user, pwd, utype):
    
    sql = "INSERT INTO m_app_user(platform,user,pass,utype) VALUES('{0}','{1}','{2}',{3})".format(platform,user,pwd,utype)
    cursor.execute(sql)


def parse_args():
    parser = argparse.ArgumentParser(description="养号账号入库")
    parser.add_argument('-f', action="store",dest='fpath',
                        default='weibo.txt', type=str,
                        help='账号文件，每行为:user,pass')
    
    parser.add_argument('-p', action="store", dest='platform',
                        default='douyin', type=str,
                        help='平台名称：douyin,huoshan,huajiao,kuaishou,douyu,huya')
    
    parser.add_argument('-t', action="store", dest='utype',
                        default=1, type=int,
                        help='账号类型：0手机，1微博，2企鹅, 3微信')
    
    args = parser.parse_args(sys.argv[1:])
    return args

def main():
    args = parse_args()
    platform = args.platform
    utype = args.utype
    db = get_db()
    cursor = db.cursor()
    f  = open(args.fpath,"r")
    for line in f.readlines():
        line = line.strip("\n").strip("\t").strip(" ")
        info = line.split("^")
        if len(info) != 2:
            print "Wrong line :"+line
            continue
        user = info[0]
        pwd = info[1]
        try:
            user_insert(cursor,platform,user,pwd,utype)
            print "Insert user:"+user
        except:
            traceback.print_exc()
    print "Done."


if __name__ == "__main__":
    main()
