# -*- coding: utf-8 -*-
"""
Created on Thu Jul  9 11:46:06 2015
Name:    prjpnt.py
Purpose: Project a point from a set of coordinates to another
Author:  Andrea Vaccari (av9g@virginia.edu)
"""


try:
    from osgeo import ogr
except ImportError:
    exit("\nERROR -> OGR required to handle projections")

try:
    from osgeo import osr
except ImportError:
    exit("\nERROR -> OSR required to handle projections")


# Transform coordinates from one spatial reference to another
class prjpnt(object):
    """
    Transform a point from a set of coordinates to another
    """
    def __init__(self, src_srs, dst_srs):
        self.ok = True
        self.trans = osr.CoordinateTransformation(src_srs, dst_srs)
        self.point = ogr.Geometry(ogr.wkbPoint)
        self.point.AddPoint(0, 0)

    @classmethod
    def epsg(self, src_epsg, dst_epsg):
        self.ok = True
        src_srs = osr.SpatialReference()
        if src_srs.ImportFromEPSG(src_epsg) != 0:
            self.ok = False

        dst_srs = osr.SpatialReference()
        if dst_srs.ImportFromEPSG(dst_epsg) != 0:
            self.ok = False

        if self.ok:
            self.trans = osr.CoordinateTransformation(src_srs, dst_srs)
            self.point = ogr.Geometry(ogr.wkbPoint)

    def prj_coo(self, coo_src):
        if self.ok:
            self.point.SetPoint(0, coo_src[0], coo_src[1])
            self.point.Transform(self.trans)
            return [self.point.GetX(), self.point.GetY()]
        else:
            return coo_src

    def isok(self):
        return self.ok

    def __del__(self):
        self.point.Destroy()
