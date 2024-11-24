from abc import abstractmethod
from bibtexparser.middlewares.names import List
from pygls.protocol.language_server import LanguageServerProtocol

from bibli_ls.bibli_config import BackendConfig, BibliBibDatabase


class BibliBackend:
    backend_type: str
    _lsp: LanguageServerProtocol
    _config: BackendConfig

    def __init__(self, config: BackendConfig, lsp: LanguageServerProtocol):
        self._lsp = lsp
        self._config = config

    @abstractmethod
    def get_libraries(self) -> List[BibliBibDatabase]:
        """Return the libraries based on backend config"""
        pass
