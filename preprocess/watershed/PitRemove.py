# -*- coding: utf-8 -*-
"""
Created Dec 2017

@author: Hao Chen

Functions:
    pitRemove:

"""

# load needed python modules
from numpy import *
import numpy
from util.fileIO import *
import heapq
import time



#-------------------
#  Read the raw DEM
#-------------------
def Test():
    directory = r'D:\pyESSITest\DEM'
    demFilename = 'srb1km.tif'
    inDem = (directory+'\\'+demFilename)

    nRows = readRaster(inDem).nRows
    nCols = readRaster(inDem).nCols
    noDataValue = readRaster(inDem).noDataValue
    geoTransform = readRaster(inDem).geoTransform
    srs = readRaster(inDem).srs
    gdalType = gdal.GDT_Float32
    DEM = readRaster(inDem).data

    print('(Cols, Rows) = ', str(nCols), str(nRows))

    DEM2 = DEM.copy()
    pitRemove(DEM2, nCols, nRows, noDataValue, geoTransform, srs, gdalType)

    outputfile = directory+'\\demfilled.tif'
    writeRaster(outputfile, nRows, nCols, DEM2, geoTransform, srs, noDataValue, gdalType)

    w1 = where(DEM != DEM2)
    n1 = size(w1[0])
    print('Number of DEM values changed by fill_pits() =', n1)
    print(' ')


def get_start_pixels(DEM, nCols, nRows,
                     EDGES_ONLY = False,
                     USE_64_BITS=False,
                     noDataValue = float32(-9999),
                     closed_basin_code = -32000, SILENT = True):

    # ---------------------------------------------------
    # Notes: Get the "start pixels" which include:
    #        (1) all edge pixels with valid data
    #        (2) all interior pixels with valid data
    #            beside a pixel with a nodata value
    #            OR a NaN value
    #        (3) all pixels with "closed basin" code

    #        Do we need to remove duplicate entries ?
    # ---------------------------------------------------

    # ----------------------------------------
    # Note that nx & ny are used to compute
    # IDs and need to have the correct type
    # ----------------------------------------

    if(USE_64_BITS):
        ID_type = 'Int64'
        nx = int64(nCols)
        ny = int64(nRows)
    else:
        ID_type = 'Int32'
        nx = int32(nCols)
        ny = int32(nRows)

    if (EDGES_ONLY):
        #------------------------------------------
        # Get IDs of edge pixels, making sure not
        # to double-count the corner pixels
        #------------------------------------------
        T_IDs = arange(nx, dtype=ID_type)
        B_IDs = T_IDs + (ny - 1) * nx
        L_IDs = (1 + arange(ny - 2, dtype=ID_type)) * nx
        R_IDs = L_IDs + (nx - 1)
        edge_IDs = concatenate([T_IDs, B_IDs, L_IDs, R_IDs])
        return edge_IDs
    else:
        #----------------------------------------
        # Prepare to get IDs for start pixels.
        # Is 100 a big enough factor of satisfy ?
        # Could have interior lakes, etc.
        #----------------------------------------
        if not(SILENT):
            print('Finding "start" pixels...')
        max_nIDs = int64(500) * (nx + ny)
        IDs      = numpy.zeros( max_nIDs, dtype=ID_type )
        n_IDs    = int64(0)

    # ----------------------------------
    # Replace NaNs with noData in DEM
    # -----------------------------------
    # Replacing NaNs with noData means
    # that flow can terminate on NaNs
    # -----------------------------------
    bad = where(isfinite(DEM) == 0)
    n_bad = size(bad[0])
    if (n_bad != 0):
        DEM[bad] = noDataValue  ###############

    # -----------------------------------------------------------
    # Add any pixel in the top edge that has valid data to IDs
    # For our purposes, they are still "beside nodata".
    # -----------------------------------------------------------
    w1 = where(DEM[0, :] > noDataValue)
    n1 = size(w1[0])
    if (n1 != 0):
        IDs[:n1] = w1[0]
        n_IDs += n1

    # --------------------------------------------------------
    # Add any pixel on left edge that has valid data to IDs
    # --------------------------------------------------------
    w2 = where(DEM[1:ny - 1, 0] > noDataValue)
    n2 = size(w2[0])
    if (n2 != 0):
        IDs[n_IDs: (n_IDs + n2)] = w2[0] * nx  ##########
        n_IDs += n2

    # ---------------------------------------------------------
    # Add any pixel on right edge that has valid data to IDs
    # ---------------------------------------------------------
    w3 = where(DEM[1:ny - 1, nx - 1] > noDataValue)
    n3 = size(w3[0])
    if (n3 != 0):
        IDs[n_IDs: (n_IDs + n3)] = (w3[0] * nx) + (nx - 1)  #########
        n_IDs += n3

    # ----------------------------------------------------------
    # Add any pixel on bottom edge that has valid data to IDs
    # ----------------------------------------------------------
    w4 = where(DEM[ny - 1, :] > noDataValue)
    n4 = size(w4[0])
    if (n4 != 0):
        IDs[n_IDs: (n_IDs + n4)] = w4[0] + nx * (ny - 1)  #########
        n_IDs += n4


    # ------------------------------------------------
    # Now scan for interior DEM pixels that:
    #   (1) have data beside noData or NaN pixels or
    #   (2) have the "closed basin" code
    # ------------------------------------------------

    # ---------------------------------------
    # Find the smallest neighbor elevation
    # ----------------------------------------------
    # Note that if there is a NaN in any of these
    # arrays, it could end up in zs.
    # NB!  (NaN < 3) = NaN, but (3 < NaN) = 3
    # To prevent this, we replace NaNs with
    # noData values as we read the DEM.
    # ----------------------------------------------
    zc = DEM[1:(ny - 1), 1:(nx - 1)]
    z1 = numpy.roll(numpy.roll(zc, 1, axis=0), -1, axis=1)  # (upper-right)
    z2 = numpy.roll(zc, -1, axis=1)  # (right)
    z3 = numpy.roll(numpy.roll(zc, -1, axis=0), -1, axis=1)  # (lower-right)
    z4 = numpy.roll(zc, -1, axis=0)  # (bottom)
    z5 = numpy.roll(numpy.roll(zc, -1, axis=0), 1, axis=1)  # (lower-left)
    z6 = numpy.roll(zc, 1, axis=1)  # (left)
    z7 = numpy.roll(numpy.roll(zc, 1, axis=0), 1, axis=1)  # (upper-left)
    z8 = numpy.roll(zc, 1, axis=0)  # (top)

    zs = numpy.minimum(z1, z2)
    zs = numpy.minimum(zs, z3)
    zs = numpy.minimum(zs, z4)
    zs = numpy.minimum(zs, z5)
    zs = numpy.minimum(zs, z6)
    zs = numpy.minimum(zs, z7)
    zs = numpy.minimum(zs, z8)

    w = where(logical_or((zc.flat == closed_basin_code),
                         (logical_and((zc.flat > noDataValue), (zs.flat <= noDataValue)))))
    nw = size(w[0])
    if (nw != 0):
        # ----------------------------------------------
        # zc has only interior pixels, so need to add
        # (nx + 1) to get IDs in the DEM itself
        # ----------------------------------------------
        IDs[n_IDs: (n_IDs + nw)] = w + nx + 1
        n_IDs += nw

    # ------------------------------------------
    # Remove unused entries from array of IDs
    # ------------------------------------------
    IDs = IDs[:n_IDs]
    return IDs

