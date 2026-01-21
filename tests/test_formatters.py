# 3rd party
import pytest as pytest
from coincidence import AdvancedFileRegressionFixture
from domdf_python_tools.paths import PathPlus, in_directory

# this package
from snippet_fmt import format_ini, format_json, format_python, format_toml, noformat


@pytest.mark.parametrize(
		"code",
		[
				pytest.param("print('hello world')", id="python"),
				pytest.param("[project]\nname = 'foo'", id="TOML"),
				pytest.param("[project]\nname: foo", id="INI"),
				pytest.param('{"project": {"name": "foo"}}', id="JSON"),
				],
		)
def test_noformat(code: str):
	assert noformat(code) == code
	assert noformat(code, reformat=True) == code


def test_reformat_python(
		tmp_pathplus: PathPlus,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):

	example_formate_toml = PathPlus(__file__).parent / "example_formate.toml"
	(tmp_pathplus / "formate.toml").write_text(example_formate_toml.read_text())

	code = '\n'.join([
			"class F:",
			"\tfrom collections import (",
			"Iterable,",
			"\tCounter,",
			"\t\t)",
			'',
			"\tdef foo(self):",
			"\t\tpass",
			'',
			"print('hello world')",
			r"assert t.uname == '\udce4\udcf6\udcfc'",
			])

	with in_directory(tmp_pathplus):

		assert format_python(code, reformat=False) == code

		advanced_file_regression.check(
				format_python(code, reformat=True),
				extension="._py",
				)


@pytest.mark.parametrize(
		"code, expected",
		[
				('["hello", "world"]', '["hello", "world"]'),
				('  [  "hello"  , \n\n\n"world" ]\n\n\n\n', '["hello", "world"]'),
				('{"hello": "world"}', '{"hello": "world"}'),
				],
		)
def test_format_json(code: str, expected: str):
	assert format_json(code) == code
	assert format_json(code, reformat=False) == code
	assert format_json(code, reformat=True) == expected


@pytest.mark.parametrize(
		"code, expected",
		[
				('["hello", "world"]', '[\n  "hello",\n  "world"\n]'),
				('  [  "hello"  , \n\n\n"world" ]\n\n\n\n', '[\n  "hello",\n  "world"\n]'),
				('{"hello": "world"}', '{\n  "hello": "world"\n}'),
				],
		)
def test_format_json_options(code: str, expected: str):
	assert format_json(code, indent=2) == code
	assert format_json(code, reformat=False, indent=2) == code
	assert format_json(code, reformat=True, indent=2) == expected


@pytest.mark.parametrize(
		"code, expected",
		[
				('[project]\nhello = "world"', '[project]\nhello = "world"\n'),
				('  [project]\n\n  \thello   =    "world"', '[project]\nhello = "world"\n'),
				],
		)
def test_format_toml(code: str, expected: str):
	assert format_toml(code) == code
	assert format_toml(code, reformat=False) == code
	assert format_toml(code, reformat=True) == expected


@pytest.mark.parametrize(
		"code, expected",
		[
				('[project]\nhello: world', '[project]\nhello = world\n\n'),
				('  [project]\n\n  \thello   =    world', '[project]\nhello = world\n\n'),
				],
		)
def test_format_ini(code: str, expected: str):
	assert format_ini(code) == code
	assert format_ini(code, reformat=False) == code
	assert format_ini(code, reformat=True) == expected
