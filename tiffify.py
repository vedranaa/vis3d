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
    parser.add_argument('factor', type=int, default=8) 
    # parser.add_argument('-f', '--factor', , type=int, default=8) - IF MORE ARGS ARE ADDED  
    args = parser.parse_args()
    
    slicer = slicers.slicer(args.source)
    writer =  slicers.tifffile.TiffWriter(args.destination)

    Z = range((len(slicer)%args.factor)//2, len(slicer), args.factor) 
    Y = range((slicer.imshape[0]%args.factor)//2, slicer.imshape[0], args.factor) 
    X = range((slicer.imshape[1]%args.factor)//2, slicer.imshape[1], args.factor) 

    print(f'Writing volume of size {len(Z)}, {len(Y)}, {len(X)}')
    for z in Z:
        slice = slicer[z]
        writer.write(slice[Y, X], contiguous=True)           
    writer.close()    

    
if __name__ == '__main__':
    
    main()
  

   
    
    
    
    