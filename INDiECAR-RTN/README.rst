=============================================
IDRIC_industrial_cluster_optimization_toolkit
=============================================


.. image:: https://img.shields.io/pypi/v/IDRIC_toolkit.svg
        :target: https://pypi.python.org/pypi/IDRIC_toolkit

.. image:: https://img.shields.io/travis/kuenglu/IDRIC_toolkit.svg
        :target: https://travis-ci.com/kuenglu/IDRIC_toolkit

.. image:: https://readthedocs.org/projects/IDRIC-toolkit/badge/?version=latest
        :target: https://IDRIC-toolkit.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status




open-source toolkit to identify cost-optimal cluster decarbonisation pathways


* Free software: MIT license
* Documentation: https://IDRIC-toolkit.readthedocs.io.


Getting started
---------------

Setting up the files, python environment and installing the *IDRIC_toolkit* as a **package**. To do this, use the following steps.

1. Set up a local copy of the this github repository on your computer. Either use github desktop client or a git bash window and the clone command.

2. Open an Anaconda command prompt (Start --> Anaconda3 --> ....)

3. In the prompt, navigate to the local path of the the *IDRIC_toolkit* of step 1 by typing

        ``cd "<your path here>/IDRIC_toolkit"``
   
   Note: you should be on the top layer of the folder, i.e. you should see a README file, the LICENSE, and a setup.py file.

4. Install the python environment *py39-IDRIC*, by typing the following into the command prompt:

        ``conda env create -f environment.yml``

5. Install the *IDRIC_toolkit* as a package by typing the following into the command prompt:

        ``python -m pip install -e .``

At this point, you should be set up to start working on the IDRIC toolkit and run simulations. You can navigate to the folder *notebooks* and open the GUI notebook. 


Features
--------

* TODO

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
