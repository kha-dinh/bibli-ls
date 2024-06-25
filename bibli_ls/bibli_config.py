from dataclasses import dataclass, field

DEFAULT_HOVER_FORMAT = ["# {entry_type}: {title}\n", "- _{author}_", "---"]
DEFAULT_COMPLETION_DOC_FORMAT = ["# {entry_type}: {title}\n", "_{author}_", "---"]


@dataclass
class HoverConfig:
    wrap: int = 80
    character_limit: int = 400
    format: str = "markdown"
    show_fields: list[str] = field(default_factory=lambda: [])
    format_string: list[str] = field(default_factory=lambda: DEFAULT_HOVER_FORMAT)


@dataclass
class CompletionConfig:
    prefix: str = "@"


@dataclass
class BibliTomlConfig:
    bibfiles: list[str] = field(default_factory=lambda: [])
    hover: HoverConfig = field(default_factory=lambda: HoverConfig())
    completion: CompletionConfig = field(default_factory=lambda: CompletionConfig())
