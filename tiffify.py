"""
`tiffify.py`: A script to save a volume as downscaled TIFF image.

This script is designed to be run from the command line with various arguments 
to control its behavior.

The main function of the script starts by parsing the command line arguments 
using `argparse`.
"""

import numpy as np
import slicers
import argparse
import os
              
def main():
    """
    Main function to execute the script.

    Positional arguments:
    - source: The source volume filename (path). This is a required argument.
    - destination: The destination filename (path). This is an optional argument 
    that defaults to `tiffified_volume.tif` if not provided.

    Options taking values:
    - factor: An integer that specifies the downscaling factor. This is optional 
      and defaults to 8 if not provided.
    - vrange: This argument consumes two values. If provided, values will be 
      scaled such that `vrange` maps to [0, 1], truncating the values outside 
      the range.
    - dtype: Specifies the destination dtype. If set to `uint8` or `uint16`, 
      values will be multiplied and casted. Note: this should only be used if 
      values are scaled to [0, 1], e.g. by using `vrange`.

    Flags:
    - overwrite: If set, allows overwriting. Use with care.
    - blend: If set, uses a filter similar to Gaussian before sampling. Note 
      that this will make the script run much slower.
    """
    # Parsing command line arguments
    parser = argparse.ArgumentParser(description='Save volume as downscaled tif.')
    parser.add_argument('source')
    parser.add_argument('destination', nargs='?')
    parser.add_argument('--factor', type=int, default=8) 
    parser.add_argument('--vrange', nargs=2)
    parser.add_argument('--dtype')
    parser.add_argument('--overwrite', action='store_true', default=False)
    parser.add_argument('--blend', action='store_true', default=False)
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

    def prepare_resampling(length):
        # Preparing to downsample by args.factor for each dimension
        first = ((length - 1) % args.factor) // 2
        S = range(first, length, args.factor)
        return S

    Z = prepare_resampling(len(slicer))
    Y = prepare_resampling(slicer.imshape[0])
    X = prepare_resampling(slicer.imshape[1])

    # Trying to read the first slice, to avoid opening file for writing if reading goes wrong.
    slice = slicer[0]    
    print(f'Writing volume of size {len(Z)}, {len(Y)}, {len(X)}... ', 
        end='', flush=True)    
    writer =  slicers.tifffile.TiffWriter(args.destination)

    def write(subslice):
        subslice = normalize(subslice)
        subslice = cast(subslice)
        writer.write(subslice)

    if not args.blend:
        subindexing = np.ix_(Y, X)    
        for z in Z:
            slice = slicer[z]
            write(slice[subindexing])   
    else:
        # Blending is achieved using a gaussian kernel of size given by factor. 
        # Even factor uses 1-element overlap, odd factor covers without overlap.

        intype = slice.dtype  # blending is done in float, but we want to cast back
        
        hf = args.factor//2  # half filter length
        overlap = args.factor%2 == 0 # flag for correctly handling the overlap
        sigma = 2 # gaussian sigma for blending, 2 seems to be good value
        filter = np.exp(-1 * np.linspace(-sigma, sigma, 2 * hf + 1) ** 2)  # odd 
        filter = filter/sum(filter)
        
        maxdim = max(max(slicer.imshape), len(slicer))  # longest dimension
        # tiled filter which is long enough, overlapping elements have same value
        toolongfilter = np.tile(filter[:args.factor], maxdim//args.factor + 2) 

        def prepare_weights(S, length):
            # preparing filtering weights 
            weights = toolongfilter[(hf - S[0]) : (hf - S[0]) + length].copy()
            # correcting weights at the boundaries to mimic 'replicate' mode
            weights[0] = 1 - weights[(max(1, S[0] - hf)) : (S[0] + hf + 1)].sum()
            weights[-1] = 1 - weights[(S[-1] - hf) : min(S[-1] + hf, len(weights)-1)].sum()
            return weights.copy()
        
        z_weights = prepare_weights(Z, len(slicer))
        y_weights = prepare_weights(Y, slicer.imshape[0]).reshape(-1, 1)
        x_weights = prepare_weights(X, slicer.imshape[1])

        def resample_and_write(in_array, temp_array, out_array, writer):
            ''' 2D blend, resample, and write to file'''
            in_array = in_array * x_weights
            for i, x in enumerate(X):
                temp_array[:, i] = in_array[:, max(x - hf, 0) : x + hf + 1].sum(axis=1)

            temp_array = y_weights * temp_array
            for i, y in enumerate(Y):
                out_array[i, :] = temp_array[max(y - hf, 0) : y + hf + 1, :].sum(axis=0)            
            write(out_array.astype(intype))  

        # Preallocating arrays for 2D blending
        temp_array = np.zeros((slicer.imshape[0], len(X)), dtype=float)
        out_array = np.zeros((len(Y), len(X)), dtype=float)   

        # Special treatment for the first slice which may have a smaller block
        this_slice = z_weights[0] * slice.astype(float)
        for i in range(1, Z[0] + hf + 1):
            slice = slicer[i]
            this_slice += z_weights[i] * slice.astype(float)
        resample_and_write(this_slice, temp_array, out_array, writer)

        # Slices in the middle
        for z in Z[1:-1]:
            if not overlap:
                slice = slicer[z - hf]
            this_slice = z_weights[z - hf] * slice.astype(float) 
            for i in range(- hf + 1, hf + 1):
                slice = slicer[z + i]
                this_slice += z_weights[z + i] * slice.astype(float)
            resample_and_write(this_slice, temp_array, out_array, writer)
        
        # Special treatment for the last slice which may have a smaller block
        if not overlap:
            slice = slicer[Z[-1] - hf]
        this_slice = z_weights[Z[-1] - hf] * slice.astype(float)
        for i in range(Z[-1] - hf + 1, len(slicer)):
            slice = slicer[i]
            this_slice += z_weights[i] * slice.astype(float)
        resample_and_write(this_slice, temp_array, out_array, writer)


    writer.close()    
    print('Done!')    
if __name__ == '__main__':
    
    main()
  

   
    
    
    
    