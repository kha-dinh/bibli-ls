"""Testing entrypoint."""

import py
from pygls import uris

from tests.utils import as_uri


TEST_ROOT = py.path.local(__file__).dirpath()
TEST_URI = as_uri(TEST_ROOT)
PROJECT_ROOT = TEST_ROOT / ".."
PROJECT_URI = as_uri(PROJECT_ROOT)
TEST_DATA = py.path.local(__file__).dirpath() / "test_data"
TEST_DATA_URI = as_uri(TEST_DATA)
