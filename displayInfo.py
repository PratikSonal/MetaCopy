'''
DISPLAY INFORMATION
'''

import ctypes

def getVirturalDesktopDimensions():
    SM_XVIRTUALSCREEN = 76 # LEFTMOST POSITION (not always 0)
    SM_YVIRTUALSCREEN = 77 # TOPMOST POSITION  (not always 0)
    
    SM_CXVIRTUALSCREEN = 78 # WIDTH (of all monitors)
    SM_CYVIRTUALSCREEN = 79 # HEIGHT (of all monitors)

    displayData = {
        "left": ctypes.windll.user32.GetSystemMetrics(SM_XVIRTUALSCREEN),
        "top": ctypes.windll.user32.GetSystemMetrics(SM_YVIRTUALSCREEN),
        "width": ctypes.windll.user32.GetSystemMetrics(SM_CXVIRTUALSCREEN),
        "height": ctypes.windll.user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
    }
    
    return displayData