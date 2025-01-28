import re
import logging
from typing import List, Match

from lsprotocol.types import Position
from pygls.workspace import TextDocument
from bibli_ls.bibli_config import CiteConfig

logger = logging.getLogger(__name__)


def clean_list(input: List[str]):
    """Strip and Clear any empty components from the list"""
    return [k.strip() for k in input if k.strip()]


def find_cites(text: str, cite_config: CiteConfig) -> List[Match[str]] | None:
    trigger = cite_config.trigger
    email_positions = [
        (m.start(), m.end()) for m in re.finditer(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", text)
    ]

    # Pattern for citation keys
    pattern = rf"{trigger}([A-Za-z0-9_-]+)"

    cite_match = []
    for match in re.finditer(pattern, text):
        start_pos = match.start()
        is_email = any(start <= start_pos < end for start, end in email_positions)

        if not is_email:
            cite_match.append(match)
    return cite_match


def citekey_at_position(
    doc: TextDocument, position: Position, cite_config: CiteConfig
) -> str | None:
    line = doc.lines[position.line]
    cite_matches = find_cites(line, cite_config)
    if not cite_matches:
        return None

    for match in cite_matches:
        key = match.group(1)
        if position.character >= match.start() and position.character < match.end():
            logger.debug(f"Returning {key}")
            return key

    return None
