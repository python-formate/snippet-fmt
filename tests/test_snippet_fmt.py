# stdlib
import shutil
import textwrap
from pathlib import Path
from typing import Dict, Iterator, List, Union, no_type_check

# 3rd party
import dom_toml
import pytest
from _pytest.capture import CaptureResult
from coincidence import AdvancedDataRegressionFixture, AdvancedFileRegressionFixture
from coincidence.params import param
from coincidence.selectors import max_version, min_version
from consolekit.terminal_colours import strip_ansi
from consolekit.testing import CliRunner, Result
from domdf_python_tools.paths import PathPlus, TemporaryPathPlus, in_directory

# this package
from snippet_fmt import PyReformatter, SnippetFmtConfigDict, reformat_docstrings, reformat_file
from snippet_fmt.__main__ import main
from snippet_fmt.config import load_toml
from tests.test_config import PYPROJECT_LANGUAGES_A

source_dir = PathPlus(__file__).parent

directives = pytest.mark.parametrize(
		"directives",
		[
				pytest.param(["code-block"], id='0'),
				pytest.param(["code"], id='1'),
				pytest.param(["code-cell"], id='2'),
				pytest.param(["sourcecode"], id='3'),
				pytest.param(["code-block", "code"], id='4'),
				pytest.param(["code-block", "code", "code-cell"], id='5'),
				pytest.param(["code-block", "code", "code-cell", "sourcecode"], id='6'),
				pytest.param(["code-block", "code", "parsed-literal"], id='7'),
				],
		)
base_languages = [
		pytest.param({}, id="empty"),
		pytest.param({"python": {"reformat": True}}, id="python"),
		pytest.param({"python3": {"reformat": True}}, id="python3"),
		pytest.param(
				{"python3": {"reformat": True}, "toml": {"reformat": False}},
				id="python3_toml_false",
				),
		pytest.param({"TOML": {"reformat": True}}, id="toml_caps"),
		pytest.param({"toml": {"reformat": True}}, id="toml"),
		pytest.param(
				{"toml": {"reformat": True}, "python": {"reformat": False}},
				id="toml_python_false",
				),
		pytest.param({"INI": {"reformat": True}}, id="ini_caps"),
		pytest.param({"ini": {"reformat": True}}, id="ini"),
		pytest.param(
				{"ini": {"reformat": True}, "python": {"reformat": False}},
				id="ini_python_false",
				),
		]
json_languages = [
		pytest.param({"JSON": {"reformat": True}}, id="json_caps", marks=max_version("3.12")),
		pytest.param(
				{"JSON": {"reformat": True}},
				id="json_caps_new_error_msg",
				marks=min_version("3.13"),
				),
		pytest.param({"json": {"reformat": True}}, id="json", marks=max_version("3.12")),
		pytest.param({"json": {"reformat": True}}, id="json_new_error_msg", marks=min_version("3.13")),
		pytest.param(
				{"JSON": {"reformat": True, "indent": 2}, "json": {"reformat": True}},
				id="json_caps_indent",
				marks=max_version("3.12"),
				),
		pytest.param(
				{"JSON": {"reformat": True, "indent": 2}, "json": {"reformat": True}},
				id="json_caps_indent_new_error_msg",
				marks=min_version("3.13"),
				),
		pytest.param(
				{"json": {"reformat": True, "indent": 2}, "JSON": {"reformat": True}},
				id="json_indent",
				marks=max_version("3.12"),
				),
		pytest.param(
				{"json": {"reformat": True, "indent": 2}, "JSON": {"reformat": True}},
				id="json_indent_new_error_msg",
				marks=min_version("3.13"),
				),
		]
languages = pytest.mark.parametrize(
		"languages",
		base_languages + json_languages,
		)
filenames = pytest.mark.parametrize(
		"filename",
		[
				param("example.rst", idx=0),
				param("py_code.rst", idx=0),
				],
		)


