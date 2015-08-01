# -*- coding: utf-8 -*-
"""
Created on Thu Jul  9 11:42:41 2015
Name:    shp2df.py
Purpose: Load a shapefile and stores it into a dataframe.
Author:  Andrea Vaccari (av9g@virginia.edu)
"""

from os.path import splitext

try:
    import shapefile as shp
except ImportError:
    exit("\nERROR -> pyshp required to read shapefiles")

try:
    from prjpnt import prjpnt
except ImportError:
    exit("\nERROR -> prjpnt required to handle projections")

try:
    from osgeo import osr
except ImportError:
    exit("\nERROR -> OSR required to handle projections")

try:
    import numpy as np
except ImportError:
    exit("\nERROR -> Numpy required")

try:
    import pandas as pd
except ImportError:
    exit("\nERROR -> Pandas required to edit excel XLS files")


# Reads a point shapefile and returns a dataframe
class shp2df(object):
    """
    Reads a point geometry shapefile and stores it in a pandas dataframe.
    """

    # TODO: allow multiple shape files. This requires the merging of the data
    # between the multiple files into a single dataframe to be returned
    def __init__(self, shp_in, out_srs=None):
        print "\nOpening and reading shapefile '{0}'.".format(shp_in)
        try:
            self.__shp_rd = shp.Reader(shp_in)
        except shp.ShapefileException:
            exit("\nERROR -> File '{0}' not found".format(shp_in))

        # Import projection
        prj_file = splitext(shp_in)[0] + '.prj'
        try:
            shp_prj = open(prj_file)
        except IOError:
            exit("\nERROR -> Could not find projection file '{0}'.".format(prj_file))
        else:
            with shp_prj:
                prj_txt = shp_prj.read()
                self.__shp_srs = osr.SpatialReference()
                if self.__shp_srs.ImportFromESRI([prj_txt]) != 0:
                    exit("\nERROR -> Error importing the projection information from '{0}'.".format(shp_in))

        # Store requested spatial reference
        self.__out_srs = out_srs

        # If destination coordinates are specified
        if self.__out_srs:
            # Define the coordinates transformation
            self.__trans = prjpnt(self.__shp_srs, self.__out_srs)
        else:
            self.__trans = None

        # Initialize data loaded indicator
        self.__dataLoaded = False

        # Define coordinate labels
        self.__coo_lbl = ['SHP_X', 'SHP_Y']

        # An empty dictionary to store the data for internal representation
        self.__data = {}

    def getCooLabels(self):
        """
        Returns the labels used for the point coordinates.
        """
        return self.__coo_lbl

    def getDataLoaded(self):
        """
        Checks if the data has been loaded
        """
        return self.__dataLoaded

    def getDF(self):
        """
        Returns the dataframe containing the shapefile data.
        """
        # Check if data is loaded
        if self.__dataLoaded is False:
            self.__loadData()

        return pd.DataFrame(self.__data)

    def getDict(self):
        """
        Returns the dictionary containing the shapefile data.
        """
        # Check if data is loaded
        if self.__dataLoaded is False:
            self.__loadData()

        return self.__data

    def getSrs(self):
        """
        Returns the original shapefile spatial reference as an OSR object.
        """
        return self.__shp_srs

    def getBbox(self):
        """
        Returns the bounding box as stored within the shapefile. This is stored
        as `[TopLeft_X, TopLeft_Y, Bottom_Right_X, Bottom Right_Y]`.
        """
        # Load bounding box
        bbox_in = self.__shp_rd.bbox

        # Check if we need to convert to different spatial reference
        if self.__trans:
            self.__bbox = self.__trans.prj_coo(bbox_in[:2])
            self.__bbox.extend(self.__trans.prj_coo(bbox_in[2:]))
        else:
            self.__bbox = bbox_in

        return self.__bbox

    def getExtent(self):
        """
        Returns the extent (envelope) of the image in the output coordinates.
        This is calculated as `[Min_X, Min_Y, Max_X, Max_Y]`'
        """
        # Check if data is loaded
        if self.__dataLoaded is False:
            self.__loadData()

        # Extract coodrinates extremes for extent calculation
        xmin = np.min(self.__data[self.__coo_lbl[0]])
        xmax = np.max(self.__data[self.__coo_lbl[0]])
        ymin = np.min(self.__data[self.__coo_lbl[1]])
        ymax = np.max(self.__data[self.__coo_lbl[1]])

        return [xmin, ymin, xmax, ymax]

    def __loadData(self):
        """
        Loads the data from the shapefile.
        """
        # Load the data from the file and drop non point shapes
        records = [(r.shape.points[0], r.record) for r in self.__shp_rd.iterShapeRecords() if r.shape.shapeType==1]
        shp_coo = [r[0] for r in records]

        # If destination coordinates are specified
        if self.__trans:
            # Convert the coordinates to the destination spatial reference
            xls_coo_x = []
            xls_coo_y = []
            for c in shp_coo:
                coo_out = self.__trans.prj_coo(c)
                xls_coo_x.append(coo_out[0])
                xls_coo_y.append(coo_out[1])
            self.__data[self.__coo_lbl[0]] = xls_coo_x
            self.__data[self.__coo_lbl[1]] = xls_coo_y
        else:
            self.__data[self.__coo_lbl[0]] = [c[0] for c in shp_coo]
            self.__data[self.__coo_lbl[1]] = [c[1] for c in shp_coo]

        # Extract the non-geometry data
        rec = [r[1] for r in records]
        itors = map(iter, [r for r in rec])
        for f in self.__shp_rd.fields[1:]:
            self.__data[f[0]] = map(next, itors)

        # Store the fact that data was loaded
        self.__dataLoaded = True

