"""
Run from command line as 
tiffify source_filename destination_filename downscale_factor=8
"""


import numpy as np
import slicers
import argparse
              
def main():

    parser = argparse.ArgumentParser(description='Save volume as downscaled tif.')
    parser.add_argument('source')
    parser.add_argument('destination')
    parser.add_argument('-f', '--factor', type=int, default=8) 
    # TODO add argument specifying dtype conversion

    args = parser.parse_args()
    if args.destination is None:
        args.destination = 'tiffified_volume.tif'
    
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
        writer.write(slice[subindexing])           
    writer.close()    
    print('Done!')
    
if __name__ == '__main__':
    
    main()
  

   
    
    
    
    