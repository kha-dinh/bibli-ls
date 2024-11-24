from dataclasses import dataclass, field
from bibtexparser.library import Library
from lsprotocol.types import MessageType
from pygls.protocol.language_server import LanguageServerProtocol


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
    format: str = "list"
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


# TODO: Is there a better way to do this?
EXPECTED_VALUES = {
    "backend_type": ["zotero_api", "bibfile"],
    "library_type": ["user", "group"],
    "doc_format.format": ["table", "list"],
}


@dataclass
class BibliTomlConfig:
    """Runtime configurations used by bibli in one place"""

    backend: dict[str, BackendConfig] = field(default_factory=lambda: {})
    bibfiles: list[str] = field(default_factory=lambda: [])
    hover: HoverConfig = field(default_factory=lambda: HoverConfig())
    completion: CompletionConfig = field(default_factory=lambda: CompletionConfig())
    cite: CiteConfig = field(default_factory=lambda: CiteConfig())

    def check_expected(self, field, value, lsp) -> bool:
        if value not in EXPECTED_VALUES[field]:
            lsp.show_message(
                f"Unexpected value in {field}: {value}",
                MessageType.Error,
            )
            return False
        return True

    def sanitize(self, lsp: LanguageServerProtocol) -> bool:
        valid = True
        for _, v in self.backend.items():
            valid |= self.check_expected("backend_type", v.backend_type, lsp)
            match v.backend_type:
                case "zotero_api":
                    valid |= self.check_expected("library_type", v.library_type, lsp)
                case "bibfile":
                    pass

        valid |= self.check_expected(
            "doc_format.format", self.hover.doc_format.format, lsp
        )

        valid |= self.check_expected(
            "doc_format.format", self.completion.doc_format.format, lsp
        )

        return valid