@pytest.fixture()
def tmp_pathplus_clean(tmp_path: Path) -> Iterator[PathPlus]:
	"""
	Pytest fixture which returns a temporary directory in the form of a
	:class:`~domdf_python_tools.paths.PathPlus` object.

	The directory is unique to each test function invocation,
	created as a sub directory of the base temporary directory.

	Use it as follows:

	.. code-block:: python

		pytest_plugins = ("coincidence", )


		def test_something(tmp_pathplus_clean: PathPlus):
			assert True
	"""  # noqa: D400

	p = PathPlus(tmp_path)
	yield p
	shutil.rmtree(p)


@pytest.fixture()
def custom_entry_point(monkeypatch) -> Iterator:
	with TemporaryPathPlus() as tmpdir:
		monkeypatch.syspath_prepend(str(tmpdir))

		dist_info = tmpdir / "snippet_fmt_demo-0.0.0.dist-info"
		dist_info.maybe_make(parents=True)
		(dist_info / "entry_points.txt").write_lines([
				"[snippet_fmt.formatters]",
				"python3 = snippet_fmt_demo:fake_format",
				])

		(tmpdir / "snippet_fmt_demo.py").write_lines([
				"def fake_format(*args, **kwargs):",
				"\treturn 'Hello World'",
				])

		yield


