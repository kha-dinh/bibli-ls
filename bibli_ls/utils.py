import re
from typing import List

from bibtexparser.exceptions import ParserStateException, ParsingException
from bibtexparser.model import Entry, Field
from lsprotocol.types import MessageType, Position, ShowMessageParams
from pygls.lsp.server import LanguageServer
from pygls.workspace import TextDocument
import logging
from typing_extensions import assert_type
import requests

from bibli_ls.database import BibliBibDatabase


from .bibli_config import BibliTomlConfig, DocFormatingConfig

logger = logging.getLogger(__name__)


def show_message(
    ls: LanguageServer, msg: str, msg_type: MessageType = MessageType.Info
):
    ls.window_show_message(
        ShowMessageParams(
            msg_type,
            msg,
        )
    )


def get_item_attachments_bbt(cite: str):
    url = "http://localhost:23119/better-bibtex/json-rpc"

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    payload = {"jsonrpc": "2.0", "method": "item.attachments", "params": [cite]}

    attachments = []
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    for attachment in data["result"]:
        attachments.append(attachment["open"])

    return attachments


def get_cite_uri(
    db: BibliBibDatabase, cite: str, config: BibliTomlConfig
) -> str | None:
    (entry, _) = db.find_in_libraries(remove_trigger(cite, config))

    if not entry:
        return None

    uri = None
    match config.view.viewer:
        case "browser":
            if entry.fields_dict.get("url"):
                uri = entry.fields_dict["url"].value
        case "zotero":
            uri = f"zotero://select/items/{cite}"

        case "zotero_bbt":
            # Hacky way to  use better-bibtex JSON RPC support to get the attachment
            # uri. See more:
            # - https://retorque.re/zotero-better-bibtex/exporting/json-rpc/index.html
            # - https://github.com/retorquere/zotero-better-bibtex/issues/1347
            uri = get_item_attachments_bbt(cite)[0]
    return uri


def remove_trigger(cite: str, config: BibliTomlConfig):
    return cite.replace(config.cite.trigger, "")


# Clear any empty components from the list
def clean_list(input: List):
    return [k.strip() for k in input if k.strip()]


def cite_at_position(
    doc: TextDocument, position: Position, config: BibliTomlConfig
) -> str | None:
    line = doc.lines[position.line]
    assert config.cite.regex

    for match in re.finditer(config.cite.regex, line):
        (cite_start, cite_end) = match.span(1)
        keys = match.group(1).split(config.cite.separator)
        keys = clean_list(keys)
        processed_keys = []
        tmp = []

        # Ignoring the parts before trigger and after post_trigger
        for k in keys:
            split = k.split(config.cite.trigger)
            split = clean_list(split)
            if len(split) == 2:
                tmp.append(config.cite.trigger + split[1])
            elif len(split) == 1:
                tmp.append(config.cite.trigger + split[0])
            else:
                raise Exception("Parsing error")
        processed_keys = tmp

        tmp = []
        for k in processed_keys:
            if not config.cite.post_trigger:
                break
            split = k.split(config.cite.post_trigger)
            split = clean_list(split)
            tmp.append(split[0])
        processed_keys = tmp

        logger.debug(f"Found cites {processed_keys} at pos {position}")
        key_pos = [line.find(k, cite_start, cite_end) for k in processed_keys]

        # Determine which cite is at the cursor
        for k, pos in zip(processed_keys, key_pos):
            if position.character >= pos and position.character < pos + len(k):
                logger.debug(f"Returning {k.strip()}")
                return k.strip()

    return None


def preprocess_bib_entry(entry: Entry, config: DocFormatingConfig):
    replace_list = ["{{", "}}", "\\vphantom", "\\{", "\\}"]
    for f in entry.fields:
        if isinstance(f.value, str):
            for r in replace_list:
                f.value = f.value.replace(r, "")

            f.value = f.value.replace("\n", " ")
            if len(f.value) > config.character_limit:
                f.value = f.value[: config.character_limit] + "..."

            entry.set_field(Field(f.key, f.value))


def build_doc_string(
    entry: Entry, config: DocFormatingConfig, bibfile: str | None = None
):
    import mdformat

    preprocess_bib_entry(entry, config)

    field_dict = {f.key: f.value for f in entry.fields}

    field_dict["entry_type"] = entry.entry_type
    if bibfile:
        field_dict["bibfile"] = bibfile

    doc_string = ""

    while True:
        try:
            if isinstance(config.header_format, List):
                doc_string += "\n".join(config.header_format).format(**field_dict)
            else:
                assert_type(config.header_format, str)
                doc_string += config.header_format.format(**field_dict)
        except KeyError as e:
            # Unknown key in the header format
            field_dict[e.args[0]] = "Unknown"
            continue
        break

    doc_string += "\n"

    # Entry type no longer needed
    field_dict.pop("entry_type")
    if config.show_fields == []:
        show_field_dict = {k: v for k, v in field_dict.items()}
    else:
        show_field_dict = {
            k: v for k, v in field_dict.items() if config.show_fields.count(k) > 0
        }

    match config.format:
        case "table":
            from py_markdown_table.markdown_table import markdown_table

            table_content = [{"Key": k, "Value": v} for k, v in show_field_dict.items()]
            # NOTE: sometimes table formatting fails with long entries
            table = (
                markdown_table(table_content)
                .set_params(
                    row_sep="markdown",
                    padding_weight="right",
                    multiline={
                        "Key": 20,
                        "Value": 80,
                    },
                    quote=False,
                )
                .get_markdown()
            )
            doc_string += table
        case "list":
            for k, v in show_field_dict.items():
                doc_string += f"- __{k}__: {v}\n"

            # Do one last beautifying for list
            doc_string = mdformat.text(
                doc_string,
                options={"wrap": config.wrap},
            )

    while True:
        try:
            if isinstance(config.footer_format, List):
                doc_string += "\n".join(config.footer_format).format(**field_dict)
            else:
                assert_type(config.footer_format, str)
                doc_string += config.footer_format.format(**field_dict)
        except KeyError as e:
            # Unknown key in the header format
            field_dict[e.args[0]] = "Unknown"
            continue
        break

    return doc_string
