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
    TEXT_DOCUMENT_HOVER,
    TEXT_DOCUMENT_REFERENCES,
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    CompletionOptions,
    CompletionParams,
    DefinitionParams,
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
from py_markdown_table.markdown_table import markdown_table
from pygls.protocol.language_server import LanguageServerProtocol, lsp_method
from pygls.server import LanguageServer

from . import __version__
from .bibli_config import BibliBibDatabase, BibliTomlConfig
from .utils import prefix_word_at_position, process_bib_entry


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
            self.try_load_configs_file(params.root_path)

        self.update_trigger_characters(
            initialize_result, server.toml_config.completion.prefix
        )
        self.schedule_file_watcher()
        self.try_find_bibfiles()
        self.parse_bibfiles()

        return initialize_result

    def try_load_configs_file(self, root_path):
        """Load config file located at the root of the project.
        Use default config if not found.
        """
        import tosholi

        # TODO: find in XDG config paths
        config_file = Path(os.path.join(root_path, ".bibli.toml"))

        try:
            f = open(config_file, "rb")
            self._server.toml_config = tosholi.load(BibliTomlConfig, f)
            self.show_message(f"Loaded configs from {config_file}")
        except FileNotFoundError:
            self.show_message("No config file found, using default settings\n")

    def try_find_bibfiles(self):
        """TODO: Get all bibtex files found if config is not given."""
        if self._server.toml_config.bibfiles == []:
            pass

        if self._server.toml_config.bibfiles == []:
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

        class BibfileChangedHandler(FileSystemEventHandler):
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
                    for file in self.lsp._server.toml_config.bibfiles:
                        if event.src_path == os.path.abspath(file):
                            self.lsp.show_message(f"Bibfile {event.src_path} modified")
                            self.lsp.parse_bibfiles()
                            self.last_event = time.time_ns()

        self.observer.schedule(
            event_handler=BibfileChangedHandler(self),
            path=self.workspace.root_path,
            recursive=True,
        )
        self.observer.start()

    def parse_bibfiles(self):
        """Parse the given bibtex files."""
        for bibfile_path in self._server.toml_config.bibfiles:
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
    toml_config: BibliTomlConfig = BibliTomlConfig()
    libraries: list[BibliBibDatabase] = []

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.index = {}
        super().__init__(*args, **kwargs)


SERVER = BibliLanguageServer(
    name="bibli-language-server",
    version=__version__,
    protocol_cls=BibliLanguageServerProtocol,
)


@SERVER.feature(TEXT_DOCUMENT_REFERENCES)
def find_references(ls: BibliLanguageServer, params: ReferenceParams):
    """textDocument/references: Find references of an object through simple ripgrep."""

    from ripgrepy import Ripgrepy

    root_path = ls.workspace.root_path
    if not root_path:
        return

    document = ls.workspace.get_text_document(params.text_document.uri)
    prefix = ls.toml_config.completion.prefix
    word = prefix_word_at_position(document, params.position, prefix)

    if not word:
        return

    # TODO: do we need to check exist in library?
    # exist = False
    # for lib in LIBRARIES:
    #     if lib.library.entries_dict.__contains__(word):
    #         exist = True
    #         break
    # if not exist:
    #     return

    rg = Ripgrepy(word, root_path)
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

    prefix = ls.toml_config.completion.prefix

    word = prefix_word_at_position(document, params.position, prefix)
    if not word:
        return

    id = word.replace(prefix, "")
    for library in ls.libraries:
        entry: Entry | None = library.library.entries_dict.get(id)
        if entry and entry.start_line:
            ls.show_document(
                ShowDocumentParams(
                    f"file://{library.path}",
                    selection=Range(
                        start=Position(entry.start_line, 0),
                        end=Position(entry.start_line, 0),
                    ),
                )
            )


@SERVER.feature(TEXT_DOCUMENT_HOVER)
def hover(ls: BibliLanguageServer, params: HoverParams):
    """textDocument/hover: Display entry metadata."""
    import mdformat

    pos = params.position
    document_uri = params.text_document.uri
    document = ls.workspace.get_text_document(document_uri)

    prefix = ls.toml_config.completion.prefix
    word = prefix_word_at_position(document, params.position, prefix)
    if not word:
        return None

    id = word.replace(prefix, "")
    for library in ls.libraries:
        entry = library.library.entries_dict.get(id)
        if entry:
            process_bib_entry(entry, ls.toml_config)

            format_dict = {f.key: f.value for f in entry.fields}
            format_dict["entry_type"] = entry.entry_type.upper()
            hover_text = [
                f.format(**format_dict) for f in ls.toml_config.hover.format_string
            ]

            hover_content = {
                k: v
                for k, v in entry.items()
                if ls.toml_config.hover.show_fields == []
                or ls.toml_config.hover.show_fields.count(k) > 0
            }

            match ls.toml_config.hover.format:
                case "markdown":
                    table_content = [
                        {"Key": k, "Value": v} for k, v in hover_content.items()
                    ]
                    table = (
                        markdown_table(table_content)
                        .set_params(
                            row_sep="markdown",
                            padding_weight="right",
                            multiline={"Key": 20, "Value": 70},
                            quote=False,
                        )
                        .get_markdown()
                    )
                    hover_text.append(table)
                case "list":
                    for k, v in hover_content.items():
                        hover_text.append(f"- __{k}__: {v}")

            return Hover(
                contents=MarkupContent(
                    kind=MarkupKind.Markdown,
                    value=mdformat.text(
                        "\n".join(hover_text),
                        options={"wrap": ls.toml_config.hover.wrap},
                    ),
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

    prefix = ls.toml_config.completion.prefix
    completion_items = []
    for library in ls.libraries:
        for k, v in library.library.entries_dict.items():
            key = prefix + k
            text_edits = []

            completion_items.append(
                CompletionItem(
                    key,
                    additional_text_edits=text_edits,
                    kind=CompletionItemKind.Field,
                    documentation=MarkupContent(
                        kind=MarkupKind.Markdown, value=f"# {v["title"]}\n"
                    ),
                )
            )

    return (
        CompletionList(is_incomplete=False, items=completion_items)
        if completion_items
        else None
    )
