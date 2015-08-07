# -*- coding: utf-8 -*-
"""
Created on Fri Aug  7 16:41:33 2015

@author: andreavaccari
"""

class ReadImage(object):
    def __init__(self):
        self.pluginClass = 'Input'
        self.pluginGroup = 'Image'
        self.pluginLabel = 'Read Image'
        self.pluginCommand = self.callback

    def callback(self, image, stack, status):
        status('Reading image...')
        status()
