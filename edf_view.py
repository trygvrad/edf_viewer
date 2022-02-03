#!/usr/bin/env python3


from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import  QTreeWidgetItem
import pyqtgraph
import os
import sys
import numpy as np
import threading
import fabio
import pathlib

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        pyqtgraph.setConfigOption('background', 'w')
        super(MainWindow, self).__init__(*args, **kwargs)
        #Load the UI Page


        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        elif __file__:
            application_path = os.path.dirname(__file__)

        i = 0
        while not os.path.exists(str(application_path) + '/edf_view.ui'):
            application_path = application_path + '/..'
            i+=1
            if i>10:
                break
        path = str(application_path) + '/edf_view.ui'

        uic.loadUi(path, self)

        self.setObjectName("MainWindow")



        colors = [
            (0, 0, 0),
            (230,0,0),
            (240,240,0),
            (255, 255, 255)
        ]
        # color maps
        cmap = pyqtgraph.ColorMap(pos=np.linspace(0.0, 1.0, 4), color=colors)
        #cmap = pyqtgraph.colormap.get('CET-L9')
        cmap = pyqtgraph.colormap.getFromMatplotlib('viridis')

        self.image_show.setColorMap(cmap)

        self.image_show.ui.roiBtn.hide()
        self.image_show.ui.menuBtn.hide()
        #self.dropEvent = self.do_drop_event

        def dragEnterEvent(ev):
            ev.accept()

        self.path.dropEvent = self.do_drop_event
        self.image_show.setAcceptDrops(True)
        self.image_show.dropEvent = self.do_drop_event
        self.image_show.dragEnterEvent = dragEnterEvent

        send_queue, return_queue = queue.Queue(), queue.Queue()
        self.rimt = rimt(send_queue, return_queue).rimt
        self.rimt_executor = RimtExecutor(send_queue, return_queue)
        self.files = []
        self.locked = False

        if len(sys.argv)>1:
            file = sys.argv[1]
            self.new_file(file)

        self.open_button.clicked.connect(self.open_clicked)

        self.label.setText('By Marie Curie fellow Trygve M. Ræder for use in the group of Hugh Simons at DTU. Use at own risk. MIT lisence. https://github.com/trygvrad/edf_viewer')
        #self.save_image_button.clicked.connect(self.save_clicked)

    def open_clicked(self,event):
        file = self.path.text().replace('\\\\','\\')
        print(file)
        try:
            self.new_file(file)
            self.label.setText(r'By Marie Curie fellow Trygve M. Ræder for use in the group of Hugh Simons at DTU. Use at own risk. MIT lisence. https://github.com/trygvrad/edf_viewer')
        except Exception as e:
            self.label.setText(str(e))
            self.label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            print(e)
    #def save_clicked(self,event):
    #    None


    def do_drop_event(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        file = files[0]
        self.new_file(file)

    def new_file(self,file):
        self.path.setText(file)
        if file[-4:] == '.edf':
            edf = fabio.open(file)
            self.image_show.getImageItem().setImage(edf.data,
                    levels = [np.percentile(edf.data, 0.1),np.percentile(edf.data, 99.9)],
                    axisOrder = 'row-major')
            self.header_tree.clear()

            motors = QTreeWidgetItem([ 'motors', '' ])
            self.header_tree.addTopLevelItem(motors)
            motor_names = edf.header['motor_mne']
            motor_pos = edf.header['motor_pos']
            for key, val in zip(motor_names.split(' '),motor_pos.split(' ')):
                item = QTreeWidgetItem([ key, val ])
                motors.addChild(item)

            other = QTreeWidgetItem([ 'other', '' ])
            self.header_tree.addTopLevelItem(other)
            for key in edf.header.keys():
                #if not 'motor' in key:
                item = QTreeWidgetItem([ key, str(edf.header[key]) ])
                other.addChild(item)

            motors.setExpanded(True)
            other.setExpanded(True)


import queue
import functools
class rimt():
    def __init__(self, send_queue, return_queue):
        self.send_queue = send_queue
        self.return_queue = return_queue
        self.main_thread = threading.currentThread()

    def rimt(self, function, *args, **kwargs):
        if threading.currentThread() == self.main_thread:
            return function(*args, **kwargs)
        else:
            self.send_queue.put(functools.partial(function, *args, **kwargs))
            return_parameters = self.return_queue.get(True)  # blocks until an item is available
        return return_parameters


class RimtExecutor():
    def __init__(self, send_queue, return_queue):
        self.send_queue = send_queue
        self.return_queue = return_queue

    def execute(self):
        for i in [0]:
            try:
                callback = self.send_queue.get(False)  # doesn't block
                #print('executing')
            except:  # queue.Empty raised when queue is empty (python3.7)
                break
            try:
                #self.return_queue.put(None)
                return_parameters = callback()
                QtCore.QCoreApplication.processEvents()
                self.return_queue.put(return_parameters)
            except Exception as e:
                return_parameters = None
                traceback.print_exc()
                print(e)
        QtCore.QTimer.singleShot(10, self.execute)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    QtCore.QTimer.singleShot(30, main_window.rimt_executor.execute) #<- must be run after the event loop has started (.show()?)
    sys.exit(app.exec_())