class TestReformatFile:

	@directives
	@languages
	@filenames
	def test_snippet_fmt(
			self,
			filename: str,
			tmp_pathplus_clean: PathPlus,
			directives: List[str],
			languages: Dict,
			advanced_file_regression: AdvancedFileRegressionFixture,
			advanced_data_regression: AdvancedDataRegressionFixture,
			capsys,
			):
		(tmp_pathplus_clean / filename).write_text((source_dir / filename).read_text())
		(tmp_pathplus_clean / "formate.toml").write_text((source_dir / "example_formate.toml").read_text())

		config: SnippetFmtConfigDict = {"languages": languages, "directives": directives}

		with in_directory(tmp_pathplus_clean):
			reformat_file(tmp_pathplus_clean / filename, config)

		advanced_file_regression.check_file(tmp_pathplus_clean / filename)
		check_out(capsys.readouterr(), tmp_pathplus_clean, advanced_data_regression)

	@directives
	@pytest.mark.parametrize("languages", base_languages)
	@filenames
	@pytest.mark.parametrize(
			"quotes",
			[
					param("'''", id="single"),
					param('"""', id="double"),
					],
			)
	@pytest.mark.parametrize(
			"indent",
			[
					param('\t', id="tab"),
					param("    ", id="4s"),
					param("        ", id="8s"),
					],
			)
	def test_docstrings(
			self,
			filename: str,
			tmp_pathplus_clean: PathPlus,
			directives: List[str],
			languages: Dict,
			quotes: str,
			indent: str,
			advanced_file_regression: AdvancedFileRegressionFixture,
			advanced_data_regression: AdvancedDataRegressionFixture,
			capsys,
			):
		docstring = textwrap.indent((source_dir / filename).read_text(), indent)
		template = f"def foo():\n{indent}{quotes}\n" + "{d}" + f"{indent}{quotes}\n{indent}pass\n"
		py_filename = (tmp_pathplus_clean / filename).with_suffix(".py")
		py_filename.write_text(template.format_map({'d': docstring}))
		(tmp_pathplus_clean / "formate.toml").write_text((source_dir / "example_formate.toml").read_text())

		config: SnippetFmtConfigDict = {"languages": languages, "directives": directives}

		with in_directory(tmp_pathplus_clean):
			reformat_docstrings(py_filename, config)

		advanced_file_regression.check_file(py_filename)
		check_out(capsys.readouterr(), tmp_pathplus_clean, advanced_data_regression)

	@pytest.mark.parametrize(
			"directives",
			[
					pytest.param(["code-block"], id='0'),
					],
			)
	@pytest.mark.parametrize(
			"languages",
			[
					pytest.param({}, id="empty"),
					pytest.param({"python": {"reformat": True}}, id="python"),
					pytest.param({"python3": {"reformat": True}}, id="python3"),
					],
			)
	@filenames
	@pytest.mark.parametrize(
			"quotes",
			[
					param('"""', id="double"),
					],
			)
	@pytest.mark.parametrize(
			"indent",
			[
					param("    ", id="4s"),
					],
			)
	def test_docstrings_class(
			self,
			filename: str,
			tmp_pathplus_clean: PathPlus,
			directives: List[str],
			languages: Dict,
			quotes: str,
			indent: str,
			advanced_file_regression: AdvancedFileRegressionFixture,
			advanced_data_regression: AdvancedDataRegressionFixture,
			capsys,
			):
		docstring = textwrap.indent((source_dir / filename).read_text(), indent)
		template = f"class foo():\n{indent}{quotes}\n" + "{d}" + f"{indent}{quotes}\n{indent}pass\n"
		py_filename = (tmp_pathplus_clean / filename).with_suffix(".py")
		py_filename.write_text(template.format_map({'d': docstring}))
		(tmp_pathplus_clean / "formate.toml").write_text((source_dir / "example_formate.toml").read_text())

		config: SnippetFmtConfigDict = {"languages": languages, "directives": directives}

		with in_directory(tmp_pathplus_clean):
			reformat_docstrings(py_filename, config)

		advanced_file_regression.check_file(py_filename)
		check_out(capsys.readouterr(), tmp_pathplus_clean, advanced_data_regression)

	@pytest.mark.parametrize(
			"directives",
			[
					pytest.param(["code-block"], id='0'),
					],
			)
	@pytest.mark.parametrize(
			"languages",
			[
					pytest.param({}, id="empty"),
					pytest.param({"python": {"reformat": True}}, id="python"),
					pytest.param({"python3": {"reformat": True}}, id="python3"),
					],
			)
	@filenames
	@pytest.mark.parametrize(
			"quotes",
			[
					param("'''", id="single"),
					],
			)
	@pytest.mark.parametrize(
			"indent",
			[
					param('\t', id="tab"),
					],
			)
	def test_docstrings_class_method(
			self,
			filename: str,
			tmp_pathplus_clean: PathPlus,
			directives: List[str],
			languages: Dict,
			quotes: str,
			indent: str,
			advanced_file_regression: AdvancedFileRegressionFixture,
			advanced_data_regression: AdvancedDataRegressionFixture,
			capsys,
			):
		docstring = textwrap.indent((source_dir / filename).read_text(), indent * 2)
		template = f"class foo():\n{indent}def bar():\n{indent*2}{quotes}\n" + "{d}" + f"{indent*2}{quotes}\n{indent*2}pass\n"
		py_filename = (tmp_pathplus_clean / filename).with_suffix(".py")
		py_filename.write_text(template.format_map({'d': docstring}))
		(tmp_pathplus_clean / "formate.toml").write_text((source_dir / "example_formate.toml").read_text())

		config: SnippetFmtConfigDict = {"languages": languages, "directives": directives}

		with in_directory(tmp_pathplus_clean):
			reformat_docstrings(py_filename, config)

		advanced_file_regression.check_file(py_filename)
		check_out(capsys.readouterr(), tmp_pathplus_clean, advanced_data_regression)

	@directives
	@pytest.mark.parametrize("languages", base_languages)
	@pytest.mark.parametrize(
			"quotes",
			[
					param("'", id="single"),
					param('"', id="double"),
					],
			)
	@pytest.mark.parametrize(
			"indent",
			[
					param('\t', id="tab"),
					param("    ", id="4s"),
					param("        ", id="8s"),
					],
			)
	def test_docstrings_single_line(
			self,
			tmp_pathplus_clean: PathPlus,
			directives: List[str],
			languages: Dict,
			quotes: str,
			indent: str,
			capsys,
			):
		source = f"def foo():\n{indent}{quotes}This is a single-line docstring{quotes}\n{indent}pass\n"
		py_filename = (tmp_pathplus_clean / "example.py")
		py_filename.write_text(source)
		(tmp_pathplus_clean / "formate.toml").write_text((source_dir / "example_formate.toml").read_text())

		config: SnippetFmtConfigDict = {"languages": languages, "directives": directives}

		with in_directory(tmp_pathplus_clean):
			reformat_docstrings(py_filename, config)

		assert py_filename.read_text() == source
		outerr = capsys.readouterr()
		assert not outerr.out
		assert not outerr.err

	@directives
	@pytest.mark.parametrize("languages", base_languages)
	@filenames
	def test_docstrings_empty_mod(
			self,
			filename: str,
			tmp_pathplus_clean: PathPlus,
			directives: List[str],
			languages: Dict,
			):

		py_filename = (tmp_pathplus_clean / filename).with_suffix(".py")
		py_filename.write_text('')
		(tmp_pathplus_clean / "formate.toml").write_text((source_dir / "example_formate.toml").read_text())

		config: SnippetFmtConfigDict = {"languages": languages, "directives": directives}

		with in_directory(tmp_pathplus_clean):
			reformat_docstrings(py_filename, config)

		assert not py_filename.read_text()

	@directives
	@pytest.mark.parametrize("languages", base_languages)
	@filenames
	def test_docstrings_empty_fn(
			self,
			filename: str,
			tmp_pathplus_clean: PathPlus,
			directives: List[str],
			languages: Dict,
			):

		py_filename = (tmp_pathplus_clean / filename).with_suffix(".py")
		py_filename.write_text("def foo():\n\tpass\n")
		(tmp_pathplus_clean / "formate.toml").write_text((source_dir / "example_formate.toml").read_text())

		config: SnippetFmtConfigDict = {"languages": languages, "directives": directives}

		with in_directory(tmp_pathplus_clean):
			reformat_docstrings(py_filename, config)

		assert py_filename.read_text() == "def foo():\n\tpass\n"

	@pytest.mark.usefixtures("custom_entry_point")
	@filenames
	def test_snippet_fmt_custom_entry_point(
			self,
			filename: str,
			tmp_pathplus_clean: PathPlus,
			advanced_file_regression: AdvancedFileRegressionFixture,
			advanced_data_regression: AdvancedDataRegressionFixture,
			capsys,
			):

		languages = {"python3": {"reformat": True}}
		directives = ["code-block", "code-cell"]

		(tmp_pathplus_clean / filename).write_text((source_dir / filename).read_text())
		(tmp_pathplus_clean / "formate.toml").write_text((source_dir / "example_formate.toml").read_text())

		config: SnippetFmtConfigDict = {"languages": languages, "directives": directives}

		with in_directory(tmp_pathplus_clean):
			reformat_file(tmp_pathplus_clean / filename, config)

		advanced_file_regression.check_file(tmp_pathplus_clean / filename)
		check_out(capsys.readouterr(), tmp_pathplus_clean, advanced_data_regression)


