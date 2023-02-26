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
    parser.add_argument('--vrange')
    parser.add_argument('--dtype')
    
    args = parser.parse_args()

    if args.destination is None:
        args.destination = 'tiffified_volume.tif'
    
    assert(not os.path.isfile(args.destination), 
        'Destination file already exists.')
    
    if args.valrange is None:
        normalize = lambda s: s
    else:
        vrange = np.array(args.valrange)
        normalize = lambda s: np.clip((s - vrange[0])/
            (vrange[1] - vrange[0]), vrange[0], vrange[1])
    
    if args.dtype is None:
        cast = lambda s: s
    else:
        cast = lambda s: s.astype(args.dtype)

    print('Opening source volume.')

    slicer = slicers.slicer(args.source)
    writer =  slicers.tifffile.TiffWriter(args.destination)

    # downsapling by args.factor
    Z = range((len(slicer)%args.factor)//2, len(slicer), args.factor) 
    Y = range((slicer.imshape[0]%args.factor)//2, slicer.imshape[0], args.factor) 
    X = range((slicer.imshape[1]%args.factor)//2, slicer.imshape[1], args.factor) 
    subindexing = np.ix_(Y, X)

    print(f'Writing a volume of size {len(Z)}, {len(Y)}, {len(X)}... ', end='')
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
  

   
    
    
    
    