from bibtexparser.model import Entry, Field
from lsprotocol.types import Position
import re
from pygls.workspace import TextDocument

from .bibli_config import BibliTomlConfig


def prefix_word_at_position(
    doc: TextDocument, position: Position, prefix: str
) -> str | None:
    re_start_word = re.compile(prefix + "[A-Za-z_0-9]*$")

    try:
        word = doc.word_at_position(position, re_start_word=re_start_word)
    except IndexError:
        word = None

    return word


def process_bib_entry(entry: Entry, config: BibliTomlConfig):
    replace_list = ["{{", "}}", "\\vphantom", "\\{", "\\}"]
    for f in entry.fields:
        if isinstance(f.value, str):
            for r in replace_list:
                f.value = f.value.replace(r, "")

            f.value = f.value.replace("\n", " ")
            if len(f.value) > config.hover.character_limit:
                f.value = f.value[: config.hover.character_limit] + "..."

            if f.key == "url":
                f.value = f"<{f.value}>"

            entry.set_field(Field(f.key, f.value))
