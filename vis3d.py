"""
Run from command line as
vis3d https://qim.compute.dtu.dk/data-repository/InSegt_data/3D/nerves_part.tiff
or (assuming text file with the link exists)
vis3d /Users/vand/Documents/PROJECTS2/goodies/goodies_to_merge/vis3d/nerves_part_url_link.txt
or (assuming a folder with tif images exists)
vis3d /Users/vand/Documents/PROJECTS2/goodies/goodies_to_merge/testing_data/walnut
or (assuming a stacked tif file exists)
vis3d /Users/vand/Documents/PROJECTS2/goodies/goodies_to_merge/testing_data/nerves_part.tiff
or simply run
vis3d and point to a supported file or folder.


Currently supported:
- folder tif* images
- .tif* file with stacked images
- url to tif* file
- .txt (or .link) file containing a url or file/folder path

TODO add support for: 
- folder with other image types readable with PIL
- dcm images (via pydicom)
- .nii.gz file, load it as numpy array via nibabel
- npy file containing 3d numpy array
- a folder containing vol + vgi file 

TODO: Have basic version work with PIL and add optional imports of tifffile, 
nibabel and/or pydicom.
    
"""

import sys 
import PyQt5.QtCore  
import PyQt5.QtWidgets 
import PyQt5.QtGui
import os
import glob
import tifffile
import PIL.Image
import numpy as np
import urllib.request

  
class Vis3d(PyQt5.QtWidgets.QWidget):
    
    def __init__(self, getslice, Z, z=None):
        
        super().__init__() 
        
        self.Z = Z
        if z==None:
            self.z = Z//2
        else:
            self.z = z
        self.getslice = getslice
            
        # Pixmap layers and atributes
        self.imagePix = self.grayToPixmap(self.getslice(self.z))
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
        self.setWindowTitle(f'z={self.z}/{self.Z}')
        
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
            self.z = min(self.z+1, self.Z-1)
            self.imagePix = self.grayToPixmap(self.getslice(self.z))
            self.update()

        elif event.key()==PyQt5.QtCore.Qt.Key_Down: # downarrow
            self.z = max(self.z-1, 0)
            self.imagePix = self.grayToPixmap(self.getslice(self.z))
            self.update()
            
        elif event.key()==PyQt5.QtCore.Qt.Key_Right: 
            self.z = min(self.z+10, self.Z-1)
            self.imagePix = self.grayToPixmap(self.getslice(self.z))
            self.update()

        elif event.key()==PyQt5.QtCore.Qt.Key_Left: 
            self.z = max(self.z-10, 0)
            self.imagePix = self.grayToPixmap(self.getslice(self.z))
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
    def grayToPixmap(gray):
        """Np grayscale array to Qt pixmap. Works for 8-bit grayscale image. Limited support for 16-bit."""

        format = PyQt5.QtGui.QImage.Format_Grayscale8
        if gray.dtype == np.uint16:
            try:
                format = PyQt5.QtGui.QImage.Format_Grayscale16
            except:
                print('Grayscale16 introduced in Qt 5.13, you have {PyQt5.QtCore.QT_VERSION_STR}')
        
        bytesPerLine = gray.nbytes//gray.shape[0]
        qimage = PyQt5.QtGui.QImage(gray.data, gray.shape[1], gray.shape[0],
                                    bytesPerLine,
                                    format)
        qpixmap = PyQt5.QtGui.QPixmap(qimage)
        return qpixmap
    
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
    
# ------------------------------------------------------- #
# -- SUPPORT FOR MORE VOLUME FORMATS TO BE ADDED BELOW -- #
# You need to: 
#     - Add slicer function for this format. It has to 
#       return uint8 (or uint16) numpy image!
#     - Extend resolve_input to recongnize the new format.

