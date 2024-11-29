from abc import abstractmethod
from bibtexparser.middlewares.names import List
from lsprotocol.types import (
    WorkDoneProgressBegin,
    WorkDoneProgressEnd,
    WorkDoneProgressReport,
)
from pygls.lsp.server import LanguageServer
from pygls.progress import Progress

from bibli_ls.bibli_config import BackendConfig
from bibli_ls.database import BibliLibrary
from bibli_ls.utils import show_message


class BibliBackend:
    backend_type: str
    _config: BackendConfig
    _ls: LanguageServer
    _name: str

    def __init__(self, name: str, config: BackendConfig, ls: LanguageServer):
        self._config = config
        self._ls = ls
        self._name = name

    @abstractmethod
    def get_libraries(self) -> List[BibliLibrary]:
        """Return the libraries based on backend config"""
        pass

    def load_progress_begin(self, location):
        self._progress = Progress(self._ls.protocol)
        self._progress.create(self._name)

        self._progress.begin(
            self._name,
            WorkDoneProgressBegin(
                title=f"Retriving backend type `{self._config.backend_type}` from `{location}`",
                # message="libraries loaded",
            ),
        )

    def load_progress_update(self, msg, loaded, total):
        self._progress.report(
            self._name,
            WorkDoneProgressReport(
                message=msg,
                percentage=int(loaded * 100 / total),
            ),
        )

    def load_progress_done(self, loaded, location):
        show_message(self._ls, f"Loaded {loaded} entries from `{location}`")
        self._progress.end(
            self._name,
            WorkDoneProgressEnd(message="Done"),
        )
