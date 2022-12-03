"""
Run from command line as (assuming a stacked tif file exists)
vis3d path_to_volume_file.tiff
or (assuming a folder with tif images exists)
vis3d path_to_folder
or (assuming text file with the link exists)
vis3d file_containing_path.txt
or simply run
vis3d and point to a supported file or folder.

Currently supported:
- folder with images
- .tif* file with stacked images
- url to .tif* file
- .vgi and corresponding vol file
- .txm file
- .txt file containing a url or file/folder path

TODO test whether txm works for txrm file, as in 2022_DANFIX_UTMOST
TODO Functionality for changing vmin and vmax
TODO When pressing I, show info about volume

TODO add support for: 
- dcm images (via pydicom?)
- .nii.gz file (via nibabel?)
- npy file containing 3d numpy array
- nrrd file (nearly raw), as in 2022_QIM_54_Butterflies
"""

import sys 
import PyQt5.QtCore  
import PyQt5.QtWidgets 
import PyQt5.QtGui
import numpy as np
import slicers

  
class Vis3d(PyQt5.QtWidgets.QWidget):
    
    def __init__(self, slicer):
        
        super().__init__() 
        
        self.slicer = slicer
        self.z = len(slicer)//2
            
        # Pixmap layers and atributes
        self.format = PyQt5.QtGui.QImage.Format_Grayscale8
        self.toint_function = slicer.toint8_function()
        if slicer.dtype == np.uint16:
            try:  # instead, I could check which version is installed
                self.format = PyQt5.QtGui.QImage.Format_Grayscale16
                self.toint_function = lambda im: im  # keep uint16
            except:
                print('Grayscale16 introduced in Qt 5.13, you have {PyQt5.QtCore.QT_VERSION_STR}')
                self.toint_function = slicer.toint8_function()
        self.updateImagePix()
        self.zoomPix = PyQt5.QtGui.QPixmap(self.imagePix.width(), self.imagePix.height()) 
        self.zoomPix.fill(self.transparentColor)
        
        # Atributes relating to the transformation between widget 
        # coordinate system and image coordinate system
        self.zoomFactor = 1 # accounts for resizing of the widget and for zooming in the part of the image
        self.padding = PyQt5.QtCore.QPoint(0, 0) # padding when aspect ratio of image and widget does not match
        self.target = PyQt5.QtCore.QRect(0, 0, self.width(),self.height()) # part of the target being drawn on
        self.source = PyQt5.QtCore.QRect(0, 0, 
                self.imagePix.width(), self.imagePix.height()) # part of the image being drawn
        self.offset = PyQt5.QtCore.QPoint(0, 0) # offset between image center and area of interest center
        
        # Atributes relating to zooming
        self.activelyZooming = False 
        self.newZoomValues = None
        self.clickedPoint = PyQt5.QtCore.QPoint()
        self.zoomPainter = None
        
        # Label for displaying text overlay
        self.textField = PyQt5.QtWidgets.QLabel(self)
        self.textField.setStyleSheet("background-color: rgba(191,191,191,191)")
        self.textField.setTextFormat(PyQt5.QtCore.Qt.RichText)
        self.textField.resize(0,0)
        self.textField.move(10,10)     
        self.hPressed = False
        self.textField.setAttribute(PyQt5.QtCore.Qt.WA_TransparentForMouseEvents)
        
        # Timer for displaying text overlay
        self.timer = PyQt5.QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hideText)

        # Playtime
        self.setTitle()
        initial_zoom = min(2000/max(self.imagePix.width(), 
                4*self.imagePix.height()/3),1) # downsize if larger than (2000,1500)
        self.resize(initial_zoom*self.imagePix.width(), 
                    initial_zoom*self.imagePix.height())
        self.showInfo('<i>Starting vis3d</i> <br> For help, hit <b>H</b>', 5000)
        print("Starting vis3d. For help, hit 'H'.")
    
    # constants
    transparentColor = PyQt5.QtGui.QColor(0, 0, 0, 0)    
    zoomColor = PyQt5.QtGui.QColor(0, 0, 0, 128) 
    
    helpText = (
        '<i>Help for vis3dD</i> <br>' 
        '<b>KEYBOARD COMMANDS:</b> <br>' 
        '&nbsp; &nbsp; <b>H</b> shows this help <br>' 
        '&nbsp; &nbsp; <b>Arrow keys</b> change slice <br>' 
        '<b>MOUSE DRAG:</b> <br>' 
        '&nbsp; &nbsp; Zooms ')

    def updateImagePix(self):  
        '''Transforms np image to Qt Pixmap (via Qt Image)'''
        gray = self.slicer[self.z]
        gray = self.toint_function(gray)
        bytesPerLine = gray.nbytes//gray.shape[0]
        qimage = PyQt5.QtGui.QImage(gray.data, 
                                    gray.shape[1], gray.shape[0],
                                    bytesPerLine, self.format)
        self.imagePix= PyQt5.QtGui.QPixmap(qimage)
            
    def showHelp(self):
        self.timer.stop()
        self.showText(self.helpText)
    
    def showInfo(self, text, time=1000):
        if not self.hPressed:
            self.timer.start(time)
            self.showText(text)
    
    def showText(self, text):
        self.textField.setText(text)
        self.textField.adjustSize()
        self.update()
          
    def hideText(self):
        self.textField.resize(0,0)
        self.update()
        
    def setTitle(self):
        self.setWindowTitle(f'z={self.z}/{len(self.slicer)}')
        
    def makeZoomPainter(self):
        painter_scribble = PyQt5.QtGui.QPainter(self.zoomPix)       
        painter_scribble.translate(-self.offset)
        painter_scribble.scale(1/self.zoomFactor, 1/self.zoomFactor)
        painter_scribble.translate(-self.padding)        
        painter_scribble.setCompositionMode(
                    PyQt5.QtGui.QPainter.CompositionMode_Source)
        return painter_scribble
    
    def paintEvent(self, event):
        """ Paint event for displaying the content of the widget."""
        painter_display = PyQt5.QtGui.QPainter(self) # this is painter used for display
        painter_display.setCompositionMode(
                    PyQt5.QtGui.QPainter.CompositionMode_SourceOver)
        painter_display.drawPixmap(self.target, self.imagePix, self.source)
        if self.activelyZooming:
            painter_display.drawPixmap(self.target, self.zoomPix, self.source)
            
    def mousePressEvent(self, event):
        if event.button() == PyQt5.QtCore.Qt.LeftButton: 
            self.activelyZooming = True
            self.clickedPoint = event.pos()
            self.zoomPix.fill(self.transparentColor) # clear (fill with transparent)
            self.zoomPainter = self.makeZoomPainter()          
            self.update()
    
    def mouseMoveEvent(self, event):
        if self.activelyZooming: 
            self.zoomPix.fill(self.transparentColor) # clear (fill with transparent)
            x = min(self.clickedPoint.x(), event.x())
            y = min(self.clickedPoint.y(), event.y())
            w = abs(self.clickedPoint.x() - event.x())
            h = abs(self.clickedPoint.y() - event.y())
            self.zoomPainter.fillRect(x, y, w, h, self.zoomColor)       
            self.update()
    
    def mouseReleaseEvent(self, event):  
        x = min(self.clickedPoint.x(), event.x())
        y = min(self.clickedPoint.y(), event.y())
        w = abs(self.clickedPoint.x() - event.x())
        h = abs(self.clickedPoint.y() - event.y())
        if w>2 and h>2: # Not zooming to les than 2x2 pixels
            self.newZoomValues = PyQt5.QtCore.QRect(x,y,w,h)
            self.executeZoom()
        else: 
            self.resetZoom()
        self.zoomPainter = None
        self.activelyZooming = False   
        self.update()
            
    def resizeEvent(self, event):
        """ Triggered by resizing of the widget window. """
        self.adjustTarget()
                
    def adjustTarget(self):
        """ Computes padding needed such that aspect ratio of the image is correct. """
       
        zoomWidth = self.width()/self.source.width()
        zoomHeight = self.height()/self.source.height() 
        
        # depending on aspect ratios, either pad up and down, or left and rigth
        if zoomWidth > zoomHeight:
            self.zoomFactor = zoomHeight
            self.padding = PyQt5.QtCore.QPoint(int((self.width() 
                            - self.source.width()*self.zoomFactor)/2), 0)
        else:
            self.zoomFactor = zoomWidth
            self.padding = PyQt5.QtCore.QPoint(0, int((self.height()
                            - self.source.height()*self.zoomFactor)/2))
            
        self.target = PyQt5.QtCore.QRect(self.padding, 
                            self.rect().bottomRight() - self.padding)
                   
    def executeZoom(self):
        """ Zooms to rectangle given by newZoomValues. """
        self.newZoomValues.translate(-self.padding)
        self.source = PyQt5.QtCore.QRect(self.newZoomValues.topLeft()/self.zoomFactor,
                self.newZoomValues.size()/self.zoomFactor)
        self.source.translate(-self.offset)
        self.source = self.source.intersected(self.imagePix.rect()) 
        self.showInfo('Zooming to ' + self.formatQRect(self.source))     
        self.offset = self.imagePix.rect().topLeft() - self.source.topLeft()
        self.adjustTarget()
        self.newZoomValues = None
    
    def resetZoom(self):
        """ Back to original zoom """
        self.source = PyQt5.QtCore.QRect(0,0,self.imagePix.width(), 
                                         self.imagePix.height())
        self.showInfo('Reseting zoom to ' + self.formatQRect(self.source))        
        self.offset = PyQt5.QtCore.QPoint(0,0)
        self.adjustTarget()        
        self.newZoomValues = None
            
    def keyPressEvent(self, event):

        if event.key()==PyQt5.QtCore.Qt.Key_Up: # uparrow          
            self.z = min(self.z+1, len(self.slicer)-1)
            self.updateImagePix()
            self.update()

        elif event.key()==PyQt5.QtCore.Qt.Key_Down: # downarrow
            self.z = max(self.z-1, 0)
            self.updateImagePix()
            self.update()
            
        elif event.key()==PyQt5.QtCore.Qt.Key_Right: 
            self.z = min(self.z+10, len(self.slicer)-1)
            self.updateImagePix()
            self.update()

        elif event.key()==PyQt5.QtCore.Qt.Key_Left: 
            self.z = max(self.z-10, 0)
            self.updateImagePix()
            self.update()

        elif event.key()==PyQt5.QtCore.Qt.Key_H: # h        
            if not self.hPressed:
                self.hPressed = True
                self.showHelp()
        elif event.key()==PyQt5.QtCore.Qt.Key_Escape: # escape
            self.closeEvent(event)
        self.setTitle()
        
    def keyReleaseEvent(self, event):
        if event.key()==PyQt5.QtCore.Qt.Key_H: # h
            self.hideText()
            self.hPressed = False
            
    # def closeEvent(self, event):
    #     self.showInfo("Bye, I'm closing")
    #     PyQt5.QtWidgets.QApplication.quit()
    #     # hint from: https://stackoverflow.com/questions/54045134/pyqt5-gui-cant-be-close-from-spyder
    #     # should also check: https://github.com/spyder-ide/spyder/wiki/How-to-run-PyQt-applications-within-Spyder
   

    @staticmethod
    def formatQRect(rect):
        coords =  rect.getCoords()
        s = f'({coords[0]},{coords[1]})--({coords[2]},{coords[3]})'
        return(s)  

    
def chose_file():
    file_dialog = PyQt5.QtWidgets.QFileDialog()
    
    # TODO, file_dialog.setHistory
    # A text file with history may be placed in
    # pathlib.Path(__file__).resolve()
    
    if file_dialog.exec_(): # file chosen
        volumenames = file_dialog.selectedFiles()
        volumename = volumenames[0]
        return volumename
    # else retuns None
    
            
def main():
    app = PyQt5.QtWidgets.QApplication([]) 
    
    # Volume name given in command line.
    if len(sys.argv)>1:
        volumename = sys.argv[1]

    # System dialog for choosing volume name.
    else:
        volumename = chose_file()  # May return None.

    if volumename:    
        slicer = slicers.slicer(volumename)                
        vis3d = Vis3d(slicer)
        vis3d.show()
        app.exec() 
        
    
if __name__ == '__main__':
    
    '''
    May be used from command-line. If no volumename given, it may be chosen 
    via a dialog window.
    '''
    main()

   
    
    
    
    