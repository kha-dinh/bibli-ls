import logging
import os.path
from pathlib import Path
from typing import Any, List, Optional, Union

import bibtexparser
from lsprotocol import types
from py_markdown_table.markdown_table import markdown_table
from pygls.protocol.language_server import LanguageServerProtocol
from pygls.server import LanguageServer


class BibliLanguageServerProtocol(LanguageServerProtocol):
    """Override some built-in functions."""

    _server: "BibliLanguageServer"


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
    # protocol_cls=JediLanguageServerProtocol,
)


@SERVER.feature(types.TEXT_DOCUMENT_HOVER)
def hover(self, params: types.HoverParams):
    pos = params.position
    document_uri = params.text_document.uri
    document = self.workspace.get_text_document(document_uri)

    root_path = self.workspace.root_path
    logging.log(logging.DEBUG, document.path)
    logging.log(logging.DEBUG, root_path)

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
    logging.log(logging.ERROR, "bibfile:" + bib_path)
    logging.log(logging.ERROR, "Selected word:" + word)
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
                    f"_{entry['author']}_",
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
                return types.Hover(
                    contents=types.MarkupContent(
                        kind=types.MarkupKind.Markdown,
                        value="\n".join(hover_content),
                    ),
                    range=types.Range(
                        start=types.Position(line=pos.line, character=0),
                        end=types.Position(line=pos.line + 1, character=0),
                    ),
                )
            return None
