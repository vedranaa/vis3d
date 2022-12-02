#%%
import slicers
import importlib
importlib.reload(slicers)
import matplotlib.pyplot as plt
import time
#%%
# TESTING IMPLEMENTATION DETAIL IN VGI SLICER

file = '/Volumes/3dimage/projects/2022_QIM_55_BugNIST/raw_data_3DIM/bugnist_tube [2022-04-12 12.53.01]/bugnist_tube_recon/bugnist_tube.vgi'

for SLICER in [slicers.VgiSlicer]: # slicers.VgiSlicerSecond, 
    time.sleep(10)
    
    t = time.time()
    slicer = SLICER(file)
    print(slicer.dtype)
    print(slicer.imshape)
    it = time.time() - t
    print(f'initializing : {it}')

    t = time.time()
    S = [800, 299, 760, 20, 900]
    fig, ax = plt.subplots(1, len(S))
    for z, a in zip(S, ax):
        im = slicer[z]
        a.imshow(im)
    rt = time.time() - t
    print(f'retreaving : {rt}')
    plt.show()

#%%
# TESTING PERFORMANCE OF SLICERS FOR STACKED TIFF

file = '/Users/VAND/Documents/PROJECTS/FastLocalThickness/local-thickness_git/data/cotton_test_volume.tif'
file = '/Users/VAND/Documents/PROJECTS/FastLocalThickness/testing_data_3D/bonesub.tif'

for SLICER in [slicers.TiffFileSlicer, slicers.TiffFileSlicerPIL]: 
    time.sleep(10)
    
    t = time.time()
    slicer = SLICER(file)
    print(slicer.dtype)
    print(slicer.imshape)
    it = time.time() - t
    print(f'initializing : {it}')


    t = time.time()
    S = [80, 199, 76, 20, 90]
    fig, ax = plt.subplots(1, len(S))
    for z, a in zip(S, ax):
        im = slicer[z]
        a.imshow(im)
    rt = time.time() - t
    print(im.dtype)
    print(f'retreaving : {rt}')
    plt.show()




# %%
# TESTING PERFORMANCE OF SLICERS FOR FOLDER OF TIFFS
folder = '/Volumes/3dimage/projects/2021_QIM_14_dental_implants/raw_data_extern/Bone_implants_project/s16007_silk/matlab_aligned_downscaled'
for SLICER in [slicers.TiffFolderSlicerPIL, slicers.TiffFolderSlicer]: 

    time.sleep(10)
    
    t = time.time()
    slicer = SLICER(folder)
    print(slicer.dtype)
    print(slicer.imshape)
    it = time.time() - t
    print(f'initializing : {it}')


    t = time.time()
    S = [80, 199, 76, 20, 90]
    fig, ax = plt.subplots(1, len(S))
    for z, a in zip(S, ax):
        im = slicer[z]
        a.imshow(im)
    rt = time.time() - t
    print(f'retreaving : {rt}')
    plt.show()


# %%

# %%

# %%
