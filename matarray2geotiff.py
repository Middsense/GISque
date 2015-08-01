# -*- coding: utf-8 -*-
"""
Created on Sat Nov 22 17:48:40 2014
Name:    matarray2geotiff.py
Purpose: Convert a 2D array within a matlab '.mat' file into a GeoTIFF.
Author:  Andrea Vaccari (av9g@virginia.edu)
"""
# ************** NEED TO CONVERT THIS TO PROPER SCRIPT ******************
import scipy.io

data = scipy.io.loadmat('propagated.mat')

xmin = data['xmin']
xmax = data['xmax']
ymin = data['ymin']
ymax = data['ymax']
finpro = data['finpro']

import numpy as np

finpro[finpro == 1.0] = -9999.0
finpro_min = np.min(finpro[finpro != -9999.0])
finpro_max = np.max(finpro[finpro != -9999.0])
finpro_ave = np.average(finpro[finpro != -9999.0])
finpro_stdev = np.std(finpro[finpro != -9999.0])

(rows, cols) = np.shape(finpro)

from osgeo import osr

srs = osr.SpatialReference()
srs.ImportFromEPSG(102746)

from osgeo import gdal

driver = gdal.GetDriverByName('GTiff')
file_out = driver.Create('propagated.tif', cols, rows, 1, gdal.GDT_Float32, ['COMPRESS=DEFLATE', 'PREDICTOR=3'])
file_out.SetProjection(srs.ExportToWkt())
geotrans = (float(xmin), float((xmax - xmin) / cols), 0.0, float(ymin), 0.0, float((ymax - ymin) / rows))
file_out.SetGeoTransform(geotrans)
band_out = file_out.GetRasterBand(1)
band_out.SetMetadata({'STATISTICS_MAXIMUM':str(finpro_max), 'STATISTICS_MINIMUM':str(finpro_min), 'STATISTICS_MEAN':str(finpro_ave), 'STATISTICS_STDDEV':str(finpro_stdev)})
band_out.SetNoDataValue(-9999.0)
band_out.WriteArray(finpro)
band_out = None
file_out = None

