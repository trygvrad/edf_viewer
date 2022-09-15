#!/usr/bin/env python3
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtWidgets import  QTreeWidgetItem
import pyqtgraph
import os
import sys
import numpy as np
import threading
import fabio
import pathlib
from PySide2.QtUiTools import QUiLoader

QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
class UiLoader(QUiLoader):
    def __init__(self, base_instance):
        QUiLoader.__init__(self, base_instance)
        self.base_instance = base_instance

    def createWidget(self, class_name, parent=None, name=''):
        if parent is None and self.base_instance:
            return self.base_instance
        elif class_name == "ImageView":
            return pyqtgraph.ImageView(parent=parent)
        else:
            # create a new widget for child widgets
            widget = QUiLoader.createWidget(self, class_name, parent, name)
            if self.base_instance:
                setattr(self.base_instance, name, widget)
            return widget

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
        if os.path.exists('edf_view.ui'):
            path = 'edf_view.ui'
        else:
            while not os.path.exists(str(application_path) + '/edf_view.ui'):
                application_path = application_path + '/..'
                i+=1
                if i>10:
                    break
            path = str(application_path) + '/edf_view.ui'

        loader = UiLoader(self)
        widget = loader.load(path)

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
        self.image_show.ui.histogram.gradient.showTicks(False)

        self.image_show.ui.roiBtn.hide()
        self.image_show.ui.menuBtn.hide()
        # hide colorbar
        #self.image_show.getHistogramWidget().gradient.hide()
        #self.image_show.ui.histogram.layout.setSpacing(0)

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

        self.label.setText(' By Marie Curie fellow Trygve M. R'+chr(int('00E6', 16))+'der for use in the group of Hugh Simons at DTU. Use at own risk. MIT lisence. https://github.com/trygvrad/edf_viewer')
        #self.save_image_button.clicked.connect(self.save_clicked)

    def open_clicked(self,event):
        file = self.path.text().replace('\\\\','\\')
        print(file)
        try:
            self.new_file(file)
            self.label.setText(' By Marie Curie fellow Trygve M. R'+chr(int('00E6', 16))+'der for use in the group of Hugh Simons at DTU. Use at own risk. MIT lisence. https://github.com/trygvrad/edf_viewer')
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
            try:
                counters = QTreeWidgetItem([ 'counters', '' ])
                self.header_tree.addTopLevelItem(counters)
                counter_names = edf.header['counter_mne']
                counter_pos = edf.header['counter_pos']
                for key, val in zip(counter_names.split(' '),counter_pos.split(' ')):
                    item = QTreeWidgetItem([ key, val ])
                    counters.addChild(item)
                    counters.setExpanded(True)
            except Exception as e:
                None
            try:
                motors = QTreeWidgetItem([ 'motors', '' ])
                self.header_tree.addTopLevelItem(motors)
                motor_names = edf.header['motor_mne']
                motor_pos = edf.header['motor_pos']
                for key, val in zip(motor_names.split(' '),motor_pos.split(' ')):
                    item = QTreeWidgetItem([ key, val ])
                    motors.addChild(item)
                    motors.setExpanded(True)
            except:
                None
            try:
                other = QTreeWidgetItem([ 'other', '' ])
                self.header_tree.addTopLevelItem(other)
                for key in edf.header.keys():
                    #if not 'motor' in key:
                    item = QTreeWidgetItem([ key, str(edf.header[key]) ])
                    other.addChild(item)

                other.setExpanded(True)
            except:
                None


import queue
import functools
class rimt():
    def __init__(self, send_queue, return_queue):
        self.send_queue = send_queue
        self.return_queue = return_queue
        self.main_thread = threading.current_thread()

    def rimt(self, function, *args, **kwargs):
        if threading.current_thread() == self.main_thread:
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

from pyqtgraph import Point
def paint(self, p, *args):
    '''
    this is a version of pyqtgraph.graphicsItems.HistogramLUTItem.HistogramLUTItem
    that when called does not add the diagonal lines connecting the colorbar to the histogram
    overload using "setattr(pyqtgraph.graphicsItems.HistogramLUTItem.HistogramLUTItem,'paint', paint)"
    before the ui is loaded
    '''
    if self.levelMode != 'mono':
        return
    pen = self.region.lines[0].pen
    rgn = self.getLevels()
    p1 = self.vb.mapFromViewToItem(self, Point(self.vb.viewRect().center().x(), rgn[0]))
    p2 = self.vb.mapFromViewToItem(self, Point(self.vb.viewRect().center().x(), rgn[1]))
    gradRect = self.gradient.mapRectToParent(self.gradient.gradRect.rect())
    p.setRenderHint(QtGui.QPainter.Antialiasing)
    '''
    for pen in [fn.mkPen((0, 0, 0, 100), width=3), pen]:
        p.setPen(pen)
        p.drawLine(p1 + Point(0, 5), gradRect.bottomLeft())
        p.drawLine(p2 - Point(0, 5), gradRect.topLeft())
        p.drawLine(gradRect.topLeft(), gradRect.topRight())
        p.drawLine(gradRect.bottomLeft(), gradRect.bottomRight())
    '''

if __name__ == "__main__":
    # remoce lines to colorbar from plot
    setattr(pyqtgraph.graphicsItems.HistogramLUTItem.HistogramLUTItem,'paint', paint)
    #
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    QtCore.QTimer.singleShot(30, main_window.rimt_executor.execute) #<- must be run after the event loop has started (.show()?)
    sys.exit(app.exec_())
