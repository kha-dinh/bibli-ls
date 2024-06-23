import logging
import os.path
from pathlib import Path
from typing import Any, List, Optional, Pattern, Tuple

import re
from attr import dataclass
import bibtexparser
from bibtexparser.bwriter import BibDatabase
from lsprotocol.types import (
    INITIALIZE,
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DOCUMENT_SYMBOL,
    TEXT_DOCUMENT_HOVER,
    CompletionOptions,
    CompletionParams,
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    DocumentSymbol,
    DidOpenTextDocumentParams,
    DocumentSymbolParams,
    Hover,
    HoverParams,
    InitializeParams,
    InitializeResult,
    MarkupContent,
    MarkupKind,
    Position,
    Range,
    SymbolKind,
    TextEdit,
)
from py_markdown_table.markdown_table import markdown_table
from pygls.protocol.language_server import LanguageServerProtocol, lsp_method
from pygls.server import LanguageServer
from pygls.workspace import TextDocument


# class BibFile(bibtexparser.bibdatabase.BibDatabase):
#     def __init__(self):
#         self.path = Path()
#         super().__init__()


@dataclass
class BibliBibDatabase(BibDatabase):
    path: Path


global CONFIG
LIBRARIES: dict[str, BibDatabase] = dict()
SYMBOLS_REGEX: Optional[Pattern] = None

# CONFIG: Optional[dict] = None


@dataclass
class BibliConfig:
    lsp: LanguageServerProtocol
    params: InitializeParams
    config_file: Optional[Path] = None
    root_path: Optional[Path] = None
    bibfiles: List[str] = []
    show_fields: List[str] = []
    cite_prefix: str = "@"
    cite_format: str = "{}"

    def __post_init__(self):
        global LIBRARIES
        import tomllib

        self.find_configs_file()
        if self.config_file:
            with open(self.config_file, "r") as f:
                config = tomllib.loads(f.read())
                self.lsp.show_message(f"Loaded configs from {self.config_file}")
                if (bibfiles := config.get("bibfiles")) is not None:
                    for bibfile_path in bibfiles:
                        if not os.path.isabs(bibfile_path) and self.params.root_path:
                            bibfile_path = os.path.join(
                                self.params.root_path, bibfile_path
                            )

                        with open(bibfile_path) as bibtex_file:
                            library: BibDatabase = bibtexparser.load(bibtex_file)
                            len = library.get_entry_list().__len__()
                            self.lsp.show_message(
                                f"loaded {len} entries from {bibfile_path}"
                            )
                            LIBRARIES[bibfile_path] = library

                if config.get("cite_prefix"):
                    self.cite_prefix = config["cite_prefix"]
                # if config.get("cite_format"):
                #     self.cite_format = config["cite_format"]
                if config.get("show_fields"):
                    self.show_fields = config["show_fields"]
        else:
            self.lsp.show_message("No config given\n")

        if self.bibfiles == []:
            self.try_find_bibfiles()

    def try_find_bibfiles(self):
        logging.error("Bibfiles not specified, trying to find them\n")

    def find_configs_file(self):
        # TODO: find in XDG config paths
        if self.params.root_path:
            self.config_file = Path(os.path.join(self.params.root_path, ".bibli.toml"))


CONFIG: Optional[BibliConfig] = None


class BibliLanguageServerProtocol(LanguageServerProtocol):
    """Override some built-in functions."""

    _server: "BibliLanguageServer"

    @lsp_method(INITIALIZE)
    def lsp_initialize(self, params: InitializeParams) -> InitializeResult:
        global CONFIG
        CONFIG = BibliConfig(self, params)
        CONFIG.__post_init__()
        # logging.error(CONFIG)

        initialize_result: InitializeResult = super().lsp_initialize(params)
        return initialize_result


class BibliLanguageServer(LanguageServer):
    """Bibli language server.

    :attr initialization_options: initialized in lsp_initialize from the
        protocol_cls.
    """

    # initialization_options: InitializationOptions
    # project: Optional[Project]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.index = {}
        super().__init__(*args, **kwargs)

    def parse(self, doc: TextDocument):
        # typedefs = {}
        # funcs = {}
        cites = {}

        for linum, line in enumerate(doc.lines):
            if SYMBOLS_REGEX is not None:
                if (match := SYMBOLS_REGEX.match(line)) is not None:
                    name = match.group(1)

                    logging.error("Match " + name + "\n")
                    start_char = match.start() + line.find(name)

                    cites[name] = dict(
                        range_=Range(
                            start=Position(line=linum, character=start_char),
                            end=Position(line=linum, character=start_char + len(name)),
                        ),
                    )

        self.index[doc.uri] = {
            "cites": cites,
        }
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
    version="0.0.1",
    protocol_cls=BibliLanguageServerProtocol,
)


@SERVER.feature(TEXT_DOCUMENT_HOVER)
def hover(ls: LanguageServer, params: HoverParams):
    pos = params.position
    document_uri = params.text_document.uri
    document = ls.workspace.get_text_document(document_uri)

    try:
        word = document.word_at_position(pos)
    except IndexError:
        return None

    for _path, library in LIBRARIES.items():
        entry = library.get_entry_dict().get(word)
        if entry:
            hover_content = [
                " ",
                f"# {entry['title']}",
                " ",
                f"- _{entry['author']}_",
                " ",
            ]
            filter = []
            # filter = ["title", "author", "ID"]
            content = {k: v for k, v in entry.items() if filter.count(k) == 0}

            if content["url"] is not None:
                content["url"] = f"<{content['url']}>"

            if CONFIG is None:
                raise ValueError("CONFIG is None")

            if CONFIG.show_fields != []:
                table_content = [
                    {"Key": k, "Value": v}
                    for k, v in content.items()
                    if CONFIG.show_fields.count(k) > 0
                ]
            else:
                table_content = [{"Key": k, "Value": v} for k, v in content.items()]

            # content['url']

            table = (
                markdown_table(table_content)
                .set_params(
                    row_sep="markdown",
                    padding_weight="right",
                    multiline=([{"Key": 20, "Value": 70}], None),
                    quote=False,
                )
                .get_markdown()
            )
            hover_content.append(table)
            # hover_content.append("")

            return Hover(
                contents=MarkupContent(
                    kind=MarkupKind.Markdown,
                    value="\n".join(hover_content),
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
        trigger_characters=[".", "'", '"', "@"],
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

            key = CONFIG.cite_prefix + k
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
