## SETUP

- Follow setps from 
https://lab.compute.dtu.dk/patmjen/hcp_tutorials/-/blob/main/HPC_Python_Guide.md  
Note: I made changes to `init.sh` file, such that it only installs what I need. My `init.sh` is
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


- Install modules. I guess this could be avoided if specifying requirenments in setup.
```
pip install PyQt5
pip install tifffile
pip install Pillow
pip install imagecodecs
```
- From `https://raw.githubusercontent.com/vedranaa/goodies/main/vis3d` get files `vis3d.py` and `setup.py`. For example using `wget` where -N overwrittes if newer, and -O overwrittes into file. (Update, I made `get_code.sh`. TODO: add.)
```
wget path/file.py
wget -N path/file.py
wget path/file.py -O file.py
````

- Editable install


## USE
- Navigate to the folder containing `init.sh` which will set the environment etc.

```
linuxsh -X
source init.sh
```

- Use `vis3d` from the terminal with one of the following
```
vis3d
vis3d path
vis3d file 
```

