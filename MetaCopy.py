import ctypes
import mss
import numpy as np
import PIL
import os
import sys

screencap = mss.mss()

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import math 
import pytesseract.pytesseract as tesseract
import pathlib
import threading

from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView as QWebView,QWebEnginePage 
from PyQt5.QtWebEngineWidgets import QWebEngineSettings

from pynput.keyboard import Listener, Controller
import pyperclip as pc

#Paste region

def screenshotRegion(screenRegion):
    return np.asarray(screencap.grab(screenRegion))

class KeyboardListener(QObject):
    textChanged = pyqtSignal(str)
    def __init__(self, shortcut, parent=None):
        super().__init__(parent) 
        self._shortcut = shortcut
        listener = Listener(on_press=self.handle_pressed)
        listener.start()
        self.mutex = threading.Lock()

    @property
    def shortcut(self):
        return self._shortcut

    def handle_pressed(self, key):
        with self.mutex:
            if str(key) == self.shortcut:
                cptext = pc.paste()
                self.textChanged.emit(cptext)

    @pyqtSlot(str)
    def update_shortcut(self, shortcut):
        with self.mutex:
            self._shortcut = shortcut

#Paste region ends

myDirectory = str(pathlib.Path(__file__).parent.absolute())
tesseractDirectory = "C:/Program Files/Tesseract-OCR" 
tessdataDirectory = "C:/Program Files/Tesseract-OCR/tessdata" 

tesseract.tesseract_cmd = tesseractDirectory + r"/tesseract.exe"
tessdataConfig = r'--tessdata-dir "%s"' % tessdataDirectory

def getTextFromImg(img, timeout = 3, language = 'eng'):
    return tesseract.image_to_string(img, timeout = timeout, lang = language, config = tessdataConfig)

def getVirturalDesktopDimensions():
    SM_XVIRTUALSCREEN = 76 # LEFTMOST POSITION (not always 0)
    SM_YVIRTUALSCREEN = 77 # TOPMOST POSITION  (not always 0)
    
    SM_CXVIRTUALSCREEN = 78 # WIDTH (of all monitors)
    SM_CYVIRTUALSCREEN = 79 # HEIGHT (of all monitors)

    return {
        "left": ctypes.windll.user32.GetSystemMetrics(SM_XVIRTUALSCREEN),
        "top": ctypes.windll.user32.GetSystemMetrics(SM_YVIRTUALSCREEN),
        "width": ctypes.windll.user32.GetSystemMetrics(SM_CXVIRTUALSCREEN),
        "height": ctypes.windll.user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
    }

'''
    Screen region selector
'''
class screenRegionPromptWidget(QMainWindow):
    active = False
    mouseDownPoint = (0, 0)
    mouseCurrentPoint = (0, 0)
    mouseUpPoint = (0, 0)
    desktop = {"left": 0, "top": 0, "width": 1920, "height": 1080}
    callback = None
    
    
    def __init__(self, *args, **kwargs):
        super(screenRegionPromptWidget, self).__init__(*args, **kwargs)
        
        # invisible background
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # "+" cursor
        self.setCursor(QCursor(Qt.CrossCursor))
        
        # get size of all monitors
        self.desktop = getVirturalDesktopDimensions()
        
        # resize window and repaint
        self.initUI()
    
    def initUI(self):
        self.resetWindow()
        self.repaint()
    

    def moveEvent(self, event):
        # The window was moved, put it in the top left, and ignore the event
        self.resetWindow()
        event.ignore()
    
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
        
        translucentWhite = QColor(255, 255, 255, 127)
        backgroundBrush = QBrush(translucentWhite)
        if self.mouseDownPoint is None: # Fill the whole screen with white
            painter.fillRect(QRect(0, 0, self.desktop['width'], self.desktop['height']), backgroundBrush)
        else:
            region = self.regionFromTwoPoints(self.mouseDownPoint, self.mouseCurrentPoint)
            region['right'] = region['left'] + region['width']
            region['bottom'] = region['top'] + region['height']
            # Rect (1)
            painter.fillRect(QRect(0, 0, region['left'], self.desktop['height']), backgroundBrush)
            # Rect (2)
            painter.fillRect(QRect(region['left'], 0, region['width'], region['top']), backgroundBrush)
            # Rect (3)
            painter.fillRect(QRect(region['left'] + region["width"], 0, self.desktop['width'] - region['right'], self.desktop['height']), backgroundBrush)
            # Rect (4)
            painter.fillRect(QRect(region['left'], region['bottom'], region['width'], self.desktop['height'] - region['bottom']), backgroundBrush)
            
            # Now draw a red outline
            painter.setPen(QPen(QColor(255, 0, 0, 255), 1, Qt.SolidLine))
            painter.drawRect(region['left'], region['top'], region['width'], region['height'])
    
    def closeEvent(self, event):
        if self.active:
            self.complete()
        else:
            event.accept()
    
    def changeEvent(self, event):
        if event.type() == QEvent.ActivationChange:
            if self.active and not self.isActiveWindow():
        
                self.raise_()
                self.activateWindow()

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
        w, h = max(1, x2-x1), max(1, y2-y1)
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

