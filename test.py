import os
import numpy as np
import mss
import PIL
import pathlib
import threading
import pytesseract.pytesseract as tesseract

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import QWebEngineView as QWebView

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
tessdataDirectory =  "/usr/share/tesseract-ocr/4.00/tessdata" if OS == 'Linux' else "C:/Program Files/Tesseract-OCR/tessdata" 

tesseract.tesseract_cmd = r'/usr/bin/tesseract' if OS == 'Linux' else tesseractDirectory + r"/tesseract.exe"
tessdataConfig = r'--tessdata-dir "%s"' % tessdataDirectory

def getTextFromImg(img, timeout = 3, language = 'eng'):
    return tesseract.image_to_string(img, timeout = timeout, lang = language, config = tessdataConfig)

# displaced to displayInfo

# displaced to screenRegion

# displaced to output

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
windowWidth_noImage = int(dimension['width'] * 0.5)
windowHeight_noImage = int(dimension['height'] * 0.5)

class mainWindowWidget(QMainWindow):
    currentScanID = 0 
    image_source = None
    currentOCRSourceLanguageIndex = 0
    lastOpenedDirectory = os.path.expanduser("~\\Pictures")

    def __init__(self, *args, **kwargs):
        super(mainWindowWidget, self).__init__(*args, **kwargs)
        self.setWindowTitle("MetaCopy")
        self.setStyleSheet(mainWindow_CSS)
        
        self.setFixedSize(windowWidth_noImage, windowHeight_noImage)
        
        self.screenRegionWindow = screenRegionPromptWidget()

        self.logo = QLabel(self, objectName = "logo")
        self.logo.setPixmap(QPixmap("Logo.png"))
        self.logo.setScaledContents(True)
        self.logo.setFixedSize(windowWidth_noImage, int(windowHeight_noImage * 0.65))
        self.logo.show()
        
        self.topbarItems = QLabel(self, objectName = "topbarItemsContainer")
        self.topbarItems.setFixedSize(windowWidth_noImage, int(windowWidth_noImage * 0.20))
        self.topbarItems.move(0, int(windowHeight_noImage * 0.65))

        self.screenSnipButton = QPushButton("CAPTURE", self.topbarItems, objectName = "screenSnipButton")
        self.screenSnipButton.clicked.connect(self.newSnipPressed)
        self.screenSnipButton.setFont(QFont("Roboto", int(windowHeight_noImage * 0.05), 50, False))
        self.screenSnipButton.setFixedSize(int(windowWidth_noImage * 0.3), int(windowHeight_noImage * 0.15))
        self.screenSnipButton.move(int(windowWidth_noImage * 0.15), int(windowHeight_noImage * 0.04))

        '''
        self.screenSnipButton = QPushButton("CONTACT US", self.topbarItems, objectName = "nopen_webbrowser")
        self.screenSnipButton.clicked.connect(self.open_webbrowser)
        self.screenSnipButton.setFont(QFont("Gotham", 14, 1000, False))
        self.screenSnipButton.setFixedSize(160, 50 - 12 )
        self.screenSnipButton.move(30+ 190 + 30, 7)
        '''

        self.openImageButton = QPushButton("UPLOAD", self.topbarItems, objectName = "openImageButton")
        self.openImageButton.clicked.connect(self.openImagePressed)
        self.openImageButton.setFont(QFont("Roboto", int(windowHeight_noImage * 0.05), 50, False))
        self.openImageButton.setFixedSize(int(windowWidth_noImage * 0.3), int(windowHeight_noImage * 0.15))
        self.openImageButton.move(int(windowWidth_noImage * 0.55), int(windowHeight_noImage * 0.04))
        
        self.basicButtonLabels = QLabel("CAPTURE: Extract text from screenshot\n UPLOAD: Upload image from your PC", self.topbarItems, objectName = "basicButtonLabels")
        self.basicButtonLabels.setFont(QFont("Roboto", int(windowHeight_noImage * 0.030), 50, False))
        self.basicButtonLabels.setFixedSize(int(windowWidth_noImage * 0.5), int(windowHeight_noImage * 0.2))
        self.basicButtonLabels.move(int(windowWidth_noImage * 0.25), int(windowHeight_noImage * 0.18))

        self.imagePreview = QLabel("", self, objectName = "imagePreview")
        self.imagePreview.hide()
        
        self.outputWindow = outputWindowWidget()
        self.outputWindow.hide()
    
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
        #print('h : ' + str(h))
        #print('w : ' + str(w))
        #print('ch : ' + str(ch))

        qimg = QImage(self.image_source.data.tobytes(), w, h, ch * w, QImage.Format_RGB888)
        self.imagePreview.setPixmap(QPixmap.fromImage(qimg).scaled(windowWidth_noImage, int(windowHeight_noImage * 0.8), Qt.KeepAspectRatio, transformMode = Qt.SmoothTransformation))
        #self.imagePreview.setFixedSize(w, h)
        
        # resize main window
        topbarWidth = windowWidth_noImage #30 + 200 + 30 + 300 + 30 + 200 + 30
        imageWidth = w
        imagePosition = 3
        topbarPosition = 3
        windowWidth = windowWidth_noImage

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
        
        self.imagePreview.setFixedSize(windowWidth_noImage, int(windowHeight_noImage * 0.8))
        self.imagePreview.setAlignment(Qt.AlignCenter)
        self.imagePreview.move(0, windowHeight_noImage)

        #self.topbarItems.move(math.floor(topbarPosition) + 100, 10)
        #self.setFixedSize(math.ceil(windowWidth), 175 + h)
        #self.basicButtonLabels.move(math.floor(topbarPosition) + 125, 75)
        #self.combo.move(math.floor(topbarPosition) + 550, 80)
        self.topbarItems.move(0, int(windowHeight_noImage * 0.65))
        self.setFixedSize(windowWidth_noImage, int(windowHeight_noImage * 1.8))
        self.basicButtonLabels.move(int(windowWidth_noImage * 0.25), int(windowHeight_noImage * 0.18))
        
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