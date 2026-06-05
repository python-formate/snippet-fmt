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
import os
import re
import textwrap
from typing import Dict, Iterator, List, Match, NamedTuple, Optional

# 3rd party
import click
import entrypoints  # type: ignore[import-untyped]
import tokenize_rt  # type: ignore[import-untyped]
from consolekit.terminal_colours import ColourTrilean, resolve_color_default
from consolekit.utils import coloured_diff
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.stringlist import StringList
from domdf_python_tools.typing import PathLike
from formate.utils import syntaxerror_for_file

# this package
import snippet_fmt.docstring
from snippet_fmt.config import SnippetFmtConfigDict
from snippet_fmt.formatters import Formatter, format_ini, format_json, format_python, format_toml, noformat

__author__: str = "Dominic Davis-Foster"
__copyright__: str = "2021 Dominic Davis-Foster"
__license__: str = "MIT License"
__version__: str = "0.1.5"
__email__: str = "dominic@davis-foster.co.uk"

__all__ = (
		"CodeBlockError",
		"DocstringReformatter",
		"PyReformatter",
		"RSTReformatter",
		"Reformatter",
		"reformat_docstrings",
		"reformat_file",
		)

TRAILING_NL_RE = re.compile(r'\n+\Z', re.MULTILINE)


class CodeBlockError(NamedTuple):
	"""
	Represents an exception raised when parsing and reformatting a code block.
	"""

	#: The character offset where the exception was raised.
	offset: int

	#: The exception itself.
	exc: Exception


# TODO: reformatter for docstrings


class Reformatter:
	"""
	Base class for reformatters.

	:param source: The file content.
	:param filename: The file being formatted, for display in error messages.
	:param config: The ``snippet_fmt`` configuration, parsed from a TOML file (or similar).

	.. autosummary-widths:: 35/100
	.. latex:clearpage::
	"""

	#: The filename being reformatted, as a POSIX-style path.
	filename: str

	#: The ``formate`` configuration, parsed from a TOML file (or similar).
	config: SnippetFmtConfigDict

	errors: List[CodeBlockError]

	def __init__(self, source: str, filename: str, config: SnippetFmtConfigDict):
		self.filename = filename
		self.config = config
		self._unformatted_source = source
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

	def compile_regex(self) -> re.Pattern:
		"""
		Compile the regular expression for finding directives.
		"""
		directives = '|'.join(self.config["directives"])

		return re.compile(
				rf'(?P<before>'
				rf'^(?P<indent>[ \t]*)\.\.[ \t]*('
				rf'({directives})::\s*(?P<lang>[A-Za-z0-9-_]+)?)\n'
				rf'((?P=indent)[ \t]+:.*\n)*'  # Limitation: should be `(?P=body_indent)` rather than `[ \t]+`
				rf'\n*'
				rf')'
				rf'(?P<code>^((?P=indent)(?P<body_indent>[ \t]+).*)?\n(^((?P=indent)(?P=body_indent).*)?\n)*)',
				re.MULTILINE,
				)

	def run(self) -> bool:
		"""
		Run the reformatter.

		:return: Whether the file was changed.
		"""

		content = StringList(self._unformatted_source)
		content.blankline(ensure_single=True)

		pattern = self.compile_regex()

		self._reformatted_source = pattern.sub(self.process_match, str(content))

		for error in self.errors:
			self.report_error(error)

		return self._reformatted_source != self._unformatted_source

	def report_error(self, error: CodeBlockError) -> None:
		"""
		Print the error message.

		:param error:
		"""

		lineno = self._unformatted_source[:error.offset].count('\n') + 1
		click.echo(f"{self.filename}:{lineno}: {error.exc.__class__.__name__}: {error.exc}", err=True)

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

		trailing_ws_match = TRAILING_NL_RE.search(match["code"])
		assert trailing_ws_match
		trailing_ws = trailing_ws_match.group()
		code = textwrap.dedent(match["code"])

		with self._collect_error(match):
			with syntaxerror_for_file(self.filename):
				code = formatter(code, **lang_config)

		code = textwrap.indent(code, match["indent"] + match["body_indent"])
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
				os.fspath(self.filename),
				os.fspath(self.filename),
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
					with contextlib.suppress(entrypoints.BadEntryPoint, ImportError):  # pylint: disable=W8205
						# TODO: show warning for bad entry point if verbose, or "strict"?
						ep = entrypoints.EntryPoint.from_string(epstr, name)
						self._formatters[name] = ep.load()


class RSTReformatter(Reformatter):
	"""
	Reformat code snippets in a reStructuredText file.

	:param filename: The filename to reformat.
	:param config: The ``snippet_fmt`` configuration, parsed from a TOML file (or similar).

	.. autosummary-widths:: 35/100
	.. latex:clearpage::
	"""

	#: The filename being reformatted.
	file_to_format: PathPlus

	def __init__(self, filename: PathLike, config: SnippetFmtConfigDict):
		self.file_to_format = PathPlus(filename)
		super().__init__(self.file_to_format.read_text(), self.file_to_format.as_posix(), config)

	def to_file(self) -> None:
		"""
		Write the reformatted source to the original file.
		"""

		self.file_to_format.write_text(self.to_string())


