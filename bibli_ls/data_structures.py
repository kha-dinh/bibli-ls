from dataclasses import dataclass
from bibtexparser.library import Library


@dataclass()
class BibliBibDatabase:
    library: Library
    path: str | None
