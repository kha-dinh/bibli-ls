from dataclasses import dataclass, field
from bibtexparser.library import Library


DEFAULT_HEADER_FORMAT = [
    "# `{entry_type}` {title}",
    "_{author}_",
    "───────────────────────────────────────────────────────────────────────────────────",
]
DEFAULT_CITE_PREFIX = "@"
DEFAULT_CITE_REGEX_STR = DEFAULT_CITE_PREFIX + "([A-Za-z_0-9]+)"

DEFAULT_WRAP = 80
DEFAULT_CHAR_LIMIT = 400
# cite_regex = re.compile(prefix + "[A-Za-z_0-9]*$")


@dataclass
class BibliBibDatabase:
    library: Library
    path: str


@dataclass
class DocFormatingConfig:
    """Config for formating a documentation string"""

    wrap: int = DEFAULT_WRAP
    character_limit: int = DEFAULT_CHAR_LIMIT
    format: str = "markdown"
    show_fields: list[str] = field(default_factory=lambda: [])
    header_format: list[str] | str = field(
        default_factory=lambda: DEFAULT_HEADER_FORMAT
    )


@dataclass
class CiteConfig:
    prefix: str = DEFAULT_CITE_PREFIX
    regex: str = DEFAULT_CITE_REGEX_STR


@dataclass
class HoverConfig:
    doc_format: DocFormatingConfig = field(default_factory=lambda: DocFormatingConfig())


@dataclass
class CompletionConfig:
    doc_format: DocFormatingConfig = field(default_factory=lambda: DocFormatingConfig())


@dataclass
class BibliTomlConfig:
    """Runtime configurations used by bibli in one place"""

    bibfiles: list[str] = field(default_factory=lambda: [])
    hover: HoverConfig = field(default_factory=lambda: HoverConfig())
    completion: CompletionConfig = field(default_factory=lambda: CompletionConfig())
    cite: CiteConfig = field(default_factory=lambda: CiteConfig())
