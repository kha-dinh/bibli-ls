"""Tests for reference requests."""

import pytest
from hamcrest import assert_that, is_in
from lsprotocol.types import (
    Location,
    Position,
    Range,
    ReferenceContext,
    ReferenceParams,
    TextDocumentIdentifier,
)

from tests import TEST_DATA
from tests.client import BibliClient
from tests.utils import as_uri


@pytest.mark.asyncio
async def test_references():
    """Test that references shows correct locations"""

    async with BibliClient(TEST_DATA) as client:
        uri = as_uri(TEST_DATA / "reference_test_2.md")

        actual = await client.text_document_references_async(
            ReferenceParams(
                context=ReferenceContext(False),
                text_document=TextDocumentIdentifier(uri),
                position=Position(line=1, character=2),
            )
        )
        assert actual
        expected = [
            Location(
                as_uri(TEST_DATA / "reference_test_1.md"),
                Range(Position(2, 10), Position(2, 25)),
            ),
            Location(
                as_uri(TEST_DATA / "reference_test_1.md"),
                Range(Position(3, 10), Position(3, 25)),
            ),
            Location(
                as_uri(TEST_DATA / "reference_test_2.md"),
                Range(Position(3, 10), Position(3, 25)),
            ),
            Location(
                as_uri(TEST_DATA / "reference_test_2.md"),
                Range(Position(1, 0), Position(1, 15)),
            ),
        ]

        assert len(actual) == len(expected)

        for loc in actual:
            assert_that(loc, is_in(expected))
