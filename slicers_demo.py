#%%
import slicers
import matplotlib.pyplot as plt

#%% 
# VGI slicer

file = ('/Volumes/3dimage/projects/2022_QIM_55_BugNIST/raw_data_3DIM/'
        'bugnist_tube [2022-04-12 12.53.01]/bugnist_tube_recon/bugnist_tube.vgi')
slicer = slicers.VgiSlicer(file)  # opens a slicer object

Z = len(slicer)
print(Z)  # number of slices in the volume
print(slicer.dtype)  # datatype 
print(slicer.imshape)  # shape of each slice 

# Extracting slices from the volume.
S = [(8*Z)//9, Z//8, Z//2, (4*Z)//5, Z//3]  # some slices smaller than Z 
fig, ax = plt.subplots(1, len(S))
for z, a in zip(S, ax):
    im = slicer[z]
    a.imshow(im)
    a.set_title(z)
plt.show()


#%% 
# TMX slicer

file = ('/Volumes/3dimage/projects/2022_DANFIX_UTMOST/raw_data_3DIM/'
        'starting sandwich/starting sandwich_2022-05-27_100917/'
        'LOFV-40kV-air-2s-18micro/starting sandwich_LOFV-40kV-air-2s-18micro_recon.txm')
slicer = slicers.TxmSlicer(file)  # opens a slicer object

Z = len(slicer)
print(Z)  # number of slices in the volume
print(slicer.dtype)  # datatype 
print(slicer.imshape)  # shape of each slice 

# Extracting slices from the volume.
S = [(8*Z)//9, Z//8, Z//2, (4*Z)//5, Z//3]  # some slices smaller than Z 
fig, ax = plt.subplots(1, len(S))
for z, a in zip(S, ax):
    im = slicer[z]
    a.imshow(im)
plt.show()

# %% 
# Tiff folder

folder = ('/Volumes/3dimage/projects/2021_QIM_14_dental_implants/raw_data_extern/'
        'Bone_implants_project/s16007_silk/matlab_aligned_downscaled')
slicer = slicers.TiffFolderSlicer(folder)

Z = len(slicer)
print(Z)  # number of slices in the volume
print(slicer.dtype)  # datatype 
print(slicer.imshape)  # shape of each slice 

# Extracting slices from the volume.
S = [(8*Z)//9, Z//8, Z//2, (4*Z)//5, Z//3]  # some slices smaller than Z 
fig, ax = plt.subplots(1, len(S))
for z, a in zip(S, ax):
    im = slicer[z]
    a.imshow(im)
plt.show()


#%%  
# Folder
folder = ('/Volumes/3dimage/projects/2021_QIM_14_dental_implants/'
        'raw_data_extern/16_1080_LR_stitched_4x4bin')
slicer = slicers.FolderSlicer(folder)

Z = len(slicer)
print(Z)  # number of slices in the volume
print(slicer.dtype)  # datatype 
print(slicer.imshape)  # shape of each slice 

# Extracting slices from the volume.
S = [(8*Z)//9, Z//8, Z//2, (4*Z)//5, Z//3]  # some slices smaller than Z 
fig, ax = plt.subplots(1, len(S))
for z, a in zip(S, ax):
    im = slicer[z]
    a.imshow(im)
plt.show()

#%% 
# TiffFile
file = ('/Users/VAND/Documents/PROJECTS/FastLocalThickness/local-thickness_git/'
        'data/cotton_test_volume.tif')
slicer = slicers.TiffFileSlicer(file)

Z = len(slicer)
print(Z)  # number of slices in the volume
print(slicer.dtype)  # datatype 
print(slicer.imshape)  # shape of each slice 

# Extracting slices from the volume.
S = [(8*Z)//9, Z//8, Z//2, (4*Z)//5, Z//3]  # some slices smaller than Z 
fig, ax = plt.subplots(1, len(S))
for z, a in zip(S, ax):
    im = slicer[z]
    a.imshow(im)
plt.show()


#%% 
# File
file = '/Users/VAND/Documents/PROJECTS/FastLocalThickness/testing_data_3D/bonesub.tif'
slicer = slicers.FileSlicer(file)

Z = len(slicer)
print(Z)  # number of slices in the volume
print(slicer.dtype)  # datatype 
print(slicer.imshape)  # shape of each slice 

# Extracting slices from the volume.
S = [(8*Z)//9, Z//8, Z//2, (4*Z)//5, Z//3]  # some slices smaller than Z 
fig, ax = plt.subplots(1, len(S))
for z, a in zip(S, ax):
    im = slicer[z]
    a.imshow(im)
plt.show()

#%% 
# Url
url = 'https://qim.compute.dtu.dk/data-repository/InSegt_data/3D/nerves_part.tiff'
slicer = slicers.FileSlicer.from_url(url)

Z = len(slicer)
print(Z)  # number of slices in the volume
print(slicer.dtype)  # datatype 
print(slicer.imshape)  # shape of each slice 

# Extracting slices from the volume.
S = [(8*Z)//9, Z//8, Z//2, (4*Z)//5, Z//3]  # some slices smaller than Z 
fig, ax = plt.subplots(1, len(S))
for z, a in zip(S, ax):
    im = slicer[z]
    a.imshow(im)
plt.show()


# %%
# Loading all volumes from links

import glob
import slicers
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')

sources = glob.glob('links_local/*.txt')
fig, ax = plt.subplots(3, int(np.ceil(len(sources)/3)))

for a, s in zip(ax.ravel(), sources):

    slicer = slicers.slicer(s)
    filename = slicer.filename
    Z = len(slicer)
    a.imshow(slicer[Z//2])
    a.set_title(f'...{filename[max(0,len(filename)-30):]}\n{Z}x{slicer.imshape}, {slicer.dtype}', 
        size=8)
    
plt.show()



# %%
