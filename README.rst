DCTag
=====
**DCTag** is a graphical toolkit for manually annotating RT-DC events
for machine-learning purposes.


For Developers
--------------
Activate your virtual environment and install DCTag in editable mode,
i.e. in the root of the repository, run::

    pip install -e .


Distribution to Users
---------------------
1. Create a new tag::

    git tag -a "0.1.0"
    git push --tags

2. Create a distribution package ``dctag_XYZ.tar.gz`` with::

    python setup.py sdist

3. Give the ``.tar.gz`` file to users and tell them to pip-install it with::

    pip install dctag_XYZ.tar.gz

We may want to have some kind of CI that builds an installer at some
point. For that, we can reuse the scripts in:
https://github.com/ZELLMECHANIK-DRESDEN/DCKit/tree/master/build-recipes


Running DCTag
-------------
If installed properly, a simple ``dctag`` should work. Otherwise (make sure
the virtual environment is active)::

    python -m dctag

