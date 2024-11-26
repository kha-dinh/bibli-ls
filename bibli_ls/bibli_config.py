import logging
from dataclasses import dataclass, field

"""Default header"""
DEFAULT_HEADER_FORMAT = [
    "# `{entry_type}` {title}",
    "_{author}_",
    "───────────────────────────────────────────────────────────────────────────────────",
]

"""Default footer"""
DEFAULT_FOOTER_FORMAT = [
    "───────────────────────────────────────────────────────────────────────────────────",
    "\n" + "\t" * 20 + "from `{bibfile}`",
]

"""Default prefix"""
DEFAULT_CITE_PREFIX = "@"

"""Default regex string"""
DEFAULT_CITE_REGEX_STR = r"@([A-Za-z_0-9]+)\b"

"""Default word wrap"""
DEFAULT_WRAP = 80

"""Default character limit"""
DEFAULT_CHAR_LIMIT = 400


@dataclass
class DocFormatingConfig:
    """
    Configs for displaying documentation strings
    """

    wrap: int = DEFAULT_WRAP
    """Line wrap config"""

    character_limit: int = DEFAULT_CHAR_LIMIT
    """Number of characters before trimming"""

    format: str = "list"
    """`list` or `markdown`"""

    show_fields: list[str] = field(default_factory=lambda: [])
    """Filter of bibtex fields to show"""

    header_format: list[str] | str = field(
        default_factory=lambda: DEFAULT_HEADER_FORMAT
    )
    """
    List of Python-style format strings for the header.
    """

    footer_format: list[str] | str = field(
        default_factory=lambda: DEFAULT_FOOTER_FORMAT
    )
    """
    List of Python-style format strings for the footer.
    """


@dataclass
class CiteConfig:
    """
    Configs for citation.
    """

    prefix: str = DEFAULT_CITE_PREFIX
    """Prefix to begin the citation."""

    regex: str = DEFAULT_CITE_REGEX_STR
    """Regex string to find the citation."""


@dataclass
class HoverConfig:
    """
    Configs for `textDocument/hover`.
    """

    doc_format: DocFormatingConfig = field(default_factory=lambda: DocFormatingConfig())
    """
    see DocFormatingConfig
    """


@dataclass
class CompletionConfig:
    """
    Configs for `textDocument/completion`.
    """

    doc_format: DocFormatingConfig = field(default_factory=lambda: DocFormatingConfig())


@dataclass
class BackendConfig:
    """
    Config for backends
    """

    backend_type: str = "bibfile"
    """Type of backend `bibfile` or `zotero_api`"""

    library_id: str = ""
    """`zotero_api` only: Online library ID"""

    library_type: str = "user"
    """`zotero_api` only: Online library type"""

    api_key: str | None = None
    """`zotero_api` only: API key """

    bibfiles: list[str] = field(default_factory=lambda: [])
    """`bibfile` only: List of bibfile paths to load"""


# TODO: Is there a better way to do this?
EXPECTED_VALUES = {
    "backend_type": ["zotero_api", "bibfile"],
    "library_type": ["user", "group"],
    "doc_format.format": ["table", "list"],
}


@dataclass
class BibliTomlConfig:
    """
    All configurations used by bibli
    """

    backends: dict[str, BackendConfig] = field(default_factory=lambda: {})
    """Dictionary of backend configs"""

    hover: HoverConfig = field(default_factory=lambda: HoverConfig())
    """See `HoverConfig`"""

    completion: CompletionConfig = field(default_factory=lambda: CompletionConfig())
    """See `CompletionConfig`"""

    cite: CiteConfig = field(default_factory=lambda: CiteConfig())
    """See `CiteConfig`"""

    def check_expected(self, field, value) -> bool:
        if value not in EXPECTED_VALUES[field]:
            logging.error(
                f"Unexpected value in {field}: {value}",
            )
            return False
        return True

    def sanitize(self) -> bool:
        valid = True
        for _, v in self.backends.items():
            valid |= self.check_expected("backend_type", v.backend_type)
            match v.backend_type:
                case "zotero_api":
                    valid |= self.check_expected("library_type", v.library_type)
                case "bibfile":
                    pass

        valid |= self.check_expected("doc_format.format", self.hover.doc_format.format)

        valid |= self.check_expected(
            "doc_format.format", self.completion.doc_format.format
        )

        return valid
