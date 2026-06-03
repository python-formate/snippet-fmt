#!/usr/bin/env python3
#
#  docstring.py
"""
Docstring processing for formatting.
"""
#
#  Copyright © 2026 Dominic Davis-Foster <dominic@davis-foster.co.uk>
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
import difflib
import string
from collections import deque
from typing import Container, Iterator, List, NamedTuple, Optional, Sequence, Tuple

# 3rd party
import tokenize_rt  # type: ignore[import-untyped]
from consolekit import terminal_colours
from domdf_python_tools.stringlist import StringList

__all__ = ["dedent", "diff", "get_parts", "get_tokens"]


class DocstringToken(NamedTuple):
	name: str
	src: str
	line: Optional[int] = None
	utf8_byte_offset: Optional[int] = None
	function_name: Optional[str] = None

	@property
	def offset(self) -> tokenize_rt.Offset:
		return tokenize_rt.Offset(self.line, self.utf8_byte_offset)

	def matches(self, *, name: str, src: str) -> bool:
		return self.name == name and self.src == src


def dedent(docstring: str) -> Tuple[str, str]:
	"""
	Remove indentation from the docstring.

	:param docstring:

	:returns: The dedented docstring and the indentation used.
	"""

	try:
		lines = docstring.split('\n')
	except (AttributeError, TypeError):
		msg = f'expected str object, not {type(docstring).__qualname__!r}'
		raise TypeError(msg) from None

	# Get length of leading whitespace, inspired by ``os.path.commonprefix()``.
	non_blank_lines = [l for l in lines if l and not l.isspace()]
	l1 = min(non_blank_lines, default='')
	l2 = max(non_blank_lines, default='')
	margin = 0
	for margin, c in enumerate(l1):
		if c != l2[margin] or c not in " \t":
			break

	return '\n'.join([l[margin:] if not l.isspace() else '' for l in lines]), l1[:margin]


def get_parts(docstring: str) -> Tuple[str, str, str, str]:
	"""
	Extract the docstring from the string literal and return prefix characters (e.g. ``u``), the quotes, indent, and the docstring.

	:param docstring:
	"""

	docstring_string: str = docstring
	prefix_char = ''

	while docstring_string[0] in string.ascii_letters:
		prefix_char = docstring_string[0]
		docstring_string = docstring_string[1:]

	if docstring_string[:2] not in {"''", '""'}:
		# Not triple quoted
		if docstring_string[0] == "'":
			# Single quoted
			quote_char = "'"
		else:
			# double quoted
			quote_char = '"'
			assert docstring_string[0] == quote_char
		assert docstring_string[-1] == quote_char
	else:
		if docstring_string[:3] == "'''":
			# Triple-Single quoted
			quote_char = "'''"
		else:
			# Triple-Double quoted
			quote_char = '"""'
			assert docstring_string[:3] == quote_char
		assert docstring_string[-3:] == quote_char

	if len(quote_char) == 3:
		docstring = docstring_string[3:-3]
	else:
		docstring = docstring_string[1:-1]

	docstring, indent = dedent(docstring)

	return prefix_char, quote_char, indent, docstring


def get_tokens(source: str) -> List[tokenize_rt.Token]:
	"""
	Tokenize the given Python source, including special ``"DOCSTRING"`` tokens for function and class docstrings.

	:param source:
	"""

	# TODO: module docstrings

	original_tokens = deque(tokenize_rt.src_to_tokens(source))

	tokens: List[tokenize_rt.Token] = []

	def _readahead_in(next_token: tokenize_rt.Token, names: Container[str]) -> tokenize_rt.Token:
		while next_token.name in names:
			tokens.append(next_token)
			next_token = original_tokens.popleft()

		return next_token

	def _readahead_not_in(next_token: tokenize_rt.Token, names: Container[str]) -> tokenize_rt.Token:
		while next_token.name not in names:
			tokens.append(next_token)
			next_token = original_tokens.popleft()

		return next_token

	while original_tokens:
		token = original_tokens.popleft()

		tokens.append(token)

		if token.name == "NAME" and token.src in {"def", "class"}:
			next_token = original_tokens.popleft()

			next_token = _readahead_in(next_token, {"UNIMPORTANT_WS"})

			assert next_token.name == "NAME", next_token
			function_name = next_token.src

			# Readahead to body

			next_token = _readahead_not_in(next_token, {"INDENT"})

			while next_token.name not in {"STRING", "DEDENT"}:
				tokens.append(next_token)
				next_token = original_tokens.popleft()

				if next_token.name in {"OP", "NAME"}:
					# Not going to be the docstring, lookahead to next line
					next_token = _readahead_not_in(next_token, {"NEWLINE"})

			if next_token.name == "STRING":

				next_token = DocstringToken(
						name="DOCSTRING",
						src=next_token.src,
						line=next_token.line,
						utf8_byte_offset=next_token.utf8_byte_offset,
						function_name=function_name,
						)

			tokens.append(next_token)

	return tokens

def _unified_diff(a: Sequence[str], b: Sequence[str], filename: str, offset: int) -> Iterator[str]:

	difflib._check_types(a, b, filename)  # type: ignore[attr-defined]

	started = False
	for group in difflib.SequenceMatcher(None, a, b).get_grouped_opcodes(3):
		if not started:
			started = True
			yield f"--- {filename}\t(original)"
			yield f"+++ {filename}\t(reformatted)"

		first, last = group[0], group[-1]
		file1_range = difflib._format_range_unified(  # type: ignore[attr-defined]
			first[1] + offset,
			last[2] + offset,
		)
		file2_range = difflib._format_range_unified(  # type: ignore[attr-defined]
			first[3] + offset,
			last[4] + offset,
		)
		yield f'@@ -{file1_range} +{file2_range} @@'

		for tag, i1, i2, j1, j2 in group:
			if tag == "equal":
				for line in a[i1:i2]:
					yield ' ' + line
				continue

			if tag in {"replace", "delete"}:
				for line in a[i1:i2]:
					yield '-' + line

			if tag in {"replace", "insert"}:
				for line in b[j1:j2]:
					yield '+' + line


def diff(
		token: tokenize_rt.Token,
		reformatted: Sequence[str],
		filename: str,
		) -> str:
	"""
	Construct a diff for the reformatted docstring.

	:param token: The docstring token.
	:param reformatted: Reformatted docstring.
	:param filename:
	"""

	buf = StringList()
	diff = _unified_diff(token.src.split('\n'), reformatted, filename, token.line - 1)

	for line in diff:
		if line.startswith('+'):
			buf.append(terminal_colours.Fore.GREEN(line))
		elif line.startswith('-'):
			buf.append(terminal_colours.Fore.RED(line))
		else:
			buf.append(line)

	buf.blankline(ensure_single=True)

	return str(buf)
