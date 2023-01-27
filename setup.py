from os.path import dirname, realpath, exists
from setuptools import setup, find_packages
import sys


description = 'Annotate .rtdc files for ML training'
name = 'dctag'
year = "2021"

sys.path.insert(0, realpath(dirname(__file__))+"/"+name)
from _version import version  # noqa: E402


setup(
    name=name,
    url='https://gitlab.gwdg.de/blood_data_analysis/dctag',
    version=version,
    packages=find_packages(),
    package_dir={name: name},
    include_package_data=True,
    license="None",
    description=description,
    long_description=open('README.rst').read() if exists('README.rst') else '',
    install_requires=["dclab>=0.42.3",
                      "h5py>=3.0.0",
                      "numpy>=1.21",
                      "pyqt5",
                      "pyqtgraph==0.13.1",
                      ],
    python_requires='>=3.8, <4',
    entry_points={"gui_scripts": ['dctag = dctag.__main__:main']},
    keywords=["RT-DC", "deformability", "cytometry", "machine-learning"],
    classifiers=['Operating System :: OS Independent',
                 'Programming Language :: Python :: 3',
                 'Intended Audience :: Science/Research',
                 ],
    platforms=['ALL']
)

