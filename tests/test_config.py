# 3rd party
import pytest
from coincidence import AdvancedDataRegressionFixture
from domdf_python_tools.paths import PathPlus

# this package
from snippet_fmt.config import load_toml

STANDALONE_LANGUAGES_A = """\
[languages.toml]
reformat = true

[languages.INI]
reformat = true

[languages.JSON]
reformat = true

[languages.json]
reformat = true
indent = 2

[languages.python]
reformat = true
config-file = "formate.toml"

[languages.python3]
reformat = true
config-file = "pyproject.toml"
"""

TABLE_LANGUAGES_A = """\
[snippet-fmt.languages.toml]
reformat = true

[snippet-fmt.languages.INI]
reformat = true

[snippet-fmt.languages.JSON]
reformat = true

[snippet-fmt.languages.json]
reformat = true
indent = 2

[snippet-fmt.languages.python]
reformat = true
config-file = "formate.toml"

[snippet-fmt.languages.python3]
reformat = true
config-file = "pyproject.toml"
"""

PYPROJECT_LANGUAGES_A = """\
[tool.snippet-fmt.languages.toml]
reformat = true

[tool.snippet-fmt.languages.INI]
reformat = true

[tool.snippet-fmt.languages.JSON]
reformat = true

[tool.snippet-fmt.languages.json]
reformat = true
indent = 2

[tool.snippet-fmt.languages.python]
reformat = true
config-file = "formate.toml"

[tool.snippet-fmt.languages.python3]
reformat = true
config-file = "pyproject.toml"
"""


@pytest.mark.parametrize(
		"config",
		[
				pytest.param('', id="empty"),
				pytest.param("directives = ['code-block']", id="standalone_directives_a"),
				pytest.param("directives = ['code']", id="standalone_directives_b"),
				pytest.param("directives = ['jupyter-execute']", id="standalone_directives_c"),
				pytest.param("directives = ['code-cell']", id="standalone_directives_d"),
				pytest.param("directives = ['code-cell', 'sourcecode']", id="standalone_directives_e"),
				pytest.param(STANDALONE_LANGUAGES_A, id="standalone_languages_a"),
				pytest.param("[snippet-fmt]", id="empty_table"),
				pytest.param("[snippet-fmt]\ndirectives = ['code-block']", id="directives_a"),
				pytest.param("[snippet-fmt]\ndirectives = ['code']", id="directives_b"),
				pytest.param("[snippet-fmt]\ndirectives = ['jupyter-execute']", id="directives_c"),
				pytest.param("[snippet-fmt]\ndirectives = ['code-cell']", id="directives_d"),
				pytest.param("[snippet-fmt]\ndirectives = ['code-cell', 'sourcecode']", id="directives_e"),
				pytest.param("[snippet_fmt]", id="empty_table_underscore"),
				pytest.param("[snippet_fmt]\ndirectives = ['code-block']", id="directives_a_underscore"),
				pytest.param("[snippet_fmt]\ndirectives = ['code']", id="directives_b_underscore"),
				pytest.param("[snippet_fmt]\ndirectives = ['jupyter-execute']", id="directives_c_underscore"),
				pytest.param("[snippet_fmt]\ndirectives = ['code-cell']", id="directives_d_underscore"),
				pytest.param(
						"[snippet_fmt]\ndirectives = ['code-cell', 'sourcecode']", id="directives_e_underscore"
						),
				pytest.param(TABLE_LANGUAGES_A, id="languages_a"),
				pytest.param("[tool.snippet-fmt]", id="pyproject_empty_table"),
				pytest.param("[tool.snippet-fmt]\ndirectives = ['code-block']", id="pyproject_directives_a"),
				pytest.param("[tool.snippet-fmt]\ndirectives = ['code']", id="pyproject_directives_b"),
				pytest.param("[tool.snippet-fmt]\ndirectives = ['jupyter-execute']", id="pyproject_directives_c"),
				pytest.param("[tool.snippet-fmt]\ndirectives = ['code-cell']", id="pyproject_directives_d"),
				pytest.
				param("[tool.snippet-fmt]\ndirectives = ['code-cell', 'sourcecode']", id="pyproject_directives_e"),
				pytest.param("[tool.snippet-fmt]", id="pyproject_underscore_empty_table"),
				pytest.param(
						"[tool.snippet_fmt]\ndirectives = ['code-block']", id="pyproject_underscore_directives_a"
						),
				pytest.param("[tool.snippet_fmt]\ndirectives = ['code']", id="pyproject_underscore_directives_b"),
				pytest.param(
						"[tool.snippet_fmt]\ndirectives = ['jupyter-execute']",
						id="pyproject_underscore_directives_c"
						),
				pytest.param(
						"[tool.snippet_fmt]\ndirectives = ['code-cell']", id="pyproject_underscore_directives_d"
						),
				pytest.param(
						"[tool.snippet_fmt]\ndirectives = ['code-cell', 'sourcecode']",
						id="pyproject_underscore_directives_e"
						),
				pytest.param(PYPROJECT_LANGUAGES_A, id="pyproject_languages_a"),
				]
		)
def test_load_toml(
		config: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):
	(tmp_pathplus / "config.toml").write_text(config)
	advanced_data_regression.check(load_toml(tmp_pathplus / "config.toml"))
