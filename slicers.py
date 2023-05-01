'''
Utility for efficient slicing of CT data.
VgiSlicer and TxmSlicer are heavily inspired by 
https://ctutils.readthedocs.io.


Author: Vedrana Dahl, 2022
'''

import numpy as np
import configparser  # for easy reading of .vgi file
import compoundfiles  # for reading .txm files
import struct  # for conversion from bytes to values
import PIL.Image
import urllib.request
import tifffile
import os

class Slicer:
    ''' Base class for volume slicers.'''

    def __init__(self):
        self.dtype = None
        self.imshape = None
        self.range = None
        self.filename = ''
    
    def __len__(self):
        return 0

    def loadvol(self, verbose=False):
        ''' Default loads slice by slice. For most slicers, it would be more 
        efficient to implement a custom loader which utilizes the ordering of 
        slices'''
        
        vol = np.empty((len(self),) + self.imshape, dtype=self.dtype)
        for z in range(len(self)):
            if verbose:
                print(f'slice {z}/{len(self)}')
            vol[z] = self[z]
        return vol
        
    def to_uint8(self):
        ''' Returns a suitable function which casts slicer output to uint8.
        TODO: include other relevant options.'''
        
        if self.dtype == np.dtype('uint8'):
            return Slicer.identity
        
        if self.dtype == np.dtype('uint16'):
            return Slicer.uint16_to_8

        if self.dtype == np.dtype('float32'):       
            if self.range is None:
                return Slicer.slicewise
            else:
                return self.to_range

        else:
            return Slicer.slicewise
        
    def to_range(self, im):
        im -= self.range[0]
        im *= 1/(self.range[1] - self.range[0])
        return (255*im).astype('uint8')

    @staticmethod
    def identity(im):
        return im

    @staticmethod
    def uint16_to_8(im):
        return (im/256).astype('uint8')

    @staticmethod
    def slicewise(im):
        im -= im.min()
        im *= 1/im.max()
        return (255*im).astype('uint8')


class VgiSlicer(Slicer):
    '''Reads slices from .vol and an associated .vgi file.'''
    
    def __init__(self, filename):

        super().__init__()        
        self.filename = filename
        parser = configparser.ConfigParser()
        config = ''
        with open(filename) as f:
            line = f.readline() # skipping first line
            while line:
                line = f.readline()
                if line[0] == '{': break
                config += line

        parser.read_string(config)
        size = parser.get('file1', 'Size')
        volsize = tuple(int(n) for n in size.split())  # (w, h, l) or (l, w, h)?!
        type = parser.get('file1', 'Datatype')
        bpe = int(parser.get('file1', 'BitsPerElement'))
        self.dtype = {('float', 32): np.dtype('float32'),
                    ('float', 64): np.dtype('float64'),
                    ('unsigned integer', 16): np.dtype('uint16'),
                    ('unsigned integer', 32): np.dtype('uint32')}[(type, bpe)]
        datarange = parser.get('file1', 'datarange')
        self.range = [float(n) for n in datarange.split()]
        self._length = volsize[2]
        self._imlength = volsize[0] * volsize[1]
        self.imshape = (volsize[0], volsize[1])
        volfilename = filename.replace('.vgi', '.vol')
        self._stream = open(volfilename)  # speedup if stream kept open

    def __del__(self):
        self._stream.close()

    def __len__(self):
        return self._length

    def __getitem__(self, z):
        self._stream.seek(self._imlength * z * self.dtype.itemsize)
        im = np.fromfile(self._stream, dtype=self.dtype, count=self._imlength)
        return im.reshape(self.imshape)


class TxmSlicer(Slicer):
    '''Reads slices from a .txm file.'''
    
    def __init__(self, filename):

        super().__init__()   
        self.filename = filename
        self._data = compoundfiles.CompoundFileReader(filename)
        # '<L' is for little-endian, unsigned long
        width = struct.unpack('<L', self._data.open(
                '/ImageInfo/ImageWidth').read())[0]
        height = struct.unpack('<L', self._data.open(
                '/ImageInfo/ImageHeight').read())[0]
        self.imshape = (height, width)
        # length = struct.unpack('<L', self._data.open(
        #     '/ImageInfo/ImagesTaken').read())[0]  # Has to be the same as len(keys).
        datatype = struct.unpack('<L', self._data.open(
                '/ImageInfo/DataType').read())[0]
        self.dtype = {5: np.dtype('uint16'), 10: np.dtype('float32')}[datatype]      
        self._keys = []
        for storage in self._data.root:
            if storage.isdir and storage.name.startswith('ImageData'):
                for stream in storage:
                    if stream.isfile and stream.name.startswith('Image'):
                        self._keys += [f'/{storage.name}/{stream.name}']
        # I believe that the value range can be extracted from fields 
        # '/GlobalMinMax/GlobalMin' and '/GlobalMinMax/GlobalMax', but maybe 
        # only for float32 datatype!? 

    def __del__(self):
        self._data.close()

    def __len__(self):
        return len(self._keys)

    def __getitem__(self, z):
        key = self._keys[z]
        im = np.frombuffer(self._data.open(key).read(), 
                           dtype=self.dtype)
        return im.reshape(self.imshape)


