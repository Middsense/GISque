# -*- coding: utf-8 -*-
"""
Created on Sat Nov 22 17:48:40 2014
Name:    ndarray2tiff.py
Purpose: Convert a 2D numpy ndarray into a single raster within a GeoTIFF file
         and copy projection and geotransform from an existing GeoTIFF.
Notes:   This file is based on gdalcopyproj.py written by Schuyler Erle,
         schuyler@nocat.net
Author:  Andrea Vaccari (av9g@virginia.edu)
Version: 0.0.0-alpha

    Copyright (C) Wed Aug 12 10:47:07 2015  Andrea Vaccari

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys
import numpy as np

try:
    from osgeo import gdal
except ImportError:
    print("GDAL module required!")
    sys.exit(1)

if len(sys.argv) < 4:
    print("Usage: ndarray2tiff.py array_file(.npy) template_file(.tif) dest_file(.tif)")
    sys.exit(1)

#==============================================================================
# Array
#==============================================================================
array_file = sys.argv[1]

try:
    array_in = np.load(array_file)
except IOError:
    print("Error opening file ", array_file, " for reading!")
    sys.exit(1)

print("\nGathering array information:")
(xsize, ysize) = np.shape(array_in)
print(" Shape (rows: {0}, cols:{1})".format(ysize, xsize))
stat_min = np.nanmin(array_in)
print(" Minimum: {0:03.2f}".format(stat_min))
stat_max = np.nanmax(array_in)
print(" Maximum: {0:03.2f}".format(stat_max))
stat_mean = np.nanmean(array_in)
print(" Mean: {0:03.2f}".format(stat_mean))
stat_stddev = np.nanstd(array_in)
print(" Standard Deviation: {0:03.2f}".format(stat_stddev))
array_tmp = None

#==============================================================================
# Template File
#==============================================================================
template_file = sys.argv[2]
template = gdal.Open(template_file)

if template is None:
    print("Error opening file ", template_file, " for reading!")
    sys.exit(1)

print("\nGathering template information:")
projection = template.GetProjection()
print(" Projection: {0}".format(projection))
geotransform = template.GetGeoTransform()
print(" Geo Transform: {0}".format(geotransform))

if projection is None and geotransform is None:
    print("Warning: No projection or geotransform find in ", template_file, "!")

metadata = template.GetMetadata()
print(" Metadata: {0}".format(metadata))
no_data = template.GetRasterBand(1).GetNoDataValue()
print(" No data value: {0:03.2f}".format(no_data))
template = None

#==============================================================================
# Writing GeoTIFF
#==============================================================================
print("\nWriting GeoTIFF...")
data_format = "GTiff"
driver = gdal.GetDriverByName(data_format)
file_out = driver.Create(sys.argv[3], ysize, xsize, 1, gdal.GDT_Float32, ['COMPRESS=DEFLATE', 'PREDICTOR=3'])

file_out.SetProjection(projection)
file_out.SetGeoTransform(geotransform)
file_out.SetMetadata = metadata

band_out = file_out.GetRasterBand(1)

band_out.SetNoDataValue(no_data)
band_out.SetMetadata({'STATISTICS_MAXIMUM': str(stat_max),
                      'STATISTICS_MINIMUM': str(stat_min),
                      'STATISTICS_MEAN': str(stat_mean),
                      'STATISTICS_STDDEV': str(stat_stddev)})
array_in[np.isnan(array_in)] = no_data
band_out.WriteArray(array_in)
print("...done!")

band_out = None
file_out = None
