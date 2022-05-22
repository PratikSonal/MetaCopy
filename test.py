import os
import numpy as np
import mss
import PIL
import math
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

from screenRegion import screenRegionPromptWidget
from output import outputWindowWidget

'''
PASTE REGION

class KeyboardListener(QObject):
    textChanged = pyqtSignal(str)
    def __init__(self, shortcut, parent = None):
        super().__init__(parent) 
        self._shortcut = shortcut
        listener = Listener(on_press = self.handle_pressed)
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

PASTE REGION ENDS
'''

screencap = mss.mss()

def screenshotRegion(screenRegion):
    #print(np.asarray(screencap.grab(screenRegion)))
    return np.asarray(screencap.grab(screenRegion))

myDirectory = str(pathlib.Path(__file__).parent.absolute())
tesseractDirectory = "C:/Program Files/Tesseract-OCR" 
tessdataDirectory = "C:/Program Files/Tesseract-OCR/tessdata" 

tesseract.tesseract_cmd = tesseractDirectory + r"/tesseract.exe"
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

    '''
    @pyqtSlot(str)
    def handle_text_changed(self, text):
        self.keyboard.type(text)
    '''

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

        '''
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
        '''

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
        #self.combo.move(math.floor(topbarPosition) + 550, 80)
        
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