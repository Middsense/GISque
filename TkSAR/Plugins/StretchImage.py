# -*- coding: utf-8 -*-
"""
Created on Thu Aug  6 18:38:38 2015

@author: andreavaccari
"""

import numpy as np

class StretchImage(object):
    def __init__(self):
        self.pluginClass = 'Analysis'
        self.pluginGroup = 'Image'
        self.pluginLabel = 'Log10 Stretch'
        self.pluginCommand = self.callback

    def callback(self, image, stack, status):
        status('Evaluating Log10...')
        image = np.log10(1.0 + image)
        status()

