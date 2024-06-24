import logging
import os.path
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Pattern

import bibtexparser
from bibtexparser import Library
from bibtexparser.model import Entry
from bibtexparser.splitter import Field
from lsprotocol.types import (
    INITIALIZE,
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_DEFINITION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DOCUMENT_SYMBOL,
    TEXT_DOCUMENT_HOVER,
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    CompletionOptions,
    CompletionParams,
    DefinitionParams,
    DidOpenTextDocumentParams,
    DocumentSymbol,
    DocumentSymbolParams,
    Hover,
    HoverParams,
    InitializeParams,
    InitializeResult,
    MarkupContent,
    MarkupKind,
    MessageType,
    Position,
    Range,
    ShowDocumentParams,
    SymbolKind,
    TextEdit,
    TypeDefinitionParams,
)
from py_markdown_table.markdown_table import markdown_table
from pygls.protocol.language_server import LanguageServerProtocol, lsp_method
from pygls.server import LanguageServer
from pygls.workspace import TextDocument

from . import __version__
from .bibli_config import BibliTomlConfig


@dataclass
class BibliBibDatabase:
    library: Library
    path: str


global CONFIG
LIBRARIES: list[BibliBibDatabase] = []
SYMBOLS_REGEX: Optional[Pattern] = None


class BibliConfig:
    lsp: LanguageServerProtocol
    params: InitializeParams
    toml_config: BibliTomlConfig = BibliTomlConfig()
    config_file: Optional[Path] = None

    def __init__(self, lsp: LanguageServerProtocol, params: InitializeParams) -> None:
        from watchdog.observers import Observer

        global LIBRARIES

        self.lsp = lsp
        self.params = params
        self.observer = Observer()

        self.try_load_configs_file()
        self.try_find_bibfiles()
        self.parse_bibfiles()

        self.schedule_file_watcher()

    def schedule_file_watcher(self):
        from watchdog.events import FileSystemEvent, FileSystemEventHandler

        class BibfileChangedHandler(FileSystemEventHandler):
            last_event = 0

            def on_modified(self, event: FileSystemEvent) -> None:
                import time

                # Avoid too many events
                if time.time_ns() - self.last_event < 10**9:
                    return

                if not event.is_directory and CONFIG is not None:
                    for file in CONFIG.toml_config.bibfiles:
                        if event.src_path == os.path.abspath(file):
                            CONFIG.lsp.show_message(
                                f"Bibfile {event.src_path} modified"
                            )
                            CONFIG.parse_bibfiles()
                            self.last_event = time.time_ns()

        self.observer.schedule(
            event_handler=BibfileChangedHandler(),
            path=self.params.root_path,
            recursive=True,
        )
        self.observer.start()

    def try_find_bibfiles(self):
        if self.toml_config.bibfiles == []:
            pass

        if self.toml_config.bibfiles == []:
            self.lsp.show_message("No bibfile found.", MessageType.Warning)

    def parse_bibfiles(self):
        global LIBRARIES
        for bibfile_path in self.toml_config.bibfiles:
            if not os.path.isabs(bibfile_path) and self.params.root_path:
                bibfile_path = os.path.join(self.params.root_path, bibfile_path)

            with open(bibfile_path, "r") as bibtex_file:
                library: Library = bibtexparser.parse_string(bibtex_file.read())
                len = library.entries.__len__()
                self.lsp.show_message(f"loaded {len} entries from {bibfile_path}")
                LIBRARIES.append(
                    BibliBibDatabase(
                        library,
                        bibfile_path,
                    )
                )

    def try_load_configs_file(self):
        import tosholi

        # TODO: find in XDG config paths
        if self.params.root_path:
            self.config_file = Path(os.path.join(self.params.root_path, ".bibli.toml"))

        if self.config_file:
            with open(self.config_file, "rb") as f:
                self.toml_config = tosholi.load(BibliTomlConfig, f)
                self.lsp.show_message(f"Loaded configs from {self.config_file}")
        else:
            self.lsp.show_message("No config file found, using default settings\n")


CONFIG: Optional[BibliConfig] = None


class BibliLanguageServerProtocol(LanguageServerProtocol):
    """Override some built-in functions."""

    _server: "BibliLanguageServer"

    @lsp_method(INITIALIZE)
    def lsp_initialize(self, params: InitializeParams) -> InitializeResult:
        global CONFIG
        CONFIG = BibliConfig(self, params)

        initialize_result: InitializeResult = super().lsp_initialize(params)

        # Register additional trigger characters
        completion_provider = initialize_result.capabilities.completion_provider
        if completion_provider:
            if completion_provider.trigger_characters:
                completion_provider.trigger_characters.append(
                    CONFIG.toml_config.completion.prefix
                )
        return initialize_result


