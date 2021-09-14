#!/usr/bin/env python3
#
#  __init__.py
"""
Format and validate code snippets in reStructuredText files.
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
#  Parts based on https://github.com/asottile/blacken-docs
#  Copyright (c) 2018 Anthony Sottile
#  MIT Licensed
#

# stdlib
import contextlib
import re
import textwrap
from typing import Dict, Iterator, List, Match, NamedTuple, Optional

# 3rd party
import click
import entrypoints  # type: ignore
from consolekit.terminal_colours import ColourTrilean, resolve_color_default
from consolekit.utils import coloured_diff
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.stringlist import StringList
from domdf_python_tools.typing import PathLike
from formate.utils import syntaxerror_for_file

# this package
from snippet_fmt.config import SnippetFmtConfigDict
from snippet_fmt.formatters import Formatter, format_ini, format_json, format_python, format_toml, noformat

__author__: str = "Dominic Davis-Foster"
__copyright__: str = "2021 Dominic Davis-Foster"
__license__: str = "MIT License"
__version__: str = "0.1.1"
__email__: str = "dominic@davis-foster.co.uk"

__all__ = ["CodeBlockError", "RSTReformatter", "reformat_file"]

INDENT_RE = re.compile("^[ \t]+(?=[^ ])", re.MULTILINE)
TRAILING_NL_RE = re.compile(r'\n+\Z', re.MULTILINE)


class CodeBlockError(NamedTuple):
	"""
	Represents an exception raised when parsing and reformatting a code block.
	"""

	#: The character offset where the exception was raised.
	offset: int

	#: The exception itself.
	exc: Exception


class RSTReformatter:
	"""
	Reformat code snippets in a reStructuredText file.

	:param filename: The filename to reformat.
	:param config: The ``snippet_fmt`` configuration, parsed from a TOML file (or similar).
	"""

	#: The filename being reformatted.
	filename: str

	#: The filename being reformatted, as a POSIX-style path.
	file_to_format: PathPlus

	#: The ``formate`` configuration, parsed from a TOML file (or similar).
	config: SnippetFmtConfigDict

	errors: List[CodeBlockError]

	def __init__(self, filename: PathLike, config: SnippetFmtConfigDict):
		self.file_to_format = PathPlus(filename)
		self.filename = self.file_to_format.as_posix()
		self.config = config
		self._unformatted_source = self.file_to_format.read_text()
		self._reformatted_source: Optional[str] = None
		self.errors = []

		self._formatters: Dict[str, Formatter] = {
				"bash": noformat,
				"python": format_python,
				"python3": format_python,
				"toml": format_toml,
				"ini": format_ini,
				"json": format_json,
				}
		self.load_extra_formatters()

	def run(self) -> bool:
		"""
		Run the reformatter.

		:return: Whether the file was changed.
		"""

		content = StringList(self._unformatted_source)
		content.blankline(ensure_single=True)

		directives = '|'.join(self.config["directives"])

		pattern = re.compile(
				rf'(?P<before>'
				rf'^(?P<indent>[ \t]*)\.\.[ \t]*('
				rf'({directives})::\s*(?P<lang>[A-Za-z0-9-_]+)?)\n'
				rf'((?P=indent)[ \t]+:.*\n)*'
				rf'\n*'
				rf')'
				rf'(?P<code>(^((?P=indent)[ \t]+.*)?\n)+)',
				re.MULTILINE,
				)

		self._reformatted_source = pattern.sub(self.process_match, str(content))

		for error in self.errors:
			lineno = self._unformatted_source[:error.offset].count('\n') + 1
			click.echo(f"{self.filename}:{lineno}: {error.exc.__class__.__name__}: {error.exc}", err=True)

		return self._reformatted_source != self._unformatted_source

	def process_match(self, match: Match[str]) -> str:
		"""
		Process a :meth:`re.Match <re.Match.expand>` for a single code block.

		:param match:
		"""

		lang = match.group("lang")

		if lang in self.config["languages"]:
			lang_config = self.config["languages"][lang]
			# TODO: show warning if not found and in "strict" mode
			formatter = self._formatters.get(lang.lower(), noformat)
		else:
			lang_config = {}
			formatter = noformat

		min_indent = min(INDENT_RE.findall(match["code"]))
		trailing_ws_match = TRAILING_NL_RE.search(match["code"])
		assert trailing_ws_match
		trailing_ws = trailing_ws_match.group()
		code = textwrap.dedent(match["code"])

		with self._collect_error(match):
			with syntaxerror_for_file(self.filename):
				code = formatter(code, **lang_config)

		code = textwrap.indent(code, min_indent)
		return f'{match["before"]}{code.rstrip()}{trailing_ws}'

	def get_diff(self) -> str:
		"""
		Returns the diff between the original and reformatted file content.
		"""

		# Based on yapf
		# Apache 2.0 License

		after = self.to_string().split('\n')
		before = self._unformatted_source.split('\n')
		return coloured_diff(
				before,
				after,
				self.filename,
				self.filename,
				"(original)",
				"(reformatted)",
				lineterm='',
				)

	def to_string(self) -> str:
		"""
		Return the reformatted file as a string.
		"""

		if self._reformatted_source is None:
			raise ValueError("'Reformatter.run()' must be called first!")

		return self._reformatted_source

	def to_file(self) -> None:
		"""
		Write the reformatted source to the original file.
		"""

		self.file_to_format.write_text(self.to_string())

	@contextlib.contextmanager
	def _collect_error(self, match: Match[str]) -> Iterator[None]:
		try:
			yield
		except Exception as e:
			self.errors.append(CodeBlockError(match.start(), e))

	def load_extra_formatters(self) -> None:
		"""
		Load custom formatters defined via entry points.
		"""

		group = "snippet_fmt.formatters"

		for distro_config, _ in entrypoints.iter_files_distros():
			if group in distro_config:
				for name, epstr in distro_config[group].items():
					with contextlib.suppress(entrypoints.BadEntryPoint, ImportError):
						# TODO: show warning for bad entry point if verbose, or "strict"?
						ep = entrypoints.EntryPoint.from_string(epstr, name)
						self._formatters[name] = ep.load()


def reformat_file(
		filename: PathLike,
		config: SnippetFmtConfigDict,
		colour: ColourTrilean = None,
		):
	"""
	Reformat the given reStructuredText file, and show the diff if changes were made.

	:param filename: The filename to reformat.
	:param config: The ``snippet-fmt`` configuration, parsed from a TOML file (or similar).
	:param colour: Whether to force coloured output on (:py:obj:`True`) or off (:py:obj:`False`).
	"""

	r = RSTReformatter(filename, config)

	ret = r.run()

	if ret:
		click.echo(r.get_diff(), color=resolve_color_default(colour))
		r.to_file()

	return ret
