import logging
import os
import re
from pathlib import Path
from typing import Any, Optional

from lsprotocol import types
from pygls.lsp.server import LanguageServer
from pygls.protocol.language_server import LanguageServerProtocol, lsp_method
from pygls.workspace.text_document import TextDocument

from bibli_ls.backends.bibtex_backend import BibfileBackend
from bibli_ls.backends.zotero_backend import ZoteroBackend

from . import __version__
from .bibli_config import BibliTomlConfig
from .database import BibliBibDatabase
from .utils import (
    build_doc_string,
    get_cite_uri,
    show_message,
)
from .parse import (
    citekey_at_position,
    find_cites
)

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
            types.MessageType.Error,
        )
    except FileNotFoundError:
        show_message(ls, "No config file found, using default settings\n")

    if not CONFIG.sanitize():
        logger.error("Invalid config")


def load_libraries(ls: LanguageServer, use_cached: bool = True):
    global DATABASE, CONFIG
    for k, v in CONFIG.backends.items():
        show_message(
            ls,
            f"Processing backend `{k}` type `{v.backend_type}`",
        )
        if v.backend_type == "zotero_api":
            if not use_cached:
                DATABASE.libraries[k] = ZoteroBackend(k, v, ls).get_libraries()
            else:
                DATABASE.libraries[k] = ZoteroBackend(k, v, ls).get_libraries_cached()

        elif v.backend_type == "bibfile":
            DATABASE.libraries[k] = BibfileBackend(k, v, ls).get_libraries()
        else:
            show_message(
                ls,
                f"Unknown backend type {v.backend_type} ",
                types.MessageType.Error,
            )


class BibliLanguageServerProtocol(LanguageServerProtocol):
    """Override some built-in functions."""

    @lsp_method(types.INITIALIZE)
    def lsp_initialize(self, params: types.InitializeParams) -> types.InitializeResult:
        """Initialize LSP"""

        initialize_result: types.InitializeResult = super().lsp_initialize(params)

        if params.root_path:
            try_load_configs_file(self._server, root_path=params.root_path)

        # Load libraries
        load_libraries(self._server)

        # Register additional trigger characters
        completion_provider = initialize_result.capabilities.completion_provider
        if completion_provider:
            completion_provider.trigger_characters = [
                CONFIG.cite.trigger,
                CONFIG.cite.prefix,
            ]

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
        self.completion_cache = []

        super().__init__(*args, **kwargs)

    def rebuild_completion_items(
        self,
    ):
        processed_keys = {}
        self.completion_cache.clear()
        for libraries in DATABASE.libraries.values():
            for lib in libraries:
                for k, entry in lib.entries_dict.items():
                    key = CONFIG.cite.trigger + k
                    text_edits = []
                    doc_string = build_doc_string(
                        entry, CONFIG.completion.doc_format, str(lib.path)
                    )

                    # Avoid showing duplicated entries
                    if not processed_keys.get(key):
                        processed_keys[key] = True
                        self.completion_cache.append(
                            types.CompletionItem(
                                key,
                                insert_text=k,
                                commit_characters=[CONFIG.cite.postfix],
                                additional_text_edits=text_edits,
                                kind=types.CompletionItemKind.Reference,
                                documentation=types.MarkupContent(
                                    kind=types.MarkupKind.Markdown,
                                    value=doc_string,
                                ),
                            )
                        )

    def diagnose(self, document: TextDocument):
        global CONFIG
        diagnostics = []

        for idx, line in enumerate(document.lines):
            cite_matches = find_cites(line, CONFIG.cite)
            if not cite_matches:
                continue
            for match in cite_matches:
                key = match.group(1)

                if DATABASE.find_in_libraries(key) != (
                        None,
                        None,
                    ):
                    continue

                message = f'Item "{key}" does not exist in library'
                severity = types.DiagnosticSeverity.Warning
                diagnostics.append(
                    types.Diagnostic(
                        message=message,
                        severity=severity,
                        range=types.Range(
                            start=types.Position(line=idx, character=match.start()),
                            end=types.Position(line=idx, character=match.end()),
                        ),
                    )
                )

        self.diagnostics[document.uri] = (document.version, diagnostics)


