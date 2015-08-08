#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
Created on Mon Aug  3 11:16:07 2015
Name:   TkSAR.py
Purpose: Example of tkinter GUI to perform simple SAR image analysis
Author:  Andrea Vaccari (av9g@virginia.edu)
Version: 0.0.0-alpha

    Copyright (C) 2015  Andrea Vaccari

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



import Tkinter as tk
import tkFont as tkfnt
import tkFileDialog as tkfd
import tkMessageBox as tkmb
from osgeo import gdal
from PIL import Image, ImageTk
import numpy as np
from sys import path
import os
from glob import glob
from importlib import import_module



class Raster(object):
    def __init__(self):
        pass

    @classmethod
    def image(self, image):
        pass


class Stack(object):
    def __init__(self):
        pass


class SarAmplitude(tk.Frame):
    def __init__(self, parent):
        """
        Initializes the main screen.

        Parameters
        ----------
        parent : class instance
            Toplevel widget of Tk which represents the main window of the
            application.
        """
        tk.Frame.__init__(self, parent)

        # Define main windows characteristics
        self.canvasSize = (600, 600)
        self.parent = parent
        self.parent.title('SAR Amplitude analysis')

        # Instantiate single image and stack classes
        self.currentImage = Raster()
        self.currentStack = Stack()

        # Check for available plugins
        self.pl, self.gr = self.instantiatePlugins()

        # Define the window components and their layout
        self.createWidgets()

        # Define the menu bar items
        self.createMenus()

        # Create the window
        self.grid()

        # We're ready to go!
        self.updateStatus()


    def instantiatePlugins(self):
        """
        Looks for plugins classes and instantiates them

        Returns
        -------
        plg : list
            A list of class instances, one for each plugin found.
        grp : list
            A list of the plugins groups.
        """
        # TODO: Implement the plugin classes: Input, Output, Analysis and use
        #       them to place widgets on the screen
        PLUGINS_DIR = 'Plugins'
        VALID_CLASSES = ['Input', 'Analysis']
        plugins_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), PLUGINS_DIR)
        plugins_files = glob(os.path.join(plugins_folder, '*.py'))
        plugins_list = [f[:-3] for _, f in [os.path.split(p) for p in plugins_files]]
        path.append(plugins_folder)  # Add plugins path to PYTHONPATH

        plg = []
        grp = set()
        for v in plugins_list:
            try:
                v = getattr(import_module(v), v)
            except ImportError as e:
                print 'TODO: handle this error: ' + e.message
                pass
            else:
                inst = v()
                if VALID_CLASSES.count(inst.pluginClass) == 0:
                    continue
                plg.append(inst)
                grp.add(inst.pluginGroup)
        return plg, list(grp)


    def updateStatus(self, string=None):
        """
        Updates the status bar

        Parameters
        ----------

        string : string
            The status string to be displayed. If ``None`` (default) then the
            message ``Ready!`` will be displayed.
        """
        if string is None:
            string = 'Ready!'
        self.statusStr.set(string)
        self.update_idletasks()


    def createMenus(self):
        """
        Defines the menubar items
        """
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
        """
        Defines the window components and their layout
        """
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







        ## Right frame: analysis ##
        rightFrame = tk.Frame(self.middleFrame)
        rightFrame.columnconfigure(0, weight=1)
        rightFrame.grid(row=0, column=2, sticky=tk.N)

        # Cycle through the analysis plugins groups and create label frames
        di = {}  # A dictionary to contain the callbacks
        for k, g in enumerate(self.gr):
            labelFrame = tk.LabelFrame(rightFrame,
                                       font=(None, 10),
                                       labelanchor=tk.NE,
                                       text=g)
            labelFrame.columnconfigure(0, weight=1)
            labelFrame.grid(row=k, column=0, sticky=tk.E+tk.W)

            # Cycle through the plugin instances and fill the dictionary
            # with the callbacks
            pl = []  # A list to contain the plugin labels
            for p in self.pl:
                if p.pluginGroup == g:
                    di[g + p.pluginLabel] = p.pluginCommand
                    pl.append(p.pluginLabel)

            # Create dropdown menus, one for each group
            var = tk.StringVar(name=g)
            var.set(g)
            var.trace('w', lambda name, idx, mode: di[name + self.parent.globalgetvar(name)](self.currentImage, self.currentStack, self.updateStatus))
            opt = tk.OptionMenu(labelFrame, var, *pl)
            opt.grid(row=0, column=0, sticky=tk.E+tk.W)







        ### Bottom: status bar and quit button ###
        bottomFrame = tk.Frame(self.parent)
        bottomFrame.grid(row=2, column=0, sticky=tk.W+tk.E)
        bottomFrame.columnconfigure(1, weight=1)

        # Quit button
        self.quitButton = tk.Button(bottomFrame,
                                    text='Quit',
                                    command=self.onExit)
        self.quitButton.grid(row=0, column=0, sticky=tk.W)

        # Status bar
        self.statusStr = tk.StringVar()
        self.statusBar = tk.Label(bottomFrame,
                                  anchor=tk.W,
                                  textvariable=self.statusStr)
        self.statusBar.grid(row=0, column=1, sticky=tk.W+tk.E)

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
