from abc import abstractmethod
from bibtexparser import Library
from bibtexparser.middlewares.names import List
from pygls.protocol.language_server import LanguageServerProtocol

from bibli_ls.bibli_config import BackendConfig, BibliBibDatabase


class BibliBackend:
    backend_type: str
    backend_config: BackendConfig
    _lsp: LanguageServerProtocol

    def __init__(self, lsp: LanguageServerProtocol):
        self._lsp = lsp

    @abstractmethod
    def get_libraries(self) -> List[BibliBibDatabase]:
        pass
