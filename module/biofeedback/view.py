#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 10 02:17:55 2019

@author: pi
"""

from PyQt5.QtWidgets import (QMainWindow, QPushButton, QWidget,
                             QVBoxLayout)
from PIL import Image
import pyqtgraph as pg
import numpy as np

 
class View(QMainWindow):
    
    '''
    any logic is handled by the controller, the view is solely for
    visualization purposes
    '''
    
    #################################################################
    # define GUI layout and connect input widgets to external slots #
    #################################################################
    def __init__(self, model, controller, patch):
        super().__init__()
        self._model = model
        self._controller = controller
        self._patch = patch
        
        # switch to using white background and black foreground
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        
        # prepare image
        self.imgorig = Image.open('overlay.jpg')
        self.imgnp = np.array(self.imgorig)
        self.img = pg.ImageItem(self.imgnp)
        self.origscale = self.img.boundingRect()
        
        # set up widget that contains the image
        self.view = pg.GraphicsView()
        self.fig = pg.ViewBox()
        self.fig.setMouseEnabled(False, False)
        self.fig.addItem(self.img)
        self.view.setCentralWidget(self.fig) 
        
        # set up GUI control elements     
        self.startBtn = QPushButton('start')
        self.startBtn.clicked.connect(self._controller.start_model)
        self.stopBtn = QPushButton('stop')
        self.stopBtn.clicked.connect(self._controller.stop_model)       

        # set up the central widget containing the image and control elements
        self.centwidget = QWidget()
        self.setCentralWidget(self.centwidget)
        self.vlayout0 = QVBoxLayout(self.centwidget)
        self.vlayout0.addWidget(self.view)
        self.vlayout0.addWidget(self.startBtn)
        self.vlayout0.addWidget(self.stopBtn)
     
        ##############################################
        # connect image to external signals #
        ##############################################
        self._controller.feedback.connect(self.update_figure)
        
    ###########
    # methods # 
    ###########
    def update_figure(self, scaling):
        # before scaling, return the viewbox back to it's original scale,
        # otherwise scaling will be applied recursively, which is not desirable
        self.fig.removeItem(self.img)
        # set ViewBox to original scale
        self.fig.setRange(self.origscale)
        # reset image
        self.fig.addItem(self.img)
        # scale ViewBox
        self.fig.scaleBy(scaling)
        