SERVER = BibliLanguageServer(
    name="bibli-language-server",
    version=__version__,
    protocol_cls=BibliLanguageServerProtocol,
)


@SERVER.thread()
@SERVER.command("library.reload_all")
def reload_all(ls: BibliLanguageServer, *args):
    load_libraries(ls, False)


@SERVER.feature(
    types.TEXT_DOCUMENT_CODE_ACTION,
    types.CodeActionOptions(code_action_kinds=[types.CodeActionKind.Empty]),
)
def code_actions(params: types.CodeActionParams):
    items = []
    document_uri = params.text_document.uri

    items.append(
        types.CodeAction(
            "Bibli: Reload all libraries",
            kind=types.CodeActionKind.Empty,
            command=types.Command("ASDASD", "library.reload_all"),
        )
    )
    return items


@SERVER.feature(types.TEXT_DOCUMENT_DID_SAVE)
def did_save(_: BibliLanguageServer, params: types.DidSaveTextDocumentParams):
    if params.text_document.uri == CONFIG_FILE.as_uri():
        logger.info(f"Config file `{CONFIG_FILE}` modified")


@SERVER.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: BibliLanguageServer, params: types.DidOpenTextDocumentParams):
    """Parse each document when it is opened"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.diagnose(doc)

    for uri, (version, diagnostics) in ls.diagnostics.items():
        ls.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(
                uri=uri, version=version, diagnostics=diagnostics
            )
        )


@SERVER.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: BibliLanguageServer, params: types.DidOpenTextDocumentParams):
    """Parse each document when it is changed"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.diagnose(doc)

    for uri, (version, diagnostics) in ls.diagnostics.items():
        ls.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(
                uri=uri, version=version, diagnostics=diagnostics
            )
        )


@SERVER.feature(types.TEXT_DOCUMENT_REFERENCES)
def find_references(ls: BibliLanguageServer, params: types.ReferenceParams):
    """textDocument/references: Find references of an object through simple ripgrep."""

    from ripgrepy import Ripgrepy

    root_path = ls.workspace.root_path
    if not root_path:
        return

    document = ls.workspace.get_text_document(params.text_document.uri)
    cite = citekey_at_position(document, params.position, CONFIG.cite)

    if not cite:
        return

    # Include trigger for better accuracy
    rg = Ripgrepy(CONFIG.cite.trigger + cite, root_path)
    result = rg.with_filename().json().run().as_dict
    references = []

    for res in result:
        if res["type"] == "match":
            # for submatch in res["data"]["submatches"]:
            submatch = res["data"]["submatches"][0]
            file_uri = "file://" + res["data"]["path"]["text"]
            line_no = res["data"]["line_number"]
            references.append(
                types.Location(
                    uri=file_uri,
                    range=types.Range(
                        start=types.Position(
                            line=line_no - 1,
                            character=submatch["start"],
                        ),
                        end=types.Position(
                            line=line_no - 1, character=submatch["end"] - 1
                        ),
                    ),
                )
            )

    # logger.debug(f"RESULTS: {references}")
    return references


