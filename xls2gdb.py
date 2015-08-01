# -*- coding: utf-8 -*-
"""
Created on Sun Apr  5 20:35:21 2015
Name:    xls2gdb.py
Purpose: Convert VDOT 10th mile road condition XLS files into ESRI shapefile
         where each feature can be either a point, a line, a buffered line or
         polygon (rectangle) with extents identified by the GPS start/stop
         latitude/longitude coordinates stored in the excel file.
Author:  Andrea Vaccari (av9g@virginia.edu)
Version: 1.0.0
"""

from os.path import exists
from sys import exit, stdout
import argparse


try:
    from pandas import read_excel
except ImportError:
    exit("\nERROR -> Pandas required to read excel XLS files")

try:
    from osgeo import ogr
except ImportError:
    exit("\nERROR -> Osgeo/ogr required to create shapefile")

try:
    from osgeo import osr
except ImportError:
    exit("\nERROR -> Osgeo/osr required to create shapefile")


def main():
    FIELD_NAME_MAPPING = {
        "VDOT System ID":                                           "VDOTSysId",
        "District":                                                 "District",
        "County (Maint. Jurisd.)":                                  "CntyMntJr",
        "LM's Invalid IRI":                                         "LMInvdIRI",
        "Year":                                                     "Year",
        "Link to External Information":                             "LnkExtInf",
        "Pavement Type":                                            "PvmntType",
        "Divided Flag":                                             "DivdFlag",
        "Number of Travel Lanes":                                   "TrvlLnNmb",
        "Lane Miles":                                               "LaneMiles",
        "Pavement Type Code":                                       "PvmTypCod",
        "Lane Width":                                               "LaneWidth",
        "LDR":                                                      "LDR",
        "NDR":                                                      "NDR",
        "LM's Valid IRI":                                           "LMValdIRI",
        "S_Rut (in)":                                               "SRut_in",
        "NIRI Average":                                             "NIRI_Avrg",
        "IRI Left WP":                                              "IRILftWp",
        "IRI Right WP":                                             "IRIRigWp",
        "LM's Excellent IRI (0-59)":                                "LMExclIRI",
        "LM's Good IRI (60-99)":                                    "LMGoodIRI",
        "LM's Fair IRI (100-139)":                                  "LMFairIRI",
        "LM's Poor IRI (140-199)":                                  "LMPoorIRI",
        "LM's Very Poor IRI (200+)":                                "LMVrPrIRI",
        "Reflective Transverse Cracking Severity 2 (lin ft)":       "RTCS2_lft",
        "Transverse Cracking Severity 1(lin ft)":                   "TCS1_lft",
        "Transverse Cracking Severity 2 (lin ft)":                  "TCS2_lft",
        "Longitudinal Cracking Severity 1 (lin ft)":                "LCS1_lft",
        "Longitudinal Cracking Severity 2 (lin ft)":                "LCS2_lft",
        "Longitudinal Joint Severity 1 (lin ft)":                   "LJS1_lft",
        "Longitudinal Joint Severity 2 (lin ft)":                   "LJS2_lft",
        "Reflective Transverse Cracking Severity 1 (lin ft)":       "RTCS1_lft",
        "W_Rut (in)":                                               "W_Rut_in",
        "Reflective Transverse Cracking Severity 3 (lin ft)":       "RTCS3_lft",
        "Reflective Longitudinal Cracking Severity 1 (lin ft)":     "RLCS1_lft",
        "Reflective Longitudinal Cracking Severity 2 (lin ft)":     "RLCS2_lft",
        "Reflective Longitudinal Cracking Severity 3 (lin ft)":     "RLCS3_lft",
        "Distress Length":                                          "Dstrs_len",
        "Alligator Sev 1 (sf)":                                     "AgtrS1_sf",
        "Alligator Sev 2 (sf)":                                     "AgtrS2_sf",
        "Patching Area - Wheel Path (sf)":                          "PcAWP_sf",
        "Alligator Sev 3 (sf)":                                     "AgtrS3_sf",
        "Delamination Area (sf)":                                   "DelmnA_sf",
        "Patching Area - Non Wheel Path (sf)":                      "PcANWP_sf",
        "Route Name":                                               "RouteName",
        "County From":                                              "CntyFrom",
        "Direction":                                                "Direction",
        "Lane":                                                     "Lane",
        "County Beg. Milepoint":                                    "CntyBgMPt",
        "County To":                                                "CntyTo",
        "County End Milepoint":                                     "CntyEdMPt",
        "CCI":                                                      "CCI",
        "Potholes (count)":                                         "PothlsCnt",
        "Bleeding Sev. 1 (sf)":                                     "BldgS1_sf",
        "Bleeding Sev. 2 (sf)":                                     "BldgS2_sf",
        "No Distress Rated":                                        "NDstrsRat",
        "Start GPS Latitude":                                       "StrGPSLat",
        "Start GPS Longitude":                                      "StrGPSLng",
        "End GPS Latitude":                                         "EndGPSLat",
        "End GPS Longitude":                                        "EndGPSLng",
        "Bridge Flag":                                              "BrdgFlag",
        "Construction Flag":                                        "CnstrFlag",
        "Lane Deviation Flag":                                      "LnDevFlag",
        "Attachment":                                               "Attachmnt",
        "Comments":                                                 "Comments",
        "SECTIONKEY":                                               "SectnKey",
        "Field-Recorded Pavement Type":                             "FldRcPvTy",
        "Surface Type":                                             "SurfType",
        "Date Tested":                                              "DateTest",
        "Speed (mph)":                                              "Speed_mph",
        "Traffic Level (1,2,3)":                                    "TrfcLevel",
        "Number of Trucks":                                         "TrucksNo",
        "Strong ? (FWD)":                                           "StrongFWD",
        "Date/Time Updated":                                        "DatTimUpd",
        "User Update":                                              "UsrUpdate",
        "LRM Currency Date":                                        "LRMCurDat",
        "LRM Version Number":                                       "LRMVerNum",
        "Network Date":                                             "NetwkDate",
        "Previous Loc Ident":                                       "PrvLocID",
        "Repeat ?":                                                 "Repeat"}

    FIELD_TYPE_MAPPING = {
        "object":           ogr.OFTString,
        "float64":          ogr.OFTReal,
        "int64":            ogr.OFTInteger,
        "datetime64[ns]":   ogr.OFTDateTime}

    DESCRIPTION = "Convert VDOT 10th mile road condition XLS files into ESRI \
        shapefile where each feature can be either a point, a line, a buffered \
        line or polygon (rectangle) with extents identified by the GPS \
        start/stop latitude/longitude coordinates stored in the excel file."

    VERSION = "1.0.0"

    parser = argparse.ArgumentParser(description=DESCRIPTION, version=VERSION)

    parser.add_argument("input_xls",
                        help="Name of the excel file to use as input \
                        (required).")
    parser.add_argument("output_shp",
                        help="Name of the ESRI shapefile to use as output \
                        (required).")

    parser.add_argument("--sheet",
                        required=True,
                        help="Name of the excel sheet to process (required).")
    parser.add_argument("--layer",
                        required=True,
                        help="Name of the shapefile layer containing the data \
                        (required).")

    src_spref = parser.add_mutually_exclusive_group()
    src_spref.add_argument("--src_epsg",
                           type=int,
                           help="EPSG spatial reference code describing the \
                           source data projection.\n \
                           102746 corresponds to the:\n \
                           NAD_1983_StatePlane_Virginia_North_FIPS_4501_Feet")
    src_spref.add_argument("--src_url",
                           help="URL of spatial reference describing the source \
                           data projection. An example of acceptable URL is:\n \
                           http://spatialreference.org/ref/esri/102746/ogcwkt/\n \
                           This is the OGC WKT format for the:\n \
                           NAD_1983_StatePlane_Virginia_North_FIPS_4501_Feet\n \
                           from the spatialreference.com website.")

    dst_spref = parser.add_mutually_exclusive_group()
    dst_spref.add_argument("--dst_epsg",
                           type=int,
                           help="EPSG spatial reference code to be used in the \
                           shapefile.")
    dst_spref.add_argument("--dst_url",
                           help="URL of spatial reference to be used in the \
                           shapefile (see '--src_url).")

    parser.add_argument("--slat",
                        default="Start GPS Latitude",
                        help="Name of field containing starting GPS latitude \
                        (default: '%(default)s').")
    parser.add_argument("--slng",
                        default="Start GPS Longitude",
                        help="Name of field containing starting GPS longitude \
                        (default: '%(default)s').")
    parser.add_argument("--elat",
                        default="End GPS Latitude",
                        help="Name of field containing ending GPS latitude \
                        (default: '%(default)s').")
    parser.add_argument("--elng",
                        default="End GPS Longitude",
                        help="Name of field containing ending GPS longitude \
                        (default: '%(default)s').")

    parser.add_argument("--geom",
                        default="lines",
                        choices=("squares", "lines", "buffered", "points"),
                        help="Type of geometry created in the shapefile. \
                        (default: '%(default)s').")
    parser.add_argument("--buflen",
                        default=0.0,
                        type=float,
                        help="Buffer radius when 'buffered' is chosen for the \
                        option '--geom'. The radius is applied on both sides of \
                        each feature. The units are the same of the selected \
                        destination spatial reference (default: '%(default)3.2f').")

    parser.add_argument("-o", "--overwrite",
                        action="store_true",
                        help="Overwrite existing files (default: 'False').")

    args = parser.parse_args()

    print "\nUsing default values for star/end latitude/longitude fields:"
    print "- " + args.slat
    print "- " + args.slng
    print "- " + args.elat
    print "- " + args.elng

    # Open the excel file
    print "\nOpening sheet '{0}' from file '{1}'".format(args.sheet, args.input_xls)
    try:
        xldata = read_excel(args.input_xls, sheetname=args.sheet)
    except IOError:
        exit("\nERROR -> File '{0}' not found!".format(args.input_xls))
    except Exception as e:
        exit("\nERROR -> Error: '{0}'".format(e))

    # Source data spatial reference
    SRC_DEF_EPSG_SRS = 4326
    src_srs = osr.SpatialReference()
    if args.src_epsg:
        if src_srs.ImportFromEPSG(int(args.src_epsg)) != 0:
            exit("\nERROR -> Error setting the source data spatial reference to EPSG:{0}".format(args.src_epsg))
        else:
            print "\nSetting source data spatial reference to EPSG:{0}".format(args.src_epsg)
            print src_srs.ExportToPrettyWkt()
    elif args.src_url:
        if src_srs.ImportFromUrl(args.src_url) != 0:
            exit("\nERROR -> Error setting the source data spatial reference to ESRI:{0}".format(args.src_url))
        else:
            print "\nSetting source data spatial reference to URL:{0}".format(args.src_url)
            print src_srs.ExportToPrettyWkt()
    else:
        print "\nWARNING -> No spatial reference for source data is defined! Using default value!"
        if src_srs.ImportFromEPSG(SRC_DEF_EPSG_SRS) != 0:
            exit("\nERROR -> Error setting the source data spatial reference to EPSG:{0}".format(SRC_DEF_EPSG_SRS))
        else:
            print "\nSetting source data spatial reference to EPSG:{0}".format(SRC_DEF_EPSG_SRS)
            print src_srs.ExportToPrettyWkt()

    # Destination shapefile spatial reference
    dst_srs = osr.SpatialReference()
    if args.dst_epsg:
        if dst_srs.ImportFromEPSG(int(args.dst_epsg)) != 0:
            exit("\nERROR -> Error setting the shapefile spatial reference to EPSG:{0}".format(args.dst_epsg))
        else:
            print "\nSetting the shapefile spatial reference to EPSG:{0}".format(args.dst_epsg)
            print dst_srs.ExportToPrettyWkt()
    elif args.dst_url:
        if dst_srs.ImportFromUrl(args.dst_url) != 0:
            exit("\nERROR -> Error setting the shapefile spatial reference to ESRI:{0}".format(args.dst_url))
        else:
            print "\nSetting shapefile spatial reference to URL:{0}".format(args.dst_url)
            print dst_srs.ExportToPrettyWkt()
    else:
        print "\nWARNING -> No spatial reference will be defined for the shapefile!"

    # Define coordinate transformation
    transf = osr.CoordinateTransformation(src_srs, dst_srs)

    # Prepare ESRI shapefile
    DRIVER = "ESRI Shapefile"
    print "\nCreating shapefile '{0}' using '{1}' features".format(args.output_shp, args.geom)
    drv = ogr.GetDriverByName(DRIVER)
    if drv is None:
        exit("\nERROR -> Driver '{0}' not available!".format(DRIVER))
    if args.overwrite:
        if exists(args.output_shp):
            drv.DeleteDataSource(args.output_shp)
    shp = drv.CreateDataSource(args.output_shp)
    if shp is None:
        exit("\nERROR -> Error creating shapefile '{0}'!".format(args.output_shp))
    print "\nCreating layer '{0}'".format(args.layer)
    if args.geom == "points":
        lyr = shp.CreateLayer(args.layer, srs=dst_srs, geom_type=ogr.wkbPoint)
    elif args.geom == "lines":
        lyr = shp.CreateLayer(args.layer, srs=dst_srs, geom_type=ogr.wkbLineString)
    else:  # Buffered and squares are both polygons
        lyr = shp.CreateLayer(args.layer, srs=dst_srs, geom_type=ogr.wkbPolygon)

    if lyr is None:
        exit("\nERROR -> Error creating layer '{0}'!".format(args.layer))

    # List fields in excel file and create corresponding fields in shapefile
    print "\nMapping of fields contained in '{0}'/'{1}':".format(args.input_xls, args.sheet)
    for a, b in xldata.dtypes.iteritems():
        f_name = FIELD_NAME_MAPPING[a]
        f_type = FIELD_TYPE_MAPPING[str(b)]
        print "{0:52} -> {1}".format(a, f_name)
        field = ogr.FieldDefn(f_name, f_type)
        if lyr.CreateField(field) != 0:
            exit("\nERROR -> Error creating field '{0}' mapped from type '{1}'".format(f_name, b))

    # Load the columns labels
    labels = xldata.columns

    # Iterate through rows of the excel file and add corresponding features to
    # the shapefile
    print "\nAdding features to '{0}' based on entries in '{1}'".format(args.output_shp, args.input_xls)
    xl_len = len(xldata)
    for row in range(xl_len):
        # Get starting/ending GPS coordinates
        slat, slng, elat, elng = xldata.ix[row][[args.slat, args.slng, args.elat, args.elng]]

        # Create the requested feature geometry
        if args.geom =="points":
            # If points, only add the strat GPS coordinates.
            # TODO: better implementation that includes all points without
            # repetitions.
            geom = ogr.Geometry(ogr.wkbPoint)
            geom.AddPoint(slng, slat)
            geom.Transform(transf)  # Convert to destination spatial reference
        elif args.geom == "squares":
            # Create a linear 2D ring (base for polygons)
            ring = ogr.Geometry(ogr.wkbLinearRing)
            ring.AddPoint(slng, slat)
            ring.AddPoint(elng, slat)
            ring.AddPoint(elng, elat)
            ring.AddPoint(slng, elat)
            ring.CloseRings()
            ring.Transform(transf)  # Convret to destination spatial reference

            # Create a polygon using the ring (rectangle)
            geom = ogr.Geometry(ogr.wkbPolygon)
            geom.AddGeometry(ring)
        else:  # Both lines and buffered start with linear features:
            # Create a linear feature
            geom = ogr.Geometry(ogr.wkbLineString)
            geom.AddPoint(slng, slat)
            geom.AddPoint(elng, elat)
            geom.Transform(transf)  # Convert to destination spatial reference
            if args.geom == "buffered":
                geom = geom.Buffer(args.buflen)

        # Prepare the feature
        featDef = lyr.GetLayerDefn()  # Get feature definition from the layer
        feat = ogr.Feature(featDef)  # Create a new feature
        feat.SetGeometry(geom)  # Set the geometry of the feature

        # Fill the fields with the corresponding values
        for l in labels:
            feat.SetField(FIELD_NAME_MAPPING[l], str(xldata.ix[row][l]))

        # Create (add) the feature
        if lyr.CreateFeature(feat) != 0:
            exit("ERROR -> Failure creating feature '{0}' in shapefile layer!".format(row))

        # Clean up
        feat.Destroy()
        geom.Destroy()
        if args.geom == "squares":
            ring.Destroy()

        # Update progress display
        stdout.write("{0:3.2f}%\r".format(100.0 * (1 + row) / xl_len))
        stdout.flush()

    # Close shapefile
    shp.Destroy()

    print "\nConversion of {0} features from '{1}'/'{2}' to '{3}' completed!".format(xl_len, args.input_xls, args.sheet, args.output_shp)

if __name__ == "__main__":
    main()