<h3 align="center">
 <img src="https://raw.githubusercontent.com/kha-dinh/bibli-ls/main/docs/logo.jpeg" width="100" alt="Logo"/><br/>
</h3>

# Bibli Language Server

A [Language Server](https://microsoft.github.io/language-server-protocol/) that brings bibliographies into your note-taking workflows.

[![image-version](https://img.shields.io/pypi/v/bibli-ls.svg)](https://python.org/pypi/bibli-ls)
[![image-license](https://img.shields.io/pypi/l/bibli-ls.svg)](https://python.org/pypi/bibli-ls)
[![image-python-versions](https://img.shields.io/badge/python->=3.8-blue)](https://python.org/pypi/bibli-ls)

## Supported LSP capabilities

| LSP Feature                                                                                                                                    | Behavior                                                                                                                                  |
| ---------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| [textDocument/definition](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_definition) | Go to the first definition found in the `.bib` files.                                                                                     |
| [textDocument/references](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_references) | Find appearance of `prefix + ID` through ripgrep.                                                                                         |
| [textDocument/hover](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_hover)           | Show metadata from `.bib` files based on configurations.                                                                                  |
| [textDocument/completion](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_completion) | Triggered by the `cite_prefix` configuration or `[`, `{`, `<`. Show completion of citation ID for bibtex entries and their documentation. |

## Configuration

Create a configuration file `.bibli.toml` at the root of your note directory. Here is a sample configurations:

```toml
bibfiles = ["references.bib"] # Relative/Absolute path to your bibliographies

[hover]
show_fields = ["abstract", "year", "booktitle"]
format = "list" # Available formats: "markdown" (markdown table) and "list" (markdown list)

[completion]
cite_prefix = "@"
```

## Installation

Install the latest release of `bibli-ls` through `pip`:

```bash
pip install bibli-ls
```

### Neovim

Automatic configuration through [lspconfig]() is not supported yet. To enable bibli-ls, put the following code in your Neovim config.

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
- Per-document bibliographies
- More LSP capabilities
  - [mkdnflow.nvim](https://github.com/jakewvincent/mkdnflow.nvim)-like opening of URL
  - Code actions
