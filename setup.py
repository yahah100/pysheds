#!/usr/bin/env python

from setuptools import setup
import os

# Read version from __init__.py
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'pysheds', '__init__.py')
    with open(version_file, 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"').strip("'")
    raise RuntimeError('Unable to find version string.')

setup(
    name="pysheds",
    version=get_version(),  
    description="🌎 Simple and fast watershed delineation in python.",
    long_description="🌎 Simple and fast watershed delineation in python.",
    long_description_content_type="text/x-rst",
    author="Matt Bartos",
    author_email="mdbartos@umich.edu",
    url="http://open-storm.org",
    packages=["pysheds"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Hydrology",
    ],
    include_package_data=True,
    install_requires=[
        "affine",
        "geojson",
        "looseversion",
        "numba",
        "numpy",
        "pandas",
        "pyproj",
        "rasterio>=1",
        "scikit-image",
        "scipy",
    ],
    extras_require=dict(
        dev=["pytest", "pytest-cov"],
        recipes=["geopandas", "ipython", "matplotlib", "seaborn"]
    ),
)
