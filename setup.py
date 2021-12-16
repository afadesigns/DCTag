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
    install_requires=["dclab>=0.39.2",  # pinned for triaging
                      "h5py>=2.8.0",
                      "numpy",
                      "pyqt5",
                      "pyqtgraph",
                      ],
    python_requires='>=3.7, <4',
    entry_points={"gui_scripts": ['dctag = dctag.__main__:main']},
    keywords=["RT-DC", "deformability", "cytometry", "machine-learning"],
    classifiers=['Operating System :: OS Independent',
                 'Programming Language :: Python :: 3',
                 'Intended Audience :: Science/Research',
                 ],
    platforms=['ALL']
)

