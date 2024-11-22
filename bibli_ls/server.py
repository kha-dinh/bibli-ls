import os
import re
from pathlib import Path
from typing import Any, Optional

from bibtexparser import bibtexparser
from bibtexparser.library import Library
from bibtexparser.model import Entry
from lsprotocol.types import (
    INITIALIZE,
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_DEFINITION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_HOVER,
    TEXT_DOCUMENT_IMPLEMENTATION,
    TEXT_DOCUMENT_REFERENCES,
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    CompletionOptions,
    CompletionParams,
    DefinitionParams,
    Diagnostic,
    DiagnosticSeverity,
    DidOpenTextDocumentParams,
    Hover,
    HoverParams,
    InitializeParams,
    InitializeResult,
    Location,
    MarkupContent,
    MarkupKind,
    MessageType,
    Position,
    Range,
    ReferenceParams,
    ShowDocumentParams,
)

from pygls.protocol.language_server import LanguageServerProtocol, lsp_method
from pygls.server import LanguageServer
from pygls.workspace.text_document import TextDocument

from bibli_ls.backends.backend import BibliBackend
from bibli_ls.backends.bibtex_backend import BibfileBackend
from bibli_ls.backends.zotero_backend import ZoteroBackend

from . import __version__
from .bibli_config import BibliBibDatabase, BibliTomlConfig
from .utils import build_doc_string, cite_at_position


class BibliLanguageServerProtocol(LanguageServerProtocol):
    """Override some built-in functions."""

    _server: "BibliLanguageServer"
    _initialize_result: InitializeResult
    _backend: BibliBackend

    @lsp_method(INITIALIZE)
    def lsp_initialize(self, params: InitializeParams) -> InitializeResult:
        from watchdog.observers import Observer

        self.observer = Observer()

        initialize_result: InitializeResult = super().lsp_initialize(params)
        self._initialize_result = initialize_result

        if params.root_path:
            self.try_load_configs_file(root_path=params.root_path)

        return initialize_result

    def apply_config(self):
        self.update_trigger_characters()
        self.schedule_file_watcher()

        backend_config = self._server.config.backend
        self.show_message(f"Backed type: `{backend_config.backend_type}`")

        self.show_message("Reloading libraries")
        self._server.libraries.clear()
        if backend_config.backend_type == "zotero_api":
            self._backend = ZoteroBackend(
                backend_config.zotero_api,
                lsp=self,
            )
            self._server.libraries += self._backend.get_libraries()

        elif backend_config.backend_type == "bibfile":
            self._backend = BibfileBackend(backend_config.bibfile, lsp=self)
            self._server.libraries += self._backend.get_libraries()
        else:
            self.show_message(
                f"Unknown backend type {backend_config.backend_type} ",
                MessageType.Error,
            )

    def try_load_configs_file(self, root_path=None, config_file=None):
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
            f = open(config_file, "rb")
            self._server.config = tosholi.load(BibliTomlConfig, f)
            self._server.config_file = config_file
            self.show_message(f"Loaded configs from `{config_file}`")
        except FileNotFoundError:
            self.show_message("No config file found, using default settings\n")

        # Update configurations based on the config
        self.apply_config()

    def update_trigger_characters(self):
        """Add cite prefix to list of trigger characters."""
        # Register additional trigger characters
        completion_provider = self._initialize_result.capabilities.completion_provider
        prefix = self._server.config.cite.prefix
        if completion_provider:
            if completion_provider.trigger_characters:
                completion_provider.trigger_characters.append(prefix)
            else:
                completion_provider.trigger_characters = [prefix]

    def schedule_file_watcher(self):
        """Schedule watchers to watch for changes in bibtex files"""
        from watchdog.events import FileSystemEvent, FileSystemEventHandler

        class FileChangedHandler(FileSystemEventHandler):
            last_event = 0

            def __init__(self, lsp: BibliLanguageServerProtocol) -> None:
                self.lsp = lsp
                super().__init__()

            def on_modified(self, event: FileSystemEvent) -> None:
                import time

                # Avoid too many events
                if time.time_ns() - self.last_event < 10**9:
                    return

                if not event.is_directory:
                    for file in self.lsp._server.config.bibfiles:
                        if event.src_path == os.path.abspath(file):
                            self.lsp.show_message(
                                f"Bibfile `{event.src_path}` modified"
                            )
                            self.lsp._server.libraries = (
                                self.lsp._backend.get_libraries()
                            )

                            self.last_event = time.time_ns()

                    if event.src_path == os.path.abspath(self.lsp._server.config_file):
                        self.lsp.show_message(
                            f"Config file `{event.src_path}` modified"
                        )
                        self.lsp.try_load_configs_file(
                            config_file=self.lsp._server.config_file
                        )
                        self.last_event = time.time_ns()

        self.observer.schedule(
            event_handler=FileChangedHandler(self),
            path=self.workspace.root_path,
            recursive=True,
        )
        self.observer.start()


