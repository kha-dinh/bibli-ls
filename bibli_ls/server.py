import logging
import os.path
from pathlib import Path
from typing import Any, Optional

import tomllib

import bibtexparser
from lsprotocol.types import (
    INITIALIZE,
    TEXT_DOCUMENT_HOVER,
    Hover,
    HoverParams,
    InitializeParams,
    InitializeResult,
    MarkupContent,
    MarkupKind,
    Position,
    Range,
)
from py_markdown_table.markdown_table import markdown_table
from pygls.protocol.language_server import LanguageServerProtocol, lsp_method
from pygls.server import LanguageServer


class BibFile(bibtexparser.bibdatabase.BibDatabase):
    _path = ""


bibfiles = []


class BibliLanguageServerProtocol(LanguageServerProtocol):
    """Override some built-in functions."""

    _server: "BibliLanguageServer"

    @lsp_method(INITIALIZE)
    def lsp_initialize(self, params: InitializeParams) -> InitializeResult:
        logging.error(params.root_path)

        if params.root_path:
            config_file = os.path.join(params.root_path, ".bibli.toml")
            with open(config_file, "r") as f:
                data = tomllib.loads(f.read())
                logging.error(data)
                for bibfile in data["bibfiles"]:
                    bibfile_path = os.path.join(params.root_path, bibfile)
                    with open(bibfile_path) as bibtex_file:
                        library = bibtexparser.load(bibtex_file)
                        logging.error(library.entries_dict)

        initialize_result: InitializeResult = super().lsp_initialize(params)
        return initialize_result

    #     """Override built-in initialization.
    #
    #     Here, we can conditionally register functions to features based
    #     on client capabilities and initializationOptions.
    #     """

    # server = self._server
    # try:
    #     server.initialization_options = initialization_options_converter.structure(
    #         {}
    #         if params.initialization_options is None
    #         else params.initialization_options,
    #         InitializationOptions,
    #     )
    # except cattrs.BaseValidationError as error:
    #     msg = (
    #         "Invalid InitializationOptions, using defaults:"
    #         f" {cattrs.transform_error(error)}"
    #     )
    #     server.show_message(msg, msg_type=MessageType.Error)
    #     server.show_message_log(msg, msg_type=MessageType.Error)
    #     server.initialization_options = InitializationOptions()


class BibliLanguageServer(LanguageServer):
    """Jedi language server.

    :attr initialization_options: initialized in lsp_initialize from the
        protocol_cls.
    :attr project: a Jedi project. This value is created in
        `JediLanguageServerProtocol.lsp_initialize`.
    """

    # initialization_options: InitializationOptions
    # project: Optional[Project]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)


SERVER = BibliLanguageServer(
    name="bibli-language-server",
    version="0.1",
    protocol_cls=BibliLanguageServerProtocol,
)


@SERVER.feature(TEXT_DOCUMENT_HOVER)
def hover(ls: LanguageServer, params: HoverParams):
    pos = params.position
    document_uri = params.text_document.uri
    document = ls.workspace.get_text_document(document_uri)

    # root_path = ls.workspace.root_path
    # logging.log(logging.DEBUG, document.path)
    # logging.log(logging.DEBUG, root_path)

    path = Path(document.path)
    upper_dir = os.path.dirname(path)

    # try:
    #     line = document.lines[pos.line]
    # except IndexError:
    #     return None

    try:
        word = document.word_at_position(pos)
    except IndexError:
        return None

    bib_path = os.path.join(upper_dir, "references.bib")
    logging.error("Found bibfile:" + bib_path)
    logging.error("Selected word:" + word)
    library = None
    if os.path.exists(bib_path):
        with open(bib_path) as bibtex_file:
            library = bibtexparser.load(bibtex_file)
            entry = library.entries_dict.get(word)
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

                # for k, v in content.items():
                #     hover_content.append(f"| {k} | {v} |")
                # hover_content.append(str(entry))
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
