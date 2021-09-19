========
Usage
========


Command Line
---------------

.. program:: snippet-fmt

.. click:: snippet_fmt.__main__:main
	:prog: snippet-fmt
	:nested: none



As a ``pre-commit`` hook
----------------------------

``snippet-fmt`` can also be used as a `pre-commit <https://pre-commit.com/>`_ hook.
To do so, add the following to your
`.pre-commit-config.yaml <https://pre-commit.com/#2-add-a-pre-commit-configuration>`_ file:

.. pre-commit::
	:rev: 0.1.2
	:hooks: snippet-fmt
	:args: --verbose

The ``args`` option can be used to provide the command line arguments shown above.
By default ``snippet-fmt`` is run with ``--verbose --diff``
