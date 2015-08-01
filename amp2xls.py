# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 14:00:26 2015
Name:    amp2xls.py
Purpose: Creates a copy, named by appending '_<period>_[_AMP][_SHP]
    [_TS][_DIF]' to the input file(s) name(s), of the selected xls input
    file(s) containing the pavement conditions. The values between square
    brackets will be included if the corresponding data was merged. Depending
    on the selected options, the new file will contain the original data plus
    the time series of the SAR amplitude values for each pixel at the
    coordinates identified in the original files, the location, distance,
    general information and time series of the displacements of the closest
    SqueeSAR scatter to each entry in the original files, and the velocity,
    and standard deviation of the velocity for the temporary scatters at the
    coordinates identified in the original files. The script will also
    generate both a CSV file and a pickled pandas dataframe containing
    original coordinates, pavement condition matrices (as selected by 'corr'
    between those available in the original files), time series of the SAR
    amplitude values, all the information, the time series as well as the
    distance for the SqueeSAR scatterer closest to each of the original
    coordinates and the velocity and its standard deviation for the temporary
    scatters corresponding to the original coordinates.
Author:  Andrea Vaccari (av9g@virginia.edu)
Version: 1.0.0
"""
import re
import argparse
from glob import glob
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from os.path import splitext, dirname, join


try:
    import numpy as np
except ImportError:
    exit("\nERROR -> Numpy required")

try:
    from scipy.spatial import KDTree
except ImportError:
    exit("\nERROR -> Scipy required")

try:
    import pandas as pd
except ImportError:
    exit("\nERROR -> Pandas required to edit excel XLS files")

try:
    from osgeo import gdal
except ImportError:
    exit("\nERROR -> GDAL required to read raster files")

try:
    from osgeo import osr
except ImportError:
    exit("\nERROR -> OSR required to handle projections")

try:
    from shp2df import shp2df
except ImportError:
    exit("\ERROR -> shp2df reuired to load shapefile data")

try:
    from prjpnt import prjpnt
except ImportError:
    exit("\nERROR -> prjpnt required to handle projections")


def process_date_range(stack, min_date, max_date, differential=False, prefix=''):
    """Finds dates within a range starting from a stack of file names \
    containing dates information.

    Parameters
    ----------
    stack : iterable
        List containing the date information as ``YYYYMMDD``. The list
        is expected to be sorted in ascending order by the contained date.
    min_date : datetime
        The low end of the selected date range
    max_date : datetime
        The high end of the selected date range
    differential : bool, optional
        If the following analysis is differential, this should be set to
        ``True``. This will mark as ``differential`` the ``processing`` field
        of the file temporally just before the first allowed. (Default:
        ``False``)
    prefix : str, optional
        A string that is going to be prepended to the output ``date`` value.

    Returns
    -------
    dict
        A dictionary, keyed by the items in ``stack`` sorted in ascending
        order, containing a dictionary with the following
        ``key -> value`` pairs:
            date : str
                string version of date: ``prefix + YYYYMMDD``
            dt_date : datetime
                datetime representation of ``date``
            months : float
                fractional months between the current date and the previous one
            processing : str
                type of processing required by the stack elemtn. The following
                are the possible values: **full** - inside the date range,
                **differential** - outside of date range but required to
                evaluate the difference in values with the following file,
                **skip** - outside of the date range.
        If no dates are found within the stack, ``None`` is returned.
    """
    dates = {}
    prev_date = dt.min
    prev_file = None
    for f in stack:
        # Look for the date field
        tk = re.search("[0-9]{8}", f)
        if tk is None:
            continue

        # Store string and datetime dates in dictionary
        date = prefix + tk.group(0)
        dt_date = dt.strptime(date, prefix + "%Y%m%d")
        if dt_date < prev_date:
            exit("\nERROR -> Dates should be sorted in ascending order!")
        if prev_date == dt.min:
            months = 0.0
        else:
            delta = dt_date - prev_date
            months = 12 * delta.days / 365.25

        # Check processing method for specific date
        if dt_date < min_date or dt_date > max_date:
            processing = 'skip'
        else:
            processing = 'full'
            # If differential processing required
            if differential is True and prev_file is not None:
                if dates[prev_file]['processing'] == 'skip':
                    dates[prev_file]['processing'] = 'differential'

        # Create dictionary entry
        dates.setdefault(f, {'date': date})
        dates[f]['dt_date'] = dt_date
        dates[f]['months'] = months
        dates[f]['processing'] = processing
        prev_file = f
        prev_date = dt_date

    # If dates is still empty, exit
    if not dates:
        return None

    return dates


def amp2xls(xls_in,  # args.xls_in
            amp_in=None,  # args.amp_in
            shp_in=None,  # args.shp_in
            ts_in=None,  # args.ts_in
            xls_epsg=4326, # args.xls_epsg
            xls_sheet_in=['IS', 'PR', 'SC'],  # args.xls_sheet_in
            keep_bad=False,  # args.keep_bad
            ndval=-9999.0,  # args.ndval
            period="winter",  # args.period
            corr=['NIRI Average', 'CCI', 'CCI Class'],  # args.corr
            pkfile=None,  # args.pkfile
            csvfile=None,  # args.txtfile
            differential=False,  # args.differential
            prepend="",  # args.prepend
            verbose=False):  # args.verbose

    # Some default values that can be turned into arguments later on
    slng = 'Start GPS Longitude'  # XLS column containing the staring GPS longitude
    slat = 'Start GPS Latitude'  # XLS column containing the staring GPS latitued
    dtest = 'Date Tested'  # XLS column contining the date when the section of road was tested
    year = 'Year'  # XLS column contining the official year for the dataset
    ts_keys = ['VEL_STDEV', 'VEL']  # Keywords identitying temporary raster files

    # Load the input excel file names
    xls_stack = glob(xls_in)
    if not xls_stack:
        exit("\nERROR -> No excel files were selected using '{0}'".format(xls_in))
    else:
        print "\nAnalyzing following excel files:"
        for x in xls_stack:
            print "- {0}".format(x)

    # Check if at least another source is selected
    if amp_in is None and shp_in is None and ts_in is None:
        exit("\nERROR -> At least and additional source (amplitude, SqueeSAR or Temporarary Scatterer) should be chosen for data extraction.")

    # Define the destination (excel) spatial reference
    xls_srs = osr.SpatialReference()
    if xls_srs.ImportFromEPSG(int(xls_epsg)) != 0:
        exit("\nERROR -> Error setting the destination data spatial reference to EPSG:{0}".format(xls_epsg))

    # Define prepend string
    if prepend != "":
        prepend += "_"

    # Load the SAR amplitude stack file names
    af = ""
    if amp_in is not None:
        sar_stack = [f for f in glob(amp_in) if f[-4:] == '.tif']
        if not sar_stack:
            exit("\nERROR -> No SAR amplitude files were selected using '{0}'".format(amp_in))
        sar_stack.sort()  # Sort the files
        # Initialize SAR spatial reference
        sar_srs = osr.SpatialReference()
        af = "_AMP"

    # If selected, open the shapefile containing displacement data
    sf = ""
    if shp_in is not None:
       # Load shapefile data
        shp = shp2df(shp_in, out_srs=xls_srs)
        shp_dat = shp.getDF()
        # Initialize spatial search tree
        [shp_x_lbl, shp_y_lbl] = shp.getCooLabels()
        kdt = KDTree(shp_dat[[shp_x_lbl, shp_y_lbl]].values)
        sf = "_SHP"

    # If selected, load the temporary scatterer files
    tsf = ""
    if ts_in is not None:
        ts_stack = [f for f in glob(ts_in) if f[-4:] == '.tif']
        if not ts_stack:
            exit("\nERROR -> No temporary scatterer files were selected using '{0}'".format(ts_in))
        # Initialize the TS spatial reference
        ts_srs = osr.SpatialReference()
        tsf = "_TS"

    # Differential processing
    dif = ""
    if differential is True:
        dif = "_DIF"

    # Load the list of correlating values selected by the user
    clist = list(corr)
    ccl = None
    # Check if the user selected 'CCI Class'
    if clist.count('CCI Class') == 1:
        ccl = clist.index('CCI Class')
        clist[ccl] = 'CCI'

    # Define the last element of the output files name
    if len(clist) > 1:
        cf = "_many"
    else:
        cf = "_" + list(corr)[0]

    # Process all the files in the xls stack
    for xls_in in xls_stack:
        print "\nOpening excel file '{0}' as input".format(xls_in)
        try:
            xlfil = pd.ExcelFile(xls_in)
        except IOError:
            exit("\nERROR -> File '{0}' not found!".format(xls_in))
        except Exception as e:
            exit("\nERROR -> Error: '{0}'".format(e))

        # Load the list of sheets selected by the user
        xls_data = xlfil.parse(list(xls_sheet_in))

        # Open output excel file
        # If using XLSX, pandas requires for openpyxl to be version 1.6.1 or
        # higher, but lower than 2.0.0.
        # When using XLS, the limit is 256 columns and 65535 rows.
        # TODO: move the decision at the end of the file where teh number of
        #       columns and rows is known. Then select driver and extension
        #       based on the amount of rows and columns.
        name, ext = splitext(xls_in)
        ext = '.xlsx'
        xls_out = prepend + name + "_" + period + af + sf + tsf + dif + ext
        print "- Creating excel file '{0}' as output".format(xls_out)
        try:
            writer = pd.ExcelWriter(xls_out)
        except IOError:
            exit("\nERROR -> File '{0}' not found!".format(xls_out))
        except Exception as e:
            exit("\nERROR -> Error: '{0}'".format(e))

        # Iterate over the selected sheets
        for sheet_in, xldata in xls_data.items():
            print "  - Processing input sheet '{0}'".format(sheet_in)

            # Clear NaN data
            xldata.fillna(0, inplace=True)

            lxldata = len(xldata)  # Length of the xldata frame
            npout_fields = list(clist)  # Copy of the corr list

            # Extract GPS start coordinates
            xls_coo = xldata[[slng, slat]].values

            # Evaluate the date range based on user selection
            meas_year = dt.strptime(str(xldata[year].irow(0)), "%Y")
            if period == "year":
                dates = [dt.strptime(str(d), "%Y%m%d") for d in xldata[dtest].values]
                max_date = max(dates)
                min_date = max(dates) - relativedelta(years=1)
            elif period == "winter":
                min_date = meas_year - relativedelta(months=3)
                max_date = meas_year + relativedelta(months=3)
            elif period == "all":
                min_date = dt.min
                max_date = dt.max
            else:
                exit("\nERROR -> The defined period ({0}) is not allowed".format(period))

            if period == "all":
                print "    - Using all available dates."
            else:
                print "    - Range of dates ({0}): {1} -> {2}".format(period, dt.strftime(min_date, "%Y-%m-%d"), dt.strftime(max_date, "%Y-%m-%d"))

            # For each SAR amplitude file, extract the amplitude values at the GPS
            if amp_in is not None:
                # Find dates to process and define processing method
                dates = process_date_range(sar_stack, min_date, max_date, differential, prefix='A')
                if dates is None:
                    exit("\nERROR -> No dates found inside {}".format(sar_stack))

                # Process amplitude files
                diff_fields = []
                diff_dict = {}
                for f in sar_stack:
                    # Skip if date is out of range
                    processing = dates[f]['processing']
                    if processing == 'skip':
                        continue

                    # Open SAR amplitude raster files
                    if verbose:
                        print "      - Extracting amplitude values from '{0}'".format(f)
                    tf = gdal.Open(f)
                    if sar_srs.ImportFromWkt(tf.GetProjectionRef()) != 0:
                        exit("\nERROR -> Error importing the projection information from '{0}'.".format(f))
                    xls2sar = prjpnt(xls_srs, sar_srs)
                    geo = tf.GetGeoTransform()
                    tfb = tf.GetRasterBand(1)
                    sar_ndval = tfb.GetNoDataValue()
                    lng_max = tfb.XSize - 1
                    lat_max = tfb.YSize - 1

                    # Loop through the coordinates in the xls
                    amp = np.zeros(lxldata)
                    for i in range(lxldata):
                        # Convert xls coordinates to raster coordinates
                        [lng, lat] = xls2sar.prj_coo(xls_coo[i])

                        # Calculate pixel location in raster coordinates
                        plng = int((lng - geo[0]) / geo[1])
                        plat = int((lat - geo[3]) / geo[5])

                        # Check if it's inside the raster file.
                        # It it is, gather amplitude.
                        if plng < 0 or plng > lng_max or plat < 0 or plat > lat_max:
                            amp[i] = np.nan
                        else:
                            amp[i] = tfb.ReadAsArray(plng, plat, 1, 1)

                        # Check if amplitude is valid.
                        if amp[i] == 0 or amp[i] == ndval or amp[i] == sar_ndval:
                            amp[i] = np.nan

                        # Mark row as bad if the corr value is negative or zero
                        if np.any(xldata[clist].irow(i) < 0):
                            amp[i] = np.nan

                    # Close gdal handles
                    tfb = None
                    tf = None

                    # If differential processing and differential frame, just
                    # store the data.
                    if differential:
                        # If differential frame
                        if processing == 'differential':
                            prev_amp = amp.copy()
                            continue

                    # If regular frame, store data
                    date = dates[f]['date']
                    xldata[date] = amp
                    npout_fields.append(date)

                    # If differential processing
                    if differential:
                        months = dates[f]['months']
                        if months != 0:
                            diff_name = 'D' + date + "({})".format(months)
                            diff_dict[diff_name] = (amp - prev_amp) / months
                            diff_fields.append(diff_name)
                        prev_amp = amp.copy()

                # If differential processing, add data
                if differential:
                    # Insert differential data in xdata after amplitude
                    xldata = pd.concat((xldata, pd.DataFrame(diff_dict)), axis=1)
                    # Append field names to npout
                    npout_fields.extend(diff_fields)

                # Remove rows marked as to be removed
                if not keep_bad:
                    xldata.dropna(inplace=True)
                    xldata.reset_index(drop=True, inplace=True)
                    xls_coo = xldata[[slng, slat]].values
                    lxldata = len(xldata)

            # If shapefile need to be analyzed
            if shp_in is not None:
                # Clear the xls data outside the shapefile bounding box
                shp_extent = shp.getExtent()
                xldata = xldata[xldata[slng] >= shp_extent[0]]
                xldata = xldata[xldata[slng] <= shp_extent[2]]
                xldata = xldata[xldata[slat] >= shp_extent[1]]
                xldata = xldata[xldata[slat] <= shp_extent[3]]
                xldata.reset_index(drop=True, inplace=True)
                xls_coo = xldata[[slng, slat]].values
                lxldata = len(xldata)

                # Look into the shapefile for the nearest point
                print "    - Looking for neighbors in shapefile"
                neigh, neigh_idx = kdt.query(xls_coo)
                print "    - Extracting SqueeSAR values from neighbors"
                n_shp = shp_dat.iloc[neigh_idx]

                # Extract processing information
                dates = process_date_range(n_shp.columns.values, min_date, max_date, differential, prefix='D')
                if dates is None:
                    exit("\nERROR -> No dates found inside {}".format(n_shp.columns.values))

                # Process the shapefile fields
                diff_fields = []
                diff_dict = {}
                for lbl in n_shp.columns.values:
#                    for date in n_shp.filter(regex='D[0-9]{8}').columns.values:
                    # Process the date fields
                    if re.search("D[0-9]{8}", lbl):
                        # Skip if date is out of range
                        processing = dates[lbl]['processing']
                        if processing == 'skip':
                            continue

                        # Get displacement data and store it
                        disp = n_shp[lbl].values

                        # If differential processing and differential frame, just
                        # store the data.
                        if differential:
                            if processing == "differential":
                                prev_disp = disp.copy()
                                continue

                        # If regular frame, store data
                        xldata[lbl] = disp
                        npout_fields.append(lbl)

                        # If differential processing
                        if differential:
                            months = dates[lbl]['months']
                            if months != 0:
                                diff_name = 'D' + lbl + "({})".format(months)
                                diff_dict[diff_name] = (disp - prev_disp) / months
                                diff_fields.append(diff_name)
                            prev_disp = disp.copy()
                    else:
                        xldata[lbl] = n_shp[lbl].values
                        npout_fields.append(lbl)

                # If differential processing, add data
                if differential:
                    # Insert differential data in xdata after amplitude
                    xldata = pd.concat((xldata, pd.DataFrame(diff_dict)), axis=1)
                    # Append field names to npout
                    npout_fields.extend(diff_fields)

                # Calculate the approximate distance between the points
                lt1 = np.radians(np.asarray(xls_coo[:, 1]))
                lt2 = np.radians(xldata[shp_y_lbl].values)
                ln1 = np.radians(np.asarray(xls_coo[:, 0]))
                ln2 = np.radians(xldata[shp_x_lbl].values)
                x = (ln2 - ln1) * np.cos(0.5 * (lt2 + lt1))
                y = lt2 - lt1
                dist = 6371000. * np.sqrt(x*x + y*y)
                xldata['Aprx. Distance (m)'] = dist
                npout_fields.append('Aprx. Distance (m)')

            # Add the TS information to output dataframe
            if ts_in is not None:
                # Look into the shapefile for the nearest point
                print "    - Extracting temporary scatter values"

                # Initialize temporary dictionary to hold data
                ts_dict = dict.fromkeys(ts_stack, [])

                # For each file store the data corresponding to the xls coordinates
                for f in ts_stack:
                    if verbose is True:
                        print "      - Extracting TS values from '{0}'".format(f)
                    tf = gdal.Open(f)
                    if ts_srs.ImportFromWkt(tf.GetProjectionRef()) != 0:
                        exit("\nERROR -> Error importing the projection information from '{0}'.".format(f))
                    xls2ts = prjpnt(xls_srs, ts_srs)
                    geo = tf.GetGeoTransform()
                    tfb = tf.GetRasterBand(1)
                    ts_ndval = tfb.GetNoDataValue()
                    lng_max = tfb.XSize - 1
                    lat_max = tfb.YSize - 1

                    # Loop through the coordinates
                    ts_val = np.zeros(lxldata)
                    for i in range(lxldata):
                        # Convert xls coordinates to TS raster coordinates
                        [lng, lat] = xls2ts.prj_coo(xls_coo[i])

                        # Calculate pixel location in TS raster coordinates
                        plng = int((lng - geo[0]) / geo[1])
                        plat = int((lat - geo[3]) / geo[5])

                        # Check if it's inside the raster file.
                        # If it is, gather TS values
                        if plng < 0 or plng > lng_max or plat < 0 or plat > lat_max:
                            ts_val[i] = np.nan
                        else:
                            ts_val[i] = float(tfb.ReadAsArray(plng, plat, 1, 1))

                        # Check if the value is valid
                        if ts_val[i] == ts_ndval or ts_val[i] == ndval:
                            ts_val[i] = np.nan

                    # Store values in temporary dictionary
                    ts_dict[f] = ts_val

                    # Close gdal handles
                    tfb = None
                    tf = None

                # TODO: For keys that can be included within other keys (for
                # example 'VEL' and 'VEL_STDEV') it is assumed that they are
                # provided in 'contains' order: 'VEL_STDEV' should come before
                # 'VEL'. See if there is a way to automatically accomplish this
                # without expecting the user to specify them in order.

                # Associate files to user provided keys
                ts_k_dict = {}
                ts_set = set(ts_stack)
                for k in ts_keys:
                    ts_k_dict[k] = [f for f in ts_set if f.count(k)]
                    ts_set = ts_set - set(ts_k_dict[k])

                # Merge data and add to output dataframe
                for k, v in ts_k_dict.iteritems():
                    xldata["TS_" + k] = np.nan * np.ones(lxldata)
                    npout_fields.append("TS_" + k)
                    for f in v:
                        xldata["TS_" + k] = np.fmax(xldata["TS_" + k], ts_dict[f])

                # Remove bad data
                if not keep_bad:
                    xldata.dropna(inplace=True)
                    xldata.reset_index(drop=True, inplace=True)
                    xls_coo = xldata[[slng, slat]].values

            # Extract subarray to pickle and convert to CSV
            npout = xldata[npout_fields].copy()

            # If the user selected 'CCI Class'
            if ccl is not None:
                # Function to map CCI values to classes
                def cci2class(cci):
                    ccicl = np.zeros_like(cci)
                    ccicl[cci <= 100] = 4
                    ccicl[cci < 90] = 3
                    ccicl[cci < 70] = 2
                    ccicl[cci < 60] = 1
                    ccicl[cci < 50] = 0
                    return ccicl

                npout.columns.values[ccl] = 'CCI Class'
                cci = npout.loc[:, 'CCI Class'].values
                npout.loc[:, 'CCI Class'] = cci2class(cci)

            # Add xls coordinates to output dataframe
            npout.insert(0, 'XLS Longitude', xls_coo[:, 0])
            npout.insert(1, 'XLS Latitude', xls_coo[:, 1])

            # Define basic name for output files
            name = prepend + dt.strftime(meas_year, "%Y") + "_" + sheet_in + "_" + period + af + sf + tsf + dif + cf

            # Store table in pickle file
            if pkfile is None:
                npkl = name + ".pkl"
            else:
                npkl = pkfile
            pth = join(dirname(xls_in), npkl)
            print "    - Saving pickled dataframe to '{0}'".format(pth)
            npout.to_pickle(pth)

            # Store table in CSV file
            if csvfile is None:
                ncsv = name + ".csv"
            else:
                ncsv = csvfile
            pth = join(dirname(xls_in), ncsv)
            print "    - Saving CSV dataframe to '{0}'".format(pth)
            npout.to_csv(pth, index=False)

            # Write to the corresponding sheet in new file
            print "    - Writing to output sheet: '{0}'".format(sheet_in)
            xldata.to_excel(writer, sheet_name=sheet_in, index=False)

        # Save and close xls file
        writer.save()
        writer.close()




if __name__ == "__main__":
    # If this is used as a script, parse the arguments
    DESCRIPTION = "Creates a copy, named by appending '_<period>_[_AMP][_SHP]\
    [_TS][_DIF]' to the input file(s) name(s), of the selected xls input \
    file(s) containing the pavement conditions. The values between square \
    brackets will be included if the corresponding data was merged. Depending \
    on the selected options, the new file will contain the original data plus \
    the time series of the SAR amplitude values for each pixel at the \
    coordinates identified in the original files, the location, distance, \
    general information and time series of the displacements of the closest \
    SqueeSAR scatter to each entry in the original files, and the velocity, \
    and standard deviation of the velocity for the temporary scatters at the \
    coordinates identified in the original files. The script will also \
    generate both a CSV file and a pickled pandas dataframe containing \
    original coordinates, pavement condition matrices (as selected by 'corr' \
    between those available in the original files), time series of the SAR \
    amplitude values, all the information, the time series as well as the \
    distance for the SqueeSAR scatterer closest to each of the original \
    coordinates and the velocity and its standard deviation for the temporary \
    scatters corresponding to the original coordinates."

    VERSION = "1.0.0"

    parser = argparse.ArgumentParser(description=DESCRIPTION, version=VERSION)

    parser.add_argument("xls_in",
                        help="Base name of the excel files containing the \
                        pavement condition info. If a regualr expression is \
                        passed, it should be enclosed in double quotes. All \
                        the files identified by the expression will be \
                        processed. (required).")

    parser.add_argument("-a", "--amp_in",
                        help="Base name of the stack of SAR amplitude raster \
                        images. If a regular expression is used, it should be \
                        enclosed in double quotes. All the files identified \
                        by the expression will be processed. It is expected \
                        for the name to include a date field formatted as \
                        'DYYYYMMDD'.")
    parser.add_argument("-s", "--shp_in",
                        help="Name of the shapefile containing the SqueeSAR \
                        displacement data.")
    parser.add_argument("-t", "--ts_in",
                        help="Base name of the raster files containing the \
                        temporary scatterers data. If a regular expression is \
                        used, it should be enclosed in double quotes. All the \
                        files identified by the expression will be processed. \
                        The file names should include 'VEL' and 'VEL_STDEV'. \
                        All the files including each of the fields will be \
                        merged to provide a single value.")

    parser.add_argument("-e", "--xls_epsg",
                        type=int,
                        default=4326,
                        help="EPSG spatial reference code to be used when \
                        reading the data from the excel source. This will be \
                        used to georeference all the other data sources. \
                        (Default: %(default)s - Corresponding to WGS84).")

    parser.add_argument("-x", "--xls_sheet_in",
                        default=['IS', 'PR', 'SC'],
                        nargs="+",
                        help="Space separated strings containing the names of \
                        the excel sheets to process within each 'xls_in'. \
                        (Default: %(default)s).")
    parser.add_argument("-b", "--keep_bad",
                        action="store_true",
                        help="If selected will keep rows including amplitude \
                        values equal to 0.0 or no-data-value and negative \
                        pavement quality values.")
    parser.add_argument("-n", "--ndval",
                        default=-9999.0,
                        type=float,
                        help="The value to use as no-data-value. \
                        (Default: '%(default)s').")
    parser.add_argument("-p", "--period",
                        default="winter",
                        choices=("year", "winter", "all"),
                        help="Period used to select SAR amplitude data. \
                        'year' will select all SAR data from within one year \
                        before the latest pavement measurement. 'winter' will \
                        select SAR data from previous October to current March. \
                        (default: '%(default)s').")
    parser.add_argument("-c", "--corr",
                        default=['NIRI Average', 'CCI', 'CCI Class'],
                        nargs='+',
                        help="Space separated strings containing the names of \
                        the fields containing road quality values to extract. \
                        'CCI Class' is a special value that separates the CCI \
                        values into classes based on the following ranges: \
                        90 - 100 -> Excellent (4); \
                        70 -  89 -> Good (3); \
                        60 -  69 -> Fair (2); \
                        50 -  59 -> Poor (1); \
                         0 -  49 -> Very Poor (0). \
                        (default: %(default)s).")
    parser.add_argument("-k", "--pkfile",
                        help="Name of the file where to store the pickled \
                        extracted dataframe. The default name is \
                        '<year from xls_in Year field>_<xls_sheet_in>_<period>\
                        [_AMP][_SHP][_TS]_<corr>.pkl'. The values between \
                        square brackets will be included if the corresponding \
                        data was merged. If a single field for 'corr' is \
                        specified, that is the one used, otherwise 'many' \
                        is appended instead of 'corr'.")
    parser.add_argument("-o", "--csvfile",
                        help="Name of the CSV file where to store the \
                        extracted dataframe. The default name is \
                        '<year from xls_in Year field>_<xls_sheet_in>_<period>\
                        [_AMP][_SHP][_TS]_<corr>.csv'. The values between \
                        square brackets will be included if the corresponding \
                        data was merged. If a single field for 'corr' is \
                        specified, that is the one used, otherwise 'many' \
                        is appended instead of 'corr'.")
    parser.add_argument("-d", "--differential",
                        action="store_true",
                        help="If selected, will add the istantaneus velocity \
                        as calcuated between consecutives amplitude and \
                        displacements values, if included in the analysis, \
                        displacemets. The velocity is calculated as \
                        [x(t+1)-x(t)]/months and the units of the numerator \
                        depend on the 'x'. The istantaneous velocity value is \
                        stored under the date corresponding to t+1 (A 'D' is \
                        prepended to the date field and the actual timw in \
                        months is included at the end of the field between \
                        parentheses. Note that differential processing \
                        assumes that the the date fields are sorted.")
    parser.add_argument("-f", "--prepend",
                        default="",
                        help="A string to prepend to the output file names \
                        (default: %(default)s).")

    parser.add_argument("--verbose",
                        action="store_true",
                        help="Increase the verbosity of the output.")

    args = parser.parse_args()

    # Call the function with the parsed parameters
    amp2xls(args.xls_in,
            args.amp_in,
            args.shp_in,
            args.ts_in,
            args.xls_epsg,
            args.xls_sheet_in,
            args.keep_bad,
            args.ndval,
            args.period,
            args.corr,
            args.pkfile,
            args.csvfile,
            args.differential,
            args.prepend,
            args.verbose)
