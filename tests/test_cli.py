"""Test the CLI."""

import sys
from io import StringIO

from hamcrest import assert_that, is_

from bibli_ls import __version__
from bibli_ls.cli import cli


class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio  # free up some memory
        sys.stdout = self._stdout


def test_get_version():
    """Test that version is printed correctly"""

    sys.argv = ["bibli_ls", "--version"]
    with Capturing() as output:
        cli()

    print(output)
    assert_that(output[0], is_(str(__version__)))
