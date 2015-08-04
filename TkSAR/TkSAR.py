#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
Created on Mon Aug  3 11:16:07 2015
Name:   TkSAR.py
Purpose: Example of tkinter GUI to perform simple SAR image analysis
Author:  Andrea Vaccari (av9g@virginia.edu)
"""



import Tkinter as tk
import tkFont as tkfnt
import tkFileDialog as tkfd
import tkMessageBox as tkmb
from osgeo import gdal
from PIL import Image, ImageTk
import numpy as np
import os


class sarImage(object):
    def __init__(self):
        self.min = 0.0
        self.max = 0.0
        self.ave = 0.0
        self.var = 0.0
        self.currentImage = np.zeros((2, 2))

    @classmethod
    def image(self, image):
        self.originalImage = image.copy()
        self.currentImage = image.copy()

    def loadImage(self, image):
        self.originalImage = image.copy()
        self.currentImage = image.copy()

    def logCompress(self):
        self.currentImage = np.log10(1.0 + self.currentImage)

    def getOriginalImage(self):
        return self.originalImage.copy()

    def getCurrentImage(self):
        return self.currentImage.copy()

    def resetOriginal(self):
        self.currentImage = self.originalImage.copy()

    def evalStats(self):
        self.min = np.nanmin(self.currentImage)
        self.max = np.nanmax(self.currentImage)
        self.ave = np.nanmean(self.currentImage)
        self.var = np.nanvar(self.currentImage)

    def getStats(self):
        return (self.min, self.max, self.ave, self.var)


class SarAmplitude(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        self.canvasSize = (600, 600)
        self.nodata = -9999.0

        self.parent = parent
        self.dispImage = sarImage()
        self.grid()
        self.parent.title('SAR Amplitude analysis')
        self.createMenus()
        self.createWidgets()
        self.updateStatus()

    def updateStatus(self, string=None):
        if string is None:
            string = 'Ready!'
        self.statusStr.set(string)
        self.update_idletasks()

    def updateStats(self):
        self.updateStatus('Evaluating image statistics...')
        self.dispImage.evalStats()
        smin, smax, save, svar = self.dispImage.getStats()
        self.statsMinStr.set('{:.4f}'.format(smin))
        self.statsMaxStr.set('{:.4f}'.format(smax))
        self.statsAveStr.set('{:.4f}'.format(save))
        self.statsVarStr.set('{:.4f}'.format(svar))
        self.updateStatus()

    def createMenus(self):
        # Menu
        self.menubar = tk.Menu(self.parent)
        self.parent.config(menu=self.menubar)

        # Menu->File
        self.fileMenu = tk.Menu(self.menubar)

        # Menu->Quit
        self.fileMenu.add_command(label='Quit',
                                  command=self.onExit)

        # Create File Menu
        self.menubar.add_cascade(label='File',
                                 menu=self.fileMenu)


    def createWidgets(self):
        ### Title ###
        self.title = tk.Label(self.parent,
                              text='SAR Image Analysis Toolbox',
                              font=tkfnt.Font(size=14,
                                              weight='bold'),
                              anchor=tk.CENTER)
        self.title.grid(row=0, column=0)




        ### Middle frame: left | image | right ###
        self.middleFrame = tk.Frame(self.parent)
        self.middleFrame.grid(row=1, column=0)





        ## Left frame ##
        self.leftFrame = tk.Frame(self.middleFrame)
        self.leftFrame.grid(row=0, column=0)

        # Left - open files frame
        self.openFilesFrame = tk.LabelFrame(self.leftFrame,
                                            text='Open')
        self.openFilesFrame.grid(row=0, column=0)

        # Open single file button
        self.openSingleButton = tk.Button(self.openFilesFrame,
                                          text='Single',
                                          command=self.openOneFile)
        self.openSingleButton.grid(row=0, column=0)

        # Open multiple file button
#        self.openMultiButton = tk.Button(self.openFilesFrame,
#                                         text='Multi',
#                                         command=self.openMultipleFiles)
#        self.openMultiButton.grid(row=1, column=0)





        ## Image Canvas ##
        self.imageCanvas = tk.Canvas(self.middleFrame,
                                     height=self.canvasSize[0],
                                     width=self.canvasSize[1])
        self.imageCanvas.grid(row=0, column=1)
        im = Image.fromarray(np.ones(self.canvasSize), mode='F')
        self.image = ImageTk.PhotoImage(im)
        self.currentImage = self.imageCanvas.create_image(0, 0,
                                                          anchor=tk.NW,
                                                          image=self.image)



        ## Right frame: display and stats ##
        self.rightFrame = tk.Frame(self.middleFrame)
        self.rightFrame.grid(row=0, column=2, sticky=tk.N)

        # Right - display frame
        self.displayFrame = tk.LabelFrame(self.rightFrame,
                                          text='Display')
        self.displayFrame.grid(row=0, column=0)

        # Update button
        self.updateButton = tk.Button(self.displayFrame,
                                      text='Update',
                                      command=self.updateImage)
        self.updateButton.grid(row=0, column=0)

        # Log compress button
        self.logCompButton = tk.Button(self.displayFrame,
                                       text='Log10 Compress',
                                       command=self.logCompImage)
        self.logCompButton.grid(row=1, column=0)

        # Right - statistics frame
        self.statsFrame = tk.LabelFrame(self.rightFrame,
                                        text='Stats')
        self.statsFrame.columnconfigure(0, weight=1)
        # Gridded in main code once an image is loaded

        # Min value
        self.statsMinFrame = tk.LabelFrame(self.statsFrame,
                                           font=(None, 10),
                                           labelanchor=tk.NE,
                                           text='Min')
        self.statsMinFrame.grid(row=0, column=0, sticky=tk.E+tk.W)
        self.statsMinFrame.columnconfigure(0, weight=1)
        self.statsMinStr = tk.StringVar()
        self.statsMin = tk.Label(self.statsMinFrame,
                                 anchor=tk.E,
                                 textvariable=self.statsMinStr)
        self.statsMin.grid(row=0, column=0, sticky=tk.E+tk.W)

        # Max value
        self.statsMaxFrame = tk.LabelFrame(self.statsFrame,
                                           font=(None, 10),
                                           labelanchor=tk.NE,
                                           text='Max')
        self.statsMaxFrame.grid(row=1, column=0, sticky=tk.E+tk.W)
        self.statsMaxFrame.columnconfigure(0, weight=1)
        self.statsMaxStr = tk.StringVar()
        self.statsMax = tk.Label(self.statsMaxFrame,
                                 anchor=tk.E,
                                 textvariable=self.statsMaxStr)
        self.statsMax.grid(row=0, column=0, sticky=tk.E+tk.W)

        # Average value
        self.statsAveFrame = tk.LabelFrame(self.statsFrame,
                                           font=(None, 10),
                                           labelanchor=tk.NE,
                                           text='Average')
        self.statsAveFrame.grid(row=2, column=0, sticky=tk.E+tk.W)
        self.statsAveFrame.columnconfigure(0, weight=1)
        self.statsAveStr = tk.StringVar()
        self.statsAve = tk.Label(self.statsAveFrame,
                                 anchor=tk.E,
                                 textvariable=self.statsAveStr)
        self.statsAve.grid(row=0, column=0, sticky=tk.E+tk.W)

        # Variance value
        self.statsVarFrame = tk.LabelFrame(self.statsFrame,
                                           font=(None, 10),
                                           labelanchor=tk.NE,
                                           text='Variance')
        self.statsVarFrame.grid(row=3, column=0, sticky=tk.E+tk.W)
        self.statsVarFrame.columnconfigure(0, weight=1)
        self.statsVarStr = tk.StringVar()
        self.statsVar = tk.Label(self.statsVarFrame,
                                 anchor=tk.E,
                                 textvariable=self.statsVarStr)
        self.statsVar.grid(row=0, column=0, sticky=tk.E+tk.W)

        # Update stats button
        self.updateStatsButton = tk.Button(self.statsFrame,
                                           text='Update',
                                           command=self.updateStats)
        self.updateStatsButton.grid(row=4, column=0, sticky=tk.E+tk.W)




        ### Bottom: status bar and quit button ###
        self.bottomFrame = tk.Frame(self.parent)
        self.bottomFrame.grid(row=2, column=0, sticky=tk.W+tk.E)

        # Quit button
        self.quitButton = tk.Button(self.bottomFrame,
                                    text='Quit',
                                    command=self.onExit)
        self.quitButton.grid(row=0, column=0)

        # Status bar
        self.statusStr = tk.StringVar()
        self.statusBar = tk.Label(self.bottomFrame,
                                  textvariable=self.statusStr)
        self.statusBar.grid(row=0, column=1, sticky=tk.W)

    def onExit(self):
        self.updateStatus('Quitting...')
        self.parent.quit()

    def openOneFile(self):
        self.updateStatus('Opening a single file...')
        fl = tkfd.askopenfilename()
        fileName = str(fl)
        msg = 'You have selected the following file:\n\n' + fileName + '\n\nProceed?'
        if tkmb.askokcancel('Selected File:', msg):
            self.fileList = []
            self.fileList.append(fl)
            self.loadImage()
        self.updateStatus()

#    def openMultipleFiles(self):
#        self.updateStatus('Opening multiple files...')
#        fl = tkfd.askopenfilenames()
#        fileList = '\n'.join((str(os.path.split(f)[1])) for f in fl)
#        msg = 'You have selected the following files:\n\n' + fileList + '\n\nProceed?'
#        if tkmb.askokcancel('Selected Files:', msg):
#            self.fileList = []
#            self.fileList.append(f for f in fl)
#        self.updateStatus()

    def loadImage(self):
        tif = gdal.Open(self.fileList[0])
        if tif is None:
            self.updateStatus(gdal.GetLastErrorMsg())
            return

        self.updateStatus('Loading: ' + str(os.path.split(self.fileList[0])[1]))
        tif_band = tif.GetRasterBand(1)  # Assumes single band (BW)
        no_data = tif_band.GetNoDataValue()
        tif_data = tif_band.ReadAsArray()
        tif_data[tif_data == no_data] = np.nan
        self.dispImage.loadImage(tif_data)
        self.updateStats()
        self.statsFrame.grid(row=1, column=0, sticky=tk.E+tk.W)
        self.updateStatus()
        tif = None  # Properly close the file

    def updateImage(self):
        self.updateStatus('Rendering image...')
        im = self.dispImage.getCurrentImage()
        im /= np.nanmax(im)
        im = Image.fromarray(255.0 * im, mode='F')
        im = im.resize((self.canvasSize[0], self.canvasSize[1]), Image.ANTIALIAS)
        self.image = ImageTk.PhotoImage(im)
        self.imageCanvas.itemconfig(self.currentImage,
                                    image=self.image)
        self.updateStatus()

    def logCompImage(self):
        self.updateStatus('Log10 compressing image...')
        self.dispImage.logCompress()
        self.updateStatus()

#    def computeStat(self):
#        """
#        Compute ``sample mean`` and ``sample standard deviation`` in two
#        steps for the raster data within the selected files.
#        """
#        # Use the first image as template
#        tf = gdal.Open(self.fileList[0])
#        tfb = tf.GetRasterBand(1)
#        XSize = tfb.XSize
#        YSize = tfb.YSize
#        nodata = tfb.GetNoDataValue()
#
#        self.mean = np.zeros((YSize, XSize))
#        d = np.zeros((YSize, XSize))
#
#        n = len(self.fileList)
#
#        for f in self.fileList:
#            self.updateStatus('Computing mean: ' + str(f))
#            tf = gdal.Open(f)
#            tfb = tf.GetRasterBand(1)
#            d = tfb.ReadAsArray()
#            d[d == nodata] = np.nan
#            self.mean += tfb.ReadAsArray()
#
#        self.mean /= n
#        self.updateStatus('Done!')
#
#        self.std = np.zeros((YSize, XSize))
#        d = np.zeros((YSize, XSize))
#
#        for t in self.fileList:
#            self.updateStatus('Computing compensated variance: ' + str(f))
#            tf = gdal.Open(f)
#            tfb = tf.GetRasterBand(1)
#            d = tfb.ReadAsArray() - self.mean
#            self.std += d * d
#
#        d = None
#        tfb = None
#        tf = None
#
#        self.std = np.sqrt(self.std / (n - 1))
#        self.updateStatus()


def main():
    root = tk.Tk()
    app = SarAmplitude(root)
    app.mainloop()



if __name__ == '__main__':
   main()