def volFileSlicer(volfile):
    ''' Slicing .vol file based on info from .vgi file.  Assumes that .vgi file
    with the same name is is placed in the same folder.'''

    def get_fileinfo(vgifile):
        '''This is reverse-engineered by looking at .vgi file.
        Later, I found a reader here: 
        https://github.com/waveform-computing/ctutils/blob/release-0.3/ctutils/readers.py 
        '''
        size, type, range, bpe = None, None, None, None
        line = True
        
        # I use ordering of fields in the vgi file to read the SECOND datarange. 
        # I don't know whether this generalizes.
        with open(vgifile) as f:
            while not(size) and line:
                line = f.readline()
                if line.startswith('Size = '):
                    size = [int(n) for n in line.split(' = ')[1].split()]
            while not(type) and line:
                line = f.readline()
                if line.startswith('Datatype = '):
                    type = line.split(' = ')[1].strip()
            while not(range) and line:
                line = f.readline()
                if line.startswith('datarange = '):
                    range = [float(n) for n in line.split(' = ')[1].split()]
            while not(bpe) and line:
                line = f.readline()
                if line.startswith('BitsPerElement = '):
                    bpe = int(line.split(' = ')[1])
        try:
            dtype = {('float', 32): np.float32,
                    ('float', 64): np.float64,
                    ('unsigned integer', 16): np.uint16,
                    ('unsigned integer', 32): np.uint32}[(type, bpe)]

            # function for values in range of uint16 (but not casted dtype)
            normalize = {('float', 32): 
                            lambda im: (65535*(im - range[0])/(range[1] - range[0])),
                    ('float', 64): 
                            lambda im: (65535*(im - range[0])/(range[1] - range[0])),
                    ('unsigned integer', 16): 
                            lambda im: im,
                    ('unsigned integer', 32): 
                            lambda im: (im/256)}[(type, bpe)]
        except:
            raise Exception(f"Can't recognize data type from {type} {bpe}")

        return size, dtype, normalize
        
    size, dtype, normalize = get_fileinfo(volfile[:-4] + '.vgi')
    print(size)
    print(dtype)
    print(normalize)

    
    Z = size[0]
    n = size[1] * size[2]
    
    def readslice(z):
        im = np.fromfile(volfile, dtype=dtype, count=n, 
                offset=n * z * dtype().nbytes)
        im = normalize(im.reshape(size[1:])).astype(np.uint16)
        return im
    
    return readslice, Z


def tiffFolderSlicer(foldername):
    # TODO: figure out dominant image format in the folder
    D = sorted(glob.glob(foldername + '/*.tif*'))
    Z = len(D)
    readslice = lambda z: tifffile.imread(D[z])
    # readslice = lambda z: np.array(PIL.Image.open(D[z]))
    return readslice, Z

def tiffFileSlicer(filename):
    tif = tifffile.TiffFile(filename)
    Z = len(tif.pages)
    readslice = lambda z: tifffile.imread(filename, key = z)
    return readslice, Z

def urlSlicer(url):
    volfile = PIL.Image.open(urllib.request.urlopen(url))
    Z = volfile.n_frames
    def readslice(z):
        volfile.seek(z)
        return(np.array(volfile))
    return readslice, Z

def npSlicer(vol):
    Z = vol.shape[0]
    readslice = lambda z: vol[z]
    return readslice, Z

def resolve_input(volumename):
    '''Given volumename resolve what this input is: a numpy array, 
    a folder containing images, an url of tiff stacked file, a tiff stacked file,
    or a text file containing a name of the volume.'''

    # Mode 'numpy' is special case, e.g. when calling vis3d from another program.
    if ((type(volumename)==np.ndarray) and (volumename.ndim==3)):
        return npSlicer(volumename) + (volumename,)

    elif os.path.isdir(volumename):

        return tiffFolderSlicer(volumename) + (volumename,)

    elif ((len(volumename)>4) and (volumename[:4]=='http') and 
          ('tif' in os.path.splitext(volumename)[-1])):
        return urlSlicer(volumename)

    else:  # a single file
        ext = os.path.splitext(volumename)[-1]
        
        if 'tif' in ext:
            return tiffFileSlicer(volumename) + (volumename,)
        
        if ext == '.vol':
            return volFileSlicer(volumename) + (volumename,)
        
        # A single file containing volume name (recursion).
        # This is the case where volumename changes.
        elif (ext=='.txt') or (ext=='.link'):
            with open(volumename) as f:
                content = f.read().strip()
                return resolve_input(content)
    
    return None, None, None
 

def slicer(volumename):
    
    app = PyQt5.QtWidgets.QApplication([]) 
    
    # Open file dialog if not given volume name
    if not volumename:
        volumename = chose_file()
            
    readslice, Z, volumename = resolve_input(volumename)

    if readslice: # file type identified
        try: # read one slice (the last one) before initiating vis3d
            readslice(Z-1)       
        except:
            raise Exception(f"Can't read slices from volume {volumename}")
    else:
        raise Exception(f'Volume format not identified for {volumename}')
            
    vis3d = Vis3d(readslice, Z)
    vis3d.show()
    app.exec() 
        
    
def main():
    if len(sys.argv)>1:
        volumename = sys.argv[1]
    else:
        volumename = None        
    
    slicer(volumename)
         
    
if __name__ == '__main__':
    
    '''
    vis3d may be used from command-line. If no volumename  or url is given, 
    it may be chosen via en dialog window.
    '''
    main()

   
    
    
    
    