outputWindow_CSS = '''
QMainWindow{
    background-color: rgb(30, 30, 30);
}
#statusLabel{
    color: white;
}
QPlainTextEdit{
    background-color: rgb(70, 70, 70);
    color: white;
}
'''
class outputWindowWidget(QMainWindow):
    ocrStatusChangeSignal = pyqtSignal(int, int, str)
    userCanceledOperation = False
    die = False
    
    def __init__(self, *args, **kwargs):
        super(outputWindowWidget, self).__init__(*args, **kwargs)
        self.setWindowTitle("Output")
        self.setStyleSheet(outputWindow_CSS)
        
        self.ocrResult = QPlainTextEdit(self, objectName = "ocrResult")
        self.ocrResult.setPlaceholderText("Loading...")
        self.ocrResult.setFont(QFont("Consolas", 14, 10, False))
        
        self.statusLabel = QLabel("Scanning image for text...", self, objectName = "statusLabel")
        self.statusLabel.setAlignment(Qt.AlignRight)
        
        self.setMinimumSize(16 * 30, 9 * 30)
        self.resize(16 * 50, 9 * 50)
        
        self.ocrStatusChangeSignal.connect(self.ocrStatusChange)
    
    def sizeUI(self):
        self.ocrResult.move(5, 5)
        self.ocrResult.setFixedSize(self.width() - 10, self.height() - 25)
        
        self.statusLabel.move(5, self.height() - 18)
        self.statusLabel.setFixedSize(self.width() - 10, 15)
    
    def resizeEvent(self, event):   
        self.sizeUI()
    
    def ocrStatusChange(self, id, status, data):
        if status == OCRSTATUS_BEGIN:
            language = data
            self.statusLabel.setText("Scanning image for (%s) text..." % str(language))
            self.ocrResult.setPlainText("")
            self.ocrResult.setPlaceholderText("Scanning...")
            self.userCanceledOperation = False
            self.show()
            self.raise_()
            self.activateWindow()
        elif self.userCanceledOperation:
            return
        elif status == OCRSTATUS_ERROR:
            err = data
            self.statusLabel.setText("Unknown Error [%s]. Try reinstalling?" % str(err))
            self.ocrResult.setPlaceholderText("Unknown error: %s\n\nTry uninstalling and reinstalling this program." % str(err))
        elif status == OCRSTATUS_FINISH:
            text = data
            self.statusLabel.setText("Scan completed! Found %d characters" % len(text))
            self.ocrResult.setPlaceholderText("Unable to screengrab, looks like the image is empty!")
            self.ocrResult.setPlainText(text)
    
    def kill(self):
        self.die = True
        self.close()
    
    def closeEvent(self, event):
        if not self.die:
            event.ignore()
            self.hide()
            self.userCanceledOperation = True
        else:
            event.accept()

'''
    Main OCR window
'''
mainWindow_CSS = '''
QMainWindow{
    background-color: rgb(63, 66, 74);
}
#screenSnipButton{
    background-color: rgb(88, 174, 245);
    border-radius: 5px;
    color: white;
}
#nopen_webbrowser{
    background-color: rgb(245, 88, 88);
    border-radius: 5px;
    color: white;
}
#screenSnipButton:hover{
    background-color: rgb(0, 100, 50);
}
#openImageButton{
    background-color: rgb(88, 245, 140);
    border-radius: 5px;
    color: white;
}
#openImageButton:hover{
    background-color: rgb(0, 50, 150);
}
#topbarItemsContainer{
    background-color: rgb(75, 75, 75);
    border-radius: 5px;
}
#basicButtonLabels{
    color: white;
}
#imagePreview{
    border: 1px solid white;

}
'''

supportedOCRLanguages = [
    {"code": "eng", "name": "English", "local": "English"}
]

