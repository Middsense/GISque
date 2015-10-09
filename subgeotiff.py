# -*- coding: utf-8 -*-
"""
Created on Sat Nov 22 17:48:40 2014
Name:    subgeotiff.py
Purpose: Extract a spatial subset of a GeoTIFF (or a stack of GeoTIFF) and
         preserves the georeferencing and projection properties of each element
         of the original stack. The tool assumes that each GeoTIFF contains a
         single band.
Author:  Andrea Vaccari (av9g@virginia.edu)
Version: 1.0.1

Revision history:
2015-10-08 (1.0.1)
Fixed issue with coordinates conversion when using EPSG.
Fixed issue with saving numpy array.

2014-11-22 (1.0.0)
Fist release
"""

from shutil import rmtree
from os import makedirs
from os.path import join, exists
from sys import exit
from glob import glob
import argparse


try:
    from osgeo import gdal
except ImportError:
    exit("\nERROR -> Osgeo/gdal package is required")

try:
    from osgeo import osr
except ImportError:
    exit("\nERROR -> Osgeo/osr required to handle projections")

try:
    from osgeo import ogr
except ImportError:
    exit("\nERROR -> Osgeo/ogr required to create geometries")

try:
    import numpy as np
except ImportError:
    exit("\nERROR -> Numpy package is required")


