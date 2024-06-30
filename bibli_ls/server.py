import logging
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

from . import __version__
from .bibli_config import BibliBibDatabase, BibliTomlConfig
from .utils import build_doc_string, cite_at_position


class BibliLanguageServerProtocol(LanguageServerProtocol):
    """Override some built-in functions."""

    _server: "BibliLanguageServer"

    @lsp_method(INITIALIZE)
    def lsp_initialize(self, params: InitializeParams) -> InitializeResult:
        from watchdog.observers import Observer

        self.observer = Observer()
        server = self._server

        initialize_result: InitializeResult = super().lsp_initialize(params)

        if params.root_path:
            self.try_load_configs_file(root_path=params.root_path)

        # TODO: Redo these init if config is reloaded
        self.update_trigger_characters(initialize_result, server.config.cite.prefix)
        self.schedule_file_watcher()
        self.try_find_bibfiles()
        self.parse_bibfiles()

        return initialize_result

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
            self.show_message(f"Loaded configs from {config_file}")
        except FileNotFoundError:
            self.show_message("No config file found, using default settings\n")

    def try_find_bibfiles(self):
        """TODO: Get all bibtex files found if config is not given."""
        if self._server.config.bibfiles == []:
            pass

        if self._server.config.bibfiles == []:
            self.show_message("No bibfile found.", MessageType.Warning)

    def update_trigger_characters(self, initialize_result, prefix):
        """Add cite prefix to list of trigger characters."""
        # Register additional trigger characters
        completion_provider = initialize_result.capabilities.completion_provider
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
                            self.lsp.show_message(f"Bibfile {event.src_path} modified")
                            self.lsp.parse_bibfiles()
                            self.last_event = time.time_ns()

                    if event.src_path == os.path.abspath(self.lsp._server.config_file):
                        self.lsp.show_message(f"Config file {event.src_path} modified")
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

    def parse_bibfiles(self):
        """Parse the given bibtex files."""

        self._server.libraries.clear()
        for bibfile_path in self._server.config.bibfiles:
            if not os.path.isabs(bibfile_path) and self.workspace.root_path:
                bibfile_path = os.path.join(self.workspace.root_path, bibfile_path)

            with open(bibfile_path, "r") as bibtex_file:
                library: Library = bibtexparser.parse_string(bibtex_file.read())
                len = library.entries.__len__()
                self.show_message(f"loaded {len} entries from {bibfile_path}")
                self._server.libraries.append(
                    BibliBibDatabase(
                        library,
                        bibfile_path,
                    )
                )


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

                message = f'Item "{key}" does not exist in library'
                severity = DiagnosticSeverity.Warning
                diagnostics.append(
                    Diagnostic(
                        message=message,
                        severity=severity,
                        range=Range(
                            start=Position(line=idx, character=match.pos),
                            end=Position(line=idx, character=match.endpos),
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

    # TODO: do we need to check exist in library?
    # exist = False
    # for lib in LIBRARIES:
    #     if lib.library.entries_dict.__contains__(word):
    #         exist = True
    #         break
    # if not exist:
    #     return

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
            line = library_doc.lines[entry.start_line]
            start = line.find(cite)
            # ls.show_message(line)

            ls.show_document(
                ShowDocumentParams(
                    library_uri,
                    selection=Range(
                        start=Position(entry.start_line, start),
                        end=Position(entry.start_line, start + len(cite)),
                    ),
                )
            )


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