@SERVER.feature(types.TEXT_DOCUMENT_DEFINITION)
def goto_definition(ls: BibliLanguageServer, params: types.DefinitionParams):
    """textDocument/definition: Jump to an object's definition."""

    definitions: types.Definition = []

    document = ls.workspace.get_text_document(params.text_document.uri)

    cite = citekey_at_position(document, params.position, CONFIG.cite)
    if not cite:
        return []

    (entry, library) = DATABASE.find_in_libraries(cite)
    if entry and library and library.path is not None:
        from ripgrepy import Ripgrepy

        rg = Ripgrepy(cite, str(library.path))
        result = rg.with_filename().json().run().as_dict
        for res in result:
            if res["type"] == "match":
                submatch = res["data"]["submatches"][0]
                line_no = res["data"]["line_number"]
                definitions.append(
                    types.Location(
                        uri=Path(library.path).as_uri(),
                        range=types.Range(
                            start=types.Position(
                                line=line_no - 1, character=submatch["start"]
                            ),
                            end=types.Position(
                                line=line_no - 1, character=submatch["end"] - 1
                            ),
                        ),
                    )
                )
    # logger.debug(f"Founr definitions: {definitions}")
    return definitions


@SERVER.feature(types.TEXT_DOCUMENT_IMPLEMENTATION)
def goto_implementation(ls: BibliLanguageServer, params: types.DefinitionParams):
    """textDocument/definition: Jump to an object's type definition."""
    document = ls.workspace.get_text_document(params.text_document.uri)

    cite = citekey_at_position(document, params.position, CONFIG.cite)
    if not cite:
        return

    uri = get_cite_uri(DATABASE, cite, CONFIG)
    if uri:
        ls.window_show_document(types.ShowDocumentParams(uri, external=True))
        return types.Location(
            params.text_document.uri, types.Range(params.position, params.position)
        )

    return None


@SERVER.feature(types.TEXT_DOCUMENT_DIAGNOSTIC)
def diagnostic(ls: BibliLanguageServer, params: types.DocumentDiagnosticParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.diagnose(doc)

    return types.RelatedFullDocumentDiagnosticReport(ls.diagnostics[doc.uri][1])


@SERVER.feature(types.TEXT_DOCUMENT_HOVER)
def hover(ls: BibliLanguageServer, params: types.HoverParams):
    """textDocument/hover: Display entry metadata."""

    pos = params.position
    document_uri = params.text_document.uri
    document = ls.workspace.get_text_document(document_uri)

    cite = citekey_at_position(document, params.position, CONFIG.cite)
    if not cite:
        return None

    (entry, library) = DATABASE.find_in_libraries(cite)
    if entry and library and library.path:
        hover_text = build_doc_string(entry, CONFIG.hover.doc_format, str(library.path))

        return types.Hover(
            contents=types.MarkupContent(
                kind=types.MarkupKind.Markdown,
                value=hover_text,
            ),
            range=types.Range(
                start=types.Position(line=pos.line, character=0),
                end=types.Position(line=pos.line + 1, character=0),
            ),
        )
    return None


@SERVER.feature(
    types.TEXT_DOCUMENT_COMPLETION,
    types.CompletionOptions(
        # resolve_provider=True,
    ),
)
def completion(
    ls: BibliLanguageServer, params: types.CompletionParams
) -> Optional[types.CompletionList]:
    """textDocument/completion: Returns completion items."""

    document_uri = params.text_document.uri
    document = ls.workspace.get_text_document(document_uri)

    # Heuristics to support cancelled completion with trigger.
    # Even if there is not a trigger, if there is a *kinda* cite at the position,
    # also trigger completion.

    should_complete = False

    char_at_pos = document.lines[params.position.line][params.position.character - 1]
    if (
        char_at_pos == CONFIG.cite.trigger
        or char_at_pos == CONFIG.cite.prefix
        or char_at_pos == CONFIG.cite.separator
    ):
        should_complete |= True

    cite = citekey_at_position(
        document,
        types.Position(params.position.line, params.position.character - 1),
        CONFIG.cite,
    )
    if cite:
        should_complete |= True

    if params.context and (
        params.context.trigger_character == CONFIG.cite.trigger
        or params.context.trigger_character == CONFIG.cite.prefix
    ):
        should_complete |= True

    if not should_complete:
        return None

    if ls.completion_cache == []:
        ls.rebuild_completion_items()

    return types.CompletionList(is_incomplete=False, items=ls.completion_cache)
