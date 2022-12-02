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
import glob  
import PIL
import urllib
import tifffile

class Slicer:
    ''' Base class for volume slicers.'''
    # Mandatory attributes: dtype, imshape
    # Recommended atributes: range
    # Mandatory methods: __len__, __getitem__

    def loadvol(self):
        ''' TODO
        Default loads slice by slice. It might be more efficient to 
        implement a custom loader which utilizes the ordering of slices'''
        pass
       

class VgiSlicer(Slicer):
    '''Reads slices from .vol and an associated .vgi file.'''
    
    def __init__(self, filename):
                
        vgifilename = filename
        volfilename = filename.replace('.vgi', '.vol')

        parser = configparser.ConfigParser()
        config = ''
        with open(vgifilename) as f:
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
        self._filenames = sorted(glob.glob(foldername + '/*.tif*'))
        im0 = tifffile.TiffFile(self._filenames[0])
        self.dtype = im0.pages[0].dtype
        self.imshape = im0.pages[0].shape
        im0.close()

    def __len__(self):
        return len(self._filenames)

    def __getitem__(self, z):
        return tifffile.imread(self._filenames[z])


class FolderSlicer(Slicer):
    def __init__(self, foldername, ext='tif*'):
        self._filenames = sorted(glob.glob(foldername + '/*.' + ext ))
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
        return cls(urllib.request.urlopen(url))
    


class npSlicer(Slicer):
    def __init__(self, vol):
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






# %%
