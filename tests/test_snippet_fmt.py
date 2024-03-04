# stdlib
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
from snippet_fmt import SnippetFmtConfigDict, reformat_file
from snippet_fmt.__main__ import main

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
				]
		)
languages = pytest.mark.parametrize(
		"languages",
		[
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
		)
filenames = pytest.mark.parametrize("filename", [param("example.rst", idx=0)])


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
			tmp_pathplus: PathPlus,
			directives: List[str],
			languages: Dict,
			advanced_file_regression: AdvancedFileRegressionFixture,
			advanced_data_regression: AdvancedDataRegressionFixture,
			capsys,
			):
		(tmp_pathplus / filename).write_text((source_dir / filename).read_text())
		(tmp_pathplus / "formate.toml").write_text((source_dir / "example_formate.toml").read_text())

		config: SnippetFmtConfigDict = {"languages": languages, "directives": directives}

		with in_directory(tmp_pathplus):
			reformat_file(tmp_pathplus / filename, config)

		advanced_file_regression.check_file(tmp_pathplus / filename)
		check_out(capsys.readouterr(), tmp_pathplus, advanced_data_regression)

	@pytest.mark.usefixtures("custom_entry_point")
	@filenames
	def test_snippet_fmt_custom_entry_point(
			self,
			filename: str,
			tmp_pathplus: PathPlus,
			advanced_file_regression: AdvancedFileRegressionFixture,
			advanced_data_regression: AdvancedDataRegressionFixture,
			capsys,
			):

		languages = {"python3": {"reformat": True}}
		directives = ["code-block", "code-cell"]

		(tmp_pathplus / filename).write_text((source_dir / filename).read_text())
		(tmp_pathplus / "formate.toml").write_text((source_dir / "example_formate.toml").read_text())

		config: SnippetFmtConfigDict = {"languages": languages, "directives": directives}

		with in_directory(tmp_pathplus):
			reformat_file(tmp_pathplus / filename, config)

		advanced_file_regression.check_file(tmp_pathplus / filename)
		check_out(capsys.readouterr(), tmp_pathplus, advanced_data_regression)


class TestCLI:

	@directives
	@languages
	@filenames
	def test_snippet_fmt(
			self,
			filename: str,
			tmp_pathplus: PathPlus,
			directives: List[str],
			languages: Dict,
			advanced_file_regression: AdvancedFileRegressionFixture,
			advanced_data_regression: AdvancedDataRegressionFixture,
			capsys,
			cli_runner: CliRunner,
			):
		(tmp_pathplus / filename).write_text((source_dir / filename).read_text())
		(tmp_pathplus / "formate.toml").write_text((source_dir / "example_formate.toml").read_text())
		dom_toml.dump(
				{"tool": {"snippet-fmt": {"languages": languages, "directives": directives}}},
				tmp_pathplus / "pyproject.toml",
				)

		with in_directory(tmp_pathplus):
			runner = CliRunner(mix_stderr=False)
			result = runner.invoke(
					main,
					args=[filename, "--no-colour", "--diff"],
					)

		advanced_file_regression.check_file(tmp_pathplus / filename)

		check_out(result, tmp_pathplus, advanced_data_regression)

		# Calling a second time shouldn't change anything
		st = (tmp_pathplus / filename).stat()
		assert st == st

		with in_directory(tmp_pathplus):
			runner = CliRunner(mix_stderr=False)
			runner.invoke(main, args=[filename])

		# mtime should be the same
		assert (tmp_pathplus / filename).stat().st_mtime == st.st_mtime


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
