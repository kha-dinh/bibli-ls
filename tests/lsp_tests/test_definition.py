"""Tests for definition requests."""

import os
import sys

import pytest
from hamcrest import assert_that, is_
from lsprotocol.types import (
    ClientCapabilities,
    DefinitionParams,
    InitializeParams,
    Location,
    Position,
    Range,
    TextDocumentIdentifier,
)
from pygls.lsp.client import BaseLanguageClient

from tests import TEST_DATA
from tests import PROJECT_ROOT, TEST_ROOT
from tests.utils import as_uri

DEFINITION_TEST_ROOT = TEST_DATA / "definition"


@pytest.mark.asyncio
async def test_definition():
    """Test that definition points to the correct entry in bibfile"""
    client = BaseLanguageClient("bibli-test", "0.1")
    await client.start_io(
        sys.executable,
        os.path.join(PROJECT_ROOT, "bibli_ls/cli.py"),
        "--log-file",
        os.path.join(TEST_ROOT, "test_lsp.log"),
        "--verbose",
    )

    response = await client.initialize_async(
        InitializeParams(
            capabilities=ClientCapabilities(),
            root_uri=as_uri(TEST_ROOT),
            root_path=str(TEST_ROOT),
        )
    )
    assert response

    uri = as_uri(DEFINITION_TEST_ROOT / "definition_test.md")
    bib_uri = as_uri(TEST_ROOT / "references.bib")
    bib2_uri = as_uri(TEST_ROOT / "references_other.bib")

    actual = await client.text_document_definition_async(
        DefinitionParams(TextDocumentIdentifier(uri), Position(line=1, character=2))
    )
    expected = [Location(bib_uri, Range(start=Position(0, 9), end=Position(0, 13)))]
    assert_that(actual, is_(expected))

    actual = await client.text_document_definition_async(
        DefinitionParams(TextDocumentIdentifier(uri), Position(line=2, character=12))
    )
    expected = [Location(bib2_uri, Range(start=Position(0, 9), end=Position(0, 13)))]
    assert_that(actual, is_(expected))

    actual = await client.text_document_definition_async(
        DefinitionParams(TextDocumentIdentifier(uri), Position(line=3, character=12))
    )
    expected = [Location(bib_uri, Range(start=Position(12, 9), end=Position(12, 13)))]
    assert_that(actual, is_(expected))
