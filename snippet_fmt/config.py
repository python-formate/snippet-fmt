#!/usr/bin/env python3
#
#  config.py
"""
Read and parse ``snippet-fmt`` configuration.
"""
#
#  Copyright © 2021 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#  OR OTHER DEALINGS IN THE SOFTWARE.
#

# stdlib
from typing import Any, Dict, List

# 3rd party
import dom_toml
from domdf_python_tools.typing import PathLike
from typing_extensions import TypedDict

__all__ = ["SnippetFmtConfigDict", "load_toml"]


class SnippetFmtConfigDict(TypedDict):
	"""
	:class:`typing.TypedDict` representing the configuration mapping parsed from ``formate.toml`` or similar.
	"""

	languages: Dict[str, Dict[str, Any]]
	"""
	The languages to reformat. The keys correspond to the value after ``.. code-block::``, including matching case.


	The values are ``key: value`` mappings giving language-specific options.
	The exact options vary, but each has a ``reformat`` option which defaults to :py:obj:`False`.
	If set to :py:obj:`True` the code snippets in that language will be reformatted,
	otherwise they will only be syntax checked.

	For example, the following code block has a value of ``'TOML'``:

	.. code-block:: rst

		.. code-block:: TOML

			key = "value"

	Different capitalisation (e.g. ``JSON`` vs ``json``) can be used to apply different settings to
	different groups of code blocks. For example, ``JSON`` code blocks could have and indent of 2,
	but ``json`` blocks have no indentation.
	"""

	directives: List[str]
	"""
	The directive types to reformat, such as ``'code-block'`` for ``.. code-block::``.

	The values are case sensitive.
	"""


def load_toml(filename: PathLike) -> SnippetFmtConfigDict:
	"""
	Load the ``snippet-fmt`` configuration mapping from the given TOML file.

	:param filename:
	"""

	config = dom_toml.load(filename)

	if "snippet-fmt" in config:
		config = config["snippet-fmt"]
	elif "snippet_fmt" in config:
		config = config["snippet_fmt"]
	elif "snippet-fmt" in config.get("tool", {}):
		config = config["tool"]["snippet-fmt"]
	elif "snippet_fmt" in config.get("tool", {}):
		config = config["tool"]["snippet_fmt"]

	snippet_fmt_config: SnippetFmtConfigDict = {
			"languages": {},
			"directives": config.get("directives", ["code", "code-block", "sourcecode"]),
			}

	if "languages" in config:
		for language, lang_config in config.get("languages", {}).items():
			snippet_fmt_config["languages"][language] = lang_config
	else:
		snippet_fmt_config["languages"] = {
				"python": {},
				"python3": {},
				"toml": {},
				"TOML": {},
				"ini": {},
				"INI": {},
				"json": {},
				"JSON": {},
				}

	return snippet_fmt_config
