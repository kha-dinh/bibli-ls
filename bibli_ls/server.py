import logging
import os.path
from pathlib import Path
from typing import Any, Optional, Pattern

import re
import bibtexparser
import tomllib
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
)
from py_markdown_table.markdown_table import markdown_table
from pygls.protocol.language_server import LanguageServerProtocol, lsp_method
from pygls.server import LanguageServer
from pygls.workspace import TextDocument


class BibFile(bibtexparser.bibdatabase.BibDatabase):
    def __init__(self):
        self.path = Path()
        super().__init__()


LIBRARIES: dict[str, BibDatabase] = dict()
CONFIG: Optional[dict] = None
SYMBOLS_REGEX: Optional[Pattern] = None


class BibliLanguageServerProtocol(LanguageServerProtocol):
    """Override some built-in functions."""

    _server: "BibliLanguageServer"

    @lsp_method(INITIALIZE)
    def lsp_initialize(self, params: InitializeParams) -> InitializeResult:
        logging.error(params.root_path)

        if params.root_path:
            config_file = os.path.join(params.root_path, ".bibli.toml")
            with open(config_file, "r") as f:
                global CONFIG
                global SYMBOLS_REGEX
                global LIBRARIES

                CONFIG = tomllib.loads(f.read())
                logging.error("Loaded configs from " + config_file)

                for bibfile in CONFIG["bibfiles"]:
                    bibfile_path = os.path.join(params.root_path, bibfile)
                    with open(bibfile_path) as bibtex_file:
                        library: BibDatabase = bibtexparser.load(bibtex_file)
                        len = library.get_entry_list().__len__()
                        logging.error(f"loaded {len} entries from {bibfile_path}")
                        # global_library.update(library.get_entry_dict())
                        LIBRARIES[bibfile_path] = library

                SYMBOLS_REGEX = re.compile(
                    re.escape(CONFIG["cite_format"]).replace(r"\{\}", r"(\w+)")
                )
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

            table_content = [{"Key": k, "Value": v} for k, v in content.items()]
            # content['url']

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
    CompletionOptions(trigger_characters=[".", "'", '"'], resolve_provider=True),
)
def completion(
    server: BibliLanguageServer, params: CompletionParams
) -> Optional[CompletionList]:
    """Returns completion items."""
    document = server.workspace.get_text_document(params.text_document.uri)
    completion_items = []
    for _path, library in LIBRARIES.items():
        for k, v in library.get_entry_dict().items():
            completion_items.append(
                CompletionItem(
                    k,
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
