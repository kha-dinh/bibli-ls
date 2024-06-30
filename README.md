<h3 align="center">
  <img
    src="https://raw.githubusercontent.com/kha-dinh/bibli-ls/main/docs/logo.jpeg"
    width="100"
    alt="Logo"
  /><br />
</h3>

# Bibli Language Server

A [Language Server](https://microsoft.github.io/language-server-protocol/) that brings bibliographies into your notes.

[![image-version](https://img.shields.io/pypi/v/bibli-ls.svg)](https://python.org/pypi/bibli-ls)
[![image-license](https://img.shields.io/pypi/l/bibli-ls.svg)](https://python.org/pypi/bibli-ls)
[![image-python-versions](https://img.shields.io/badge/python->=3.8-blue)](https://python.org/pypi/bibli-ls)

## Supported LSP capabilities

| LSP Features                                                                                                                                    | Behavior                                                                                                                 |
| ----------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| [textDocument/definition](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_definition)  | Go to the first definition found in the `.bib` files.                                                                    |
| [textDocument/references](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_references)  | Find appearance of `prefix + ID` with ripgrep.                                                                           |
| [textDocument/hover](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_hover)            | Show metadata from `.bib` files based on configurations.                                                                 |
| [textDocument/completion](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_completion)  | Triggered by the `cite_prefix` configuration. Show completion of citation ID for bibtex entries and their documentation. |
| [textDocument/diagnoistic](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_completion) | Find citations without a proper entry in the bibfile.                                                                    |

## Configuration

Create a configuration file `.bibli.toml` at the root of your note directory. Here is a sample configuration:

```toml
bibfiles = ["references.bib"] # Relative/Absolute path to your bibliographies

[cite]
prefix = "@" #

[hover.doc_format]
show_fields = ["abstract", "year", "booktitle", "url"]
format = "table" # Available formats: "table"  and "list" (markdown)

[completion.doc_format]
show_fields = ["abstract", "year", "booktitle"]
format = "list"

```

## Installation

Install the latest release of `bibli-ls` through `pip`:

```bash
pip install bibli-ls
```

### Neovim

Automatic configuration through [lspconfig]() has yet to be supported. To enable bibli-ls, put the following code in your Neovim config.

```lua
local lspconfig = require("lspconfig")
local configs = require("lspconfig.configs")

if not configs.bibli_ls then
 configs.bibli_ls = {
  default_config = {
   cmd = { "bibli_ls" },
   filetypes = { "markdown" },
   root_dir = lspconfig.util.root_pattern(".bibli.toml"),
  },
 }
end

lspconfig.bibli_ls.setup({})
```

### Planned Features (TODO)

- Universal: Works with any note format
- LSP-native configurations
- Per-document bibliographies
- More LSP capabilities
  - [mkdnflow.nvim](https://github.com/jakewvincent/mkdnflow.nvim)-like opening of URL
  - Code actions
