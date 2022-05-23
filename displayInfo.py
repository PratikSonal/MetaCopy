'''
DISPLAY INFORMATION
'''
from sys import platform
import ctypes
from screeninfo import get_monitors

def getOS():
    if platform == "linux" or platform == "linux2":
        return 'Linux'
    elif platform == "win32":
        return 'Windows'

def getVirturalDesktopDimensions():
    SM_XVIRTUALSCREEN = 76 # LEFTMOST POSITION (not always 0)
    SM_YVIRTUALSCREEN = 77 # TOPMOST POSITION  (not always 0)
    
    SM_CXVIRTUALSCREEN = 78 # WIDTH (of all monitors)
    SM_CYVIRTUALSCREEN = 79 # HEIGHT (of all monitors)

    OS = getOS()
    displayData = {}

    if OS == 'Windows':
        displayData = {
            "left": ctypes.windll.user32.GetSystemMetrics(SM_XVIRTUALSCREEN),
            "top": ctypes.windll.user32.GetSystemMetrics(SM_YVIRTUALSCREEN),
            "width": ctypes.windll.user32.GetSystemMetrics(SM_CXVIRTUALSCREEN),
            "height": ctypes.windll.user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
        }
    else:
        monitor = get_monitors()
        displayData = {
            "left": monitor[0].x,
            "top": monitor[0].y,
            "width": monitor[0].width,
            "height": monitor[0].height
        }
    
    return displayData