class BibliLanguageServer(LanguageServer):
    """Bibli language server.

    :attr initialization_options: initialized in lsp_initialize from the
        protocol_cls.
    """

    # initialization_options: InitializationOptions
    config_file: Path
    config: BibliTomlConfig
    libraries: list[BibliBibDatabase]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.index = {}
        self.diagnostics = {}
        self.libraries = []
        self.config = BibliTomlConfig()

        super().__init__(*args, **kwargs)

    def find_in_libraries(self, key: str) -> Entry | None:
        for lib in self.libraries:
            if lib.library.entries_dict.__contains__(key):
                return lib.library.entries_dict[key]

        return None

    def diagnose(self, document: TextDocument):
        diagnostics = []

        for idx, line in enumerate(document.lines):
            for match in re.finditer(self.config.cite.regex, line):
                key = match.group(1)
                if self.find_in_libraries(key):
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


@SERVER.feature(TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: BibliLanguageServer, params: DidOpenTextDocumentParams):
    """Parse each document when it is opened"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.diagnose(doc)

    for uri, (version, diagnostics) in ls.diagnostics.items():
        ls.publish_diagnostics(uri=uri, version=version, diagnostics=diagnostics)


@SERVER.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: BibliLanguageServer, params: DidOpenTextDocumentParams):
    """Parse each document when it is changed"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.diagnose(doc)

    for uri, (version, diagnostics) in ls.diagnostics.items():
        ls.publish_diagnostics(uri=uri, version=version, diagnostics=diagnostics)


@SERVER.feature(TEXT_DOCUMENT_REFERENCES)
def find_references(ls: BibliLanguageServer, params: ReferenceParams):
    """textDocument/references: Find references of an object through simple ripgrep."""

    from ripgrepy import Ripgrepy

    root_path = ls.workspace.root_path
    if not root_path:
        return

    document = ls.workspace.get_text_document(params.text_document.uri)
    cite = cite_at_position(document, params.position, ls.config)

    if not cite:
        return

    # Include prefix for more accuracy
    rg = Ripgrepy(ls.config.cite.prefix + cite, root_path)
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
    """textDocument/definition: Jump to an object's type definition."""
    document = ls.workspace.get_text_document(params.text_document.uri)

    cite = cite_at_position(document, params.position, ls.config)
    if not cite:
        return

    for library in ls.libraries:
        entry = library.library.entries_dict.get(cite)
        if entry and entry.start_line:
            # match = re.search(ls.config.cite.regex, document.lines[entry.start_line])
            library_uri = f"file://{library.path}"
            library_doc = ls.workspace.get_text_document(library_uri)

            neightbour_lines = library_doc.lines[
                entry.start_line - 2 : entry.start_line + 2
            ]

            # bibtexparse is not very accurate on identifying start line, so we search
            # for it neighboring lines
            for idx, line in enumerate(neightbour_lines):
                start = line.find(cite)
                if start != -1:
                    actual_start_line = entry.start_line + idx - 2
                    ls.show_document(
                        ShowDocumentParams(
                            library_uri,
                            selection=Range(
                                start=Position(actual_start_line, start),
                                end=Position(actual_start_line, start + len(cite)),
                            ),
                        )
                    )
                    return


@SERVER.feature(TEXT_DOCUMENT_IMPLEMENTATION)
def goto_implementation(ls: BibliLanguageServer, params: DefinitionParams):
    """textDocument/definition: Jump to an object's type definition."""
    document = ls.workspace.get_text_document(params.text_document.uri)

    cite = cite_at_position(document, params.position, ls.config)
    if not cite:
        return

    for library in ls.libraries:
        entry = library.library.entries_dict.get(cite)
        if entry and entry.fields_dict.get("url"):
            ls.show_document(
                ShowDocumentParams(entry.fields_dict["url"].value, external=True)
            )

            return
    return None


@SERVER.feature(TEXT_DOCUMENT_HOVER)
def hover(ls: BibliLanguageServer, params: HoverParams):
    """textDocument/hover: Display entry metadata."""

    pos = params.position
    document_uri = params.text_document.uri
    document = ls.workspace.get_text_document(document_uri)

    cite = cite_at_position(document, params.position, ls.config)
    if not cite:
        return None

    for library in ls.libraries:
        entry = library.library.entries_dict.get(cite)
        if entry:
            hover_text = build_doc_string(entry, ls.config.hover.doc_format)

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
    ls: BibliLanguageServer, params: CompletionParams
) -> Optional[CompletionList]:
    """textDocument/completion: Returns completion items."""

    prefix = ls.config.cite.prefix
    completion_items = []

    for library in ls.libraries:
        for k, entry in library.library.entries_dict.items():
            key = prefix + k
            text_edits = []
            doc_string = build_doc_string(entry, ls.config.completion.doc_format)
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
