"""
Save a volume as downscaled tif.

Run from command line, for example: 
    tiffify source destination -factor 4

    Positional arguments:
    - source, source volume filename (path)
    - destination, destination filename (path), defaults to tiffified_volume.tif

    Options taking values:
    - factor, int, defaults to 8. Downscaling factor.
    - vrange, consumes two arguments. If given values will be scaled such that
        vrange maps to [0, 1], truncating the values outside the range 
    - dtype, destination dtype. If set to uint8 or uint16 values will be 
        multiplied and casted. NOTE: use only if values are scaled to [0, 1], 
        e.g. by using vrange.

    Flag:
    - overwrite. If set than allows overwritting. NOTE: use with care.

"""


import numpy as np
import slicers
import argparse
import os
              
def main():

    parser = argparse.ArgumentParser(description='Save volume as downscaled tif.')
    parser.add_argument('source')
    parser.add_argument('destination', nargs='?')
    parser.add_argument('--factor', type=int, default=8) 
    parser.add_argument('--vrange', nargs=2)
    parser.add_argument('--dtype')
    parser.add_argument('--overwrite', action='store_true', default=False)
    
    args = parser.parse_args()

    if args.destination is None:
        args.destination = 'tiffified_volume.tif'
    
    if (not args.overwrite) and os.path.exists(args.destination):
        print('Destination already exists. Aborting')
        return
    
    # Normalization function, if vrange given
    if args.vrange is None:
        normalize = lambda s: s
    else:
        vmin, vmax = args.vrange
        vmin, vmax = float(vmin), float(vmax)
        normalize = lambda s: np.clip((s.astype(float) - vmin)/(vmax - vmin), 0, 1)
    
    # Casting, if dtype given
    if args.dtype is None:
        cast = lambda s: s
    else:
        m = {'uint8': 255, 'uint16': 65535}
        cast = lambda s: (m[args.dtype] * s).astype(args.dtype)

    print('Opening source volume.')
    slicer = slicers.slicer(args.source)
    
    # Preparing to downsample by args.factor
    Z = range((len(slicer)%args.factor)//2, len(slicer), args.factor) 
    Y = range((slicer.imshape[0]%args.factor)//2, slicer.imshape[0], args.factor) 
    X = range((slicer.imshape[1]%args.factor)//2, slicer.imshape[1], args.factor) 
    subindexing = np.ix_(Y, X)

    # Trying on the first slice, to avoid opening file if something goes wrong.
    slice = slicer[0]
    subslice = slice[subindexing]
    subslice = normalize(subslice)
    subslice = cast(subslice)
    
    print(f'Writing volume of size {len(Z)}, {len(Y)}, {len(X)}... ', end='')    
    writer =  slicers.tifffile.TiffWriter(args.destination)

    for z in Z:
        slice = slicer[z]
        subslice = slice[subindexing]
        subslice = normalize(subslice)
        subslice = cast(subslice)
        writer.write(subslice)           
    writer.close()    
    print('Done!')
    
if __name__ == '__main__':
    
    main()
  

   
    
    
    
    