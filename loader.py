#!/usr/bin/python
# -*- coding: utf-8 -*-
import PyQt5
import pyqtgraph
import os
import sys
import numpy
import threading
import pathlib
import fabio
import fabio.HiPiCimage
import fabio.pilatusimage
import fabio.binaryimage
import fabio.raxisimage
import fabio.pixiimage
import fabio.mpaimage
import fabio.adscimage
import time

try:
    # determine if application is a script file or frozen exe
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(__file__)
    i = 0
    while not os.path.exists(str(application_path) + '/edf_view.py'):
        application_path = application_path + '/..'
        i+=1
        if i>10:
            break
    path = application_path + '/edf_view.py'
    with open(path) as f:
        code = compile(f.read(), path, 'exec')
        exec(code, globals(), locals())
except Exception as e:
    print(e)
    time.sleep(20)