#   get_start_pixels()
#-----------------------------------------------------------------------

def pitRemove(DEM, nCols, nRows, noDataValue, geoTransform, srs, gdalType, USE_64_BITS=False, SILENT=False):

    # ----------------------------------------------------------
    # Notes:  This RAM-based version is about 4 times faster
    #         than a similar file-based version.
    # ----------------------------------------------------------
    # Notes:  Assume that original DEM has already been
    #         copied to raw_DEM_file.

    #         Be sure to call Check_Overwrite on files.
    # ----------------------------------------------------------
    # DEM        Time (s)     Max heap   Same?   New values
    # ----------------------------------------------------------
    # Small_KY                2925       Yes     419
    # KY_Sub     9.59         21280      Yes     4901
    # Beaver     65.86        83212      Yes     52353
    # Jing
    # Loess2                  781582     Yes     1543427
    # ----------------------------------------------------------
    # Small   (132 x 108)     = 14256
    # KY_Sub  (408 x 468)     = 190944      (5160.6 pix/sec)
    # Beaver  (915 x 1405)    = 1285575     (4652.7 pix/sec)
    # Jing    (3312 x 3771)   = 12489552
    # Loess2  (6016 x 4250)   = 25568000    (4674.3 pix/sec)
    # Amazon  (37558 x 25009) = 939288022   (2.3 days ??)
    # S.Amer  (56871 x 84906) = 4828689126  (11.89 days ??)
    # ----------------------------------------------------------
    #USE_MY_HEAP = False
    ### USE_MY_HEAP = True
    start = time.time()

    if (USE_64_BITS):
        ID_type = 'Int64'
        nx = numpy.int64(nCols)
        ny = numpy.int64(nRows)
    else:
        ID_type = 'Int32'
        nx = numpy.int32(nCols)
        ny = numpy.int32(nRows)
    n_pixels = (nx * ny)

    # --------------------------------------------
    # Get the "start pixels" which include:
    #   (1) all edge pixels with valid data
    #   (2) all interior pixels with valid data
    #       beside a pixel with a nodata value
    #   (3) all pixels with "closed basin" code
    # --------------------------------------------
    # Do we need to remove duplicate entries ?
    # --------------------------------------------
    # *** IDs = get_start_pixels(DEM, nx, ny, /EDGES_ONLY)


    IDs = get_start_pixels(DEM, nx, ny)
    n_IDs = size(IDs)

    # ------------------------------
    # Initialize the CLOSED array
    # ----------------------------------------
    # Set all nodata & NaN pixels to CLOSED
    # ----------------------------------------
    OPEN = uint8(0)
    CLOSED = uint8(1)
    ON_HEAP = uint8(2)
    ## C  = numpy.zeros( (ny, nx), dtype='UInt8' ).flat  # (iterator for 1D indices)
    C = numpy.zeros(n_pixels, dtype='UInt8')
    w = where(logical_or((DEM <= noDataValue), (isfinite(DEM) == 0)))
    nw = size(w[0])
    w = w[0]  ############## (need this ?)
    if (nw != 0):
        C[w] = CLOSED
    n_closed = int64(nw)
    n_raised = int64(0)
    if not (SILENT):
        print('Number of noData and NaN values =', nw)
        print('Finished initializing "closed" array.')
        print(' ')

    # ------------------------------------------
    # Initialize variables for priority queue
    # including arrays called heap and IDs
    # ------------------------------------------
    if not (SILENT):
        print('Putting boundary pixels on heap...')

    fast_heap = numpy.column_stack((DEM.flat[IDs], IDs))
    fast_heap = fast_heap.tolist()
    heapq.heapify(fast_heap)
    n_heap = len(fast_heap)

    # --------------------------------------------
    # Should this be here ? (Added on 11/03/09)
    # Should make code a little faster ?
    # --------------------------------------------
    C[IDs] = ON_HEAP
    if not(SILENT):
        print('Number of pixels on heap = ' + str(n_heap))
        print('Finished with heap insertion.')
        print(' ')

    # ----------------------------------
    # Prepare to compute neighbor IDs
    # ----------------------------------
    incs = array([-nx - 1, -nx, -nx + 1, -1, 1, nx - 1, nx, nx + 1], dtype=ID_type)
    tstr = str(n_pixels)

    # ------------------------------------------
    # Process pixels to fill pits until there
    # are no pixels left on the heap
    # ------------------------------------------
    # NB!  Both while loops work for Small,
    #      KY_Sub, but not Beaver
    # -----------------------------------------

    while (n_heap > 0):
        ### while (n_closed < n_pixels):

        # --------------------------------------
        # Print status message every so often
        # --------------------------------------
        if ((n_closed % 5000) == 0):
            nstr = str(n_closed) + ' of '
            if not (SILENT):
                print('n_closed = ' + nstr + tstr)
            time.sleep(float32(0.001))

        # ----------------------------------------
        # Get pixel in heap with min elevation,
        # and remove it from the heap array
        # ----------------------------------------

        pair = heapq.heappop(fast_heap)
        min_ID = pair[1]
        zmin = pair[0]
        ## print 'zmin =', zmin

        # ------------------------------------------
        # Flag pixel with min elevation as CLOSED
        # ------------------------------------------
        #print(str(int(min_ID)))
        C[int(min_ID)] = CLOSED
        n_closed += 1

        # ------------------------------------
        # Get IDs of this pixel's neighbors
        # ------------------------------------
        ID_vals = (min_ID + incs)

        # -------------------------------------------
        # Find neighbors with valid IDs that are
        # still OPEN (i.e. not(ON_HEAP or CLOSED))
        # -------------------------------------------
        w = where(logical_and((ID_vals >= 0), (ID_vals < n_pixels)))
        if (size(w[0]) != 0):
            ID_vals = ID_vals[w[0]]
        # -------------------------------------
        # Next line excludes neighbor pixels
        # that are either ON_HEAP or CLOSED
        # -------------------------------------
        ID_vals = ID_vals.astype(int)
        #print(ID_vals[1])
        C_vals = C[ID_vals]
        w2 = where(C_vals == OPEN)
        if (size(w2[0]) != 0):
            ID_vals = ID_vals[w2[0]]
        else:
            ID_vals = []

        # --------------------------------------
        # Process each of the neighbor pixels
        # --------------------------------------
        for ID in ID_vals:

            # ------------------------------------
            # Raise neighbor elevation,
            # if it is smaller than zmin & OPEN
            # ------------------------------------
            if (DEM.flat[ID] < zmin):
                DEM.flat[ID] = zmin
                n_raised += 1
            ## DEM.flat[ ID ] = numpy.maximum( DEM.flat[ ID ], zmin )

            # ---------------------------
            # Flag neighbor as ON_HEAP
            # ---------------------------
            C[ID] = ON_HEAP

            # ---------------------------------
            # Add neighbor to priority queue
            # ---------------------------------
            #print(type(fast_heap))
            heapq.heappush(fast_heap, list((DEM.flat[ID], ID)))

        n_heap = len(fast_heap)

    # ---------------------
    # Print final report
    # ---------------------
    if not (SILENT):
        print('Total pixels   = ' + tstr)
        print('Raised  pixels = ' + str(n_raised))
        print('Drained pixels = ' + str(n_closed))

        # -----------------------------------------------------
        # Would be better to use CSDMS_base.print_run_time()
        # -----------------------------------------------------
        run_time = (time.time() - start)
        rt_str = ('%10.4f' % run_time) + ' [seconds]'
        print('Run time for fill_pits() = ' + rt_str)
        print('Finished with fill_pits().')
        print(' ')

# pitRemove()
# -----------------------------------------------------------------------

Test()







