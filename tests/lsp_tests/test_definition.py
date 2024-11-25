"""Tests for definition requests."""

import pytest
from hamcrest import assert_that, is_
from lsprotocol.types import (
    DefinitionParams,
    Location,
    Position,
    Range,
    TextDocumentIdentifier,
)

from tests import TEST_DATA, TEST_ROOT
from tests.client import BibliClient
from tests.utils import as_uri

DEFINITION_TEST_ROOT = TEST_DATA / "definition"


@pytest.mark.asyncio
async def test_definition():
    """Test that definition points to the correct entry in bibfile"""
    async with BibliClient() as client:
        uri = as_uri(DEFINITION_TEST_ROOT / "definition_test.md")
        bib_uri = as_uri(TEST_ROOT / "references.bib")
        bib2_uri = as_uri(TEST_ROOT / "references_other.bib")

        actual = await client.text_document_definition_async(
            DefinitionParams(TextDocumentIdentifier(uri), Position(line=1, character=2))
        )
        expected = [Location(bib_uri, Range(start=Position(0, 9), end=Position(0, 13)))]
        assert_that(actual, is_(expected))

        actual = await client.text_document_definition_async(
            DefinitionParams(
                TextDocumentIdentifier(uri), Position(line=2, character=12)
            )
        )
        expected = [
            Location(bib2_uri, Range(start=Position(0, 9), end=Position(0, 13)))
        ]
        assert_that(actual, is_(expected))

        actual = await client.text_document_definition_async(
            DefinitionParams(
                TextDocumentIdentifier(uri), Position(line=3, character=12)
            )
        )
        expected = [
            Location(bib_uri, Range(start=Position(12, 9), end=Position(12, 13)))
        ]
        assert_that(actual, is_(expected))