class TiffFolderSlicer(Slicer):

    def __init__(self, foldername):

        super().__init__()   
        self.filename = foldername
        self._filenames = list_imfiles(foldername, ['.tif', '.tiff'])
        im0 = tifffile.TiffFile(self._filenames[0])
        self.dtype = im0.pages[0].dtype
        self.imshape = im0.pages[0].shape
        im0.close()

    def __len__(self):
        return len(self._filenames)

    def __getitem__(self, z):
        return tifffile.imread(self._filenames[z])


class FolderSlicer(Slicer):

    def __init__(self, foldername, ext=['.tif', '.tiff']):

        super().__init__()   
        self.filename = foldername
        self._filenames = list_imfiles(foldername, ext)
        im0 = PIL.Image.open(self._filenames[0])
        self.dtype = PIL_mode_to_np_dtype(im0.mode)
        self.imshape = im0.size
        im0.close()
        
    def __len__(self):
        return len(self._filenames)

    def __getitem__(self, z):
        return np.array(PIL.Image.open(self._filenames[z]))


class TiffFileSlicer(Slicer):
    
    def __init__(self, filename):

        super().__init__()   
        self.filename = filename
        self._tiffFile = tifffile.TiffFile(filename)
        self._len = len(self._tiffFile.pages)
        self.dtype = self._tiffFile.pages[0].dtype
        self.imshape = self._tiffFile.pages[0].shape

    def __del__(self):
        self._tiffFile.close()

    def __len__(self):
        return self._len

    def __getitem__(self, z):
        return self._tiffFile.pages[z].asarray()


class FileSlicer(Slicer):
    
    def __init__(self, filename):

        super().__init__()   
        self.filename = filename
        self._volfile = PIL.Image.open(filename)
        self.dtype = PIL_mode_to_np_dtype(self._volfile.mode)
        self.imshape = self._volfile.size
        
    def __del__(self):
        self._volfile.close()
     
    def __len__(self):
        return self._volfile.n_frames

    def __getitem__(self, z):
        self._volfile.seek(z)
        return np.array(self._volfile)

    @classmethod
    def from_url(cls, url):
        slicer = cls(urllib.request.urlopen(url))
        slicer.filename = url
        return slicer
    


class npSlicer(Slicer):
    ''' A silly slicer, allowing vis3d to work on numpy arrays. '''

    def __init__(self, vol):

        super().__init__()   
        self._vol = vol
        self.dtype = vol.dtype
        self.imshape = vol.shape[1:]
    
    def __len__(self):
        return(self._vol.shape[0])

    def __getitem__(self, z):
        return self._vol[z]


def PIL_mode_to_np_dtype(mode):
    '''This is neither complete, nor have all cases been tested!!! ''' 

    if 'I;16' in mode:
        mode = 'I;16'
    dtype = {'L': np.dtype('uint8'),
            'I': np.dtype('int32'),
            'F': np.dtype('float32'),
            'I;16': np.dtype('uint16')}[mode]
    return dtype


def list_imfiles(folder, ext=['.tif', '.tiff']):

    files = os.listdir(folder)
    if ext is None:
        extlist = ['.png', '.jpg', '.tiff', '.tif']
        hist = dict.fromkeys(extlist, 0)
        for f in files:
            ext = os.path.splitext(f)[-1].lower()
            if ext in extlist:
                hist[ext] += 1
        ext = max(hist)

    # usint `in ext` to allow for both .tif and .tiff
    files = [os.path.join(folder, f) for f in files
            if os.path.splitext(f)[-1].lower() in ext]
    files = sorted(files)
    return files


def slicer(source):
    '''Given a source (tries to) resolve which slicer to use. This supports
    vgi+vol files, txm files, numpy arrays, a folder containing tiff images, 
    an url of tiff stacked file, a tiff stacked file, or a text file containing 
    a name of any of such files volume.

    '''

    # In an unusual case of being given np array
    if ((type(source)==np.ndarray) and (source.ndim==3)):
        return npSlicer(source)

    elif os.path.isdir(source):
        try:
            return TiffFolderSlicer(source)  # trying tiff
        except:
            return FolderSlicer(source, None)  # trying any type images
             
    elif ((len(source)>4) and (source[:4]=='http') and 
          ('tif' in os.path.splitext(source)[-1].lower())):
        return FileSlicer.from_url(source)

    else:  # a single file
        ext = os.path.splitext(source)[-1]
        
        if 'tif' in ext:
            #  TiffFileSlicer seems to handle strange filenames
            #  better than FileSlicer
            try:
                return TiffFileSlicer(source) 
            except:
                return FileSlicer(source) 
        
        if ext == '.vgi':
            return VgiSlicer(source)
        
        if ext == '.vol':
            return VgiSlicer(source.replace('.vol', '.vgi'))

        if ext == '.txm' or ext=='.txrm':
            return TxmSlicer(source)
        
        # A single file containing volume name, resolved by recursion.
        elif ext=='.txt':
            with open(source) as f:
                content = f.read().strip()
                return slicer(content) 
        else:
            raise Exception(f"Couldn't resolve volume {source}.")
    
# %%