def subgeotiff(data_in, data_out, bbox, prj_epsg, prj_url, dest_dir, overwrite, npout, ndval):
    # Check if the input data exists
    files = glob(data_in)
    if not files:
        exit("\nERROR -> No file were selected using '{0}'".format(data_in))

    print "\n{0} files selected using '{1}'".format(len(files), data_in)

    # Check if we need to create an output directory
    if dest_dir:
        if overwrite:
            try:
                rmtree(data_out)
            except OSError as e:
                exit("\nERROR -> Removing directory {0} ({1})".format(data_out, e))
        else:
            if exists(data_out):
                exit("\nERROR -> Directory already exists. Use -o to overwrite.")
        makedirs(data_out)

    # Check for the range spatial reference
    if prj_epsg or prj_url:
        rng_srs = osr.SpatialReference()

        if prj_epsg:
            if rng_srs.ImportFromEPSG(int(prj_epsg)) != 0:
                exit("\nERROR -> Error setting the range spatial reference to EPSG:{0}".format(prj_epsg))
            else:
                print "\nSetting range spatial reference to EPSG:{0}".format(prj_epsg)
        else:
            if rng_srs.ImportFromUrl(prj_url) != 0:
                exit("\nERROR -> Error setting the range spatial reference to ESRI:{0}".format(prj_url))
            else:
                print "\nSetting range spatial reference to URL:{0}".format(prj_url)
    else:
        print "\nWARNING -> No spatial reference for range is defined! Using pixels!"
        rng_srs = None

    # If not pixels, then create point geometries
    if rng_srs:
        if bbox:
            [bbsl, bbst, bber, bbeb] = bbox
            tl = ogr.Geometry(ogr.wkbPoint)
            tl.AddPoint(bbsl, bbst)
            br = ogr.Geometry(ogr.wkbPoint)
            br.AddPoint(bber, bbeb)
        else:
            rng_srs = None

    # Create a spatial reference object for the soruce images
    src_srs = osr.SpatialReference()

    # Prepare gdal for output
    data_format = "GTiff"
    driver = gdal.GetDriverByName(data_format)
    print "\nOutput format set to '{0}'".format(data_format)

    fout_cnt = 0

    # Array to contain the numpy array
    np_out = None

    # Cycle through input stack
    for f in files:
        print "\nOpening: {0}".format(f)
        fin = gdal.Open(f)
        print "- Reading input file properties"
        proj = fin.GetProjection()
        src_srs.ImportFromWkt(proj)
        print "  - Input spatial reference"
        ingeo = fin.GetGeoTransform()
        print "  - Input geotransform: {0}".format(ingeo)
        metadata = fin.GetMetadata()

        # If coordinates
        if rng_srs:
            transf = osr.CoordinateTransformation(rng_srs, src_srs)
            tl.SetPoint(0, bbsl, bbst)
            tl.Transform(transf)
            tl_coo = tl.GetPoint()
            print "    - top left: {0} -> {1}".format((bbsl, bbst), tl_coo)
            br.SetPoint(0, bber, bbeb)
            br.Transform(transf)
            br_coo = br.GetPoint()
            print "    - bottom right: {0} -> {1}".format((bber, bbeb), br_coo)
            sr = int((tl_coo[1] - ingeo[3])/ingeo[5])
            sc = int((tl_coo[0] - ingeo[0])/ingeo[1])
            er = int((br_coo[1] - ingeo[3])/ingeo[5])
            ec = int((br_coo[0] - ingeo[0])/ingeo[1])
            ranges = True
        else:  # If pixels range
            if bbox:
                [sc, sr, ec, er] = [int(r) for r in bbox]
                ranges = True
            else:
                print "\nWARNING -> Range not defined. Creating a copy of input."
                ranges = False

        if ranges:
            # Check range parameters
            if sr < 0 or sc < 0 or er < 0 or ec < 0:
                exit("\nERROR -> Pixel range values should be positive")
            if er == sr or ec == sc:
                exit("\nERROR -> Pixel range should be greater than zero")
            if er < sr:
                print("\nWARNING -> start row ({0}) larger then end row ({1}). Swapping.".format(sr, er))
                sr, er = er, sr
            if ec < sc:
                print("\nWARNING -> start col ({0}) larger then end col ({1}). Swapping.".format(sc, ec))
                sc, ec = ec, sc
            print "    - Using pixel range: ({0}, {1}) -> ({2}, {3})".format(sr, sc, er, ec)
            routsize = er - sr
            coutsize = ec - sc

        print "- Reading input raster band properties"
        bndin = fin.GetRasterBand(1)
        ndv = bndin.GetNoDataValue()
        dtyp = bndin.DataType
        rinsize = bndin.YSize
        cinsize = bndin.XSize
        if ranges:
            if routsize > rinsize:
                print "\nWARNING -> row output size ({0}) larger than input size ({1}). Shrinking output to match.".format(routsize, rinsize)
                er = rinsize
                routsize = er - sr
                print "           New limits ({0} - {1}).".format(sr, er)
            if coutsize > cinsize:
                print "\nWARNING -> col output size ({0}) larger than input size ({1}). Shrinking output to match.".format(coutsize, cinsize)
                ec = cinsize
                coutsize = ec - sc
                print "           New limits ({0} - {1}).".format(sc, ec)
        else:
            sc = 0
            sr = 0
            coutsize, routsize = cinsize, rinsize
        print "- Reading input raster subset"
        datout = bndin.ReadAsArray(sc, sr, coutsize, routsize)

        # Check if we need to change the no-data value
        if ndval:
            if ndval != ndv:
                datout[datout == ndv] = ndval
                ndv = ndval

        # Check if we are creating the numpy array
        if npout:
            print "- Adding to numpy array "
            if np_out is not None:
                try:
                    np_out = np.dstack((np_out, datout))
                except ValueError:
                    print "\WARNING -> Size of current stack image {0} not compatible with previous size {1}: skipping!".format(np.shape(datout), np.shape(np_out))
                    pass
            else:
                np_out = datout

        fname = data_out + "_{0:03d}.tif".format(fout_cnt)
        if dest_dir:
            fname = join(data_out, fname)
        print "- Creating subset raster file: {0}".format(fname)
        fout = driver.Create(fname, coutsize, routsize, 1, dtyp, ['COMPRESS=DEFLATE', 'PREDICTOR=3'])
        if not fout:
            bndin = None
            fin = None
            exit("\nERROR -> error creating output file '{0}'".format(fout))
        print "- Writing output file properties"
        bndout = fout.GetRasterBand(1)
        fout.SetProjection(proj)
        fout.SetMetadata(metadata)
        outgeo = list(ingeo)
        outgeo[0] += sc * outgeo[1]
        outgeo[3] += sr * outgeo[5]
        print "  - Output geotransform: {0}".format(outgeo)
        fout.SetGeoTransform(outgeo)

        print "- Writing output raster band properties"
        bndout.SetNoDataValue(ndv)
        print "  - Writing new statistics."
        bomin = np.min(datout[datout != ndv])
        bomax = np.max(datout[datout != ndv])
        boavg = np.mean(datout[datout != ndv])
        bostd = np.std(datout[datout != ndv])
        bndout.SetMetadata({'STATISTICS_MAXIMUM': str(bomax),
                            'STATISTICS_MINIMUM': str(bomin),
                            'STATISTICS_MEAN': str(boavg),
                            'STATISTICS_STDDEV': str(bostd)})
        print "- Writing output raster"
        bndout.WriteArray(datout)

        print "- Flushing and closing files"
        bndout = None
        fout = None
        bndin = None
        fin = None

        fout_cnt += 1
    # If we have defined geometries, destroy them
    if rng_srs:
        tl.Destroy()
        br.Destroy()

    # If we want the array, save it
    if npout:
        print "- Saving numpy array"
        fname = data_out + ".npy"
        if dest_dir:
            fname = join(data_out, fname)
        with open(fname, 'w') as fil:
            np.save(fil, np_out)

