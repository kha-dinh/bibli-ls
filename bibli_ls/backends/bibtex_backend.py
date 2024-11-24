import os
from bibtexparser.writer import Library
from lsprotocol.types import MessageType
from pygls.protocol.language_server import LanguageServerProtocol
from pyzotero.zotero import bibtexparser
from bibli_ls.backends.backend import BibliBackend
from bibli_ls.bibli_config import BackendConfig, BibliBibDatabase


class BibfileBackend(BibliBackend):
    def __init__(self, config: BackendConfig, lsp: LanguageServerProtocol) -> None:
        super().__init__(config, lsp)

        """TODO: Get all bibtex files found if config is not given."""
        if config.bibfiles == []:
            lsp.show_message("No bibfile found.", MessageType.Warning)

    def get_libraries(self):
        libraries = []
        for bibfile_path in self._config.bibfiles:
            if not os.path.isabs(bibfile_path) and self._lsp.workspace.root_path:
                bibfile_path = os.path.join(self._lsp.workspace.root_path, bibfile_path)

            with open(bibfile_path, "r") as bibtex_file:
                library: Library = bibtexparser.parse_string(bibtex_file.read())
                len = library.entries.__len__()
                self._lsp.show_message(f"Loaded {len} entries from `{bibfile_path}`")
                libraries.append(
                    BibliBibDatabase(
                        library,
                        bibfile_path,
                    )
                )
        return libraries
