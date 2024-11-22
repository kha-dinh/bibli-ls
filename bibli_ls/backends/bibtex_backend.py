import os
from bibtexparser.writer import Library
from lsprotocol.types import MessageType
from pygls.protocol.language_server import LanguageServerProtocol
from pyzotero.zotero import bibtexparser
from bibli_ls.backends.backend import BibliBackend
from bibli_ls.bibli_config import BackendBibfileConfig, BibliBibDatabase


class BibfileBackend(BibliBackend):
    _lsp: LanguageServerProtocol
    _config: BackendBibfileConfig

    def __init__(
        self, config: BackendBibfileConfig, lsp: LanguageServerProtocol
    ) -> None:
        self._config = config
        """TODO: Get all bibtex files found if config is not given."""
        if config.bibfiles == []:
            lsp.show_message("No bibfile found.", MessageType.Warning)

        super().__init__(lsp)

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
