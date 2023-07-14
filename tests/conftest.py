import os
import sys

import pytest


dir_name = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(0, dir_name + '/../')
sys.path.insert(0, dir_name)


LIBFIXTURES = ()

pytest.register_assert_rewrite(*LIBFIXTURES)
pytest_plugins = (
    # Our own plugins
    *LIBFIXTURES,
    # Third party plugins
)
