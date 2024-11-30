# Table of Contents

* [bibli\_config](#bibli_config)
  * [logger](#bibli_config.logger)
  * [DEFAULT\_HEADER\_FORMAT](#bibli_config.DEFAULT_HEADER_FORMAT)
  * [DEFAULT\_FOOTER\_FORMAT](#bibli_config.DEFAULT_FOOTER_FORMAT)
  * [DEFAULT\_CITE\_TRIGGER](#bibli_config.DEFAULT_CITE_TRIGGER)
  * [DEFAULT\_CITE\_PREFIX](#bibli_config.DEFAULT_CITE_PREFIX)
  * [DEFAULT\_CITE\_POSTFIX](#bibli_config.DEFAULT_CITE_POSTFIX)
  * [DEFAULT\_CITE\_SEPARATOR](#bibli_config.DEFAULT_CITE_SEPARATOR)
  * [DEFAULT\_CITE\_REGEX\_STR](#bibli_config.DEFAULT_CITE_REGEX_STR)
  * [DEFAULT\_WRAP](#bibli_config.DEFAULT_WRAP)
  * [DocFormatingConfig](#bibli_config.DocFormatingConfig)
    * [wrap](#bibli_config.DocFormatingConfig.wrap)
    * [character\_limit](#bibli_config.DocFormatingConfig.character_limit)
    * [format](#bibli_config.DocFormatingConfig.format)
    * [show\_fields](#bibli_config.DocFormatingConfig.show_fields)
    * [header\_format](#bibli_config.DocFormatingConfig.header_format)
    * [footer\_format](#bibli_config.DocFormatingConfig.footer_format)
  * [CiteConfig](#bibli_config.CiteConfig)
    * [trigger](#bibli_config.CiteConfig.trigger)
    * [prefix](#bibli_config.CiteConfig.prefix)
    * [postfix](#bibli_config.CiteConfig.postfix)
    * [separator](#bibli_config.CiteConfig.separator)
    * [regex](#bibli_config.CiteConfig.regex)
  * [HoverConfig](#bibli_config.HoverConfig)
    * [doc\_format](#bibli_config.HoverConfig.doc_format)
  * [CompletionConfig](#bibli_config.CompletionConfig)
  * [BackendConfig](#bibli_config.BackendConfig)
    * [backend\_type](#bibli_config.BackendConfig.backend_type)
    * [library\_id](#bibli_config.BackendConfig.library_id)
    * [library\_type](#bibli_config.BackendConfig.library_type)
    * [api\_key](#bibli_config.BackendConfig.api_key)
    * [bibfiles](#bibli_config.BackendConfig.bibfiles)
  * [BibliTomlConfig](#bibli_config.BibliTomlConfig)
    * [backends](#bibli_config.BibliTomlConfig.backends)
    * [hover](#bibli_config.BibliTomlConfig.hover)
    * [completion](#bibli_config.BibliTomlConfig.completion)
    * [cite](#bibli_config.BibliTomlConfig.cite)

<a id="bibli_config"></a>

# bibli\_config

<a id="bibli_config.logger"></a>

#### logger

```python
logger = logging.getLogger(__name__)
```

Default header

<a id="bibli_config.DEFAULT_HEADER_FORMAT"></a>

#### DEFAULT\_HEADER\_FORMAT

```python
DEFAULT_HEADER_FORMAT = [
    "# `{entry_type}` {title}",
    "_{author}_",
    "─────────────────── ...
```

Default footer

<a id="bibli_config.DEFAULT_FOOTER_FORMAT"></a>

#### DEFAULT\_FOOTER\_FORMAT

```python
DEFAULT_FOOTER_FORMAT = [
    "───────────────────────────────────────────────────────────────────── ...
```

Default cite trigger

<a id="bibli_config.DEFAULT_CITE_TRIGGER"></a>

#### DEFAULT\_CITE\_TRIGGER

```python
DEFAULT_CITE_TRIGGER = "@"
```

Default prefix

<a id="bibli_config.DEFAULT_CITE_PREFIX"></a>

#### DEFAULT\_CITE\_PREFIX

```python
DEFAULT_CITE_PREFIX = r"\["
```

Default postfix

<a id="bibli_config.DEFAULT_CITE_POSTFIX"></a>

#### DEFAULT\_CITE\_POSTFIX

```python
DEFAULT_CITE_POSTFIX = r"\]"
```

Default separator

<a id="bibli_config.DEFAULT_CITE_SEPARATOR"></a>

#### DEFAULT\_CITE\_SEPARATOR

```python
DEFAULT_CITE_SEPARATOR = r","
```

Default cite regex string

<a id="bibli_config.DEFAULT_CITE_REGEX_STR"></a>

#### DEFAULT\_CITE\_REGEX\_STR

```python
DEFAULT_CITE_REGEX_STR = rf"{DEFAULT_CITE_PREFIX}([\w\W]+?){DEFAULT_CITE_POSTFIX}"
```

Default word wrap

<a id="bibli_config.DEFAULT_WRAP"></a>

#### DEFAULT\_WRAP

```python
DEFAULT_WRAP = 80
```

Default character limit

<a id="bibli_config.DocFormatingConfig"></a>

## DocFormatingConfig Objects

```python
@dataclass
class DocFormatingConfig()
```

Configs for displaying documentation strings

<a id="bibli_config.DocFormatingConfig.wrap"></a>

#### wrap: `int`

```python
wrap = DEFAULT_WRAP
```

Line wrap config

<a id="bibli_config.DocFormatingConfig.character_limit"></a>

#### character\_limit: `int`

```python
character_limit = DEFAULT_CHAR_LIMIT
```

Number of characters before trimming

<a id="bibli_config.DocFormatingConfig.format"></a>

#### format: `str`

```python
format = "list"
```

`list` or `markdown`

<a id="bibli_config.DocFormatingConfig.show_fields"></a>

#### show\_fields: `list[str]`

```python
show_fields = field(default_factory=lambda: [])
```

Filter of bibtex fields to show

<a id="bibli_config.DocFormatingConfig.header_format"></a>

#### header\_format: `list[str] | str`

```python
header_format = field(default_factory=lambda: DEFAULT_HEADER_FORMAT)
```

List of Python-style format strings for the header.

<a id="bibli_config.DocFormatingConfig.footer_format"></a>

#### footer\_format: `list[str] | str`

```python
footer_format = field(default_factory=lambda: DEFAULT_FOOTER_FORMAT)
```

List of Python-style format strings for the footer.

<a id="bibli_config.CiteConfig"></a>

## CiteConfig Objects

```python
@dataclass
class CiteConfig()
```

Configs for citation.

<a id="bibli_config.CiteConfig.trigger"></a>

#### trigger: `str`

```python
trigger = DEFAULT_CITE_TRIGGER
```

Trigger completion.

<a id="bibli_config.CiteConfig.prefix"></a>

#### prefix: `str`

```python
prefix = DEFAULT_CITE_PREFIX
```

Prefix to begin the citation (must be updated if trigger is updated).
Brackets (`([{`) should be escaped (`\(\[\{`).

<a id="bibli_config.CiteConfig.postfix"></a>

#### postfix: `str`

```python
postfix = DEFAULT_CITE_POSTFIX
```

Prefix to begin the citation.
Brackets (`])}`) should be escaped (`\]\)\}`).

<a id="bibli_config.CiteConfig.separator"></a>

#### separator: `str`

```python
separator = DEFAULT_CITE_SEPARATOR
```

separator between citations
Brackets (`])}`) should be escaped (`\]\)\}`).

<a id="bibli_config.CiteConfig.regex"></a>

#### regex: `str`

```python
regex = DEFAULT_CITE_REGEX_STR
```

Regex string to find the citation.

<a id="bibli_config.HoverConfig"></a>

## HoverConfig Objects

```python
@dataclass
class HoverConfig()
```

Configs for `textDocument/hover`.

<a id="bibli_config.HoverConfig.doc_format"></a>

#### doc\_format: `DocFormatingConfig`

```python
doc_format = field(default_factory=lambda: DocFormatingConfig())
```

see DocFormatingConfig

<a id="bibli_config.CompletionConfig"></a>

## CompletionConfig Objects

```python
@dataclass
class CompletionConfig()
```

Configs for `textDocument/completion`.

<a id="bibli_config.BackendConfig"></a>

## BackendConfig Objects

```python
@dataclass
class BackendConfig()
```

Config for backends

<a id="bibli_config.BackendConfig.backend_type"></a>

#### backend\_type: `str`

```python
backend_type = "bibfile"
```

Type of backend `bibfile` or `zotero_api`

<a id="bibli_config.BackendConfig.library_id"></a>

#### library\_id: `str`

```python
library_id = ""
```

`zotero_api` only: Online library ID

<a id="bibli_config.BackendConfig.library_type"></a>

#### library\_type: `str`

```python
library_type = "user"
```

`zotero_api` only: Online library type

<a id="bibli_config.BackendConfig.api_key"></a>

#### api\_key: `str | None`

```python
api_key = None
```

`zotero_api` only: API key

<a id="bibli_config.BackendConfig.bibfiles"></a>

#### bibfiles: `list[str]`

```python
bibfiles = field(default_factory=lambda: [])
```

`bibfile` only: List of bibfile paths to load

<a id="bibli_config.BibliTomlConfig"></a>

## BibliTomlConfig Objects

```python
@dataclass
class BibliTomlConfig()
```

All configurations used by bibli

<a id="bibli_config.BibliTomlConfig.backends"></a>

#### backends: `dict[str, BackendConfig]`

```python
backends = field(default_factory=lambda: {})
```

Dictionary of backend configs

<a id="bibli_config.BibliTomlConfig.hover"></a>

#### hover: `HoverConfig`

```python
hover = field(default_factory=lambda: HoverConfig())
```

See `HoverConfig`

<a id="bibli_config.BibliTomlConfig.completion"></a>

#### completion: `CompletionConfig`

```python
completion = field(default_factory=lambda: CompletionConfig())
```

See `CompletionConfig`

<a id="bibli_config.BibliTomlConfig.cite"></a>

#### cite: `CiteConfig`

```python
cite = field(default_factory=lambda: CiteConfig())
```

See `CiteConfig`

