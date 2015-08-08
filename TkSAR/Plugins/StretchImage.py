# -*- coding: utf-8 -*-
"""
Created on Thu Aug  6 18:38:38 2015
Name:
Purpose:
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

