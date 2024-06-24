import logging
import os.path
import re
from pathlib import Path
from typing import Any, Optional, Pattern

from .bibli_config import BibliTomlConfig

import bibtexparser
from bibtexparser.bwriter import BibDatabase
from lsprotocol.types import (
    INITIALIZE,
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DOCUMENT_SYMBOL,
    TEXT_DOCUMENT_HOVER,
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    CompletionOptions,
    CompletionParams,
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
    SymbolKind,
    TextEdit,
)
from py_markdown_table.markdown_table import markdown_table
from pygls.protocol.language_server import LanguageServerProtocol, lsp_method
from pygls.server import LanguageServer
from pygls.workspace import TextDocument

from . import __version__

# @dataclass
# class BibliBibDatabase(BibDatabase):
#     path: Path


global CONFIG
LIBRARIES: dict[str, BibDatabase] = dict()
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
        for bibfile_path in self.toml_config.bibfiles:
            if not os.path.isabs(bibfile_path) and self.params.root_path:
                bibfile_path = os.path.join(self.params.root_path, bibfile_path)

            with open(bibfile_path) as bibtex_file:
                library: BibDatabase = bibtexparser.load(bibtex_file)
                len = library.get_entry_list().__len__()
                self.lsp.show_message(f"loaded {len} entries from {bibfile_path}")
                LIBRARIES[bibfile_path] = library

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


def process_bib_entry(entry: dict, config: BibliTomlConfig):
    replace_list = ["{{", "}}", "\\vphantom", "\\{", "\\}"]
    for k, v in entry.items():
        if isinstance(v, str):
            for r in replace_list:
                v = v.replace(r, "")

            v = v.replace("\n", " ")
            if len(v) > config.hover.character_limit:
                v = v[: config.hover.character_limit] + "..."
            entry[k] = v

        if k == "url":
            entry[k] = f"<{v}>"


@SERVER.feature(TEXT_DOCUMENT_HOVER)
def hover(ls: LanguageServer, params: HoverParams):
    import copy

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

    # TODO: make our own data structure for libraries and bib entries
    for _, library in LIBRARIES.items():
        entry = copy.deepcopy(library.get_entry_dict().get(word))
        if entry:
            process_bib_entry(entry, CONFIG.toml_config)

            hover_text = [
                f.format(**entry) for f in CONFIG.toml_config.hover.format_string
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

            # hover_content.append("")

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
    for _path, library in LIBRARIES.items():
        for k, v in library.get_entry_dict().items():
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

    logging.error(completion_items)
    return (
        CompletionList(is_incomplete=False, items=completion_items)
        if completion_items
        else None
    )
