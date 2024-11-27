import os
from pathlib import Path
from bibtexparser.middlewares.latex_encoding import logging
from bibtexparser.writer import Library
from lsprotocol.types import MessageType
from pygls.lsp.server import LanguageServer
from pyzotero.zotero import bibtexparser
from bibli_ls.backends.backend import BibliBackend
from bibli_ls.bibli_config import BackendConfig
from bibli_ls.database import BibliLibrary


class BibfileBackend(BibliBackend):
    def __init__(self, config: BackendConfig, ls: LanguageServer) -> None:
        super().__init__(config, ls)

        """TODO: Get all bibtex files found if config is not given."""
        if config.bibfiles == []:
            logging.warning("No bibfile found.", MessageType.Warning)

    def get_libraries(self):
        libraries = []
        for bibfile_path in self._config.bibfiles:
            if not os.path.isabs(bibfile_path) and self._ls.workspace.root_path:
                bibfile_path = os.path.join(self._ls.workspace.root_path, bibfile_path)

            with open(bibfile_path, "r") as bibtex_file:
                library: Library = bibtexparser.parse_string(bibtex_file.read())
                len = library.entries.__len__()
                logging.info(f"Loaded {len} entries from `{bibfile_path}`")
                libraries.append(
                    BibliLibrary(
                        library.blocks,
                        Path(bibfile_path),
                    )
                )
        return libraries
