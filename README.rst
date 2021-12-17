DCTag
=====
**DCTag** is a graphical toolkit for manually annotating RT-DC events
for machine-learning purposes.

Running DCTag
-------------
If installed properly, a simple ``dctag`` should work. Otherwise (make sure
the virtual environment is active)::

    python -m dctag


For Developers
--------------
Here is how we manage contributions:

1. Fork this repository.
2. Create an issue or open the issue that you want to address.
3. Assign yourself to that issue so nobody else is working on it.
4. Verify that nobody else is currently working an an issue that might
   interfer with your issue (e.g. editing same part of a file)
5. Clone into your fork and make sure your fork is up-to-date with the current `main` branch::

      git remote add upstream git@gitlab.gwdg.de:blood_data_analysis/dctag
      git fetch upstream
      git checkout main
      # THIS WILL PURGE ALL OF YOUR CURRENT CHANGES!
      # DO NOT DO THIS IF YOU HAVE ALREADY STARTED WORKING ON SOMETHING!
      git reset --hard upstream/main
      git push origin main --force

6. Activate your virtual environment and install dctag in editable mode::

      pip install -e .

7. Create a new branch that starts with your issue number and short description::

      git branch 15-keyboard-control
      git checkout 15-keyboard-control

8. Make your changes and commit::

      git commit -a -m "feat: introduced keyboard control"
      # for the first push
      git push --set-upstream origin 15-keyboard-control
      # for consecutive changes
      git commit -a -m "fix: layout reversed"
      git push

9. Go to you fork and you will see the text::

      You pushed to 15-keyboard-control at USERNAME / DCTag 1 minute ago

   Below that is a big blue merge button that will create a merge request
   to the target ``blood_data_analysis/dctag:main``.
   Assign Paul to the merge request.

Testing
-------
To run all tests, install the requirements and run pytest::

    pip install -r tests/requirements.txt
    pytest tests


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


