from multiprocessing.pool import AsyncResult
import os
from bibtexparser.middlewares.names import List
from lsprotocol.types import (
    MessageType,
    WorkDoneProgressBegin,
    WorkDoneProgressEnd,
    WorkDoneProgressReport,
)
from pygls.progress import Progress
from pyzotero.zotero import Zotero
from bibtexparser.library import Library
from bibli_ls.backends.backend import BibliBackend
from bibli_ls.bibli_config import BackendConfig, BibliBibDatabase
from bibtexparser import bibtexparser

import multiprocessing


class ZoteroBackend(BibliBackend):
    _zot: Zotero

    def __init__(self, config: BackendConfig, lsp):
        super().__init__(config, lsp)
        if config.library_id == "":
            lsp.show_message("Library ID not specified", MessageType.Error)
            return

        if config.api_key is None:
            lsp.show_message("API key not specified", MessageType.Error)
            return
        lsp.show_message(
            f"Initializing zotero API connection library_id `{config.library_id}`, library_type `{config.library_type}`"
        )
        self._zot = Zotero(config.library_id, config.library_type, config.api_key)

    def get_libraries(
        self,
    ) -> List[BibliBibDatabase]:
        count = self._zot.count_items()
        loaded = 0
        limit = 10

        library = Library()
        pool = multiprocessing.Pool(16)

        progress = Progress(self._lsp)
        progress.create("bibli")
        progress.begin(
            "bibli",
            WorkDoneProgressBegin(
                title=f"Retriving online library from `{self._zot.library_id}`",
                message="libraries loaded",
            ),
        )

        results: List[AsyncResult] = []
        for i in range(0, count, limit):
            results.append(
                pool.apply_async(
                    self._zot.items,
                    kwds={"start": i, "limit": limit, "content": "bibtex"},
                )
            )

        for r in results:
            items = r.get()
            loaded += len(items)
            items_str = "\n".join(items)
            bibtexparser.parse_string(items_str, library=library)

            progress.report(
                "bibli",
                WorkDoneProgressReport(
                    message="libraries loaded",
                    percentage=int(loaded * 100 / count),
                ),
            )

        progress.end(
            "bibli",
            WorkDoneProgressEnd(message="Done"),
        )

        pool.close()
        pool.join()

        # Writing to file
        filename = f".zotero_api_{self._zot.library_id}.bib"
        root_path = self._lsp.workspace.root_path
        cache_file = None
        if root_path:
            cache_file = os.path.join(root_path, filename)
            self._lsp.show_message(f"Writing to bibfile to `{cache_file}`")
            bibtexparser.write_file(cache_file, library)

        return [BibliBibDatabase(library, cache_file)]
