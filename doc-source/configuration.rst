==============
Configuration
==============

``snippet-fmt`` is configured using the ``pyproject.toml`` file in the root of your project
(alongside ``setup.py``, ``tox.ini`` etc.).
The file uses the `TOML <https://github.com/toml-lang/toml>`_ syntax,
with the configuration in the ``[tool.snippet-fmt]`` table.

The table can contain two keys: :ref:`hooks <snippet_fmt_toml_languages>`
and :ref:`config <snippet_fmt_toml_directives>`

Alternatively, the :option:`-c / --config-file <snippet-fmt -c>` option can be used to point to a different TOML file.
The layout is the same except the table ``[snippet-fmt]`` rather than ``[tool.snippet.fmt]``.


.. _snippet_fmt_toml_languages:

``languages``
--------------

This is a list of languages to check and reformat.

These correspond to the value after ``.. code-block::``, ignoring case.

For example, the following codeblock has a value of ``'toml'``:

.. code-block:: rst

	.. code-block:: TOML

		key = "value"


The currently supported languages are:

* JSON -- syntax check only.
* INI -- syntax check only.
* TOML -- syntax check only, v0.5.0.
* Python / Python3 -- syntax check and reformatting using formate_.

Defaults to ``['python', 'toml', 'ini', 'json']``.

.. _formate: https://formate.readthedocs.io


.. _snippet_fmt_toml_directives:

``directives``
----------------

The directive types to reformat, such as ``'code-block'`` for ``.. code-block::``.

The values are case sensitive.

Defaults to ``['code', 'code-block', 'sourcecode']``.


Example
-----------

.. code-block:: toml

	[tool.snippet-fmt]
	languages = ['python', 'toml', 'ini']
	directives = ['code', 'code-block', 'sourcecode']
