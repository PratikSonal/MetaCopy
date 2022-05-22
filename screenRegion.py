'''
SCREEN REGION SELECTOR
'''

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from PyQt5.QtWidgets import (
    QMainWindow,
    QPlainTextEdit,
    QLabel,
    QApplication,
    QComboBox,
)

from displayInfo import getVirturalDesktopDimensions

class screenRegionPromptWidget(QMainWindow):
    active = False
    # coordinates
    mouseDownPoint = (0, 0)
    mouseCurrentPoint = (0, 0)
    mouseUpPoint = (0, 0)
    desktop = {"left": 0, "top": 0, "width": 1920, "height": 1080} # default assumed values
    callback = None
    
    def __init__(self, *args, **kwargs):
        super(screenRegionPromptWidget, self).__init__(*args, **kwargs)
        
        # Make the background translucent during cropping
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # conventional "+" cursor for cropping
        self.setCursor(QCursor(Qt.CrossCursor))
        
        # Get current display dimensions of monitor
        self.desktop = getVirturalDesktopDimensions()
        
        # resize window and repaint
        self.initUI()
    
    def initUI(self):
        self.resetWindow()
        self.repaint()
    
    '''
    def moveEvent(self, event):
        # The window was moved, put it in the top left, and ignore the event
        self.resetWindow()
        event.ignore()
        print('executed')
    '''

    def mousePressEvent(self, event):
        if self.active:
            self.mouseDownPoint = (event.x(), event.y())
        
    def mouseMoveEvent(self, event):
        if self.active and self.mouseDownPoint is not None:
            self.mouseCurrentPoint = (event.x(), event.y())
            self.repaint()
    
    def mouseReleaseEvent(self, event):
        if self.active and self.mouseDownPoint is not None:
            # we just finished a screenshot
            self.mouseUpPoint = (event.x(), event.y())
            self.complete()
    
    def paintEvent(self, event):
        if not self.active:
            return
        
        painter = QPainter(self)
        bgColour = QColor(255, 255, 255, 75)
        backgroundBrush = QBrush(bgColour)

        if self.mouseDownPoint is None: # Fill the whole screen with white
            painter.fillRect(QRect(0, 0, self.desktop['width'], self.desktop['height']), backgroundBrush)
        else:
            region = self.regionFromTwoPoints(self.mouseDownPoint, self.mouseCurrentPoint)
            region['right'] = region['left'] + region['width']
            region['bottom'] = region['top'] + region['height']
            # coordinates: 1
            painter.fillRect(QRect(0, 0, region['left'], self.desktop['height']), backgroundBrush)
            # coordinates: 2
            painter.fillRect(QRect(region['left'], 0, region['width'], region['top']), backgroundBrush)
            # coordinates: 3
            painter.fillRect(QRect(region['left'] + region["width"], 0, self.desktop['width'] - region['right'], self.desktop['height']), backgroundBrush)
            # coordinates: 4
            painter.fillRect(QRect(region['left'], region['bottom'], region['width'], self.desktop['height'] - region['bottom']), backgroundBrush)
            
            # Draw a white outline around cropping zone
            painter.setPen(QPen(QColor(255, 255, 255, 255), 1, Qt.SolidLine))
            painter.drawRect(region['left'], region['top'], region['width'], region['height'])
    
    def closeEvent(self, event):
        if self.active:
            self.complete()
        else:
            event.accept()
    
    '''
    def changeEvent(self, event):
        if event.type() == QEvent.ActivationChange:
            print('executed')
            if self.active and not self.isActiveWindow():
                print('executed 2')
                self.raise_()
                self.activateWindow()
    '''

    def reset(self):
        self.mouseDownPoint = None
        self.mouseUpPoint = None
        self.active = False
        self.callback = None
        self.initUI()
    
    def promptForRegion(self, callback = None):
        self.reset()
        self.active = True
        self.callback = callback
        self.show()
    
    def regionFromTwoPoints(self, a, b):
        x1, x2 = min(a[0], b[0]), max(a[0], b[0])
        y1, y2 = min(a[1], b[1]), max(a[1], b[1])
        w, h = max(1, x2 - x1), max(1, y2 - y1)
        return {"left": x1, "top": y1, "width": w, "height": h}
    
    def complete(self):
        if self.active and self.mouseDownPoint is not None and self.mouseUpPoint is not None:
            region = self.regionFromTwoPoints(self.mouseDownPoint, self.mouseUpPoint)
            callback = self.callback
            self.reset()
            self.hide()
            if callback:
                callback(region)
        else: # Failed / user canceled
            callback = self.callback
            self.reset()
            self.hide()
            if callback:
                callback(None)
    

    def resetWindow(self):
        self.move(self.desktop['left'], self.desktop['top'])
        self.setFixedSize(self.desktop['width'], self.desktop['height'])