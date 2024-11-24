from dataclasses import dataclass, field
from bibtexparser.library import Library


DEFAULT_HEADER_FORMAT = [
    "# `{entry_type}` {title}",
    "_{author}_",
    "───────────────────────────────────────────────────────────────────────────────────",
]
DEFAULT_FOOTER_FORMAT = [
    "───────────────────────────────────────────────────────────────────────────────────",
    "\n" + "\t" * 20 + "from `{bibfile}`",
]
DEFAULT_CITE_PREFIX = "@"
DEFAULT_CITE_REGEX_STR = r"@([A-Za-z_0-9]+)\b"

DEFAULT_WRAP = 80
DEFAULT_CHAR_LIMIT = 400
# cite_regex = re.compile(prefix + "[A-Za-z_0-9]*$")


@dataclass
class BibliBibDatabase:
    library: Library
    path: str | None


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
    footer_format: list[str] | str = field(
        default_factory=lambda: DEFAULT_FOOTER_FORMAT
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
class BackendConfig:
    backend_type: str = "bibfile"
    library_id: str = ""
    library_type: str = "user"
    api_key: str | None = None
    bibfiles: list[str] = field(default_factory=lambda: [])


@dataclass
class BibliTomlConfig:
    """Runtime configurations used by bibli in one place"""

    backend: dict[str, BackendConfig] = field(default_factory=lambda: {})
    bibfiles: list[str] = field(default_factory=lambda: [])
    hover: HoverConfig = field(default_factory=lambda: HoverConfig())
    completion: CompletionConfig = field(default_factory=lambda: CompletionConfig())
    cite: CiteConfig = field(default_factory=lambda: CiteConfig())