supportedOCRScripts = [
    {"code": "script/Latin", "name": "Latin", "alphabet": "abcdefg", "examples": ["English", "French", "Spanish"]}
]

OCRSTATUS_BEGIN = 0
OCRSTATUS_ERROR = 1
OCRSTATUS_TIMEOUT = 2
OCRSTATUS_FINISH = 3
class mainWindowWidget(QMainWindow):
    currentScanID = 0 
    image_source = None
    currentOCRSourceLanguageIndex = 0
    lastOpenedDirectory = os.path.expanduser("~\\Pictures")

    @pyqtSlot(str)
    def handle_text_changed(self, text):
        self.keyboard.type(text)

    def __init__(self, *args, **kwargs):
        super(mainWindowWidget, self).__init__(*args, **kwargs)
        self.setWindowTitle("Text Screengrab")
        
        #windowWidth_noImage = 100 + 150 + 100 + 150 + 100
        #self.setFixedSize(windowWidth_noImage, 70 + 60)
        windowWidth_noImage = 640
        self.setFixedSize(windowWidth_noImage, 480)
        
        self.screenRegionWindow = screenRegionPromptWidget()
         
        self.topbarItems = QLabel(self, objectName = "topbarItemsContainer")
        self.topbarItems.setFixedSize(windowWidth_noImage - 40, 50)
        self.topbarItems.move(20, 20)
        
        self.screenSnipButton = QPushButton("CAPTURE", self.topbarItems, objectName = "screenSnipButton")
        self.screenSnipButton.clicked.connect(self.newSnipPressed)
        self.screenSnipButton.setFont(QFont("Gotham", 20, 1000, False))
        self.screenSnipButton.setFixedSize(200, 50 - 12 )
        self.screenSnipButton.move(7, 7)

        self.screenSnipButton = QPushButton("CONTACT US", self.topbarItems, objectName = "nopen_webbrowser")
        self.screenSnipButton.clicked.connect(self.open_webbrowser)
        self.screenSnipButton.setFont(QFont("Gotham", 14, 1000, False))
        self.screenSnipButton.setFixedSize(160, 50 - 12 )
        self.screenSnipButton.move(30+ 190 + 30, 7)

        self.openImageButton = QPushButton("UPLOAD", self.topbarItems, objectName = "openImageButton")
        self.openImageButton.clicked.connect(self.openImagePressed)
        self.openImageButton.setFont(QFont("Gotham", 20, 1000, False))
        self.openImageButton.setFixedSize(160, 50 - 10 )
        self.openImageButton.move(60 + 320 + 60, 7)
        
        self.basicButtonLabels = QLabel("CAPTURE: Extract text from screenshot\nVIEW: Upload image from your PC", self, objectName = "basicButtonLabels")
        self.basicButtonLabels.setFont(QFont("Gotham", 11, 100, False))
        self.basicButtonLabels.setFixedSize(250 + 10 + 250, 50)
        self.basicButtonLabels.move(25, 80)

        #drop down menu
        self.combo = QComboBox(self)
        shotcut_list = [
            "Key.f1",
            "Key.f2",
            "Key.f3",
            "Key.f4",
            "Key.f5",
            "Key.f6",
            "Key.f7",
            "Key.f8",
            "Key.f9",
            "Key.f10",
            "Key.f11",
            "Key.f12",
        ]
        self.combo.addItems(shotcut_list)
        shortcut = self.combo.currentText()
        self.combo.setGeometry(450, 85, 110, 40)
        self.combo.setEditable(True)
        font = QFont('Times', 14)
        self.combo.setFont(font)
        #ends

        #key capture
        self.keyboard = Controller()
        self.listener = KeyboardListener(self.combo.currentText())
        self.combo.activated[str].connect(self.listener.update_shortcut)
        self.listener.textChanged.connect(self.handle_text_changed)
        #ends
        
        self.imagePreview = QLabel("", self, objectName = "imagePreview")
        self.imagePreview.hide()
        
        self.outputWindow = outputWindowWidget()
        self.outputWindow.hide()
        
        self.setStyleSheet(mainWindow_CSS)
    
    def newSnipPressed(self):
        self.hide()
        self.outputWindow.close() 
        self.screenRegionWindow.promptForRegion(callback = self.gotScreenRegionForSnip)
   
    def open_webbrowser(self):

        self.web = QWebView()
        self.web.load(QUrl("https://pratiksonal.github.io/"))
        self.web.show()

    def openImagePressed(self):
        dialogTitle = "VIEW IMAGE"
        openInDirectory = self.lastOpenedDirectory
        acceptedFiles = "Image files (*.png *.jpeg *jpg)"
        
        (fname, x) = QFileDialog.getOpenFileName(self, dialogTitle, openInDirectory, acceptedFiles)
        if x == '':
            return
        else:
            img = None
            try:
                self.lastOpenedDirectory = str(pathlib.Path(fname).parent)
                
                pic = PIL.Image.open(fname)
                
                img = np.array(pic)
                if img.shape[-1] == 4:
                    img = img[:,:,:3]
                
            except BaseException as e:
                print("Failed to open image: %s" % str(e))
            
            self.newImage(img)
    
    def startOCR(self, image, id, language):
        text = None
        
        try:
            text = getTextFromImg(image, timeout = 120, language = language['code'])
        except BaseException as e:
            if "Tesseract process timeout" in str(e):
                if id != self.currentScanID:
                    return
                return self.outputWindow.ocrStatusChangeSignal.emit(id, OCRSTATUS_TIMEOUT, str(e))
            else:
                if id != self.currentScanID:
                    return
                return self.outputWindow.ocrStatusChangeSignal.emit(id, OCRSTATUS_ERROR, str(e))

        if id != self.currentScanID:
            return
        if text is None:
            text = ""
        return self.outputWindow.ocrStatusChangeSignal.emit(id, OCRSTATUS_FINISH, str(text))
    
    def gotScreenRegionForSnip(self, region):
        if region is None:
            print("Screen Snip CANCELED")
            self.show()
        else:
            img = screenshotRegion(region)
            self.show()
            
            if img.shape[-1] == 4: # drop alpha channel
                img = img[:,:,:3]
            img = img[:,:,::-1] # BGR -> RGB
            
            self.newImage(img)
    
    def newImage(self, img):
        self.image_source = img
        
        self.newOCR()
    
        
    def newOCR(self):
        if self.image_source is None: 
            return
        
        self.currentScanID += 1
        if self.currentScanID == 1: 
        #    self.basicButtonLabels.hide()
            self.imagePreview.show()
        #    self.topbarItems.setFixedSize(3 + 100 + 3 + 100 + 3 + 200 + 3, 50 - 6)
        
        language = None
        if self.currentOCRSourceLanguageIndex < len(supportedOCRLanguages):
            language = supportedOCRLanguages[self.currentOCRSourceLanguageIndex]
        else:
            language = supportedOCRScripts[self.currentOCRSourceLanguageIndex - len(supportedOCRLanguages) - 1]
        
        # show image
        h, w, ch = self.image_source.shape
        qimg = QImage(self.image_source.data.tobytes(), w, h, ch * w, QImage.Format_RGB888)
        self.imagePreview.setPixmap(QPixmap.fromImage(qimg))
        self.imagePreview.setFixedSize(w, h)
        
        # resize main window
        topbarWidth = 30 + 200 + 30 + 300 + 30 + 200 + 30
        imageWidth = w
        imagePosition = 3
        topbarPosition = 3
        windowWidth = 300
        if topbarWidth == imageWidth:
            imagePosition = topbarPosition = 3
            windowWidth = 3 + topbarWidth + 3
        elif topbarWidth > imageWidth:
            topbarPosition = 3
            imagePosition = 3 + (topbarWidth - imageWidth)/2
            windowWidth = 3 + topbarWidth + 3
        else: #if topbarWidth < imageWidth:
            imagePosition = 3
            topbarPosition = 3 + (imageWidth - topbarWidth)/2
            windowWidth = 3 + imageWidth + 3
        
        self.imagePreview.move(math.floor(imagePosition), 150)
        self.topbarItems.move(math.floor(topbarPosition) + 100, 10)
        self.setFixedSize(math.ceil(windowWidth), 175 + h)
        self.basicButtonLabels.move(math.floor(topbarPosition) + 125, 75)
        self.combo.move(math.floor(topbarPosition) + 550, 80)
        
        # notify outputWindow to get ready, and begin OCR
        self.outputWindow.ocrStatusChangeSignal.emit(self.currentScanID, OCRSTATUS_BEGIN, language['name'])
        threading.Thread(target = self.startOCR, args = [self.image_source, self.currentScanID, language]).start()
    
    def closeEvent(self, event):
        self.outputWindow.kill()
        self.screenRegionWindow.active = False
        self.screenRegionWindow.close()

if __name__ == "__main__":
    app = QApplication([])
    window = mainWindowWidget()
    window.show()
    app.exec_()