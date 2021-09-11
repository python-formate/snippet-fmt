==============
Configuration
==============

``snippet-fmt`` is configured using the ``pyproject.toml`` file in the root of your project
(alongside ``setup.py``, ``tox.ini`` etc.).
The file uses the TOML_ syntax,
with the configuration in the ``[tool.snippet-fmt]`` table.

The table can contain two keys: :tconf:`languages` and :tconf:`directives`

Alternatively, the :option:`-c / --config-file <snippet-fmt -c>` option can be used to point to a different TOML file.
The layout is the same except the table ``[snippet-fmt]`` rather than ``[tool.snippet.fmt]``.


.. tconf:: languages

	This is a table of tables giving languages to check and reformat.

	These correspond to the value after ``.. code-block::``, preserving case.

	For example, the following codeblock has a value of ``'TOML'``:

	.. code-block:: rst

		.. code-block:: TOML

			key = "value"

	Each language has a corresponding check / reformat function,
	which is determined from the lowercased form of the language name.
	This allows certain code blocks in a language to be excluded from formatting
	by using a different case, such as using ``TOML`` for most code blocks
	and ``toml`` for ones which shouldn't be reformatted.


	The currently supported languages (matched case insensitively) are:

	* JSON
	* INI
	* TOML
	* Python / Python3

	Each sub table contains options specific to that language (and capitalisation).
	The exact options vary, but each has a ``reformat`` option which defaults to :py:obj:`False`.
	If set to :py:obj:`True` the code snippets in that language will be reformatted,
	otherwise they will only be syntax checked.

	By default all languages are enabled for checks only.


.. tconf:: directives

	The directive types to reformat, such as ``'code-block'`` for ``.. code-block::``.

	The values are case sensitive.

	Defaults to ``['code', 'code-block', 'sourcecode']``.


Supported Languages
-------------------------

The following languages are supported by ``snippet-fmt``:


Python / Python3
^^^^^^^^^^^^^^^^^^^^

Reformatting Python_ files with formate_.


:bold-title:`Options`

.. tconf:: python.reformat
	:type: :toml:`Boolean`
	:default: False

	If set to ``true`` the code blocks matching this language and capitalisation will be reformatted, otherwise they will only be syntax checked.


.. tconf:: python.config-file
	:type: :toml:`String`
	:default: formate.toml

	The TOML_ file containing the configuration for formate_.

	.. TODO:: link for formate's docs


JSON
^^^^^^^^

Syntax checking and reformatting of JSON files, using Python's :mod:`json` module.


:bold-title:`Options`

.. tconf:: json.reformat
	:type: :toml:`Boolean`
	:default: False

	If set to ``true`` the code blocks matching this language and capitalisation will be reformatted, otherwise they will only be syntax checked.


.. tconf:: json.ensure_ascii
	:type: :toml:`Boolean`
	:default: false

	If ``true``, the output is guaranteed to have all incoming non-ASCII characters escaped. If ``false`` (the default), these characters will be output as-is.

.. tconf:: json.allow_nan
	:type: :toml:`Boolean`
	:default: true

	If ``true`` (the default), then ``NaN``, ``Infinity``, and ``-Infinity`` will be encoded as such. This behavior is not JSON specification compliant, but is consistent with most JavaScript based encoders and decoders. Otherwise an error will be raised when attepting to reformat files containing such floats.

	.. note:: JSON snippets containing ``NaN`` etc. when this option is ``false`` and ``reformat`` is also ``false`` will pass, as this check only takes place durinh reformatting.


.. tconf:: json.sort_keys
	:type: :toml:`Boolean`
	:default: false

	If ``true`` then the keys will be sorted alphabetically.


.. tconf:: json.indent
	:type: :toml:`Integer` or :toml:`string`

	If ``indent`` is a non-negative integer or string, then JSON array elements and object members will be pretty-printed with that indent level. An indent level of 0, negative, or "" will only insert newlines. If not specified a compact representation will be used. Using a positive integer indent indents that many spaces per level. If indent is a string (such as "\t"), that string is used to indent each level.


.. tconf:: json.separators
	:type: :toml:`Array` of :toml:`string`

	A 2-element array of ``[item_separator, key_separator]``.
	The default is ``(', ', ': ')`` if ``indent`` is unspecified and ``(',', ': ')`` otherwise.
	To get the most compact JSON representation, you should specify ``(',', ':')`` to eliminate whitespace.


TOML
^^^^^^^^

Syntax checking and reformatting of TOML_ files using the `toml <https://pypi.org/project/toml>`__ library.

.. note:: This only supports TOML_ version `0.5.0 <https://toml.io/en/v0.5.0>`_.


:bold-title:`Options`

.. tconf:: toml.reformat
	:type: :toml:`Boolean`
	:default: False

	If set to ``true`` the code blocks matching this language and capitalisation will be reformatted, otherwise they will only be syntax checked.


INI
^^^^^^^^

Syntax checking and reformatting of INI files, using Python's :mod:`configparser` module.


:bold-title:`Options`

.. tconf:: ini.reformat
	:type: :toml:`Boolean`
	:default: False

	If set to ``true`` the code blocks matching this language and capitalisation will be reformatted, otherwise they will only be syntax checked.


Example
-----------

.. code-block:: toml

	[tool.snippet-fmt]
	directives = ['code', 'code-block', 'sourcecode']

	[tool.snippet-fmt.languages.python]
	reformat = true
	config-file = "pyproject.toml"

	[tool.snippet-fmt.languages.TOML]
	reformat = true

	[tool.snippet-fmt.languages.toml]
	[tool.snippet-fmt.languages.ini]

This will:

* look at ``.. code::``, ``.. code-block::`` and ``.. sourcecode::`` directives
  for ``python``, ``TOML``, ``toml``, and ``ini``.
* Code blocks marked ``python`` and ``TOML`` will be reformatted.
* Code blocks marked ``toml`` and ``ini`` will only be checked for valid syntax.
* formate_ is configured to take its configuration from ``pyproject.toml``.


.. _TOML: https://toml.io/en/
.. _formate: https://formate.readthedocs.io
.. _Python: https://python.org
