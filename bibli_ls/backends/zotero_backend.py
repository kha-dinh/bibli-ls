from bibtexparser.middlewares.names import List
from lsprotocol.types import (
    WorkDoneProgressBegin,
    WorkDoneProgressEnd,
    WorkDoneProgressReport,
)
from pygls.progress import Progress
from pyzotero.zotero import Zotero
from bibtexparser.library import Library
from bibli_ls.backends.backend import BibliBackend
from bibli_ls.bibli_config import BackendZoteroAPIConfig, BibliBibDatabase
from bibtexparser import bibtexparser


class ZoteroBackend(BibliBackend):
    _zot: Zotero

    def __init__(self, config: BackendZoteroAPIConfig, lsp):
        lsp.show_message(
            f"Initializing zotero API connection library_id `{config.library_id}`, library_type `{config.library_type}`"
        )
        self._zot = Zotero(config.library_id, config.library_type, config.api_key)
        self._lsp = lsp

    def get_libraries(
        self,
    ) -> List[BibliBibDatabase]:
        count = self._zot.count_items()
        loaded = 0
        limit = 50

        library = Library()

        progress = Progress(self._lsp)
        progress.create("bibli")
        progress.begin(
            "bibli",
            WorkDoneProgressBegin(
                title=f"Retriving online library from `{self._zot.library_id}`",
                message="message",
            ),
        )
        while loaded < count:
            items = self._zot.items(start=loaded, limit=limit, content="bibtex")
            loaded += len(items)
            items_str = "\n".join(items)
            bibtexparser.parse_string(items_str, library=library)

            progress.report(
                "bibli",
                WorkDoneProgressReport(
                    message="Libraries loaded",
                    percentage=int(loaded * 100 / count),
                ),
            )
        progress.end(
            "bibli",
            WorkDoneProgressEnd(message="Done"),
        )

        return [BibliBibDatabase(library, None)]
