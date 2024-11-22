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

| LSP Features                                                                                                                                           | Behavior                                                                                                                 |
| ------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| [textDocument/definition](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_definition)         | Go to the first definition found in the `.bib` files.                                                                    |
| [textDocument/references](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_references)         | Find appearance of `prefix + ID` with ripgrep.                                                                           |
| [textDocument/hover](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_hover)                   | Show metadata from `.bib` files based on configurations.                                                                 |
| [textDocument/completion](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_completion)         | Triggered by the `cite_prefix` configuration. Show completion of citation ID for bibtex entries and their documentation. |
| [textDocument/diagnoistic](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_completion)        | Find citations without a proper entry in the bibfile.                                                                    |
| [textDocument/implementation](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_implementation) | (Non-standard) Open `url` field of the citation in an external browser (TODO: make configurable).                        |

## Configuration

Create a configuration file `.bibli.toml` at the root of your note directory. Here is a sample configuration:

```toml

[backend]
backend_type = "zotero_api" # Available backends: "bibfile", "zotero_api"

[backend.bibfile]
bibfiles = ["references.bib"]

[backend.zotero_api]
library_id = "5123456" # Your library ID
library_type = "user" # "user"" or "group"
api_key = "XXXXXXXXXXXXXXXXXXXXXXXX"

[cite]
prefix = "@" # e.g., "@john2024paper"

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

# Alternatively, on Arch:
pipx install bibli-ls
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
      -- Optional: visit the URL of the citation with LSP DocumentImplementation
      on_attach = function(client, bufnr)
        vim.keymap.set({ "n" }, "<cr>", function()
          vim.lsp.buf.implementation()
        end)
      end,
    },
  }
end

lspconfig.bibli_ls.setup({})
```

## Backends

Currently, Bibli supports `bibfile` and `zotero_api` backends.

`bibfile` backend loads the library from a local bibtex file.

`zotero_api` backend connects directly to your Zotero web library, removing the need for maintaining separated bibfile.

- [More on setting up citation keys](/docs/custom-cite-keys.md)

## Building from source

From the root directory:

```bash
pyproject-build
pip install dist/bibli_ls-{version}-py3-none-any.whl # --force-reinstall if needed
# Or for Arch
pipx install . # --force-reinstall if needed


```
