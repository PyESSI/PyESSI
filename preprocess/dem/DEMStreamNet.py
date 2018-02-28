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
from osgeo import gdal
from utils.fileIO import readRaster, writeRaster


class DEMRiverNet:
    def __init__(self):
        self.workDir = ""  # Data direction
        self.dem = ""  # Input DEM (GeoTIFF file)
        self.np = 0  # Number of parallel processors
        self.threshold = 0
        self.outlet = None
        self.streamSkeleton = None
        self.noDataValue = None

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
        self.modifiedOutlet = ""
        self.streamOrder = ""
        self.chNetwork = ""
        self.chCoord = ""
        self.streamNet = ""
        self.subbasin = ""
        self.watershed = ""

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
        strCmd = "mpiexec -n %d %s -z %s -fel %s" % (
            self.np, exe, self.workDir + os.sep + self.dem, self.workDir + os.sep + self.filledDem)
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
        strCmd = "mpiexec -n %d %s -fel %s -p %s  -sd8 %s" % (
            self.np, exe, self.workDir + os.sep + self.filledDem, self.workDir + os.sep + self.flowDir,
            self.workDir + os.sep + self.slope)
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
            self.np, exe, self.workDir + os.sep + self.filledDem, self.workDir + os.sep + self.flowDirDinf,
            self.workDir + os.sep + self.slopeDinf)
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
                    self.np, exe, self.workDir + os.sep + self.flowDir, self.workDir + os.sep + self.outlet,
                    self.workDir + os.sep + self.streamSkeleton, self.workDir + os.sep + self.acc)
            else:
                strCmd = "mpiexec -n %d %s -p %s -o %s -ad8 %s -nc" % (
                    self.np, exe, self.workDir + os.sep + self.flowDir, self.workDir + os.sep + self.outlet,
                    self.workDir + os.sep + self.acc)
        else:
            if self.streamSkeleton is not None:
                strCmd = "mpiexec -n %d %s -p %s -wg %s -ad8 %s -nc" % (
                    self.np, exe, self.workDir + os.sep + self.flowDir, self.workDir + os.sep + self.streamSkeleton,
                    self.workDir + os.sep + self.acc)
            else:
                strCmd = "mpiexec -n %d %s -p %s -ad8 %s -nc" % (
                    self.np, exe, self.workDir + os.sep + self.flowDir, self.workDir + os.sep + self.acc)
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
            self.np, exe, self.workDir + os.sep + self.flowDir, self.workDir + os.sep + self.flowPath,
            self.workDir + os.sep + self.tLenFlowPath, self.workDir + os.sep + self.streamOrder)
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
        strCmd = "mpiexec -n %d %s -fel %s -ss %s" % (
            self.np, exe, self.workDir + os.sep + self.filledDem, self.workDir + os.sep + self.streamSkeleton)
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
            self.np, exe, self.workDir + os.sep + self.filledDem, self.workDir + os.sep + self.flowDir,
            self.workDir + os.sep + self.acc, self.workDir + os.sep + self.acc,
            self.workDir + os.sep + self.modifiedOutlet, drpfile, minthresh,
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
            self.np, exe, self.workDir + os.sep + self.acc, str(self.threshold),
            self.workDir + os.sep + self.streamRaster)
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
            self.np, exe, self.workDir + os.sep + self.flowDir, self.workDir + os.sep + self.streamRaster,
            self.workDir + os.sep + self.outlet, self.workDir + os.sep + self.modifiedOutlet)
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
            self.np, exe, self.workDir + os.sep + self.filledDem, self.workDir + os.sep + self.flowDir,
            self.workDir + os.sep + self.acc, self.workDir + os.sep + self.streamRaster,
            self.workDir + os.sep + self.modifiedOutlet,
            self.workDir + os.sep + self.streamOrder, self.workDir + os.sep + self.chNetwork,
            self.workDir + os.sep + self.chCoord, self.workDir + os.sep + self.streamNet,
            self.workDir + os.sep + self.subbasin)
        if mpiexeDir is not None:
            strCmd = mpiexeDir + os.sep + strCmd
        if self.np == 0:
            raise Exception("np must larger than zero.", self.np)
        print(strCmd)
        process = subprocess.Popen(strCmd, shell=True, stdout=subprocess.PIPE)
        print(process.stdout.readlines())

    # / *++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                                   +
    # +                Function：Watershed delineation                                    +
    # +                                                                                   +
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def Watershed(self, exeDir=None):
        '''
        Watershed delineation
        :param mpiexeDir:
        :param exeDir:
        :return:
        '''
        os.chdir(self.workDir)
        if exeDir is not None:
            exe = exeDir + os.sep + "GageWatershed"
        else:
            exe = "GageWatershed"
        strCmd = "%s -p %s -o %s -gw %s" % (
            exe, self.workDir + os.sep + self.flowDir, self.workDir + os.sep + self.modifiedOutlet,
            self.workDir + os.sep + self.watershed)
        if self.np == 0:
            raise Exception("np must larger than zero.", self.np)
        print(strCmd)
        process = subprocess.Popen(strCmd, shell=True, stdout=subprocess.PIPE)
        print(process.stdout.readlines())

    # / *++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                                   +
    # +                Function：lip raster by watershed boundary                         +
    # +                                                                                   +
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def ClipRasterByWatershed(self):
        '''
        Clip raster by watershed boundary
        :return:
        '''
        if self.noDataValue is None:
            raise Exception("noDataValue must not be None.", self.noDataValue)

        watershedFile = self.workDir + os.sep + self.watershed
        print(watershedFile)
        wsd = readRaster(watershedFile).data
        rows = readRaster(watershedFile).nRows
        cols = readRaster(watershedFile).nCols
        geotrans = readRaster(watershedFile).geotrans
        srs = readRaster(watershedFile).srs
        noDataValue_ws = readRaster(watershedFile).noDataValue

        filledDemFile = self.workDir + os.sep + self.filledDem
        flowDirFile = self.workDir + os.sep + self.flowDir
        slopeFile = self.workDir + os.sep + self.slope
        accFile = self.workDir + os.sep + self.acc
        streamRasterFile = self.workDir + os.sep + self.streamRaster
        flowDirDinfFile = self.workDir + os.sep + self.flowDirDinf
        slopeDinfFile = self.workDir + os.sep + self.slopeDinf
        flowPathFile = self.workDir + os.sep + self.flowPath
        tLenFlowPathFile = self.workDir + os.sep + self.tLenFlowPath
        streamOrderFile = self.workDir + os.sep + self.streamOrder

        fil = readRaster(filledDemFile).data
        fld = readRaster(flowDirFile).data
        slp = readRaster(slopeFile).data
        acm = readRaster(accFile).data
        stm = readRaster(streamRasterFile).data
        fdd = readRaster(flowDirDinfFile).data
        spd = readRaster(slopeDinfFile).data
        flp = readRaster(flowPathFile).data
        tlf = readRaster(tLenFlowPathFile).data
        sto = readRaster(streamOrderFile).data

        for i in range(rows):
            for j in range(cols):
                if wsd[i][j] == noDataValue_ws:
                    fil[i][j] = self.noDataValue
                    fld[i][j] = self.noDataValue
                    slp[i][j] = self.noDataValue
                    acm[i][j] = self.noDataValue
                    stm[i][j] = self.noDataValue
                    fdd[i][j] = self.noDataValue
                    spd[i][j] = self.noDataValue
                    flp[i][j] = self.noDataValue
                    tlf[i][j] = self.noDataValue
                    sto[i][j] = self.noDataValue
                else:
                    continue

        writeRaster(filledDemFile, rows, cols, fil, geotrans, srs, self.noDataValue, gdal.GDT_Float32)
        writeRaster(flowDirFile, rows, cols, fld, geotrans, srs, self.noDataValue, gdal.GDT_Float32)
        writeRaster(slopeFile, rows, cols, slp, geotrans, srs, self.noDataValue, gdal.GDT_Float32)
        writeRaster(accFile, rows, cols, acm, geotrans, srs, self.noDataValue, gdal.GDT_Float32)
        writeRaster(streamRasterFile, rows, cols, stm, geotrans, srs, self.noDataValue, gdal.GDT_Float32)
        writeRaster(flowDirDinfFile, rows, cols, fdd, geotrans, srs, self.noDataValue, gdal.GDT_Float32)
        writeRaster(slopeDinfFile, rows, cols, spd, geotrans, srs, self.noDataValue, gdal.GDT_Float32)
        writeRaster(flowPathFile, rows, cols, flp, geotrans, srs, self.noDataValue, gdal.GDT_Float32)
        writeRaster(tLenFlowPathFile, rows, cols, tlf, geotrans, srs, self.noDataValue, gdal.GDT_Float32)
        writeRaster(streamOrderFile, rows, cols, sto, geotrans, srs, self.noDataValue, gdal.GDT_Float32)

