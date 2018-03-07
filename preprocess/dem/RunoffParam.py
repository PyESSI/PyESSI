# -*- coding: utf-8 -*-

"""
@Class: RunoffParam
@Author: Huiran Gao
@Functions:
    汇流参数提取
    class name: RunoffParam
    Function:   (1)流域边界提取              WatershedBound
                (2)流域汇流栅格编码           RoutingGridCode
                (3)栅格汇流最优次序等级矩阵    RoutingOptimalOrder
                (4)栅格汇流最优次序矩阵       RoutingOptimalSequ
                (5)汇流栅格上下游节点         RoutingUDNode
                (6)计算栅格水流路径长度       RouteLength
                (7)计算栅格水流路径平均坡度    RouteMeanSlp
                (8)计算栅格汇流时间          RouteTime

Created: 2018-02-17
Revised:
"""

import os
import sys
import math
import numpy
import numba
from util.fileIO import *
from preprocess.dem.utils_dem import *


class RunoffParam:
    def __init__(self):
        self.workDir = ""    # working direction
        self.dem = ""        # Input dem (GeoTIFF file)
        self.flowDir = ""    # Input flow direction (GeoTIFF file)
        self.streamOrd = ""  # Input stream order (GeoTIFF file)
        self.outlet = ""     # Input outlet (Shape file)
        self.d8 = [1, 8, 7, 6, 5, 4, 3, 2]  # d8算法的8个流向(流出) TauDEM
        self.fd8 = [5, 4, 3, 2, 1, 8, 7, 6]  # d8算法的8个流向(流进) TauDEM
        self.subbasinsNum = 0

        # Parameter
        self.dKV = 0 # Velocity constant

        # Data info
        self.demData = None
        self.flowDirData = None
        self.streamOrdData = None
        self.rows = 0
        self.cols = 0
        self.geotrans = None
        self.srs = None
        self.noDataValue = None

        # Watershed
        self.outX = None
        self.outY = None
        self.ii = []  # 栅格数据队列,存放有入流关系的相邻栅格的坐标
        self.jj = []  # 栅格数据队列,存放有入流关系的相邻栅格的坐标

        # Output
        self.routingCode = None
        self.routingSequ = None
        self.routingOdr = None
        self.gridUD = None
        self.gridFlowLength = None
        self.gridMeanSlp = None
        self.routingTime = None
        self.wsm = None  # Data of watershedMask
        self.rtc = None  # Data of routingCode
        self.rsq = None  # Data of routingSequ
        self.ror = None  # Data of routingOdr
        self.gfl = None  # Data of gridFlowLength
        self.gms = None  # Data of gridMeanSlp
        self.rtt = None  # Data of routingTime

    # / *++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                                   +
    # +                            Function：Get base data                                +
    # +                                                                                   +
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def SetInfo(self):
        '''
        获取栅格数据信息
        :return:
        '''
        if self.workDir == "":
            raise Exception("workDir can not be empty.", self.workDir)
        if self.streamOrd == "" or self.flowDir == "" or self.dem == "":
            raise Exception("streamOrd, dem or flowDir can not be empty.", self.streamOrd, self.flowDir, self.dem)

        demFile = self.workDir + os.sep + self.dem
        flowDirFile = self.workDir + os.sep + self.flowDir
        streamOrdFile = self.workDir + os.sep + self.streamOrd
        self.demData = readRaster(demFile).data
        self.flowDirData = readRaster(flowDirFile).data
        self.streamOrdData = readRaster(streamOrdFile).data
        self.watershedData = readRaster(flowDirFile).data
        self.rows = readRaster(flowDirFile).nRows
        self.cols = readRaster(flowDirFile).nCols
        self.geotrans = readRaster(flowDirFile).geoTransform
        self.srs = readRaster(flowDirFile).srs
        self.noDataValue = readRaster(flowDirFile).noDataValue
        print(self.noDataValue)


    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                      +
    # +                      Function：Routing code                          +
    # +                                                                      +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def RoutingGridCode(self):
        '''
        流域汇流栅格编码，先行后列顺序编码
        :return:
        '''
        print("Calculating Routing code")
        if self.flowDirData is None:
            raise Exception("flowDirData can not be empty.", self.flowDirData)

        self.rtc = numpy.zeros((self.rows, self.cols))
        k = 1
        for m in range(self.rows):
            for n in range(self.cols):
                if (m * self.rows + n) % int(self.rows * self.cols / 100) == 0:
                    print("▋", end='')
                    sys.stdout.flush()
                if self.flowDirData[m][n] != self.noDataValue:
                    self.rtc[m][n] = k
                    k += 1
                else:
                    self.rtc[m][n] = self.noDataValue

        print()
        writeRaster(self.workDir + os.sep + self.routingCode, self.rows, self.cols, self.rtc, self.geotrans,
                       self.srs, self.noDataValue, gdal.GDT_Float32)
        return 0

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                      +
    # +      Function：Calculate routing order and routing sequence           +
    # +                                                                      +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def RoutingOptimalOrder(self):
        '''
        计算栅格汇流最优次序等级矩阵
        :return:
        '''
        print("Calculating routing order")
        if self.routingCode == None:
            raise Exception("routingCode can not be empty.", self.routingCode)
        else:
            self.rtc = readRaster(self.workDir + os.sep + self.routingCode).data

        self.ror = numpy.zeros((self.rows, self.cols))
        dMax = numpy.max(self.rtc)
        dMin = numpy.min(self.rtc)
        totnum = int(dMax)

        # 坐标初始化
        self.ii = numpy.zeros(totnum)
        self.jj = numpy.zeros(totnum)

        inum = 0
        totin = 1
        self.ii[0] = self.outX
        self.jj[0] = self.outY

        while inum < totin:
            if inum % int(dMax / 100) == 0:
                print("▋", end='')
                sys.stdout.flush()
            itet, pos = self.PixelFlowIn(int(self.ii[inum]), int(self.jj[inum]), totin, self.ror)
            # print(inum)
            # totin = pos
            totin += itet
            inum += 1

        print()
        print("inum: %s" % inum)
        for k in range(inum - 1, -1, -1):
            if k % int(inum / 100) == 0:
                print("▋", end='')
                sys.stdout.flush()
            dMax2 = 0
            n8, i8, j8 = self.PixelFlowIn_b(int(self.ii[k]), int(self.jj[k]), b=False)
            # print("n8: %d" % n8)
            for n in range(n8):
                if dMax2 <= self.ror[int(i8[n])][int(j8[n])]:
                    dMax2 = self.ror[int(i8[n])][int(j8[n])]
            # print(self.ii[k],self.jj[k],self.ror[int(self.ii[k])][int(self.jj[k])] + dMax + 1)
            self.ror[int(self.ii[k])][int(self.jj[k])] = self.ror[int(self.ii[k])][int(self.jj[k])] + dMax2 + 1

        inum = 0
        totin = 1
        self.ii[0] = self.outX
        self.jj[0] = self.outY
        print()
        while inum < totin:
            if inum % int(dMax / 100) == 0:
                print("▋", end='')
                sys.stdout.flush()
            itet, pos, pvalue = self.PixelRouteOrder(int(self.ii[inum]), int(self.jj[inum]), totin, self.ror)
            self.ror = pvalue
            # totin = pos
            totin += itet
            inum += 1

        for m in range(self.rows):
            for n in range(self.cols):
                if self.rtc[m][n] == self.noDataValue:
                    self.ror[m][n] = self.noDataValue
                else:
                    continue

        print()
        writeRaster(self.workDir + os.sep + self.routingOdr, self.rows, self.cols, self.ror, self.geotrans,
                       self.srs, self.noDataValue, gdal.GDT_Float32)
        return 0

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                      +
    # +      Function：Calculate routing order and routing sequence           +
    # +                                                                      +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def RoutingOptimalSequ(self):
        '''
        计算栅格汇流最优次序矩阵
        :return:
        '''
        print("Calculating routing sequence")
        if self.routingOdr == None:
            raise Exception("routingOdr can not be empty.", self.routingOdr)
        else:
            self.ror = readRaster(self.workDir + os.sep + self.routingOdr).data

        self.rsq = numpy.zeros((self.rows, self.cols))

        isequ = 1
        dMax = self.ror[self.outX][self.outY]
        # print("dMax: %d" % dMax)
        for dk in range(1, int(dMax + 1)):
            if dk % int(dMax / 100) == 0:
                print("▋", end='')
                sys.stdout.flush()
            for i in range(self.rows):
                for j in range(self.cols):
                    if self.rtc[i][j] != self.noDataValue:
                        if int(self.ror[i][j]) == dk and int(self.rsq[i][j]) == 0:
                            self.rsq[i][j] = isequ
                            isequ += 1
                    else:
                        self.rsq[i][j] = self.noDataValue

        print()
        writeRaster(self.workDir + os.sep + self.routingSequ, self.rows, self.cols, self.rsq, self.geotrans,
                       self.srs, self.noDataValue, gdal.GDT_Float32)
        return 0

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                      +
    # +       Function：Calculate upslope and downslope node of routing grid       +
    # +                                                                      +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def RoutingUDNode(self):
        '''
        计算汇流栅格上下游节点
        :return:
        '''
        print("Calculating upslope and downslope node of routing grid")
        if self.routingSequ == None:
            raise Exception("routingSequ can not be empty.", self.routingSequ)
        else:
            self.rsq = readRaster(self.workDir + os.sep + self.routingSequ).data
            self.rtc = readRaster(self.workDir + os.sep + self.routingCode).data
        if self.gridUD == None:
            raise Exception("gridUD can not be empty.", self.gridUD)

        # 初始化变量
        strtmp = ""
        strLine = ""
        strtmpArr = []
        UDArr = []
        dMax = numpy.max(self.rtc)
        dMin = numpy.min(self.rsq)
        n = 0
        nSize = int(dMax)
        # print("dMax: %d" % dMax)
        RouteSequ = numpy.zeros(nSize)
        i8 = numpy.empty(8)
        j8 = numpy.empty(8)
        px = 0
        py = 0

        for i in range(self.rows):
            for j in range(self.cols):
                if (i * self.rows + j) % int(self.rows * self.cols / 100) == 0:
                    print("▋", end='')
                    sys.stdout.flush()
                if self.rtc[i][j] == self.noDataValue:
                    continue
                else:
                    strLine = "%d\t" % int(self.rtc[i][j])
                    strtmp = "%d\t" % int(self.rsq[i][j])
                    # print(n)
                    RouteSequ[n] = int(self.rsq[i][j])
                    n += 1
                    strLine += strtmp

                    n8, i8, j8 = self.PixelFlowIn_b(i, j, b=False)
                    for k in range(8):
                        if i8[k] == 0 or j8[k] == 0:
                            strtmp = "%d\t" % 0
                        else:
                            strtmp = "%d\t" % int(self.rsq[int(i8[k])][int(j8[k])])
                        strLine += strtmp

                    hasDown, px, py = self.PixelFlowOut(i, j, px, py)
                    if hasDown:
                        strtmp = "%d\t" % int(self.rsq[px][py])
                        strLine += strtmp
                    else:
                        strtmp = "%d\t" % -1
                        strLine += strtmp

                    if i == 0 or j == 0 or i == self.rows - 1 or j == self.cols - 1:
                        dslope = 0.
                    else:
                        p = XElevGradient(self.demData, i, j, self.geotrans[1])
                        q = YElevGradient(self.demData, i, j, self.geotrans[1])
                        if p * p + q * q == 0.:
                            dslope = 0.
                        else:
                            dslope = math.tanh(math.sqrt(p * p + q * q))
                    strtmp = "%.4f\t" % dslope
                    strLine += strtmp

                    dlen = GridFlowLength(self.flowDirData[i][j], self.geotrans[1], self.d8)
                    strtmp = "%.1f\t" % dlen
                    strLine += strtmp

                    strtmp = "%d\t" % int(self.streamOrdData[i][j])
                    strLine += strtmp

                    strtmp = "%d\t" % i
                    strLine += strtmp
                    strtmp = "%d" % j
                    strLine += strtmp

                    strtmpArr.append(strLine)

        for i in range(nSize):
            for j in range(nSize):
                if i == RouteSequ[j]:
                    UDArr.append(strtmpArr[j])
                    # print(strtmpArr)
                    break

        print("\n\tSave as %s" % self.gridUD)
        if os.path.isfile(self.workDir + os.sep + self.gridUD):
            os.remove(self.workDir + os.sep + self.gridUD)
        UDFile = open(self.workDir + os.sep + self.gridUD, 'w')
        for ud in range(len(UDArr)):
            UDFile.write(UDArr[ud] + "\n")
        UDFile.close()

        print()
        return 0

    # / *++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                                   +
    # +                      Function：Calculate flow route length                        +
    # +                                                                                   +
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def RouteLength(self):
        '''
        计算栅格水流路径长度
        :return:
        '''
        print("Calculating flow route length...")
        if self.flowDir == None or self.routingCode == None:
            raise Exception("flowDir or routingCode can not be empty.", self.flowDir, self.routingCode)
        else:
            self.rtc = readRaster(self.workDir + os.sep + self.routingCode).data
        if self.subbasinsNum == 0:
            raise Exception("subbasinsNum can not be zero.", self.subbasinsNum)

        self.gfl = numpy.zeros((self.rows, self.cols))

        for i in range(self.subbasinsNum):
            dMax = numpy.max(self.rtc)
            dMin = numpy.min(self.rtc)
            totnum = int(dMax)

            # 坐标初始化
            self.ii = numpy.zeros(totnum)
            self.jj = numpy.zeros(totnum)

            inum = 0
            totin = 1
            self.ii[0] = self.outX
            self.jj[0] = self.outY

            while inum < totin:
                if inum % int(dMax / 100) == 0:
                    print("▋", end='')
                    sys.stdout.flush()
                itet, pos = self.PixelFlowIn(int(self.ii[inum]), int(self.jj[inum]), totin, self.gfl)
                totin += itet
                inum += 1

            dlen = 0
            downx = 0
            downy = 0
            for k in range(inum):
                dlen = GridFlowLength(int(self.flowDirData[int(self.ii[k])][int(self.jj[k])]), self.geotrans[1],
                                      self.d8)
                self.gfl[int(self.ii[k])][int(self.jj[k])] = dlen
                hasDown, downx, downy = self.PixelFlowOut(int(self.ii[k]), int(self.jj[k]), downx, downy)
                if hasDown:
                    self.gfl[int(self.ii[k])][int(self.jj[k])] += self.gfl[int(downx)][int(downy)]

        for m in range(self.rows):
            for n in range(self.cols):
                if self.rtc[m][n] == self.noDataValue:
                    self.gfl[m][n] = self.noDataValue
                else:
                    continue

        print()
        writeRaster(self.workDir + os.sep + self.gridFlowLength, self.rows, self.cols, self.gfl, self.geotrans,
                       self.srs, self.noDataValue, gdal.GDT_Float32)
        return 0

    # / *++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                                   +
    # +                      Function：Calculate mean slope of route                      +
    # +                                                                                   +
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def RouteMeanSlp(self):
        '''
        计算栅格水流路径平均坡度
        :return:
        '''
        print("Calculating mean slope of route")
        if self.routingCode == None:
            raise Exception("routingCode can not be empty.", self.routingCode)
        else:
            self.rtc = readRaster(self.workDir + os.sep + self.routingCode).data
        if self.subbasinsNum == 0:
            raise Exception("subbasinsNum can not be zero.", self.subbasinsNum)

        self.gms = numpy.zeros((self.rows, self.cols))

        for i in range(self.subbasinsNum):
            meanSlp = numpy.zeros((self.rows, self.cols))
            gridNum = numpy.zeros((self.rows, self.cols))

            dMax = numpy.max(self.rtc)
            dMin = numpy.min(self.rtc)
            totnum = int(dMax)

            # 坐标初始化
            self.ii = numpy.zeros(totnum)
            self.jj = numpy.zeros(totnum)

            inum = 0
            totin = 1
            self.ii[0] = self.outX
            self.jj[0] = self.outY

            while inum < totin:
                if inum % int(dMax / 100) == 0:
                    print("▋", end='')
                    sys.stdout.flush()
                itet, pos = self.PixelFlowIn(int(self.ii[inum]), int(self.jj[inum]), totin, self.gms)
                totin += itet
                inum += 1

            downX = 0
            downY = 0

            for k in range(inum):
                if self.ii[k] == 0 or self.jj[k] == 0 or self.ii[k] == self.rows - 1 or self.jj[k] == self.cols - 1:
                    dslope = 0
                else:
                    p = XElevGradient(self.demData, int(self.ii[k]), int(self.jj[k]), self.geotrans[1])
                    q = YElevGradient(self.demData, int(self.ii[k]), int(self.jj[k]), self.geotrans[1])
                    if p * p + q * q == 0.:
                        dslope = 0
                    else:
                        dslope = math.tanh(math.sqrt(p * p + q * q))
                meanSlp[int(self.ii[k])][int(self.jj[k])] = dslope
                gridNum[int(self.ii[k])][int(self.jj[k])] = 1
                hasDown, downX, downY = self.PixelFlowOut(int(self.ii[k]), int(self.jj[k]), downX, downY)
                if hasDown:
                    meanSlp[int(self.ii[k])][int(self.jj[k])] += meanSlp[int(downX)][int(downY)]
                    gridNum[int(self.ii[k])][int(self.jj[k])] += gridNum[int(downX)][int(downY)]

            for t in range(inum):
                meanSlp[int(self.ii[t])][int(self.jj[t])] = meanSlp[int(self.ii[t])][int(self.jj[t])] / gridNum[int(self.ii[t])][int(self.jj[t])]
                self.gms[int(self.ii[t])][int(self.jj[t])] = meanSlp[int(self.ii[t])][int(self.jj[t])]

        for m in range(self.rows):
            for n in range(self.cols):
                if self.rtc[m][n] == self.noDataValue:
                    self.gms[m][n] = self.noDataValue
                else:
                    continue

        print()
        writeRaster(self.workDir + os.sep + self.gridMeanSlp, self.rows, self.cols, self.gms, self.geotrans,
                       self.srs, self.noDataValue, gdal.GDT_Float32)
        return 0

    # / *++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                                   +
    # +                      Function：Calculate route time                               +
    # +                                                                                   +
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    # +                              L          L                                         +
    # +                        tc = --- = ------------                                    +
    # +                              V      dKv*Sqrt(S)                                   +
    # +                                                                                   +
    # +                          L   -- 栅格的水流路径长度；                                  +
    # +                          S   -- 栅格的平均坡度；                                      +
    # +                          dKV -- 速度常数，包含糙率、水力半径等因素                       +
    # +                                 对水流的影响(外部输入，需率定)                          +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++*/
    def RouteTime(self):
        '''
        计算栅格汇流时间
        :return:
        '''
        print("Calculating route time")
        if self.gridFlowLength == None or self.gridMeanSlp == None:
            raise Exception("gridFlowLength or gridMeanSlp can not be empty.", self.gridFlowLength, self.gridMeanSlp)
        else:
            self.gfl = readRaster(self.workDir + os.sep + self.gridFlowLength).data
            self.gms = readRaster(self.workDir + os.sep + self.gridMeanSlp).data
        if self.dKV == 0:
            raise Exception("dKV can not be empty.", self.dKV)

        self.rtt = numpy.zeros((self.rows, self.cols))

        for i in range(self.rows):
            for j in range(self.cols):
                if (i * self.rows + j) % int(self.rows * self.cols / 100) == 0:
                    print("▋", end='')
                    sys.stdout.flush()
                if self.gms[i][j] != self.noDataValue and self.gfl[i][j] != self.noDataValue:
                    if self.gms[i][j] == 0:
                        self.rtt[i][j] = 0
                    else:
                        self.rtt[i][j] = self.gfl[i][j] / (self.dKV * math.sqrt(self.gms[i][j]))
                else:
                    self.rtt[i][j] = self.noDataValue

        print()
        writeRaster(self.workDir + os.sep + self.routingTime, self.rows, self.cols, self.rtt, self.geotrans,
                       self.srs, self.noDataValue, gdal.GDT_Float32)

        return 0

    # / *++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                                   +
    # +                      Function：Statistics flow in pixels                          +
    # +                                                                                   +
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def PixelFlowIn(self, cx, cy, pos, pvalue, dvalue=0):
        '''
        计算邻域栅格向中心栅格入流的栅格数量
        :param cx: 中心栅格坐标
        :param cy: 中心栅格坐标
        :param ii: 栅格数据队列,存放与本栅格有入流关系的相邻栅格的坐标
        :param jj: 栅格数据队列,存放与本栅格有入流关系的相邻栅格的坐标
        :param pos: 当前存放栅格坐标的位置
        :param pvalue:
        :param dvalue:判断当前栅格是否已计算
        :return:
        '''
        iret = 0
        bLeft = False
        bTop = False
        bRight = False
        bBottom = False

        if cx == 0:
            bTop = True
        if cy == 0:
            bLeft = True
        if cx == self.rows - 1:
            bBottom = True
        if cy == self.cols - 1:
            bRight = True

        def NewElementInMem(kii, kjj, isize, rx, ry):
            bret = False
            for ki in range(isize):
                if int(kii[ki]) == int(rx) and int(kjj[ki]) == int(ry):
                    bret = True
                    break
            return bret

        if bTop == False and bLeft == False:
            if int(self.flowDirData[cx - 1][cy - 1]) == int(self.fd8[5]) and int(pvalue[cx - 1][cy - 1]) == int(dvalue):
                if NewElementInMem(self.ii, self.jj, pos, cx - 1, cy - 1) == False:
                    self.ii[pos] = cx - 1
                    self.jj[pos] = cy - 1
                    pos += 1
                    iret += 1

        if bTop == False:
            if int(self.flowDirData[cx - 1][cy]) == int(self.fd8[6]) and int(pvalue[cx - 1][cy]) == int(dvalue):
                if NewElementInMem(self.ii, self.jj, pos, cx - 1, cy) == False:
                    self.ii[pos] = cx - 1
                    self.jj[pos] = cy
                    pos += 1
                    iret += 1

        if bTop == False and bRight == False:
            if int(self.flowDirData[cx - 1][cy + 1]) == int(self.fd8[7]) and int(pvalue[cx - 1][cy + 1]) == int(dvalue):
                if NewElementInMem(self.ii, self.jj, pos, cx - 1, cy + 1) == False:
                    self.ii[pos] = cx - 1
                    self.jj[pos] = cy + 1
                    pos += 1
                    iret += 1

        if bLeft == False:
            if int(self.flowDirData[cx][cy - 1]) == int(self.fd8[4]) and int(pvalue[cx][cy - 1]) == int(dvalue):
                if NewElementInMem(self.ii, self.jj, pos, cx, cy - 1) == False:
                    self.ii[pos] = cx
                    self.jj[pos] = cy - 1
                    pos += 1
                    iret += 1

        if bRight == False:
            if int(self.flowDirData[cx][cy + 1]) == int(self.fd8[0]) and int(pvalue[cx][cy + 1]) == int(dvalue):
                if NewElementInMem(self.ii, self.jj, pos, cx, cy + 1) == False:
                    self.ii[pos] = cx
                    self.jj[pos] = cy + 1
                    pos += 1
                    iret += 1

        if bBottom == False and bLeft == False:
            if int(self.flowDirData[cx + 1][cy - 1]) == int(self.fd8[3]) and int(pvalue[cx + 1][cy - 1]) == int(dvalue):
                if NewElementInMem(self.ii, self.jj, pos, cx + 1, cy - 1) == False:
                    self.ii[pos] = cx + 1
                    self.jj[pos] = cy - 1
                    pos += 1
                    iret += 1

        if bBottom == False:
            if int(self.flowDirData[cx + 1][cy]) == int(self.fd8[2]) and int(pvalue[cx + 1][cy]) == int(dvalue):
                if NewElementInMem(self.ii, self.jj, pos, cx + 1, cy) == False:
                    self.ii[pos] = cx + 1
                    self.jj[pos] = cy
                    pos += 1
                    iret += 1

        if bBottom == False and bRight == False:
            if int(self.flowDirData[cx + 1][cy + 1]) == int(self.fd8[1]) and int(pvalue[cx + 1][cy + 1]) == int(dvalue):
                if NewElementInMem(self.ii, self.jj, pos, cx + 1, cy + 1) == False:
                    self.ii[pos] = cx + 1
                    self.jj[pos] = cy + 1
                    pos += 1
                    iret += 1

        return iret, pos

    # / *++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                                   +
    # +                      Function：Statistics flow in pixels                          +
    # +                                                                                   +
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def PixelFlowIn_b(self, cx, cy, b=False):
        '''

        :param cx: 中心栅格坐标
        :param cy: 中心栅格坐标
        :param b: True - 按8流向存放数据; False - 按递增次序存放数据
        :return:
        '''

        iret = 0
        bLeft = False
        bTop = False
        bRight = False
        bBottom = False

        if cx == 0:
            bTop = True
        if cy == 0:
            bLeft = True
        if cx == self.rows - 1:
            bBottom = True
        if cy == self.cols - 1:
            bRight = True

        ii = numpy.zeros(8)
        jj = numpy.zeros(8)

        if bTop == False and bLeft == False:
            if self.flowDirData[cx - 1][cy - 1] == self.fd8[5]:
                if b:
                    ii[5] = cx - 1
                    jj[5] = cy - 1
                else:
                    ii[iret] = cx - 1
                    jj[iret] = cy - 1
                iret += 1

        if bTop == False:
            if self.flowDirData[cx - 1][cy] == self.fd8[6]:
                if b:
                    ii[6] = cx - 1
                    jj[6] = cy
                else:
                    ii[iret] = cx - 1
                    jj[iret] = cy
                iret += 1

        if bTop == False and bRight == False:
            if self.flowDirData[cx - 1][cy + 1] == self.fd8[7]:
                if b:
                    ii[7] = cx - 1
                    jj[7] = cy + 1
                else:
                    ii[iret] = cx - 1
                    jj[iret] = cy + 1
                iret += 1

        if bLeft == False:
            if self.flowDirData[cx][cy - 1] == self.fd8[4]:
                if b:
                    ii[4] = cx
                    jj[4] = cy - 1
                else:
                    ii[iret] = cx
                    jj[iret] = cy - 1
                iret += 1

        if bRight == False:
            if self.flowDirData[cx][cy + 1] == self.fd8[0]:
                if b:
                    ii[0] = cx
                    jj[0] = cy + 1
                else:
                    ii[iret] = cx
                    jj[iret] = cy + 1
                iret += 1

        if bBottom == False and bLeft == False:
            if self.flowDirData[cx + 1][cy - 1] == self.fd8[3]:
                if b:
                    ii[3] = cx + 1
                    jj[3] = cy - 1
                else:
                    ii[iret] = cx + 1
                    jj[iret] = cy - 1
                iret += 1

        if bBottom == False:
            if self.flowDirData[cx + 1][cy] == self.fd8[2]:
                if b:
                    ii[2] = cx + 1
                    jj[2] = cy
                else:
                    ii[iret] = cx + 1
                    jj[iret] = cy
                iret += 1

        if bBottom == False and bRight == False:
            if self.flowDirData[cx + 1][cy + 1] == self.fd8[1]:
                if b:
                    ii[1] = cx + 1
                    jj[1] = cy + 1
                else:
                    ii[iret] = cx + 1
                    jj[iret] = cy + 1
                iret += 1

        return iret, ii, jj

    # / *++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                                   +
    # +                      Function：Calculate routing order                            +
    # +                                                                                   +
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def PixelRouteOrder(self, cx, cy, pos, pvalue):
        '''
        对当前处理栅格的上游入流栅格设定汇流演算等级
        :param cx:
        :param cy:
        :param pos:
        :param pvalue:
        :param dvalue:
        :return:
        '''
        iret = 0
        bLeft = False
        bTop = False
        bRight = False
        bBottom = False

        if cx == 0:
            bTop = True
        if cy == 0:
            bLeft = True
        if cx == self.rows - 1:
            bBottom = True
        if cy == self.cols - 1:
            bRight = True

        dcurdeg = pvalue[cx][cy]

        if bTop == False and bLeft == False:
            if self.flowDirData[cx - 1][cy - 1] == self.fd8[5]:
                pvalue[cx - 1][cy - 1] = dcurdeg - 1
                self.ii[pos] = cx - 1
                self.jj[pos] = cy - 1
                pos += 1
                iret += 1

        if bTop == False:
            if self.flowDirData[cx - 1][cy] == self.fd8[6]:
                pvalue[cx - 1][cy] = dcurdeg - 1
                self.ii[pos] = cx - 1
                self.jj[pos] = cy
                pos += 1
                iret += 1

        if bTop == False and bRight == False:
            if self.flowDirData[cx - 1][cy + 1] == self.fd8[7]:
                pvalue[cx - 1][cy + 1] = dcurdeg - 1
                self.ii[pos] = cx - 1
                self.jj[pos] = cy + 1
                pos += 1
                iret += 1

        if bLeft == False:
            if self.flowDirData[cx][cy - 1] == self.fd8[4]:
                pvalue[cx][cy - 1] = dcurdeg - 1
                self.ii[pos] = cx
                self.jj[pos] = cy - 1
                pos += 1
                iret += 1

        if bRight == False:
            if self.flowDirData[cx][cy + 1] == self.fd8[0]:
                pvalue[cx][cy + 1] = dcurdeg - 1
                self.ii[pos] = cx
                self.jj[pos] = cy + 1
                pos += 1
                iret += 1

        if bBottom == False and bLeft == False:
            if self.flowDirData[cx + 1][cy - 1] == self.fd8[3]:
                pvalue[cx + 1][cy - 1] = dcurdeg - 1
                self.ii[pos] = cx + 1
                self.jj[pos] = cy - 1
                pos += 1
                iret += 1

        if bBottom == False:
            if self.flowDirData[cx + 1][cy] == self.fd8[2]:
                pvalue[cx + 1][cy] = dcurdeg - 1
                self.ii[pos] = cx + 1
                self.jj[pos] = cy
                pos += 1
                iret += 1

        if bBottom == False and bRight == False:
            if self.flowDirData[cx + 1][cy + 1] == self.fd8[1]:
                pvalue[cx + 1][cy + 1] = dcurdeg - 1
                self.ii[pos] = cx + 1
                self.jj[pos] = cy + 1
                pos += 1
                iret += 1

        return iret, pos, pvalue

    # / *++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                                   +
    # +                      Function：Statistics flow out pixels                          +
    # +                                                                                   +
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def PixelFlowOut(self, cx, cy, px, py):
        '''
        计算邻域栅格向中心栅格出流的栅格数量
        :param cx: 中心栅格坐标
        :param cy: 中心栅格坐标
        :return: True - 找到下游栅格；False - 没有下游栅格
                 px, py
        '''
        bLeft = False
        bTop = False
        bRight = False
        bBottom = False

        if cx == 0:
            bTop = True
        if cy == 0:
            bLeft = True
        if cx == self.rows - 1:
            bBottom = True
        if cy == self.cols - 1:
            bRight = True

        if bTop == False and bLeft == False:
            if int(self.flowDirData[cx][cy]) == int(self.d8[5]):
                px = cx - 1
                py = cy - 1
                return True, px, py

        if bTop == False:
            if int(self.flowDirData[cx][cy]) == int(self.d8[6]):
                px = cx - 1
                py = cy
                return True, px, py

        if bTop == False and bRight == False:
            if int(self.flowDirData[cx][cy]) == int(self.d8[7]):
                px = cx - 1
                py = cy + 1
                return True, px, py

        if bLeft == False:
            if int(self.flowDirData[cx][cy]) == int(self.d8[4]):
                px = cx
                py = cy - 1
                return True, px, py

        if bRight == False:
            if int(self.flowDirData[cx][cy]) == int(self.d8[0]):
                px = cx
                py = cy + 1
                return True, px, py

        if bBottom == False and bLeft == False:
            if int(self.flowDirData[cx][cy]) == int(self.d8[3]):
                px = cx + 1
                py = cy - 1
                return True, px, py

        if bBottom == False:
            if int(self.flowDirData[cx][cy]) == int(self.d8[2]):
                px = cx + 1
                py = cy
                return True, px, py

        if bBottom == False and bRight == False:
            if int(self.flowDirData[cx][cy]) == int(self.d8[1]):
                px = cx + 1
                py = cy + 1
                return True, px, py

        return False, px, py

# if __name__ == "__main__":
#     r = RunoffParam()
#     r.workDir = tauDir
#     r.flowDir = flowDir
#     r.streamOrd = streamOrder
#     r.dem = DEMFileName
#     r.SetInfo()
#
#     r.outX = 230
#     r.outY = 72
#
#     r.watershedMask = mask_to_ext
#     # r.WatershedBound()
#
#     r.routingCode = routingCode
#     # r.RoutingGridCode()
#
#     r.routingOdr = routingOdr
#     r.routingSequ = routingSequ
#     # r.RoutingOptimalOrder()
#     # r.RoutingOptimalSequ()
#
#     r.RoutingUDNode()