class TestCLI:

	@directives
	@languages
	@filenames
	def test_snippet_fmt(
			self,
			filename: str,
			tmp_pathplus_clean: PathPlus,
			directives: List[str],
			languages: Dict,
			advanced_file_regression: AdvancedFileRegressionFixture,
			advanced_data_regression: AdvancedDataRegressionFixture,
			):
		(tmp_pathplus_clean / filename).write_text((source_dir / filename).read_text())
		(tmp_pathplus_clean / "formate.toml").write_text((source_dir / "example_formate.toml").read_text())
		dom_toml.dump(
				{"tool": {"snippet-fmt": {"languages": languages, "directives": directives}}},
				tmp_pathplus_clean / "pyproject.toml",
				)

		with in_directory(tmp_pathplus_clean):
			runner = CliRunner(mix_stderr=False)
			result = runner.invoke(
					main,
					args=[filename, "--no-colour", "--diff"],
					)

		advanced_file_regression.check_file(tmp_pathplus_clean / filename)

		check_out(result, tmp_pathplus_clean, advanced_data_regression)

		# Calling a second time shouldn't change anything
		st = (tmp_pathplus_clean / filename).stat()
		assert st == st

		with in_directory(tmp_pathplus_clean):
			runner = CliRunner(mix_stderr=False)
			runner.invoke(main, args=[filename])

		# mtime should be the same
		assert (tmp_pathplus_clean / filename).stat().st_mtime == st.st_mtime

	@directives
	@pytest.mark.parametrize("languages", base_languages)
	@filenames
	@pytest.mark.parametrize(
			"quotes",
			[
					param("'''", id="single"),
					param('"""', id="double"),
					],
			)
	@pytest.mark.parametrize(
			"indent",
			[
					param('\t', id="tab"),
					param("    ", id="4s"),
					param("        ", id="8s"),
					],
			)
	def test_docstrings(
			self,
			filename: str,
			tmp_pathplus_clean: PathPlus,
			directives: List[str],
			languages: Dict,
			quotes: str,
			indent: str,
			advanced_file_regression: AdvancedFileRegressionFixture,
			):
		docstring = textwrap.indent((source_dir / filename).read_text(), indent)
		template = f"def foo():\n{indent}{quotes}\n" + "{d}" + f"{indent}{quotes}\n{indent}pass\n"
		py_filename = (tmp_pathplus_clean / filename).with_suffix(".py")
		py_filename.write_text(template.format_map({'d': docstring}))
		(tmp_pathplus_clean / "formate.toml").write_text((source_dir / "example_formate.toml").read_text())
		dom_toml.dump(
				{"tool": {"snippet-fmt": {"languages": languages, "directives": directives}}},
				tmp_pathplus_clean / "pyproject.toml",
				)

		with in_directory(tmp_pathplus_clean):
			runner = CliRunner(mix_stderr=False)
			result = runner.invoke(
					main,
					args=[py_filename.name, "--no-colour", "--diff"],
					)

		advanced_file_regression.check_file(py_filename)

		# check_out(result, tmp_pathplus_clean, advanced_data_regression)

		# Calling a second time shouldn't change anything
		st = py_filename.stat()
		assert st == st

		with in_directory(tmp_pathplus_clean):
			runner = CliRunner(mix_stderr=False)
			runner.invoke(main, args=[py_filename.name])

		# mtime should be the same
		assert py_filename.stat().st_mtime == st.st_mtime