class DocstringReformatter(Reformatter):
	"""
	Reformat code snippets in a docstring from a Python file.

	:param token: The docstring token to format.
	:param filename: The filename being reformated.
	:param config: The ``snippet_fmt`` configuration, parsed from a TOML file (or similar).

	.. autosummary-widths:: 35/100
	.. latex:clearpage::
	"""

	#: The docstring token being reformatted.
	token: tokenize_rt.Token

	#: Letters before the string e.g. ``f``, ``u``, ``r``, ``fr``
	prefix_char: str

	#: Quotes used for the docstring, e.g. ``'`` or ``"""``
	quote_char: str

	#: The docstring's indentation.
	indent: str

	def __init__(self, token: tokenize_rt.Token, filename: PathLike, config: SnippetFmtConfigDict):
		self.token = token

		prefix_char, quote_char, indent, docstring = snippet_fmt.docstring.get_parts(token.src)
		self.prefix_char = prefix_char
		self.quote_char = quote_char
		self.indent = indent

		super().__init__(docstring, PathPlus(filename).as_posix(), config)

	def report_error(self, error: CodeBlockError) -> None:
		"""
		Print the error message.

		:param error:
		"""

		lineno = self._unformatted_source[:error.offset].count('\n') + 1
		click.echo(
				f"{self.filename}:{lineno+self.token.line-1}: {error.exc.__class__.__name__}: {error.exc}",
				err=True,
				)

	def get_diff(self) -> str:
		"""
		Returns the diff between the original and reformatted file content.
		"""

		after = self.to_string().split('\n')
		return snippet_fmt.docstring.diff(
				self.token,
				after,
				os.fspath(self.filename),
				)

	def to_string(self) -> str:
		"""
		Return the reformatted file as a string.
		"""

		if self._reformatted_source is None:
			raise ValueError("'Reformatter.run()' must be called first!")

		parts = [
				self.prefix_char,
				self.quote_char,
				textwrap.indent(self._reformatted_source, self.indent).rstrip(),
				]

		if len(self.quote_char) == 3:
			parts.append('\n')
			parts.append(self.indent)

		parts.append(self.quote_char)

		return ''.join(parts)

	def to_token(self) -> tokenize_rt.Token:
		"""
		Return the docstring as a token for ``tokenize_rt``.
		"""

		return tokenize_rt.Token(
				name="STRING",
				src=self.to_string(),
				line=self.token.line,
				utf8_byte_offset=self.token.utf8_byte_offset,
				)

	def run(self) -> bool:
		"""
		Run the reformatter.

		:return: Whether the file was changed.
		"""

		content = StringList(self._unformatted_source)
		if len(self.quote_char) == 3:
			content.blankline(ensure_single=True)

		pattern = self.compile_regex()

		self._reformatted_source = pattern.sub(self.process_match, str(content))

		for error in self.errors:
			self.report_error(error)

		return self._reformatted_source != self._unformatted_source


class PyReformatter(RSTReformatter):
	"""
	Reformat code snippets in docstrings in a Python file.

	:param filename: The filename to reformat.
	:param config: The ``snippet_fmt`` configuration, parsed from a TOML file (or similar).

	.. autosummary-widths:: 35/100
	.. latex:clearpage::
	"""

	def run(self) -> bool:
		"""
		Run the reformatter.

		:return: Whether the file was changed.
		"""

		original_tokens = snippet_fmt.docstring.get_tokens(self._unformatted_source)
		tokens: List[tokenize_rt.Token] = []

		file_ret = 0

		for token in original_tokens:

			if token.name == "DOCSTRING":
				r = DocstringReformatter(token, self.file_to_format, self.config)

				with syntaxerror_for_file(self.filename):
					if r.run():
						token = r.to_token()
						file_ret = True

			tokens.append(token)

		self._reformatted_source = tokenize_rt.tokens_to_src(tokens)
		if file_ret:
			assert tokenize_rt.tokens_to_src(tokens) != self._unformatted_source
			return True
		else:
			assert tokenize_rt.tokens_to_src(tokens) == self._unformatted_source
			return False


def reformat_file(
		filename: PathLike,
		config: SnippetFmtConfigDict,
		colour: ColourTrilean = None,
		) -> int:
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


def reformat_docstrings(
		filename: PathLike,
		config: SnippetFmtConfigDict,
		colour: ColourTrilean = None,
		) -> int:
	"""
	Reformat docstrings in the given Python file, and show the diff if changes were made.

	:param filename: The filename to reformat.
	:param config: The ``snippet-fmt`` configuration, parsed from a TOML file (or similar).
	:param colour: Whether to force coloured output on (:py:obj:`True`) or off (:py:obj:`False`).
	"""

	file = PathPlus(filename)
	source = file.read_text()

	original_tokens = snippet_fmt.docstring.get_tokens(source)
	tokens: List[tokenize_rt.Token] = []

	file_ret = 0

	for token in original_tokens:

		if token.name == "DOCSTRING":
			r = DocstringReformatter(token, file, config)

			with syntaxerror_for_file(file.name):
				if r.run():
					token = r.to_token()
					click.echo(r.get_diff(), color=resolve_color_default(colour))
					file_ret = True

		tokens.append(token)

	if file_ret:
		file.write_text(tokenize_rt.tokens_to_src(tokens))
		assert tokenize_rt.tokens_to_src(tokens) != source
		return True
	else:
		assert tokenize_rt.tokens_to_src(tokens) == source
		return False
