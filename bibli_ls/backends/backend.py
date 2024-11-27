from abc import abstractmethod
from bibtexparser.middlewares.names import List
from pygls.lsp.server import LanguageServer

from bibli_ls.bibli_config import BackendConfig
from bibli_ls.database import BibliLibrary


class BibliBackend:
    backend_type: str
    _config: BackendConfig
    _ls: LanguageServer

    def __init__(self, config: BackendConfig, ls: LanguageServer):
        self._config = config
        self._ls = ls

    @abstractmethod
    def get_libraries(self) -> List[BibliLibrary]:
        """Return the libraries based on backend config"""
        pass
