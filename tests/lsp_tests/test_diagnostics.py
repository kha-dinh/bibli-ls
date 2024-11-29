"""Tests for diagnostic requests."""

import pytest
from hamcrest import assert_that, is_
from lsprotocol.types import (
    DefinitionParams,
    Diagnostic,
    DiagnosticSeverity,
    DocumentDiagnosticParams,
    DocumentDiagnosticRequest,
    FullDocumentDiagnosticReport,
    Location,
    Position,
    Range,
    RelatedFullDocumentDiagnosticReport,
    TextDocumentIdentifier,
)

from tests import TEST_DATA, TEST_ROOT
from tests.client import BibliClient
from tests.utils import as_uri


@pytest.mark.asyncio
async def test_diagnostic():
    """Test that correct diagnostics are returned"""

    async with BibliClient(TEST_DATA) as client:
        uri = as_uri(TEST_DATA / "diagnostic_test.md")

        actual = await client.text_document_diagnostic_async(
            DocumentDiagnosticParams(TextDocumentIdentifier(uri))
        )
        assert isinstance(actual, RelatedFullDocumentDiagnosticReport)

        expected = RelatedFullDocumentDiagnosticReport(
            [
                Diagnostic(
                    Range(Position(1, 2), Position(1, 10)),
                    message='Item "unknown1" does not exist in library',
                    severity=DiagnosticSeverity.Warning,
                ),
                Diagnostic(
                    Range(Position(2, 12), Position(2, 20)),
                    message='Item "unknown2" does not exist in library',
                    severity=DiagnosticSeverity.Warning,
                ),
                Diagnostic(
                    Range(Position(3, 12), Position(3, 20)),
                    message='Item "unknown3" does not exist in library',
                    severity=DiagnosticSeverity.Warning,
                ),
            ]
        )
        assert_that(actual, is_(expected))
