#!/bin/python
'''
各种任务控制基类,需要协调设备、网络和动作的工作。暂不考虑优先级问题。
'''

class TaskerBase:
    def __init__(self,rd,task):
        self._task = task #任务信息，json数据
        self._rd = rd #redis客户端
    
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

    
