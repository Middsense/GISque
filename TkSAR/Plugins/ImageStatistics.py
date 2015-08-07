# -*- coding: utf-8 -*-
"""
Created on Wed Aug  5 22:19:54 2015
Name:
Purpose:
Author:  Andrea Vaccari (av9g@virginia.edu)
Version: 0.0.0-alpha

    Copyright (C) Fri Aug  7 18:05:55 2015  Andrea Vaccari

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

class ImageStatistics(object):
    def __init__(self):
        self.pluginClass = 'Analysis'
        self.pluginGroup = 'Image'
        self.pluginLabel = 'Statistics'
        self.pluginCommand = self.callback


    def callback(self, image, stack, status):
        self.status = status
        self.status(self.pluginLabel)
        smin = 0.0
        smax = 0.0
        save = 0.0
        svar = 0.0
        self.minStr = tk.StringVar()
        self.minStr.set('{:.4f}'.format(smin))
        self.maxStr = tk.StringVar()
        self.maxStr.set('{:.4f}'.format(smax))
        self.aveStr = tk.StringVar()
        self.aveStr.set('{:.4f}'.format(save))
        self.varStr = tk.StringVar()
        self.varStr.set('{:.4f}'.format(svar))

        self.createWidgets()

    def update(self):
        pass

    def onExit(self):
        self.status()
        self.topLevel.destroy()

    def createWidgets(self):
        # Define to level pop-up window
        self.topLevel = tk.Toplevel()
        self.topLevel.title = 'Image statistics'
        self.topLevel.columnconfigure(0, weight=1)

        # Min value
        minFrame = tk.LabelFrame(self.topLevel,
                                      font=(None, 10),
                                      labelanchor=tk.NE,
                                      text='Min')
        minFrame.grid(row=0, column=0, sticky=tk.E+tk.W)
        minFrame.columnconfigure(0, weight=1)
        minLabel = tk.Label(minFrame,
                            anchor=tk.E,
                            textvariable=self.minStr)
        minLabel.grid(row=0, column=0, sticky=tk.E+tk.W)

        # Max value
        maxFrame = tk.LabelFrame(self.topLevel,
                                      font=(None, 10),
                                      labelanchor=tk.NE,
                                      text='Max')
        maxFrame.grid(row=1, column=0, sticky=tk.E+tk.W)
        maxFrame.columnconfigure(0, weight=1)
        maxLabel = tk.Label(maxFrame,
                            anchor=tk.E,
                            textvariable=self.maxStr)
        maxLabel.grid(row=0, column=0, sticky=tk.E+tk.W)

        # Average value
        aveFrame = tk.LabelFrame(self.topLevel,
                                      font=(None, 10),
                                      labelanchor=tk.NE,
                                      text='Average')
        aveFrame.grid(row=2, column=0, sticky=tk.E+tk.W)
        aveFrame.columnconfigure(0, weight=1)
        aveLabel = tk.Label(aveFrame,
                            anchor=tk.E,
                            textvariable=self.aveStr)
        aveLabel.grid(row=0, column=0, sticky=tk.E+tk.W)

        # Variance value
        varFrame = tk.LabelFrame(self.topLevel,
                                      font=(None, 10),
                                      labelanchor=tk.NE,
                                      text='Variance')
        varFrame.grid(row=3, column=0, sticky=tk.E+tk.W)
        varFrame.columnconfigure(0, weight=1)
        varLabel = tk.Label(varFrame,
                            anchor=tk.E,
                            textvariable=self.varStr)
        varLabel.grid(row=0, column=0, sticky=tk.E+tk.W)

        # Update stats button
        updateButton = tk.Button(self.topLevel,
                                      text='Update',
                                      command=self.update)
        updateButton.grid(row=4, column=0, sticky=tk.E+tk.W)

        # Quit button
        quitButton = tk.Button(self.topLevel,
                                    text='Quit',
                                    command=self.onExit)
        quitButton.grid(row=5, column=0, sticky=tk.E+tk.W)
