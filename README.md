# edf_viewer

Simple pyqt5 application to view .edf files from the ESRF.
Developed for use with DF-XRM data

Using pyQt5, pyqtgraph and fabio

a .edf file can be provided as an input argument such that you may associate \*.edf files with edf_view.py

![](example.png?raw=true)

The exe is compiled in python3.10 using pyinstaller with the following packages/versions:
python3 -m pip list
Package                   Version
------------------------- ---------
altgraph                  0.17.2
cycler                    0.11.0
fabio                     0.14.0
fonttools                 4.37.1
future                    0.18.2
h5py                      3.7.0
kiwisolver                1.4.4
matplotlib                3.5.3
numpy                     1.23.3
packaging                 21.3
pefile                    2022.5.30
Pillow                    9.2.0
pyinstaller               5.4.1
pyinstaller-hooks-contrib 2022.10
pyparsing                 3.0.9
pyqtgraph                 0.12.4
PySide2                   5.15.2.1
python-dateutil           2.8.2
pywin32-ctypes            0.2.0
scipy                     1.9.1
shiboken2                 5.15.2.1
six                       1.16.0
