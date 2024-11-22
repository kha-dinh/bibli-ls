from bibtexparser.middlewares.names import List
from pyzotero.zotero import Zotero
from bibtexparser.library import Library
from bibli_ls.backends.backend import BibliBackend
from bibli_ls.bibli_config import BackendZoteroAPIConfig, BibliBibDatabase
from bibli_ls.server import LanguageServerProtocol
from bibtexparser import bibtexparser

# zot = zotero.Zotero(library_id, library_type, api_key)
# we've retrieved the latest five top-level items in our library
# we can print each item's item type and ID


class ZoteroBackend(BibliBackend):
    _zot: Zotero

    def __init__(self, config: BackendZoteroAPIConfig, lsp):
        lsp.show_message(
            f"Initializing zotero API connection library_id `{config.library_id}`, library_type `{config.library_type}`"
        )
        self._zot = Zotero(config.library_id, config.library_type, config.api_key)
        self._lsp = lsp
        # self.print_items()

    def get_libraries(
        self,
    ) -> List[BibliBibDatabase]:
        count = self._zot.count_items()
        loaded = 0
        limit = 100

        library = Library()
        while loaded < count:
            # items = self.items(start=loaded, limit=limit, content="bibtex")
            items = self._zot.items(start=loaded, limit=limit, content="bibtex")

            # if len(items) == 0:
            #     break
            loaded += len(items)
            items_str = "\n".join(items)
            bibtexparser.parse_string(items_str, library=library)

            self._lsp.show_message(
                f"Retrieved {loaded}/{count} entries from library `{self._zot.library_id}`"
            )

        return [BibliBibDatabase(library, None)]
