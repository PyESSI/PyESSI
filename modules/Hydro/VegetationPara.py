# -*- coding: utf-8 -*-
"""
Created Jan 2018

@author: Hao Chen

Class:
    VegInfo
        functions:
            __init__(self)
            ReadVegFile(self, vegFilename)

Functions:
    GetVegTypeName(VegTypeID)


"""

# load needed python modules
import os
import util.config


class VegInfo:
    def __init__(self, vtn, vfd):
        self.Veg_Name = ""
        self.Albedo = []
        self.LAI = []
        self.CoverDeg = []
        self.LAIMX = 0.
        self.LAIMN = 0.
        self.doffset = 0.
        self.InitVWC = 0.
        self.dManning_n = 0.05

        self.vegTypename = vtn
        self.vegFileDict = vfd

    def ReadVegFile(self, vegFilename):
        vegInfos = self.vegFileDict[vegFilename]
        self.Veg_Name = vegInfos[0].split('\n')[0].split(':')[1].strip()
        self.LAIMX = float(vegInfos[1].split('\n')[0].split(':')[1].strip())
        self.LAIMN = float(vegInfos[2].split('\n')[0].split(':')[1].strip())
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