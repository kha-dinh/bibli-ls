import logging
import os
import re
from pathlib import Path
from typing import Any, Optional

from lsprotocol.types import (
    INITIALIZE,
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_DEFINITION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_SAVE,
    TEXT_DOCUMENT_HOVER,
    TEXT_DOCUMENT_IMPLEMENTATION,
    TEXT_DOCUMENT_REFERENCES,
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    CompletionOptions,
    CompletionParams,
    Definition,
    DefinitionParams,
    Diagnostic,
    DiagnosticSeverity,
    DidOpenTextDocumentParams,
    DidSaveTextDocumentParams,
    Hover,
    HoverParams,
    InitializeParams,
    InitializeResult,
    Location,
    MarkupContent,
    MarkupKind,
    MessageType,
    Position,
    PublishDiagnosticsParams,
    Range,
    ReferenceParams,
    ShowDocumentParams,
)
from pygls.lsp.server import LanguageServer
from pygls.protocol.language_server import LanguageServerProtocol, lsp_method
from pygls.workspace.text_document import TextDocument

from bibli_ls.backends.bibtex_backend import BibfileBackend
from bibli_ls.backends.zotero_backend import ZoteroBackend

from . import __version__
from .bibli_config import BibliTomlConfig
from .database import BibliBibDatabase
from .utils import build_doc_string, cite_at_position, show_message

logger = logging.getLogger(__name__)

CONFIG = BibliTomlConfig()
CONFIG_FILE: Path
DATABASE = BibliBibDatabase()


def try_load_configs_file(ls: LanguageServer, root_path=None, config_file=None):
    """Load config file located at the root of the project.
    Use default config if not found.
    """
    import tosholi

    if not config_file:
        if root_path:
            config_file = Path(os.path.join(root_path, ".bibli.toml"))

    if not config_file:
        return

    try:
        global CONFIG, CONFIG_FILE
        f = open(config_file, "rb")

        CONFIG = tosholi.load(BibliTomlConfig, f)  # type: ignore
        CONFIG_FILE = config_file
        show_message(ls, f"Loaded configs from `{config_file}`")
    except NameError as e:
        show_message(
            ls,
            f"Failed to parse config file `{config_file}` error {e}\n",
            MessageType.Error,
        )
    except FileNotFoundError:
        show_message(ls, "No config file found, using default settings\n")

    if not CONFIG.sanitize():
        logger.error("Invalid config")


def load_libraries(ls: LanguageServer):
    global DATABASE
    DATABASE.libraries.clear()
    for k, v in CONFIG.backends.items():
        show_message(
            ls,
            f"Processing backend `{k}` type `{v.backend_type}`",
        )
        if v.backend_type == "zotero_api":
            DATABASE.libraries += ZoteroBackend(v, ls).get_libraries()

        elif v.backend_type == "bibfile":
            DATABASE.libraries += BibfileBackend(v, ls).get_libraries()
        else:
            show_message(
                ls,
                f"Unknown backend type {v.backend_type} ",
                MessageType.Error,
            )


class BibliLanguageServerProtocol(LanguageServerProtocol):
    """Override some built-in functions."""

    @lsp_method(INITIALIZE)
    def lsp_initialize(self, params: InitializeParams) -> InitializeResult:
        """Initialize LSP"""

        initialize_result: InitializeResult = super().lsp_initialize(params)

        if params.root_path:
            try_load_configs_file(self._server, root_path=params.root_path)

        # Load libraries
        load_libraries(self._server)

        # Register additional trigger characters
        completion_provider = initialize_result.capabilities.completion_provider
        prefix = CONFIG.cite.prefix
        if completion_provider:
            if completion_provider.trigger_characters:
                completion_provider.trigger_characters = list(
                    completion_provider.trigger_characters
                ).append(prefix)
            else:
                completion_provider.trigger_characters = [prefix]

        return initialize_result


class BibliLanguageServer(LanguageServer):
    """Bibli language server.

    :attr initialization_options: initialized in lsp_initialize from the
        protocol_cls.
    """

    # initialization_options: InitializationOptions

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.index = {}
        self.diagnostics = {}

        super().__init__(*args, **kwargs)

    def diagnose(self, document: TextDocument):
        global CONFIG
        diagnostics = []

        for idx, line in enumerate(document.lines):
            for match in re.finditer(CONFIG.cite.regex, line):
                key = match.group(1)
                if DATABASE.find_in_libraries(key):
                    continue

                (start, end) = match.span(1)
                message = f'Item "{key}" does not exist in library'
                severity = DiagnosticSeverity.Warning
                diagnostics.append(
                    Diagnostic(
                        message=message,
                        severity=severity,
                        range=Range(
                            start=Position(line=idx, character=start),
                            end=Position(line=idx, character=end),
                        ),
                    )
                )

        self.diagnostics[document.uri] = (document.version, diagnostics)


SERVER = BibliLanguageServer(
    name="bibli-language-server",
    version=__version__,
    protocol_cls=BibliLanguageServerProtocol,
)


@SERVER.feature(TEXT_DOCUMENT_DID_SAVE)
def did_save(_: BibliLanguageServer, params: DidSaveTextDocumentParams):
    if params.text_document.uri == CONFIG_FILE.as_uri():
        logger.info(f"Config file `{CONFIG_FILE}` modified")


