import os
import re
from pathlib import Path
from typing import Any, Optional

from bibtexparser.model import Entry
from lsprotocol.types import (
    EXIT,
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
    Definition,
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
from watchdog.events import FileModifiedEvent
from watchdog.observers import Observer

from bibli_ls.backends.backend import BibliBackend
from bibli_ls.backends.bibtex_backend import BibfileBackend
from bibli_ls.backends.zotero_backend import ZoteroBackend

from . import __version__
from .bibli_config import BibliTomlConfig
from .data_structures import BibliBibDatabase
from .utils import build_doc_string, cite_at_position


class BibliLanguageServerProtocol(LanguageServerProtocol):
    """Override some built-in functions."""

    _server: "BibliLanguageServer"
    _initialize_result: InitializeResult
    _backend: BibliBackend

    @lsp_method(INITIALIZE)
    def lsp_initialize(self, params: InitializeParams) -> InitializeResult:
        from watchdog.observers import Observer

        self._observer = None

        initialize_result: InitializeResult = super().lsp_initialize(params)
        self._initialize_result = initialize_result

        if params.root_path:
            self.try_load_configs_file(root_path=params.root_path)

        self.schedule_file_watcher()
        self.load_libraries()
        return initialize_result

    def load_libraries(self):
        backend_config = self._server.config.backends

        self._server.libraries.clear()
        for k, v in backend_config.items():
            self.show_message(f"Processing backend `{k}` type `{v.backend_type}`")
            if v.backend_type == "zotero_api":
                self._backend = ZoteroBackend(v, lsp=self)
                self._server.libraries += self._backend.get_libraries()

            elif v.backend_type == "bibfile":
                self._backend = BibfileBackend(v, lsp=self)
                self._server.libraries += self._backend.get_libraries()

            else:
                self.show_message(
                    f"Unknown backend type {v.backend_type} ",
                    MessageType.Error,
                )

    def apply_config(self):
        self.update_trigger_characters()

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
        except NameError as e:
            self.show_message(
                f"Failed to parse config file `{config_file}` error {e}\n",
                MessageType.Error,
            )
        except FileNotFoundError:
            self.show_message("No config file found, using default settings\n")

        if not self._server.config.sanitize(self):
            self.show_message("Invalid config", MessageType.Error)
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

                if event.is_directory:
                    return
                # Avoid too many events
                if time.time_ns() - self.last_event < 10**9:
                    return

                for lib in self.lsp._server.libraries:
                    if not lib.path:
                        continue

                    if os.path.abspath(lib.path) != event.src_path:
                        continue

                    self.lsp.show_message(f"Bibfile `{event.src_path}` modified")
                    # Just reloading config for now since it would be too complicated to reload specific library
                    self.lsp.load_libraries()

                if event.src_path == os.path.abspath(self.lsp._server.config_file):
                    self.lsp.show_message(f"Config file `{event.src_path}` modified")
                    self.lsp.try_load_configs_file(
                        config_file=self.lsp._server.config_file
                    )
                self.last_event = time.time_ns()

        if self.workspace.root_path:
            del self._observer

            self._observer = Observer()

            self._observer.schedule(
                event_handler=FileChangedHandler(self),
                path=self.workspace.root_path,
                recursive=True,
                event_filter=[FileModifiedEvent],
            )
            self._observer.start()

    @lsp_method(EXIT)
    def lsp_exit(self, *args) -> None:
        if self._observer:
            self._observer.stop()
            del self._observer


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
    """textDocument/definition: Jump to an object's definition."""

    definitions: Definition = []

    document = ls.workspace.get_text_document(params.text_document.uri)

    cite = cite_at_position(document, params.position, ls.config)
    if not cite:
        return

    for library in ls.libraries:
        entry = library.library.entries_dict.get(cite)
        library_uri = f"file://{library.path}"

        if entry and library.path:
            from ripgrepy import Ripgrepy

            rg = Ripgrepy(cite, library.path)
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

    cite = cite_at_position(document, params.position, ls.config)
    if not cite:
        return

    for library in ls.libraries:
        entry = library.library.entries_dict.get(cite)
        if entry and entry.fields_dict.get("url"):
            ls.show_document(
                ShowDocumentParams(entry.fields_dict["url"].value, external=True)
            )

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
            hover_text = build_doc_string(
                entry, ls.config.hover.doc_format, library.path
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

    prefix = ls.config.cite.prefix
    completion_items = []

    processed_keys = {}
    for library in ls.libraries:
        for k, entry in library.library.entries_dict.items():
            key = prefix + k
            text_edits = []
            doc_string = build_doc_string(
                entry, ls.config.completion.doc_format, library.path
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
