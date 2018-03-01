# -*- coding: utf-8 -*-
"""
Created Jan 2018

@author: Hao Chen

Functions:
    class: SoilInfo
    GetSoilTypeName(SoilTypeID)


"""


# load needed python modules
import os
import utils.config


class CHydroSimulate:
    def __init__(self):
        self.m_OutRow = 0
        self.m_OutCol = 0

    #/ *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #+                                                        +
    #+                读入全流域栅格汇流参数文件 +
    #+                                                        +
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #+               读入栅格汇流最优次序参数文件 +
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def ReadInRoutingPara(self):
        bret = False
        self.m_OutRow = 0
        self.m_OutCol = 0
        strFileName = open(utils.config.workSpace + os.sep + 'DEM'+ os.sep + utils.config.DEMFileName.split('.')[0] + '_gud.txt')

        bret = True

        return bret



    def StormRunoffSim_Horton(self):
        print('StormRunoffSim_Horton')

    def StormRunoffSim_GreenAmpt(self):
        print('StormRunoffSim_GreenAmpt')

    #/ *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #+                                                        +
    #+            长时段降雨～径流过程模拟函数定义 +
    #+                                                        +
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def LongTermRunoffSimulate(self):
        if utils.config.SurfRouteMethod == 1:
            if self.ReadInRoutingPara():
                print('LongTermRunoffSimulate')