@SERVER.feature(TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: BibliLanguageServer, params: DidOpenTextDocumentParams):
    """Parse each document when it is opened"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.diagnose(doc)

    for uri, (version, diagnostics) in ls.diagnostics.items():
        ls.text_document_publish_diagnostics(
            PublishDiagnosticsParams(uri=uri, version=version, diagnostics=diagnostics)
        )


@SERVER.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: BibliLanguageServer, params: DidOpenTextDocumentParams):
    """Parse each document when it is changed"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.diagnose(doc)

    for uri, (version, diagnostics) in ls.diagnostics.items():
        ls.text_document_publish_diagnostics(
            PublishDiagnosticsParams(uri=uri, version=version, diagnostics=diagnostics)
        )


@SERVER.feature(TEXT_DOCUMENT_REFERENCES)
def find_references(ls: BibliLanguageServer, params: ReferenceParams):
    """textDocument/references: Find references of an object through simple ripgrep."""

    from ripgrepy import Ripgrepy

    root_path = ls.workspace.root_path
    if not root_path:
        return

    document = ls.workspace.get_text_document(params.text_document.uri)
    cite = cite_at_position(document, params.position, CONFIG)

    if not cite:
        return

    search_string = CONFIG.cite.prefix + cite

    # Include prefix for more accuracy
    rg = Ripgrepy(search_string, root_path)
    result = rg.with_filename().json().run().as_dict
    references = []

    for res in result:
        if res["type"] == "match":
            # for submatch in res["data"]["submatches"]:
            submatch = res["data"]["submatches"][0]
            file_uri = "file://" + res["data"]["path"]["text"]
            line_no = res["data"]["line_number"]
            references.append(
                Location(
                    uri=file_uri,
                    range=Range(
                        start=Position(line=line_no - 1, character=submatch["start"]),
                        end=Position(line=line_no - 1, character=submatch["end"] - 1),
                    ),
                )
            )

    return references


@SERVER.feature(TEXT_DOCUMENT_DEFINITION)
def goto_definition(ls: BibliLanguageServer, params: DefinitionParams):
    """textDocument/definition: Jump to an object's definition."""

    definitions: Definition = []

    document = ls.workspace.get_text_document(params.text_document.uri)

    cite = cite_at_position(document, params.position, CONFIG)
    if not cite:
        return

    for library in DATABASE.libraries:
        entry = library.entries_dict.get(cite)
        library_uri = f"file://{library.path}"

        if entry and library.path:
            from ripgrepy import Ripgrepy

            rg = Ripgrepy(cite, str(library.path))
            result = rg.with_filename().json().run().as_dict
            for res in result:
                if res["type"] == "match":
                    submatch = res["data"]["submatches"][0]
                    line_no = res["data"]["line_number"]
                    definitions.append(
                        Location(
                            uri=library_uri,
                            range=Range(
                                start=Position(
                                    line=line_no - 1, character=submatch["start"]
                                ),
                                end=Position(
                                    line=line_no - 1, character=submatch["end"] - 1
                                ),
                            ),
                        )
                    )

    return definitions


@SERVER.feature(TEXT_DOCUMENT_IMPLEMENTATION)
def goto_implementation(ls: BibliLanguageServer, params: DefinitionParams):
    """textDocument/definition: Jump to an object's type definition."""
    document = ls.workspace.get_text_document(params.text_document.uri)

    cite = cite_at_position(document, params.position, CONFIG)
    if not cite:
        return

    for library in DATABASE.libraries:
        entry = library.entries_dict.get(cite)
        if entry and entry.fields_dict.get("url"):
            ls.window_show_document(
                ShowDocumentParams(entry.fields_dict["url"].value, external=True)
            )

    return None


@SERVER.feature(TEXT_DOCUMENT_HOVER)
def hover(ls: BibliLanguageServer, params: HoverParams):
    """textDocument/hover: Display entry metadata."""

    pos = params.position
    document_uri = params.text_document.uri
    document = ls.workspace.get_text_document(document_uri)

    cite = cite_at_position(document, params.position, CONFIG)
    if not cite:
        return None

    for library in DATABASE.libraries:
        entry = library.entries_dict.get(cite)
        if entry:
            hover_text = build_doc_string(
                entry, CONFIG.hover.doc_format, str(library.path)
            )

            return Hover(
                contents=MarkupContent(
                    kind=MarkupKind.Markdown,
                    value=hover_text,
                ),
                range=Range(
                    start=Position(line=pos.line, character=0),
                    end=Position(line=pos.line + 1, character=0),
                ),
            )
    return None


@SERVER.feature(
    TEXT_DOCUMENT_COMPLETION,
    CompletionOptions(
        # resolve_provider=True,
    ),
)
def completion(
    ls: BibliLanguageServer, _: CompletionParams
) -> Optional[CompletionList]:
    """textDocument/completion: Returns completion items."""

    prefix = CONFIG.cite.prefix
    completion_items = []

    processed_keys = {}
    for library in DATABASE.libraries:
        for k, entry in library.entries_dict.items():
            key = prefix + k
            text_edits = []
            doc_string = build_doc_string(
                entry, CONFIG.completion.doc_format, str(library.path)
            )

            # Avoid showing duplicated entries
            if not processed_keys.get(key):
                processed_keys[key] = True
                completion_items.append(
                    CompletionItem(
                        key,
                        additional_text_edits=text_edits,
                        kind=CompletionItemKind.Field,
                        documentation=MarkupContent(
                            kind=MarkupKind.Markdown,
                            value=doc_string,
                        ),
                    )
                )

    return (
        CompletionList(is_incomplete=False, items=completion_items)
        if completion_items
        else None
    )
