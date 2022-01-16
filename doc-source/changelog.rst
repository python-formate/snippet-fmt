===============
Changelog
===============

v0.2.0
----------

* CLI -- Now exits with code ``4`` if syntax errors are encountered when checking code blocks.
* :meth:`RSTReformatter.run <snippet_fmt.RSTReformatter.run>` -- Now returns ``4`` if an error occurred, and ``1`` if the file was changed.

.. note:: A Return code of ``5`` indicates a combination of a syntax error and the file being reformatted.

v0.1.4
----------

Fixed typo in the regular expression preventing single line code blocks from matching.

v0.1.3
----------

Ensure indentation is preserved with nested directives.

v0.1.2
----------

Correctly handle indentation containing mixed tabs and spaces.

v0.1.1
----------

Corrected filetypes in ``.pre-commit-hooks.yaml``.

v0.1.0
----------

Initial Release
