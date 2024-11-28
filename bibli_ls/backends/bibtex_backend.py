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

logger = logging.getLogger(__name__)


class BibfileBackend(BibliBackend):
    def __init__(self, name: str, config: BackendConfig, ls: LanguageServer) -> None:
        super().__init__(name, config, ls)

        """TODO: Get all bibtex files found if config is not given."""
        if config.bibfiles == []:
            logger.warning("No bibfile found.", MessageType.Warning)

    def get_libraries(self):
        libraries = []
        total_files = len(self._config.bibfiles)
        loaded_files = 0
        total_entries = 0
        self.load_progress_begin(f"{self._config.bibfiles}")
        for bibfile_path in self._config.bibfiles:
            if not os.path.isabs(bibfile_path) and self._ls.workspace.root_path:
                bibfile_path = os.path.join(self._ls.workspace.root_path, bibfile_path)

            with open(bibfile_path, "r") as bibtex_file:
                library: Library = bibtexparser.parse_string(bibtex_file.read())
                total_entries += len(library.entries)

                libraries.append(
                    BibliLibrary(
                        library.blocks,
                        Path(bibfile_path),
                    )
                )
                self.load_progress_update(bibfile_path, loaded_files, total_files)
            loaded_files += 1
        self.load_progress_done(total_entries, f"{self._config.bibfiles}")
        return libraries
