#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 10 01:19:16 2019

@author: pi
"""

import sys
from PyQt5.QtWidgets import QApplication
from model import Model
from view import View
from controller import Controller


class Application(QApplication):
    def __init__(self, sys_argv):
        super(Application, self).__init__(sys_argv)
        self._model = Model()
        self._controller = Controller(self._model)
        self._view = View(self._model, self._controller)
        self._view.show()


if __name__ == '__main__':
    app = Application(sys.argv)
    sys.exit(app.exec_())

