"""Test the CLI."""

import sys
from io import StringIO

from hamcrest import assert_that, is_

from bibli_ls import __version__
from bibli_ls.bibli_config import BibliTomlConfig
from bibli_ls.cli import cli


class Capturing(list):
    """Utility class to capture stdout of a function"""

    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *_):
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


def test_default_config():
    """Test printing the default config"""

    import tosholi

    sys.argv = ["bibli_ls", "--default-config"]
    with Capturing() as output:
        cli()

    expected = BibliTomlConfig()
    actual = tosholi.loads(BibliTomlConfig, output[0])  # type: ignore
    assert_that(actual, is_(expected))
