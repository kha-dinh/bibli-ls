"""Tests for completion requests."""

import pytest
from hamcrest import assert_that, is_, is_in
from lsprotocol.types import (
    CompletionContext,
    CompletionItem,
    CompletionList,
    CompletionParams,
    CompletionTriggerKind,
    Position,
    TextDocumentIdentifier,
)

from tests import TEST_DATA
from tests.client import BibliClient
from tests.utils import as_uri


@pytest.mark.asyncio
async def test_completion():
    """Test that completion points to the correct entry in bibfile"""

    async with BibliClient(TEST_DATA) as client:
        uri = as_uri(TEST_DATA / "completion_test.md")

        actual = await client.text_document_completion_async(
            CompletionParams(
                TextDocumentIdentifier(uri),
                Position(line=1, character=2),
                CompletionContext(CompletionTriggerKind(2), "@"),
            )
        )
        assert actual
        assert isinstance(actual, CompletionList)

        assert_that(len(actual.items), is_(4))
        assert_that(actual.items[0].label, is_("@test1"))
        assert_that(actual.items[1].label, is_("@test2"))
        assert_that(actual.items[2].label, is_("@test3"))
        assert_that(actual.items[3].label, is_("@reference_test"))


        actual = await client.text_document_completion_async(
            CompletionParams(
                TextDocumentIdentifier(uri),
                Position(line=3, character=3),
            )
        )
        assert actual
        assert isinstance(actual, CompletionList)

        # Non trigger should not have completion
        actual = await client.text_document_completion_async(
            CompletionParams(
                TextDocumentIdentifier(uri),
                Position(line=2, character=8),
            )
        )
        assert_that(actual, is_(None))