if __name__ == "__main__":
    # If it is used as a script, parse the arguments
    DESCRIPTION = "Extract a spatial subset of a GeoTIFF (or a stack of \
        GeoTIFF) and preserves the georeferencing and projection properties of \
        each element of the original stack. The tool assumes that each GeoTIFF \
        contains a single band."

    VERSION = "1.0.0"

    parser = argparse.ArgumentParser(description=DESCRIPTION, version=VERSION)

    parser.add_argument("data_in",
                        help="'Name' (regular expressions are valid) of the \
                        input stack (required).")
    parser.add_argument("data_out",
                        help="'Base name' of the output stack. The output \
                        files will be numbered by appending _000, _001, ... \
                        before the .TIF extension (required).")

    parser.add_argument("-r", "--range",
                        type=float,
                        nargs='+',
                        help="Space separated coordinates of the top left and \
                        bottom right corners of the rectangle enclosing the \
                        selection: east north west south.")

    src_spref = parser.add_mutually_exclusive_group()
    src_spref.add_argument("-p", "--prj_epsg",
                           type=int,
                           default=0,
                           help="EPSG spatial reference code describing the \
                           projection to be used to interpret the range \
                           specified with the '-r (--range)' option.\n \
                           102746 corresponds to the:\n \
                           NAD_1983_StatePlane_Virginia_North_FIPS_4501_Feet \
                           If no value is specified, the range will be assumed \
                           to be in pixels.")
    src_spref.add_argument("-u", "--prj_url",
                           help="URL of spatial reference describing the \
                           projection to be used to interpret the range \
                           specified with the '-r (--range)' oprion.\n \
                           An example of acceptable URL is:\n \
                           http://spatialreference.org/ref/esri/102746/ogcwkt/\n \
                           This is the OGC WKT format for the:\n \
                           NAD_1983_StatePlane_Virginia_North_FIPS_4501_Feet\n \
                           from the spatialreference.com website.")

    parser.add_argument("-d", "--dir",
                        action="store_false",
                        help="Create a directory to store the output using the \
                        'data_out' base name (default: 'True').")
    parser.add_argument("-o", "--overwrite",
                        action="store_true",
                        help="Overwrite existing files (default: 'False').")
    parser.add_argument("-a", "--npout",
                        action="store_true",
                        help="If specified, it will create a .npy file using \
                        the base name specified in 'data_out' stored in the \
                        location specified by the '-d' (or '--dir'). The file \
                        will include the 3D 'npout' array coposed by stacking \
                        along the 3rd dimension the GeoTIFF subsets. The array \
                        will only stack subset of equal size.")
    parser.add_argument("-n", "--ndval",
                        type=float,
                        help="When defined, sets the new 'no-data-value' for \
                        the generated substack. (Default: '%(default)s').")

    args = parser.parse_args()

    # Call the function with the parsed parameters
    subgeotiff(args.data_in,
               args.data_out,
               args.range,
               args.prj_epsg,
               args.prj_url,
               args.dir,
               args.overwrite,
               args.npout,
               args.ndval)


