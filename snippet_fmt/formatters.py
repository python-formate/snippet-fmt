#!/usr/bin/env python3
#
#  formatters.py
"""
Formatters and syntax checkers.
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
import ast
import json
import os
from configparser import ConfigParser
from io import StringIO
from typing import Any, Callable, Optional, TypeVar

# 3rd party
import dom_toml
import dom_toml.decoder
import formate
from domdf_python_tools.paths import PathPlus

__all__ = [
		"Formatter",
		"format_toml",
		"format_ini",
		"format_json",
		"format_python",
		"noformat",
		]

# 3rd party
from typing_extensions import Protocol


class Formatter(Protocol):
	"""
	:class:`typing.Protocol` for formatter functions.
	"""

	def __call__(self, code: str, **config: Any) -> str: ...  # noqa: D102


def noformat(code: str, **config) -> str:
	r"""
	A no-op formatter.

	:param code: The code to check and reformat.
	:param \*\*config: The language-specific configuration.

	:returns: The original code unchanged.
	"""

	return code


class StringReformatter(formate.Reformatter):

	def __init__(self, code: str, config: formate.FormateConfigDict):
		self.file_to_format = PathPlus(os.devnull)  # in case someone tries to write to the file
		self.filename = "snippet.py"
		self.config = config
		self._unformatted_source = code
		self._reformatted_source: Optional[str] = None

	def to_file(self) -> None:  # pragma: no cover
		"""
		Write the reformatted source to the original file.
		"""

		raise NotImplementedError(f"Unsupported by {self.__class__!r}")


def format_python(code: str, **config) -> str:
	r"""
	Check the syntax of, and reformat, the given Python code.

	:param code: The code to check and reformat.
	:param \*\*config: The language-specific configuration.

	:returns: The reformatted code.
	"""

	if config.get("reformat", False):
		formate_config = formate.config.load_toml(config.get("config-file", "formate.toml"))
		r = StringReformatter(code, formate_config)
		r.run()
		return r.to_string()
	else:
		ast.parse(code)
		return code


def format_toml(code: str, **config) -> str:
	r"""
	Check the syntax of, and reformat, the given TOML configuration.

	:param code: The code to check.
	:param \*\*config: The language-specific configuration.

	:returns: The original code unchanged.
	"""

	toml_content = dom_toml.loads(code)

	if config.get("reformat", False):
		return dom_toml.dumps(toml_content)
	else:
		return code


def format_ini(code: str, **config) -> str:
	r"""
	Check the syntax of, and reformat, the given INI configuration.

	:param code: The code to check.
	:param \*\*config: The language-specific configuration.

	:returns: The original code unchanged.
	"""

	parser = ConfigParser()
	parser.read_string(code)

	if config.get("reformat", False):
		output = StringIO()
		parser.write(output)
		return output.getvalue()
	else:
		return code


def format_json(code: str, **config) -> str:
	r"""
	Check the syntax of, and reformat, the given JSON source.

	:param code: The code to check.
	:param \*\*config: The language-specific configuration.

	:returns: The original code unchanged.
	"""

	json_content = json.loads(code)
	config = config.copy()

	if config.pop("reformat", False):
		config.setdefault("ensure_ascii", False)
		return json.dumps(json_content, **config)
	else:
		return code
