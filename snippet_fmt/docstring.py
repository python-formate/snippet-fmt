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
import string
from collections import deque
from typing import List, NamedTuple, Optional, Tuple

# 3rd party
import tokenize_rt
from domdf_python_tools.typing import PathLike

__all__ = ["DocstringToken", "dedent", "get_parts", "get_tokens"]


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


def dedent(text):

	try:
		lines = text.split('\n')
	except (AttributeError, TypeError):
		msg = f'expected str object, not {type(text).__qualname__!r}'
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

	original_tokens = deque(tokenize_rt.src_to_tokens(source))

	tokens: List[tokenize_rt.Token] = []

	while original_tokens:
		token = original_tokens.popleft()

		tokens.append(token)

		if token.name == "NAME" and token.src in {"def", "class"}:
			next_token = original_tokens.popleft()

			while next_token.name in {"UNIMPORTANT_WS"}:
				tokens.append(next_token)
				next_token = original_tokens.popleft()

			assert next_token.name == "NAME", next_token
			function_name = next_token.src

			# Readahead to body

			while next_token.name not in {"INDENT"}:
				tokens.append(next_token)
				next_token = original_tokens.popleft()

			while next_token.name not in {"STRING", "DEDENT"}:
				tokens.append(next_token)
				next_token = original_tokens.popleft()

				if next_token.name in {"OP", "NAME"}:
					# Not going to be the docstring, lookahead to next line
					while next_token.name not in {"NEWLINE"}:
						tokens.append(next_token)
						next_token = original_tokens.popleft()

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
