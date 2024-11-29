from pathlib import Path
from typing import Union

from bibtexparser.library import Library
from bibtexparser.model import Block, Entry
from typing_extensions import List


class BibliLibrary(Library):
    path: Path | None

    def __init__(self, blocks: Union[List[Block], None] = None, path=None):
        super().__init__(blocks)
        self.path = path


class BibliBibDatabase:
    libraries: dict[str, list[BibliLibrary]]

    def __init__(self) -> None:
        self.libraries = {}

    def find_in_libraries(
        self, key: str
    ) -> tuple[Entry, BibliLibrary] | tuple[None, None]:
        for libs in self.libraries.values():
            for lib in libs:
                if lib.entries_dict.__contains__(key):
                    return lib.entries_dict[key], lib
        return None, None
