'''
Following info from: https://stackoverflow.com/a/50468400
Install with
pip install -e </path/to/folder/containing/setup.py>
-e stands for editable,  so it will then create a link from the site-packages
directory to the directory in which the code lives, meaning the latest version
will be used without need to reinstall.

'''
from setuptools import setup

setup(
    name='vis3d',
    version='0.0.2',
    py_modules = 'vis3d',
    entry_points={
        'console_scripts': [
            'vis3d=vis3d:main',
            'tiffify=tiffify:main'
        ]
    },
    install_requires = ['PyQt5', 'tifffile', 'Pillow', 
                        'imagecodecs', 'compoundfiles']
)
