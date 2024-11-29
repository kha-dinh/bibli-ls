import logging
import os
from pathlib import Path

from bibtexparser import bibtexparser
from bibtexparser.middlewares.names import List
from pygls.lsp.server import LanguageServer
from pyzotero.zotero import Zotero

from bibli_ls.backends.backend import BibliBackend
from bibli_ls.backends.bibtex_backend import BibfileBackend
from bibli_ls.bibli_config import BackendConfig
from bibli_ls.database import BibliLibrary
from bibli_ls.utils import show_message

logger = logging.getLogger(__name__)


class ZoteroBackend(BibliBackend):
    _zot: Zotero

    def __init__(self, name: str, config: BackendConfig, ls: LanguageServer):
        super().__init__(name, config, ls)
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

    def get_cache_file_path(self) -> str | None:
        if not self._ls.workspace.root_path:
            return None

        filename = f".{self._name}_{self._zot.library_type}_{self._zot.library_id}.bib"
        return os.path.join(self._ls.workspace.root_path, filename)

    def get_libraries_cached(self) -> List[BibliLibrary]:
        cache_file = self.get_cache_file_path()

        if cache_file and os.path.exists(Path(cache_file)):
            show_message(self._ls, f"Loading from cached library `{cache_file}`")
            bibtex_backend = BibfileBackend(
                "cache_file",
                BackendConfig(backend_type="bibfile", bibfiles=[cache_file]),
                self._ls,
            )
            return bibtex_backend.get_libraries()
        else:
            return self.get_libraries()

    def get_libraries(self):
        count = self._zot.count_items()
        loaded = 0
        limit = 100

        show_message(
            self._ls,
            f"Fetching `{count}` items from `{self._zot.library_type}` library `{self._zot.library_id}`",
        )

        self.library = BibliLibrary(path=self.get_cache_file_path())

        self.load_progress_begin(self._zot.library_id)

        for i in range(0, count, limit):
            items = self._zot.items(start=i, limit=limit, content="bibtex")
            logger.error(items)
            loaded += len(items)
            items_str = "\n".join(items)
            bibtexparser.parse_string(items_str, library=self.library)
            self.load_progress_update(self._zot.library_id, loaded, count)

        self.load_progress_done(loaded, self._zot.library_id)

        # TODO: Filter out the empty entries

        self.load_progress_done(loaded, self._zot.library_id)

        cache_file = self.get_cache_file_path()
        # Writing to file
        if cache_file:
            show_message(self._ls, f"Writing to bibfile to `{cache_file}`")
            bibtexparser.write_file(cache_file, self.library)

        return [self.library]
