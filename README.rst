DCTag
=====
**DCTag** is a graphical toolkit for manually annotating RT-DC events
for machine-learning purposes.


Installing DCTag
----------------
This section is only for users. If you are a developer and want to contribute to DCTag, you have
to clone the repository and install in editable mode (see below).

Depending on how you set up GitLab, one of those commands will work::

    pip install dctag@git+ssh://git@gitlab.gwdg.de/blood_data_analysis/dctag.git@X.Y.Z
    pip install dctag@git+https://gitlab.gwdg.de/blood_data_analysis/dctag.git@X.Y.Z

where ``X.Y.Z`` is the version of DCTag you are interested in. E.g. to install DCTag 0.4.1 via SSH
(works if you have two-factor authentication enabled), run::

    pip install dctag@git+ssh://git@gitlab.gwdg.de/blood_data_analysis/dctag.git@0.4.1

Windows users please note that this might only work with git bash.

To **upgrade** to a new version, use the ``--upgrade`` argument::

    pip install --upgrade dctag@git+ssh://git@gitlab.gwdg.de/blood_data_analysis/dctag.git@0.4.1

For more information and some more examples, please see `issue #9 <https://gitlab.gwdg.de/blood_data_analysis/dctag/-/issues/9>`_.

Running DCTag
-------------
If installed properly, a simple ``dctag`` should work. Otherwise (make sure
the virtual environment is active)::

    python -m dctag


For Developers
--------------
Here is how we manage contributions:

1. Fork this repository, create your virtual environment and install in editable mode via
   ``pip install -e .`` in the repository root.
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
      # For this to work you have to go to your fork, "Settings". "Repository"
      # "Protected branches" and activate "Allowed to force push" for ``main`` in the list.
      git push origin main --force
      git push --tags

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
1. Create a new tag (you can also do this via the web interface)::

       git tag -a "0.1.0"
       git push --tags

   At this point, users will be able to install with the description
   provided a the top of this readme.

2. Create a distribution package ``dctag_XYZ.whl`` with::

       python setup.py bdist_wheel

   There is also CI/CD which creates ``.whl`` files automatically. Go to
   https://gitlab.gwdg.de/blood_data_analysis/dctag/-/pipelines, and in the list click on
   the three-vertical-dots-button and select download ``run:archive``. The ``.whl`` is
   in the zip archive you downloaded. However, these artifacts are deleted after some time.


3. Give the ``.whl`` file to users and tell them to pip-install it with::

       pip install dctag_XYZ.whl
