import logging
import multiprocessing
import os
from multiprocessing.pool import AsyncResult
from pathlib import Path

from bibtexparser import bibtexparser
from bibtexparser.library import Library
from bibtexparser.middlewares.names import List
from lsprotocol.types import (
    WorkDoneProgressBegin,
    WorkDoneProgressEnd,
    WorkDoneProgressReport,
)
from pygls.lsp.server import LanguageServer
from pygls.progress import Progress
from pyzotero.zotero import Zotero

from bibli_ls.backends.backend import BibliBackend
from bibli_ls.bibli_config import BackendConfig
from bibli_ls.database import BibliLibrary

logger = logging.getLogger(__name__)


class ZoteroBackend(BibliBackend):
    _zot: Zotero

    def __init__(self, config: BackendConfig, ls: LanguageServer):
        super().__init__(config, ls)
        if config.library_id == "":
            logger.error("Library ID not specified")
            return

        if config.api_key is None:
            logger.error("API key not specified")
            return

        logger.info(
            f"Initializing zotero API connection library_id `{config.library_id}`, library_type `{config.library_type}`",
        )
        self._zot = Zotero(config.library_id, config.library_type, config.api_key)

    def get_libraries(
        self,
    ):
        count = self._zot.count_items()
        loaded = 0
        limit = 100

        library = Library()
        pool = multiprocessing.Pool(16)

        progress = Progress(self._ls.protocol)
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
            lib = bibtexparser.parse_string(items_str)

            for entry in lib.entries_dict.values():
                if entry.fields_dict.get("author") and entry.fields_dict.get("title"):
                    library.add(entry)

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
        root_path = self._ls.workspace.root_path
        cache_file = None
        if root_path:
            cache_file = os.path.join(root_path, filename)
            logger.info(f"Writing to bibfile to `{cache_file}`")
            bibtexparser.write_file(cache_file, library)

        return [
            BibliLibrary(
                library.blocks,
                Path(cache_file) if cache_file else None,
            )
        ]
