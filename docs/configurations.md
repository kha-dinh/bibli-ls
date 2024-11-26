# Table of Contents

* [bibli\_ls.bibli\_config](#bibli_ls.bibli_config)
  * [DEFAULT\_HEADER\_FORMAT](#bibli_ls.bibli_config.DEFAULT_HEADER_FORMAT)
  * [DEFAULT\_FOOTER\_FORMAT](#bibli_ls.bibli_config.DEFAULT_FOOTER_FORMAT)
  * [DEFAULT\_CITE\_PREFIX](#bibli_ls.bibli_config.DEFAULT_CITE_PREFIX)
  * [DEFAULT\_CITE\_REGEX\_STR](#bibli_ls.bibli_config.DEFAULT_CITE_REGEX_STR)
  * [DEFAULT\_WRAP](#bibli_ls.bibli_config.DEFAULT_WRAP)
  * [DocFormatingConfig](#bibli_ls.bibli_config.DocFormatingConfig)
    * [wrap](#bibli_ls.bibli_config.DocFormatingConfig.wrap)
    * [character\_limit](#bibli_ls.bibli_config.DocFormatingConfig.character_limit)
    * [format](#bibli_ls.bibli_config.DocFormatingConfig.format)
    * [show\_fields](#bibli_ls.bibli_config.DocFormatingConfig.show_fields)
    * [header\_format](#bibli_ls.bibli_config.DocFormatingConfig.header_format)
    * [footer\_format](#bibli_ls.bibli_config.DocFormatingConfig.footer_format)
  * [CiteConfig](#bibli_ls.bibli_config.CiteConfig)
    * [prefix](#bibli_ls.bibli_config.CiteConfig.prefix)
    * [regex](#bibli_ls.bibli_config.CiteConfig.regex)
  * [HoverConfig](#bibli_ls.bibli_config.HoverConfig)
    * [doc\_format](#bibli_ls.bibli_config.HoverConfig.doc_format)
  * [CompletionConfig](#bibli_ls.bibli_config.CompletionConfig)
  * [BackendConfig](#bibli_ls.bibli_config.BackendConfig)
    * [backend\_type](#bibli_ls.bibli_config.BackendConfig.backend_type)
    * [library\_id](#bibli_ls.bibli_config.BackendConfig.library_id)
    * [library\_type](#bibli_ls.bibli_config.BackendConfig.library_type)
    * [api\_key](#bibli_ls.bibli_config.BackendConfig.api_key)
    * [bibfiles](#bibli_ls.bibli_config.BackendConfig.bibfiles)
  * [BibliTomlConfig](#bibli_ls.bibli_config.BibliTomlConfig)
    * [backends](#bibli_ls.bibli_config.BibliTomlConfig.backends)
    * [hover](#bibli_ls.bibli_config.BibliTomlConfig.hover)
    * [completion](#bibli_ls.bibli_config.BibliTomlConfig.completion)
    * [cite](#bibli_ls.bibli_config.BibliTomlConfig.cite)

<a id="bibli_ls.bibli_config"></a>

# bibli\_ls.bibli\_config

<a id="bibli_ls.bibli_config.DEFAULT_HEADER_FORMAT"></a>

#### DEFAULT\_HEADER\_FORMAT

```python
DEFAULT_HEADER_FORMAT = [
    "# `{entry_type}` {title}",
    "_{author}_",
    "─────────────────── ...
```

Default footer

<a id="bibli_ls.bibli_config.DEFAULT_FOOTER_FORMAT"></a>

#### DEFAULT\_FOOTER\_FORMAT

```python
DEFAULT_FOOTER_FORMAT = [
    "───────────────────────────────────────────────────────────────────── ...
```

Default prefix

<a id="bibli_ls.bibli_config.DEFAULT_CITE_PREFIX"></a>

#### DEFAULT\_CITE\_PREFIX

```python
DEFAULT_CITE_PREFIX = "@"
```

Default regex string

<a id="bibli_ls.bibli_config.DEFAULT_CITE_REGEX_STR"></a>

#### DEFAULT\_CITE\_REGEX\_STR

```python
DEFAULT_CITE_REGEX_STR = r"@([A-Za-z_0-9]+)\b"
```

Default word wrap

<a id="bibli_ls.bibli_config.DEFAULT_WRAP"></a>

#### DEFAULT\_WRAP

```python
DEFAULT_WRAP = 80
```

Default character limit

<a id="bibli_ls.bibli_config.DocFormatingConfig"></a>

## DocFormatingConfig Objects

```python
@dataclass
class DocFormatingConfig()
```

Configs for displaying documentation strings

<a id="bibli_ls.bibli_config.DocFormatingConfig.wrap"></a>

#### wrap: `int`

```python
wrap = DEFAULT_WRAP
```

Line wrap config

<a id="bibli_ls.bibli_config.DocFormatingConfig.character_limit"></a>

#### character\_limit: `int`

```python
character_limit = DEFAULT_CHAR_LIMIT
```

Number of characters before trimming

<a id="bibli_ls.bibli_config.DocFormatingConfig.format"></a>

#### format: `str`

```python
format = "list"
```

`list` or `markdown`

<a id="bibli_ls.bibli_config.DocFormatingConfig.show_fields"></a>

#### show\_fields: `list[str]`

```python
show_fields = field(default_factory=lambda: [])
```

Filter of bibtex fields to show

<a id="bibli_ls.bibli_config.DocFormatingConfig.header_format"></a>

#### header\_format: `list[str] | str`

```python
header_format = field(default_factory=lambda: DEFAULT_HEADER_FORMAT)
```

List of Python-style format strings for the header.

<a id="bibli_ls.bibli_config.DocFormatingConfig.footer_format"></a>

#### footer\_format: `list[str] | str`

```python
footer_format = field(default_factory=lambda: DEFAULT_FOOTER_FORMAT)
```

List of Python-style format strings for the footer.

<a id="bibli_ls.bibli_config.CiteConfig"></a>

## CiteConfig Objects

```python
@dataclass
class CiteConfig()
```

Configs for citation.

<a id="bibli_ls.bibli_config.CiteConfig.prefix"></a>

#### prefix: `str`

```python
prefix = DEFAULT_CITE_PREFIX
```

Prefix to begin the citation.

<a id="bibli_ls.bibli_config.CiteConfig.regex"></a>

#### regex: `str`

```python
regex = DEFAULT_CITE_REGEX_STR
```

Regex string to find the citation.

<a id="bibli_ls.bibli_config.HoverConfig"></a>

## HoverConfig Objects

```python
@dataclass
class HoverConfig()
```

Configs for `textDocument/hover`.

<a id="bibli_ls.bibli_config.HoverConfig.doc_format"></a>

#### doc\_format: `DocFormatingConfig`

```python
doc_format = field(default_factory=lambda: DocFormatingConfig())
```

see DocFormatingConfig

<a id="bibli_ls.bibli_config.CompletionConfig"></a>

## CompletionConfig Objects

```python
@dataclass
class CompletionConfig()
```

Configs for `textDocument/completion`.

<a id="bibli_ls.bibli_config.BackendConfig"></a>

## BackendConfig Objects

```python
@dataclass
class BackendConfig()
```

Config for backends

<a id="bibli_ls.bibli_config.BackendConfig.backend_type"></a>

#### backend\_type: `str`

```python
backend_type = "bibfile"
```

Type of backend `bibfile` or `zotero_api`

<a id="bibli_ls.bibli_config.BackendConfig.library_id"></a>

#### library\_id: `str`

```python
library_id = ""
```

`zotero_api` only: Online library ID

<a id="bibli_ls.bibli_config.BackendConfig.library_type"></a>

#### library\_type: `str`

```python
library_type = "user"
```

`zotero_api` only: Online library type

<a id="bibli_ls.bibli_config.BackendConfig.api_key"></a>

#### api\_key: `str | None`

```python
api_key = None
```

`zotero_api` only: API key

<a id="bibli_ls.bibli_config.BackendConfig.bibfiles"></a>

#### bibfiles: `list[str]`

```python
bibfiles = field(default_factory=lambda: [])
```

`bibfile` only: List of bibfile paths to load

<a id="bibli_ls.bibli_config.BibliTomlConfig"></a>

## BibliTomlConfig Objects

```python
@dataclass
class BibliTomlConfig()
```

All configurations used by bibli

<a id="bibli_ls.bibli_config.BibliTomlConfig.backends"></a>

#### backends: `dict[str, BackendConfig]`

```python
backends = field(default_factory=lambda: {})
```

Dictionary of backend configs

<a id="bibli_ls.bibli_config.BibliTomlConfig.hover"></a>

#### hover: `HoverConfig`

```python
hover = field(default_factory=lambda: HoverConfig())
```

See `HoverConfig`

<a id="bibli_ls.bibli_config.BibliTomlConfig.completion"></a>

#### completion: `CompletionConfig`

```python
completion = field(default_factory=lambda: CompletionConfig())
```

See `CompletionConfig`

<a id="bibli_ls.bibli_config.BibliTomlConfig.cite"></a>

#### cite: `CiteConfig`

```python
cite = field(default_factory=lambda: CiteConfig())
```

See `CiteConfig`

