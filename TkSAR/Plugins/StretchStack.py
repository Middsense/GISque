# -*- coding: utf-8 -*-
"""
Created on Fri Aug  7 11:38:33 2015

@author: andreavaccari
"""

class StretchStack(object):
    def __init__(self):
        self.pluginClass = 'Analysis'
        self.pluginGroup = 'Stack'
        self.pluginLabel = 'Log10 Stretch'
        self.pluginCommand = self.callback

    def callback(self, image, stack, status):
        status('Evaluating Log10...')
        status()
