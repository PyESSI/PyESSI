# -*- coding: utf-8 -*-

"""
@Class: DEMRiverNet
@Author: Huiran Gao
@Functions:
    基于TauDEM提取河网
    class name: DEMStreamNet
    Function:   (1)填洼处理              Fill
                (2)计算流向              FlowDirD8， FlowDirDinf
                (3)计算水流累积矩阵       FlowAccD8
                (4)计算河网顺序          GridNet
                (5)修正流域入水口         MoveOutlet
                (6)提取河网             StreamNet

Created: 2018-02-13
Revised:
"""

import os
import subprocess


class DEMRiverNet:
    def __init__(self):
        self.workDir = ""  # Data direction
        self.dem = ""  # Input DEM (GeoTIFF file)
        self.np = 0  # Number of parallel processors
        self.threshold = 0
        self.outlet = None
        self.streamSkeleton = None

        # Output
        self.filledDem = ""
        self.flowDir = ""
        self.slope = ""
        self.acc = ""
        self.streamRaster = ""
        self.flowDirDinf = ""
        self.slopeDinf = ""
        self.flowPath = ""
        self.tLenFlowPath = ""
        # self.weightDinf = ""
        # self.dirCodeDinf = ""
        self.modifiedOutlet = ""
        self.streamOrder = ""
        self.chNetwork = ""
        self.chCoord = ""
        self.streamNet = ""
        self.subbasin = ""

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                Function：Pits remove                   +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def Fill(self, mpiexeDir=None, exeDir=None):
        os.chdir(self.workDir)
        if exeDir is not None:
            exe = exeDir + os.sep + "PitRemove"
        else:
            exe = "PitRemove"
        if self.np == 0:
            raise Exception("np must larger than zero.", self.np)
        strCmd = "mpiexec -n %d %s -z %s -fel %s" % (self.np, exe, self.dem, self.filledDem)
        if mpiexeDir is not None:
            strCmd = mpiexeDir + os.sep + strCmd
        print(strCmd)
        process = subprocess.Popen(strCmd, shell=True, stdout=subprocess.PIPE)
        print(process.stdout.readlines())

    # / *++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                                   +
    # +                Function：Calculating D8 and Dinf flow direction                   +
    # +                                                                                   +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                          TauDEM D8算法栅格水流流向定义                                +
    # +		                           4   3   2                                          +
    # +		                           5   X   1	                                      +
    # +		                           6   7   8                                          +
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def FlowDirD8(self, mpiexeDir=None, exeDir=None):
        os.chdir(self.workDir)
        if exeDir is not None:
            exe = exeDir + os.sep + "D8FlowDir"
        else:
            exe = "D8FlowDir"
        if self.np == 0:
            raise Exception("np must larger than zero.", self.np)
        strCmd = "mpiexec -n %d %s -fel %s -p %s  -sd8 %s" % (self.np, exe, self.filledDem, self.flowDir, self.slope)
        if mpiexeDir is not None:
            strCmd = mpiexeDir + os.sep + strCmd
        print(strCmd)
        process = subprocess.Popen(strCmd, shell=True, stdout=subprocess.PIPE)
        print(process.stdout.readlines())

    def FlowDirDinf(self, mpiexeDir=None, exeDir=None):
        '''
        Dinf flow direction
        :param mpiexeDir:
        :param exeDir:
        :return: flowDir.tif, slope.tif
        '''
        os.chdir(self.workDir)
        if exeDir is not None:
            exe = exeDir + os.sep + "DinfFlowDir"
        else:
            exe = "DinfFlowDir"
        if self.np == 0:
            raise (Exception("np must larger than zero.", self.np))
        strCmd = "mpiexec -n %d %s -fel %s -ang %s -slp %s" % (
            self.np, exe, self.filledDem, self.flowDirDinf, self.slopeDinf)
        if mpiexeDir is not None:
            strCmd = mpiexeDir + os.sep + strCmd
        print(strCmd)
        process = subprocess.Popen(strCmd, shell=True, stdout=subprocess.PIPE)
        print(process.stdout.readlines())

    # / *++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                                   +
    # +                Function：D8 flow accumulation                                     +
    # +                                                                                   +
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def FlowAccD8(self, mpiexeDir=None, exeDir=None):
        '''
        D8 flow accumulation
        :param mpiexeDir:
        :param exeDir:
        :return: Acc.tif
        '''
        os.chdir(self.workDir)
        if exeDir is not None:
            exe = exeDir + os.sep + "AreaD8"
        else:
            exe = "AreaD8"
        if self.outlet is not None:
            if self.streamSkeleton is not None:
                strCmd = "mpiexec -n %d %s -p %s -o %s -wg %s -ad8 %s -nc" % (
                    self.np, exe, self.flowDir, self.outlet, self.streamSkeleton, self.acc)
            else:
                strCmd = "mpiexec -n %d %s -p %s -o %s -ad8 %s -nc" % (
                    self.np, exe, self.flowDir, self.outlet, self.acc)
        else:
            if self.streamSkeleton is not None:
                strCmd = "mpiexec -n %d %s -p %s -wg %s -ad8 %s -nc" % (
                    self.np, exe, self.flowDir, self.streamSkeleton, self.acc)
            else:
                strCmd = "mpiexec -n %d %s -p %s -ad8 %s -nc" % (self.np, exe, self.flowDir, self.acc)
        if self.np == 0:
            raise Exception("np must larger than zero.", self.np)
        # -nc means donot consider edge contaimination
        if mpiexeDir is not None:
            strCmd = mpiexeDir + os.sep + strCmd
        print(strCmd)
        process = subprocess.Popen(strCmd, shell=True, stdout=subprocess.PIPE)
        print(process.stdout.readlines())

    # / *++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                                       +
    # +                Function：Generating stream grid net                                   +
    # +                (1) the longest flow path along D8 flow directions to each grid cell   +
    # +                (2) the total length of all flow paths that end at each grid cell      +
    # +                (3) the grid network order.                                            +
    # +                                                                                       +
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def GridNet(self, mpiexeDir=None, exeDir=None):
        '''
        Generating stream grid net
        :param mpiexeDir:
        :param exeDir:
        :return:
        '''
        os.chdir(self.workDir)
        if exeDir is not None:
            exe = exeDir + os.sep + "GridNet"
        else:
            exe = "GridNet"
        strCmd = "mpiexec -n %d %s -p %s -plen %s -tlen %s -gord %s" % (
            self.np, exe, self.flowDir, self.flowPath, self.tLenFlowPath, self.streamOrder)
        if mpiexeDir is not None:
            strCmd = mpiexeDir + os.sep + strCmd
        if self.np == 0:
            raise Exception("np must larger than zero.", self.np)
        print(strCmd)
        process = subprocess.Popen(strCmd, shell=True, stdout=subprocess.PIPE)
        print(process.stdout.readlines())

    # / *++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                                   +
    # +                Function：Generating stream skeleton                               +
    # +                                                                                   +
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def StreamSkeleton(self, mpiexeDir=None, exeDir=None):
        '''
        Generating stream skeleton
        :param mpiexeDir:
        :param exeDir:
        :return: streamSkeleton.tif
        '''
        os.chdir(self.workDir)
        if exeDir is not None:
            exe = exeDir + os.sep + "PeukerDouglas"
        else:
            exe = "PeukerDouglas"
        strCmd = "mpiexec -n %d %s -fel %s -ss %s" % (self.np, exe, self.filledDem, self.streamSkeleton)
        if mpiexeDir is not None:
            strCmd = mpiexeDir + os.sep + strCmd
        if self.np == 0:
            raise Exception("np must larger than zero.", self.np)
        print(strCmd)
        process = subprocess.Popen(strCmd, shell=True, stdout=subprocess.PIPE)
        print(process.stdout.readlines())

    # / *++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                                   +
    # +                Function：Drop analysis to select optimal threshold                +
    # +                                                                                   +
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def DropAnalysis(self, drpfile, minthresh, maxthresh, numthresh, logspace, mpiexeDir=None, exeDir=None):
        '''
        Drop analysis to select optimal threshold
        :param drpfile:
        :param minthresh:
        :param maxthresh:
        :param numthresh:
        :param logspace:
        :param mpiexeDir:
        :param exeDir:
        :return:
        '''
        os.chdir(self.workDir)
        if exeDir is not None:
            exe = exeDir + os.sep + "DropAnalysis"
        else:
            exe = "DropAnalysis"
        strCmd = "mpiexec -n %d %s -fel %s -p %s -ad8 %s -ssa %s -o %s -drp %s -par %f %f %f" % (
            self.np, exe, self.filledDem, self.flowDir, self.acc, self.acc, self.modifiedOutlet, drpfile, minthresh,
            maxthresh, numthresh)
        if logspace == 'false':
            strCmd = strCmd + ' 1'
        else:
            strCmd = strCmd + ' 0'
        if mpiexeDir is not None:
            strCmd = mpiexeDir + os.sep + strCmd
        if self.np == 0:
            raise Exception("np must larger than zero.", self.np)
        print(strCmd)
        process = subprocess.Popen(strCmd, shell=True, stdout=subprocess.PIPE)
        print(process.stdout.readlines())

    # / *++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                                   +
    # +                Function：Generating stream raster initially                       +
    # +                                                                                   +
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def StreamRaster(self, mpiexeDir=None, exeDir=None):
        '''
        Generating stream raster initially
        :param mpiexeDir:
        :param exeDir:
        :return: streamRaster
        '''
        os.chdir(self.workDir)
        if exeDir is not None:
            exe = exeDir + os.sep + "Threshold"
        else:
            exe = "Threshold"
        strCmd = "mpiexec -n %d %s -ssa %s -thresh %s  -src %s" % (
            self.np, exe, self.acc, str(self.threshold), self.streamRaster)
        if mpiexeDir is not None:
            strCmd = mpiexeDir + os.sep + strCmd
        if self.np == 0:
            raise Exception("np must larger than zero.", self.np)
        print(strCmd)
        process = subprocess.Popen(strCmd, shell=True, stdout=subprocess.PIPE)
        print(process.stdout.readlines())

    # / *++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                                   +
    # +                Function：Moving outlet to stream                                  +
    # +                                                                                   +
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def MoveOutlet(self, mpiexeDir=None, exeDir=None):
        '''
        Moving outlet to stream pixel
        :param mpiexeDir:
        :param exeDir:
        :return:
        '''
        os.chdir(self.workDir)
        if exeDir is not None:
            exe = exeDir + os.sep + "MoveOutletsToStreams"
        else:
            exe = "MoveOutletsToStreams"
        strCmd = "mpiexec -n %d %s -p %s -src %s -o %s -om %s" % (
            self.np, exe, self.flowDir, self.streamRaster, self.outlet, self.modifiedOutlet)
        if mpiexeDir is not None:
            strCmd = mpiexeDir + os.sep + strCmd
        if self.np == 0:
            raise Exception("np must larger than zero.", self.np)
        print(strCmd)
        process = subprocess.Popen(strCmd, shell=True, stdout=subprocess.PIPE)
        print(process.stdout.readlines())

    # / *++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                                   +
    # +                Function：Generating stream net                                    +
    # +                                                                                   +
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def StreamNet(self, mpiexeDir=None, exeDir=None):
        '''
        Generating stream net
        :param mpiexeDir:
        :param exeDir:
        :return:
        '''
        os.chdir(self.workDir)
        if exeDir is not None:
            exe = exeDir + os.sep + "StreamNet"
        else:
            exe = "StreamNet"
        strCmd = "mpiexec -n %d %s -fel %s -p %s -ad8 %s -src %s -o %s  -ord %s -tree %s -coord %s -net %s -w %s" % (
            self.np, exe, self.filledDem, self.flowDir, self.acc, self.streamRaster, self.modifiedOutlet,
            self.streamOrder, self.chNetwork, self.chCoord, self.streamNet, self.subbasin)
        if mpiexeDir is not None:
            strCmd = mpiexeDir + os.sep + strCmd
        if self.np == 0:
            raise Exception("np must larger than zero.", self.np)
        print(strCmd)
        process = subprocess.Popen(strCmd, shell=True, stdout=subprocess.PIPE)
        print(process.stdout.readlines())
