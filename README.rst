============
snippet-fmt
============

.. start short_desc

**Format and validate code snippets in reStructuredText files.**

.. end short_desc


.. start shields

.. list-table::
	:stub-columns: 1
	:widths: 10 90

	* - Docs
	  - |docs| |docs_check|
	* - Tests
	  - |actions_linux| |actions_windows| |actions_macos| |coveralls|
	* - PyPI
	  - |pypi-version| |supported-versions| |supported-implementations| |wheel|
	* - Activity
	  - |commits-latest| |commits-since| |maintained| |pypi-downloads|
	* - QA
	  - |codefactor| |actions_flake8| |actions_mypy|
	* - Other
	  - |license| |language| |requires|

.. |docs| image:: https://img.shields.io/readthedocs/snippet-fmt/latest?logo=read-the-docs
	:target: https://snippet-fmt.readthedocs.io/en/latest
	:alt: Documentation Build Status

.. |docs_check| image:: https://github.com/python-formate/snippet-fmt/workflows/Docs%20Check/badge.svg
	:target: https://github.com/python-formate/snippet-fmt/actions?query=workflow%3A%22Docs+Check%22
	:alt: Docs Check Status

.. |actions_linux| image:: https://github.com/python-formate/snippet-fmt/workflows/Linux/badge.svg
	:target: https://github.com/python-formate/snippet-fmt/actions?query=workflow%3A%22Linux%22
	:alt: Linux Test Status

.. |actions_windows| image:: https://github.com/python-formate/snippet-fmt/workflows/Windows/badge.svg
	:target: https://github.com/python-formate/snippet-fmt/actions?query=workflow%3A%22Windows%22
	:alt: Windows Test Status

.. |actions_macos| image:: https://github.com/python-formate/snippet-fmt/workflows/macOS/badge.svg
	:target: https://github.com/python-formate/snippet-fmt/actions?query=workflow%3A%22macOS%22
	:alt: macOS Test Status

.. |actions_flake8| image:: https://github.com/python-formate/snippet-fmt/workflows/Flake8/badge.svg
	:target: https://github.com/python-formate/snippet-fmt/actions?query=workflow%3A%22Flake8%22
	:alt: Flake8 Status

.. |actions_mypy| image:: https://github.com/python-formate/snippet-fmt/workflows/mypy/badge.svg
	:target: https://github.com/python-formate/snippet-fmt/actions?query=workflow%3A%22mypy%22
	:alt: mypy status

.. |requires| image:: https://dependency-dash.herokuapp.com/github/python-formate/snippet-fmt/badge.svg
	:target: https://dependency-dash.herokuapp.com/github/python-formate/snippet-fmt/
	:alt: Requirements Status

.. |coveralls| image:: https://img.shields.io/coveralls/github/python-formate/snippet-fmt/master?logo=coveralls
	:target: https://coveralls.io/github/python-formate/snippet-fmt?branch=master
	:alt: Coverage

.. |codefactor| image:: https://img.shields.io/codefactor/grade/github/python-formate/snippet-fmt?logo=codefactor
	:target: https://www.codefactor.io/repository/github/python-formate/snippet-fmt
	:alt: CodeFactor Grade

.. |pypi-version| image:: https://img.shields.io/pypi/v/snippet-fmt
	:target: https://pypi.org/project/snippet-fmt/
	:alt: PyPI - Package Version

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/snippet-fmt?logo=python&logoColor=white
	:target: https://pypi.org/project/snippet-fmt/
	:alt: PyPI - Supported Python Versions

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/snippet-fmt
	:target: https://pypi.org/project/snippet-fmt/
	:alt: PyPI - Supported Implementations

.. |wheel| image:: https://img.shields.io/pypi/wheel/snippet-fmt
	:target: https://pypi.org/project/snippet-fmt/
	:alt: PyPI - Wheel

.. |license| image:: https://img.shields.io/github/license/python-formate/snippet-fmt
	:target: https://github.com/python-formate/snippet-fmt/blob/master/LICENSE
	:alt: License

.. |language| image:: https://img.shields.io/github/languages/top/python-formate/snippet-fmt
	:alt: GitHub top language

.. |commits-since| image:: https://img.shields.io/github/commits-since/python-formate/snippet-fmt/v0.1.1
	:target: https://github.com/python-formate/snippet-fmt/pulse
	:alt: GitHub commits since tagged version

.. |commits-latest| image:: https://img.shields.io/github/last-commit/python-formate/snippet-fmt
	:target: https://github.com/python-formate/snippet-fmt/commit/master
	:alt: GitHub last commit

.. |maintained| image:: https://img.shields.io/maintenance/yes/2021
	:alt: Maintenance

.. |pypi-downloads| image:: https://img.shields.io/pypi/dm/snippet-fmt
	:target: https://pypi.org/project/snippet-fmt/
	:alt: PyPI - Downloads

.. end shields

Installation
--------------

.. start installation

``snippet-fmt`` can be installed from PyPI.

To install with ``pip``:

.. code-block:: bash

	$ python -m pip install snippet-fmt

.. end installation


.. code-block:: python

	def foo(bar):
		print("hello")


.. code-block:: TOML

	hello = "world
