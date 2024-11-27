"""Tests for definition requests."""

import pytest
from hamcrest import assert_that, contains_string
from lsprotocol.types import (
    HoverParams,
    Position,
    TextDocumentIdentifier,
)

from tests import TEST_DATA
from tests.client import BibliClient
from tests.utils import as_uri


@pytest.mark.asyncio
async def test_hover():
    """Test that completion show the correct contents"""

    async with BibliClient() as client:
        uri = as_uri(TEST_DATA / "definition_test.md")

        actual = await client.text_document_hover_async(
            HoverParams(TextDocumentIdentifier(uri), Position(line=1, character=2))
        )
        assert actual

        # Just doing simple string matching for now
        assert_that(str(actual), contains_string("john_snow"))
        assert_that(str(actual), contains_string("1984"))
