def foo():
	"""

	.. code-block:: python

		>>> string_to_unicode("NH4+")
		'NH₄⁺'
		>>> string_to_unicode("Fe(CN)6+2")
		'Fe(CN)₆²⁺'
		>>> string_to_unicode("Fe(CN)6+2(aq)")
		'Fe(CN)₆²⁺(aq)'
		>>> string_to_unicode(".NHO-(aq)")
		'⋅NHO⁻(aq)'
		>>> string_to_unicode("alpha-FeOOH(s)")
		'α-FeOOH(s)'
	"""


def bar():
	"""

	.. code-block:: python

		>>> for i in hill_order('H', "C[12]", 'O'):
		... 	print(i, end='')
		CHO
	"""


def baz():
	"""

	.. code-block:: python

		>>> for i in hill_order('H', "C[12]", 'O'):
		... 	print(i, end='')
		CHO
	"""
