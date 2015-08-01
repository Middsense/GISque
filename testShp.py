# -*- coding: utf-8 -*-

from os.path import exists
from sys import exit
import argparse
import numpy as np

try:
    from osgeo import ogr
except ImportError:
    exit("\nERROR -> Osgeo/ogr required to generate shapefiles")

try:
    from osgeo import osr
except ImportError:
    exit("\nERROR -> Osgeo/osr required to create shapefile")


def testShp(shpFmt, output_shp, dst_epsg, dst_url, overwrite):
    GSPEED = -1.0  # mm/month
    TINT = np.linspace(0.0, 12.0, 13)  # months
    BBOX = (300, 300)  # feet

    # Destination shapefile spatial reference
    dst_srs = osr.SpatialReference()
    if dst_epsg:
        if dst_srs.ImportFromEPSG(dst_epsg) != 0:
            exit("\nERROR -> Error setting the shapefile spatial reference to EPSG:{0}".format(dst_epsg))
        else:
            print "\nSetting the shapefile spatial reference to EPSG:{0}".format(dst_epsg)
            print dst_srs.ExportToPrettyWkt()
    elif dst_url:
        if dst_srs.ImportFromUrl(dst_url) != 0:
            exit("\nERROR -> Error setting the shapefile spatial reference to ESRI:{0}".format(dst_url))
        else:
            print "\nSetting shapefile spatial reference to URL:{0}".format(dst_url)
            print dst_srs.ExportToPrettyWkt()
    else:
        print "\nWARNING -> No spatial reference will be defined for the shapefile!"

    # Prepare ESRI shapefile
    DRIVER = "ESRI Shapefile"
    drv = ogr.GetDriverByName(DRIVER)
    if drv is None:
        exit("\nERROR -> Driver '{0}' not available!".format(DRIVER))
    if overwrite:
        if exists(output_shp):
            drv.DeleteDataSource(output_shp)
    shp = drv.CreateDataSource(output_shp)
    if shp is None:
        exit("\nERROR -> Error creating shapefile '{0}'!".format(output_shp))
    LAYER = "testData"
    print "\nCreating layer '{0}'".format(LAYER)
    lyr = shp.CreateLayer(LAYER, srs=dst_srs, geom_type=ogr.wkbPoint)
    if lyr is None:
        exit("\nERROR -> Error creating layer '{0}'!".format(LAYER))

    # Create desired dataset
    if shpFmt == "linGrowSub":
#*************************
        pass
    else:
        pass



if __name__ == "__main__":
    # If it is used as a script, parse the arguments
    DESCRIPTION = "Generates test shapefiles"

    VERSION = "1.0.0"

    parser = argparse.ArgumentParser(description=DESCRIPTION, version=VERSION)

    parser.add_argument("output_shp",
                        help="Name of the ESRI shapefile to use as output \
                        (required).")

    dst_spref = parser.add_mutually_exclusive_group()
    dst_spref.add_argument("--dst_epsg",
                           type=int,
                           default=102746,
                           help="EPSG spatial reference code describing the \
                           source data projection.\n \
                           102746 corresponds to the:\n \
                           NAD_1983_StatePlane_Virginia_North_FIPS_4501_Feet\n\
                           Default: '%(default)s').")
    dst_spref.add_argument("--dst_url",
                           help="URL of spatial reference describing the source \
                           data projection. An example of acceptable URL is:\n \
                           http://spatialreference.org/ref/esri/102746/ogcwkt/\n \
                           This is the OGC WKT format for the:\n \
                           NAD_1983_StatePlane_Virginia_North_FIPS_4501_Feet\n \
                           from the spatialreference.com website.")

    parser.add_argument("-s", "--shpFmt",
                        default="linGrowSub",
                        choices=("linGrowSub", "statSub", "flatReg"),
                        help="Defines the type of dataset to create. The \
                        available options are:\n\
                        `linGrowSub` -> linearly growing subsidence\n\
                        `statSub` -> time-static subsidence\n\
                        `flatReg` -> time-staic flat region")
    parser.add_argument("-o", "--overwrite",
                        action="store_true",
                        help="Overwrite existing files (default: 'False').")

    args = parser.parse_args()

    testShp(args.shpFmt,
            args.output_shp,
            args.dst_epsg,
            args.dst_url,
            args.overwrite)
