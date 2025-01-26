import logging
from dataclasses import dataclass, field

from attr import asdict

logger = logging.getLogger(__name__)


@dataclass
class Unionable:
    def __or__(self, other):
        return self.__class__(**asdict(self) | asdict(other))


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


"""Default cite trigger"""
DEFAULT_CITE_PRESET = "pandoc"

"""Default word wrap"""
DEFAULT_WRAP = 80

"""Default character limit"""
DEFAULT_CHAR_LIMIT = 400


@dataclass
class ViewConfig:
    """
    Configs for viewing documents
    """

    viewer: str = "browser"
    """`zotero`, `zotero_bbt` or `browser`"""


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
class CiteConfig(Unionable):
    """
    Configs for citation.
    """

    preset: str = "pandoc"
    """Trigger completion and also marks the beginning of citation key."""

    trigger: str = "@"
    """Trigger completion and also marks the beginning of citation key."""

    post_trigger: str = ","
    """Trigger completion and also marks the beginning of citation key."""

    prefix: str = "["
    r"""
    Prefix to begin the citation (must be updated if trigger is updated). 
    Brackets (`([{`) should be escaped (`\(\[\{`).
    """

    postfix: str = "]"
    r"""Prefix to begin the citation.
    Brackets (`])}`) should be escaped (`\]\)\}`).
    """

    separator: str = ";"
    r"""separator between citations
    Brackets (`])}`) should be escaped (`\]\)\}`).
    """

    regex: str = ""
    """Regex string to find the *block* of citation (`[@cite1; @cite2]`). 
    This is to be built automatically based on prefix and postfix.
    Configuring this is NOT supported yet."""


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


def build_cite_regex(postfix, prefix):
    return f"\\{postfix}([\\w\\W]+?)\\{prefix}"


PANDOC_CITE_PRESET: CiteConfig = CiteConfig(
    preset="pandoc",
    trigger="@",
    post_trigger=",",
    prefix="[",
    postfix="]",
    separator=";",
    regex=build_cite_regex("[", "]"),
)


CITE_PRESETS = {"pandoc": PANDOC_CITE_PRESET}


# TODO: Is there a better way to do this?
EXPECTED_VALUES = {
    "backend_type": ["zotero_api", "bibfile"],
    "library_type": ["user", "group"],
    "doc_format.format": ["table", "list"],
    "view.viewer": ["browser", "zotero", "zotero_bbt"],
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

    cite: CiteConfig = field(default_factory=lambda: CITE_PRESETS[DEFAULT_CITE_PRESET])
    """See `CiteConfig`"""

    view: ViewConfig = field(default_factory=lambda: ViewConfig())
    """See `ViewingConfig`"""

    def check_expected(self, field, value) -> bool:
        if value not in EXPECTED_VALUES[field]:
            logger.error(
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

        valid |= self.check_expected("view.viewer", self.view.viewer)

        valid |= self.check_expected(
            "doc_format.format", self.completion.doc_format.format
        )

        # Apply preset and user configs
        if self.cite.preset != DEFAULT_CITE_PRESET:
            if not CITE_PRESETS.get(self.cite.preset):
                logger.error(f"Unknown preset {self.cite.preset}")
                return False
            self.cite = CITE_PRESETS[self.cite.preset] | self.cite

        # Recompute cite regex to make sure
        self.cite.regex = build_cite_regex(self.cite.prefix, self.cite.postfix)
        return valid
