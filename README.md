## SETUP

- Follow setps from 
https://lab.compute.dtu.dk/patmjen/hcp_tutorials/-/blob/main/HPC_Python_Guide.md  
In particular, log on a real node using X11 forwarding `linuxsh -X`, navigate to project folder and place `init.sh` there. I made changes to `init.sh` such that it only installs what I need. 

```
#!/bin/bash
# Based on simple init script for Python on DTU HPC
# by Patrick M. Jensen, patmjen@dtu.dk, 2022

# Configuration
PYTHON_VERSION=3.9.14  # Python version
VENV_DIR=.  # Where to store your virtualenv
VENV_NAME=vis3denv  # Name of your virtualenv

# Load modules
module load python3/$PYTHON_VERSION
module load $(module avail -o modulepath -t -C "python-${PYTHON_VERSION}" | grep "numpy/")

# Create virtualenv if needed and activate it
if [ ! -d "${VENV_DIR}/${VENV_NAME}" ]
then
    echo INFO: Did not find virtualenv. Creating...
    virtualenv "${VENV_DIR}/${VENV_NAME}"
fi
source "${VENV_DIR}/${VENV_NAME}/bin/activate"
```

- Call `. init.sh`

- Install modules. I guess this could be avoided if specifying requirements in the setup file.
```
pip install PyQt5
pip install tifffile
pip install Pillow
pip install imagecodecs
pip install compoundfiles
```
- Get files from `https://github.com/vedranaa/vis3d`, at least `vis3d.py`, `slicers.py`, and `setup.py`. Either clone the repository, or use  `wget` where -N overwrittes if newer. For this I made  `get_code.sh` which is executed using `. get_code.sh`.
```
#!/bin/bash

wget -N https://raw.githubusercontent.com/vedranaa/vis3d/main/vis3d.py 
wget -N https://raw.githubusercontent.com/vedranaa/vis3d/main/slicers.py 
wget -N https://raw.githubusercontent.com/vedranaa/vis3d/main/setup.py
````

- Run editable install when in the folder containing `setup.py`
```
pip install -e .
```

- Optionally, you can also get the links to a few volumes from 3DIM from the `links_gbar` folder. For this, I made a subfoder under my project to which I copied files using `get_links.sh` similar to before. 

```
#!/bin/bash

wget -N https://raw.githubusercontent.com/vedranaa/vis3d/main/links_gbar/bone_projections.txt 
wget -N https://raw.githubusercontent.com/vedranaa/vis3d/main/links_gbar/bone_reconstruction.txt 
wget -N https://raw.githubusercontent.com/vedranaa/vis3d/main/links_gbar/bugnist.txt 
wget -N https://raw.githubusercontent.com/vedranaa/vis3d/main/links_gbar/dental_implant_silk.txt 
wget -N https://raw.githubusercontent.com/vedranaa/vis3d/main/links_gbar/dental_implant_stitched.txt 
wget -N https://raw.githubusercontent.com/vedranaa/vis3d/main/links_gbar/kidney_elettra.txt 
wget -N https://raw.githubusercontent.com/vedranaa/vis3d/main/links_gbar/kidney_rat3.txt 
wget -N https://raw.githubusercontent.com/vedranaa/vis3d/main/links_gbar/nerves_part_url.txt 
````


## USE
- Log on the node, navigate to the project folder and run `init.sh` which will set the environment etc.

```
linuxsh -X
. init.sh
```

- Use `vis3d` from the terminal with one of the following
```
vis3d
vis3d path
vis3d file 
```

