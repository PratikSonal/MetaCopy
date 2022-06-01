import os
import numpy as np
import mss
import PIL
import pathlib
import threading
import pytesseract.pytesseract as tesseract
import cv2

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
from displayInfo import getVirturalDesktopDimensions, getOS

from screenRegion import screenRegionPromptWidget
from output import outputWindowWidget

screencap = mss.mss()

def screenshotRegion(screenRegion):
    return np.asarray(screencap.grab(screenRegion))

OS = getOS()
myDirectory = str(pathlib.Path(__file__).parent.absolute())
tesseractDirectory = "C:/Program Files/Tesseract-OCR" 
tessdataDirectory =  "/usr/share/tesseract-ocr/5/tessdata" if OS == 'Linux' else "C:/Program Files/Tesseract-OCR/tessdata" 

tesseract.tesseract_cmd = '/usr/bin/tesseract' if OS == 'Linux' else tesseractDirectory + r"/tesseract.exe"
tessdataConfig = r'--tessdata-dir "%s"' % tessdataDirectory

def getTextFromImg(img, timeout = 3, language = 'eng'):
    return tesseract.image_to_string(img, timeout = timeout, lang = language, config = tessdataConfig)

def preprocess(img):
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)

    kernel = np.ones((1,1), np.uint8)
    img = cv2.dilate(img, kernel, iterations=1)
    img = cv2.erode(img, kernel, iterations=1)
    #img = cv2.GaussianBlur(img, (5,5), 0)
    #img = cv2.medianBlur(img,5)

    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
    _, dist = cv2.threshold(thresh, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    #status = cv2.imwrite('C:/Users/Pratik Sonal/Pictures/python_grey_data.png', img)
    return dist


mainWindow_CSS = '''
QMainWindow{
    background-color: rgb(66, 66, 66);
}
#screenSnipButton{
    background-color: rgb(2, 119, 189);
    border-radius: 15px;
    color: white;
}
#nopen_webbrowser{
    background-color: rgb(245, 88, 88);
    border-radius: 15px;
    color: white;
}
#screenSnipButton:hover{
    background-color: rgb(41, 182, 246);
}
#openImageButton{
    background-color: rgb(2, 119, 189);
    border-radius: 15px;
    color: white;
}
#openImageButton:hover{
    background-color: rgb(41, 182, 246);
}
#topbarItemsContainer{
    background-color: rgb(75, 75, 75);
}
#logo{
    background-color: rgb(75, 75, 75);
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

dimension = getVirturalDesktopDimensions()
WIDTH = int(dimension['width'] * 0.5)
HEIGHT = int(dimension['height'] * 0.5)

class mainWindowWidget(QMainWindow):
    currentScanID = 0 
    image_source = None
    currentOCRSourceLanguageIndex = 0
    lastOpenedDirectory = os.path.expanduser("~\\Pictures")

    def __init__(self, *args, **kwargs):
        super(mainWindowWidget, self).__init__(*args, **kwargs)
        self.setWindowTitle("MetaCopy")
        self.setStyleSheet(mainWindow_CSS)
        
        self.setFixedSize(WIDTH, HEIGHT)
        
        self.screenRegionWindow = screenRegionPromptWidget()

        self.logo = QLabel(self, objectName = "logo")
        self.logo.setPixmap(QPixmap("Logo.png"))
        self.logo.setScaledContents(True)
        self.logo.setFixedSize(WIDTH, int(HEIGHT * 0.65))
        self.logo.show()
        
        self.topbarItems = QLabel(self, objectName = "topbarItemsContainer")
        self.topbarItems.setFixedSize(WIDTH, int(WIDTH * 0.20))
        self.topbarItems.move(0, int(HEIGHT * 0.65))

        self.screenSnipButton = QPushButton("CAPTURE", self.topbarItems, objectName = "screenSnipButton")
        self.screenSnipButton.clicked.connect(self.newSnipPressed)
        self.screenSnipButton.setFont(QFont("Roboto", int(HEIGHT * 0.05), 50, False))
        self.screenSnipButton.setFixedSize(int(WIDTH * 0.3), int(HEIGHT * 0.15))
        self.screenSnipButton.move(int(WIDTH * 0.15), int(HEIGHT * 0.04))

        self.openImageButton = QPushButton("UPLOAD", self.topbarItems, objectName = "openImageButton")
        self.openImageButton.clicked.connect(self.openImagePressed)
        self.openImageButton.setFont(QFont("Roboto", int(HEIGHT * 0.05), 50, False))
        self.openImageButton.setFixedSize(int(WIDTH * 0.3), int(HEIGHT * 0.15))
        self.openImageButton.move(int(WIDTH * 0.55), int(HEIGHT * 0.04))
        
        self.basicButtonLabels = QLabel("CAPTURE: Extract text from screenshot\n UPLOAD: Upload image from your PC", self.topbarItems, objectName = "basicButtonLabels")
        self.basicButtonLabels.setFont(QFont("Roboto", int(HEIGHT * 0.030), 50, False))
        self.basicButtonLabels.setFixedSize(int(WIDTH * 0.5), int(HEIGHT * 0.2))
        self.basicButtonLabels.move(int(WIDTH * 0.25), int(HEIGHT * 0.18))

        self.imagePreview = QLabel("", self, objectName = "imagePreview")
        self.imagePreview.hide()
        
        self.outputWindow = outputWindowWidget()
        self.outputWindow.hide()
    
    def newSnipPressed(self):
        self.hide()
        self.outputWindow.close() 
        self.screenRegionWindow.promptForRegion(callback = self.gotScreenRegionForSnip)

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
                #remove alpha channels
                if img.shape[-1] == 4:
                    img = img[:,:,:3]
                
            except BaseException as e:
                print("Failed to open image: %s" % str(e))
            
            self.newImage(img)
    
    def startOCR(self, image, id, language):
        text = None
        
        try:
            image = preprocess(image)
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
            print("Screen snipping cancelled")
            self.show()
        else:
            img = screenshotRegion(region)
            self.show()
            
            if img.shape[-1] == 4: # drop alpha channel/image transparency factor
                img = img[:,:,:3]
            img = img[:,:,::-1] # convert BGR -> RGB

            self.newImage(img)
    
    def newImage(self, img):
        self.image_source = img
        self.newOCR()
        
    def newOCR(self):
        if self.image_source is None: 
            return
        
        self.currentScanID += 1
        if self.currentScanID == 1: 
            self.imagePreview.show()
        
        language = None
        if self.currentOCRSourceLanguageIndex < len(supportedOCRLanguages):
            language = supportedOCRLanguages[self.currentOCRSourceLanguageIndex]
        else:
            language = supportedOCRScripts[self.currentOCRSourceLanguageIndex - len(supportedOCRLanguages) - 1]
        
        # show image
        h, w, ch = self.image_source.shape

        qimg = QImage(self.image_source.data.tobytes(), w, h, ch * w, QImage.Format_RGB888)
        self.imagePreview.setPixmap(QPixmap.fromImage(qimg).scaled(WIDTH, int(HEIGHT * 0.8), Qt.KeepAspectRatio, transformMode = Qt.SmoothTransformation))
        
        # resize main window
        self.imagePreview.setFixedSize(WIDTH, int(HEIGHT * 0.8))
        self.imagePreview.setAlignment(Qt.AlignCenter)
        self.imagePreview.move(0, HEIGHT)

        self.topbarItems.move(0, int(HEIGHT * 0.65))
        self.setFixedSize(WIDTH, int(HEIGHT * 1.8))
        self.basicButtonLabels.move(int(WIDTH * 0.25), int(HEIGHT * 0.18))
        
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