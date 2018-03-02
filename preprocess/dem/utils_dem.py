# -*- coding: utf-8 -*-

# @Utility functions

import os
import math


# West-East direction
def XElevGradient(dem, cx, cy, resolusion):
    dret = (
           dem[cx + 1][cy - 1] + 2 * dem[cx + 1][cy] + dem[cx + 1][cy + 1] - dem[cx - 1][cy - 1] - 2 * dem[cx - 1][cy] -
           dem[cx - 1][cy + 1]) / (8. * resolusion)
    return dret


# South-North direction
def YElevGradient(dem, cx, cy, resolusion):
    dret = (
           dem[cx - 1][cy - 1] + 2 * dem[cx][cy - 1] + dem[cx + 1][cy - 1] - dem[cx + 1][cy + 1] - 2 * dem[cx][cy + 1] -
           dem[cx - 1][cy + 1]) / (8. * resolusion)
    return dret


# River length
def GridFlowLength(direct, resolusion, d8):
    dret = 0.
    if direct == d8[0] or direct == d8[2] or direct == d8[4] or direct == d8[6]:
        dret = resolusion
    if direct == d8[1] or direct == d8[3] or direct == d8[5] or direct == d8[7]:
        dret = resolusion * math.sqrt(2)
    return dret