class BibliLanguageServer(LanguageServer):
    """Bibli language server.

    :attr initialization_options: initialized in lsp_initialize from the
        protocol_cls.
    """

    # initialization_options: InitializationOptions

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.index = {}
        super().__init__(*args, **kwargs)

    def parse(self, doc: TextDocument):
        pass
        # cites = {}
        # for linum, line in enumerate(doc.lines):
        #     if SYMBOLS_REGEX is not None:
        #         if (match := SYMBOLS_REGEX.match(line)) is not None:
        #             name = match.group(1)
        #
        #             logging.error("Match " + name + "\n")
        #             start_char = match.start() + line.find(name)
        #
        #             cites[name] = dict(
        #                 range_=Range(
        #                     start=Position(line=linum, character=start_char),
        #                     end=Position(line=linum, character=start_char + len(name)),
        #                 ),
        #             )
        #
        # self.index[doc.uri] = {
        #     "cites": cites,
        # }
        #     if (match := TYPE.match(line)) is not None:
        #         self.parse_typedef(typedefs, linum, line, match)
        #
        #     elif (match := FUNCTION.match(line)) is not None:
        #         self.parse_function(funcs, linum, line, match)
        #
        # self.index[doc.uri] = {
        #     "types": typedefs,
        #     "functions": funcs,

    # }
    # logging.info("Index: %s", self.index)


SERVER = BibliLanguageServer(
    name="bibli-language-server",
    version=__version__,
    protocol_cls=BibliLanguageServerProtocol,
)


@SERVER.feature(TEXT_DOCUMENT_DEFINITION)
def goto_definition(ls: BibliLanguageServer, params: DefinitionParams):
    """Jump to an object's type definition."""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    # index = ls.index.get(doc.uri)
    # if index is None:
    #     return

    word = doc.word_at_position(params.position)
    for library in LIBRARIES:
        entry: Entry | None = library.library.entries_dict.get(word)
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

    # for match in ARGUMENT.finditer(line):
    #     if match.group("name") == word:
    #         if (range_ := index["types"].get(match.group("type"), None)) is not None:
    #             return types.Location(uri=doc.uri, range=range_)


# @SERVER.feature(TEXT_DOCUMENT_DID_CHANGE)
# def did_change(ls: BibliLanguageServer, params: DidOpenTextDocumentParams):
#     """Parse each document when it is changed"""
#     # doc = ls.workspace.get_text_document(params.text_document.uri)
#     ls.show_message(f"{params.text_document.uri} changed")
#     # ls.parse(doc)


def process_bib_entry(entry: Entry, config: BibliTomlConfig):
    replace_list = ["{{", "}}", "\\vphantom", "\\{", "\\}"]
    for f in entry.fields:
        if isinstance(f.value, str):
            for r in replace_list:
                f.value = f.value.replace(r, "")

            f.value = f.value.replace("\n", " ")
            if len(f.value) > config.hover.character_limit:
                f.value = f.value[: config.hover.character_limit] + "..."

            if f.key == "url":
                f.value = f"<{f.value}>"

            entry.set_field(Field(f.key, f.value))


@SERVER.feature(TEXT_DOCUMENT_HOVER)
def hover(ls: LanguageServer, params: HoverParams):
    import mdformat

    pos = params.position
    document_uri = params.text_document.uri
    document = ls.workspace.get_text_document(document_uri)

    try:
        word = document.word_at_position(pos)
    except IndexError:
        return None

    if CONFIG is None:
        raise ValueError("CONFIG is None")

    for library in LIBRARIES:
        entry = library.library.entries_dict.get(word)
        if entry:
            process_bib_entry(entry, CONFIG.toml_config)

            hover_text = [
                f.format(**{f.key: f.value for f in entry.fields})
                for f in CONFIG.toml_config.hover.format_string
            ]

            hover_content = {
                k: v
                for k, v in entry.items()
                if CONFIG.toml_config.hover.show_fields == []
                or CONFIG.toml_config.hover.show_fields.count(k) > 0
            }

            match CONFIG.toml_config.hover.format:
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

            # hover_text.append(str(entry))

            return Hover(
                contents=MarkupContent(
                    kind=MarkupKind.Markdown,
                    value=mdformat.text("\n".join(hover_text), options={"wrap": 80}),
                ),
                range=Range(
                    start=Position(line=pos.line, character=0),
                    end=Position(line=pos.line + 1, character=0),
                ),
            )
        return None


@SERVER.feature(
    TEXT_DOCUMENT_COMPLETION,
    # TODO: How to change trigger character based on config file?
    CompletionOptions(
        trigger_characters=["[", "<", "{"],
        # resolve_provider=True,
    ),
)
def completion(
    server: BibliLanguageServer, params: CompletionParams
) -> Optional[CompletionList]:
    """Returns completion items."""
    completion_items = []
    for library in LIBRARIES:
        for k, v in library.library.entries_dict.items():
            if CONFIG is None:
                raise ValueError("CONFIG is None")

            key = CONFIG.toml_config.completion.prefix + k
            text_edits = []

            # left = CONFIG.cite_format.find("{}")
            # right = left + 2

            # left_insert = CONFIG.cite_format[:left]
            # right_insert = CONFIG.cite_format[right:]
            #
            # server.show_message(word)
            # if word[0] == "@":
            # text_edits.append(
            #     TextEdit(
            #         Range(
            #             start=Position(
            #                 params.position.line, params.position.character - 1
            #             ),
            #             end=Position(
            #                 params.position.line, params.position.character - 1
            #             ),
            #         ),
            #         left_insert,
            #     )
            # )
            #
            # text_edits.append(
            #     TextEdit(
            #         Range(
            #             start=Position(
            #                 params.position.line, params.position.character + len(key)
            #             ),
            #             end=Position(
            #                 params.position.line, params.position.character + len(key)
            #             ),
            #         ),
            #         right_insert,
            #     )
            # )
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
