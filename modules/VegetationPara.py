# -*- coding: utf-8 -*-
"""
Created Jan 2018

@author: Hao Chen

Functions:
    class: VegInfo
    GetVegTypeName(VegTypeID)


"""


# load needed python modules
import os
import utils.config


class VegInfo:
    def __init__(self):
        self.Veg_Name = ""
        self.Albedo = []
        self.LAI = []
        self.CoverDeg = []
        self.LAIMAX = 0.
        self.LAIMIN = 0.
        self.doffset = 0.
        self.InitVWC = 0.
        self.dManning_n = 0.05


    def ReadVegFile(self,vegFilename):
        if os.path.exists(utils.config.workSpace + os.sep + 'Vegetation' + os.sep + vegFilename):
            vegInfos = open(utils.config.workSpace + os.sep + 'Vegetation' + os.sep +vegFilename,'r').readlines()
            self.Veg_Name = vegInfos[0].split('\n')[0].split(':')[1].strip()
            self.LAIMAX = float(vegInfos[1].split('\n')[0].split(':')[1].strip())
            self.LAIMIN = float(vegInfos[2].split('\n')[0].split(':')[1].strip())
            self.doffse = float(vegInfos[3].split('\n')[0].split(':')[1].strip())
            self.InitVWC = 0.
            self.dManning_n = float(vegInfos[4].split('\n')[0].split(':')[1].strip())
            self.LAI = []
            self.Albedo = []
            self.CoverDeg = []
            for i in range(12):
                self.LAI.append(float(vegInfos[5].split('\n')[0].split(':')[1].strip().split()[i]))
                self.Albedo.append(float(vegInfos[6].split('\n')[0].split(':')[1].strip().split()[i]))
                self.CoverDeg.append(float(vegInfos[7].split('\n')[0].split(':')[1].strip().split()[i]))
        else:
            print('Vegetation info File does not exist!')


def GetVegTypeName(VegTypeID):
    if os.path.exists(utils.config.workSpace + os.sep + 'LookupTable' + os.sep + 'LulcType.txt'):
        vegTypeInfos = open(utils.config.workSpace + os.sep + 'LookupTable' + os.sep + 'LulcType.txt','r').readlines()
        vegIdName = []
        for i in range(len(vegTypeInfos)):
            vegIdName.append((vegTypeInfos[i].split('\n')[0].split('\t')[0].strip(),vegTypeInfos[i].split('\n')[0].split('\t')[1].strip()))
        vegTypeName = dict(vegIdName)
        return vegTypeName[str(VegTypeID)]