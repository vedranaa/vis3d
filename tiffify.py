"""
Run from command line as 
tiffify source_filename destination_filename downscale_factor=8
"""


import numpy as np
import slicers
import argparse
import os
              
def main():

    parser = argparse.ArgumentParser(description='Save volume as downscaled tif.')
    parser.add_argument('source')
    parser.add_argument('destination', nargs='?')
    parser.add_argument('-f', '--factor', type=int, default=8) 
    parser.add_argument('--vrange', nargs=2)
    parser.add_argument('--dtype')
    parser.add_argument('--overwrite', type=bool, action='store_true', default=False)
    
    args = parser.parse_args()

    print(f'args.overwrite=')

    if args.destination is None:
        args.destination = 'tiffified_volume.tif'
    
    if (not args.overwrite) and os.path.isfile(args.destination):
        print('Destination file already exists. Aborting')
        return
    
    if args.vrange is None:
        normalize = lambda s: s
    else:
        vmin, vmax = args.vrange
        normalize = lambda s: np.clip((s.astype(float) - vmin)/(vmax - vmin), 0, 1)
    
    if args.dtype is None:
        cast = lambda s: s
    else:
        m = {'uint8': 255, 'uint16': 65535}
        cast = lambda s: (m[args.dtype] * s).astype(args.dtype)

    print('Opening source volume.')

    slicer = slicers.slicer(args.source)
    writer =  slicers.tifffile.TiffWriter(args.destination)

    # downsapling by args.factor
    Z = range((len(slicer)%args.factor)//2, len(slicer), args.factor) 
    Y = range((slicer.imshape[0]%args.factor)//2, slicer.imshape[0], args.factor) 
    X = range((slicer.imshape[1]%args.factor)//2, slicer.imshape[1], args.factor) 
    subindexing = np.ix_(Y, X)

    print(f'Writing volume of size {len(Z)}, {len(Y)}, {len(X)}... ', end='')
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
  

   
    
    
    
    