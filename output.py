'''
OUTPUT WINDOW
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

outputWindow_CSS = '''
QMainWindow{
    #background-color: rgb(30, 30, 30);
    background-color: rgb(255, 255, 255);
}
#statusLabel{
    #color: white;
    color: black
}
QPlainTextEdit{
    #background-color: rgb(70, 70, 70);
    #color: white;
    background-color: rgb(0, 0, 0);
    color: black;
}
'''

OCRSTATUS_BEGIN = 0
OCRSTATUS_ERROR = 1
OCRSTATUS_TIMEOUT = 2
OCRSTATUS_FINISH = 3

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