@no_type_check
def check_out(
		result: Union[Result, CaptureResult[str]],
		tmpdir: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		) -> None:

	if hasattr(result, "stdout"):
		stdout = result.stdout
	else:
		stdout = result.out

	if hasattr(result, "stderr"):
		stderr = result.stderr
	else:
		stderr = result.err

	data_dict = {
			"out": strip_ansi(stdout.replace(tmpdir.as_posix(), "...")).split('\n'),
			"err": strip_ansi(stderr.replace(tmpdir.as_posix(), "...")).split('\n'),
			}

	advanced_data_regression.check(data_dict)


def test_code_block(tmp_pathplus: PathPlus, advanced_file_regression: AdvancedFileRegressionFixture):
	py_code = '''\
def foo():
	"""

	.. code-block:: python

		>>> string_to_unicode("NH4+")
		'NH₄⁺'
		>>> string_to_unicode( "Fe(CN)6+2" )
		'Fe(CN)₆²⁺'
		>>> string_to_unicode('Fe(CN)6+2(aq)')
		'Fe(CN)₆²⁺(aq)'
		>>> string_to_unicode(".NHO-(aq)")
		'⋅NHO⁻(aq)'
		>>> string_to_unicode("alpha-FeOOH(s)")
		'α-FeOOH(s)'
	"""


def bar():
	"""

	.. code-block:: python

		>>> for i in hill_order("H", "C[12]", 'O'): print(i, end='')
		CHO
	"""


def baz():
	"""

	.. code-block:: python

		>>> for i in hill_order('H', 'C[12]', 'O'):
		... 	print(i, end='')
		CHO

	.. code-block:: python

		>>> for _ in range(5):
		... 	print("Hello World")
		Hello World
		Hello World
		Hello World
		Hello World
		Hello World
	"""

'''

	(tmp_pathplus / "code.py").write_text(py_code)
	(tmp_pathplus / "pyproject.toml").write_text(PYPROJECT_LANGUAGES_A)
	config = load_toml(tmp_pathplus / "pyproject.toml")
	r = PyReformatter((tmp_pathplus / "code.py"), config=config)
	r.run()
	advanced_file_regression.check(r.to_string(), extension="._py")
