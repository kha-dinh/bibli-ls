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

Create a configuration file `.bibli.toml` at the root of your note directory. Here is a sample configuration. For the complete list of configurations, refer to the [documentation](/docs/configurations.md) and the [default config](/docs/default-config.toml).

```toml

[backends]
# Backends can be of any names
[backends.mylib]
backend_type = "bibfile" # Available backends: "bibfile", "zotero_api"
bibfiles = ["references.bib"]

[backends.my_lab_lib]
backend_type = "zotero_api"
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

- `bibfile` backend loads the library from a local bibtex file.

- `zotero_api` backend connects directly to your Zotero web library, removing the need for maintaining separated bibfiles. It cache the results in a bibfile named `.{backend name}_{library type}_{library id}.bib`. Run the command LSP `library.reload_all` to refetch the online content.

  - [More on setting up citation keys for online libraries](/docs/custom-cite-keys.md)


## Using Nix

### Installation via Flakes

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    bibli-ls.url = "github:kha-dinh/bibli-ls";
  };
}
```

Then you can use it in your configuration:

```nix
{
  environment.systemPackages = [ inputs.bibli-ls.packages.${system}.default ];
}
```

### Home Manager Configuration

Add bibli-ls to your home-manager configuration:

```nix
{ config, pkgs, inputs, ... }:
{
  home.packages = [ inputs.bibli-ls.packages.${system}.default ];

  home.file."Sync/Notes/zk/permanent/.bibli.toml".text = ''
    [backends]
    [backends.library]
    backend_type = "bibfile"
    bibfiles = ["${config.home.homeDirectory}/Sync/Bibliography/library.bib"]
  '';
}
```

### Updating Dependencies

The flake.nix file contains Python package dependencies with their specific versions and hashes. To update a dependency:

1. Find the new wheel URL from PyPI
2. Update the version and URL in flake.nix
3. Update the SHA256 hash. You can get the new hash by intentionally using a wrong hash and Nix will tell you the correct one:

```bash
nix build # Will fail and show the correct hash
```

Example of updating a dependency in flake.nix:

```nix
pygls = buildWheel {
  pname = "pygls";
  version = "2.0.0a2"; # Update version
  url = "https://files.pythonhosted.org/packages/..."; # Update URL
  sha256 = "sha256-..."; # Update hash
  propagatedBuildInputs = [ lsprotocol ];
};
```

## Building from source

From the root directory:

```bash
pip install . # --force-reinstall if needed
# Or for Arch
pipx install . # --force-reinstall if needed
# And Nix
nix build # The built package will be available in `./result`.
```
