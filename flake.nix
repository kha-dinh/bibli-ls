{
  description = "A simple LSP server for your bibliographies";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        bibtexparser2 = pkgs.python3Packages.buildPythonPackage {
          pname = "bibtexparser";
          version = "2.0.0b4";
          format = "wheel";

          src = pkgs.fetchurl {
            url = "https://files.pythonhosted.org/packages/3f/64/6eda019a3b0d3aa6834865c126b66cfd442f56829befdca571c40662f8a6/bibtexparser-2.0.0b4-py3-none-any.whl";
            sha256 = "sha256-FOWMfvltp4z2dce7LPFbA2E9Rj737c09ruIPU7SJzoM=";
          };

          propagatedBuildInputs = with pkgs.python3Packages; [
          ];

          doCheck = false;
        };

        pyzotero = pkgs.python3Packages.buildPythonPackage {
          pname = "pyzotero";
          version = "1.5.25";
          format = "wheel";

          src = pkgs.fetchurl {
            url = "https://files.pythonhosted.org/packages/cb/3c/717f90930fbba6ec433a8b6eb9c8854089b7cd54118fb3dd5822d53bdfc7/pyzotero-1.5.25-py3-none-any.whl";
            sha256 = "sha256-ZSkTDLfH53OWPZLbfnoYtpipesgVZ2YyC1Xr1MfpTtU=";
          };

          propagatedBuildInputs = with pkgs.python3Packages; [
            bibtexparser2
            feedparser
            pytz
            requests
          ];

          doCheck = false;
        };

        py-markdown-table = pkgs.python3Packages.buildPythonPackage {
          pname = "py-markdown-table";
          version = "1.2.0";
          format = "pyproject";

          src = pkgs.fetchPypi {
            pname = "py_markdown_table";
            version = "1.2.0";
            sha256 = "sha256-uuMMqX274UT/phiXlsi+1kWV6kyqTUI3nhFY3Y0myHM=";
          };

          nativeBuildInputs = with pkgs.python3Packages; [
            poetry-core
          ];

          propagatedBuildInputs = with pkgs.python3Packages; [
          ];

          doCheck = false;
        };

        tosholi = pkgs.python3Packages.buildPythonPackage {
          pname = "tosholi";
          version = "0.1.0";
          format = "pyproject";

          src = pkgs.fetchPypi {
            pname = "tosholi";
            version = "0.1.0";
            sha256 = "sha256-MmykuNgxCzKvmei+c6O2Yosw88i027jnvGDkKiWpGlI=";
          };

          nativeBuildInputs = with pkgs.python3Packages; [
            setuptools
            setuptools_scm
          ];

          propagatedBuildInputs = with pkgs.python3Packages; [
            dacite
            tomli-w
          ];

          doCheck = false;
        };

        ripgrepy = pkgs.python3Packages.buildPythonPackage {
          pname = "ripgrepy";
          version = "2.0.0";
          format = "setuptools";

          src = pkgs.fetchPypi {
            pname = "ripgrepy";
            version = "2.0.0";
            sha256 = "sha256-bdhxuv6FkwEJc1TR8XFUD7yb040/j1L4oZbcKFIghdo=";
          };

          propagatedBuildInputs = with pkgs.python3Packages; [
          ];

          doCheck = false;
        };

        watchdog = pkgs.python3Packages.buildPythonPackage {
          pname = "watchdog";
          version = "6.0.0";
          format = "setuptools";

          src = pkgs.fetchPypi {
            pname = "watchdog";
            version = "6.0.0";
            sha256 = "sha256-nd98gv2jro4k3s2hM47eZuHJmIPbk3Edj7lB6qLYwoI=";
          };

          propagatedBuildInputs = with pkgs.python3Packages; [
          ];

          doCheck = false;
        };

        pygls = pkgs.python3Packages.buildPythonPackage {
          pname = "pygls";
          version = "2.0.0a2";
          format = "wheel";

          src = pkgs.fetchurl {
            url = "https://files.pythonhosted.org/packages/f8/47/7d7b3911fbd27153ee38a1a15e3977c72733a41ee8d7f6ce6dca65843fe9/pygls-2.0.0a2-py3-none-any.whl";
            sha256 = "sha256-sgI2kyFAk0OqZEDXMRHZ+gwi5YBGb/HHaWuDWLuR8kM=";
          };

          propagatedBuildInputs = with pkgs.python3Packages; [
          ];

          doCheck = false;
        };

        mdformat = pkgs.python3Packages.buildPythonPackage {
          pname = "mdformat";
          version = "0.7.19";
          format = "wheel";

          src = pkgs.fetchurl {
            url = "https://files.pythonhosted.org/packages/a5/7e/a7a904ec104e21c85333a02dd54456f53d5be31bee716217a1450844a044/mdformat-0.7.19-py3-none-any.whl";
            sha256 = "sha256-XDYJkq3BGM8Uecu+krs71m3NfxpaOirWZ1kVYixnjPE=";
          };

          propagatedBuildInputs = with pkgs.python3Packages; [
          ];

          doCheck = false;
        };
      in
      {
        packages.default = pkgs.python3Packages.buildPythonPackage {
          pname = "bibli-ls";
          version = "0.1.6.2";

          src = ./.;
          format = "pyproject";

          propagatedBuildInputs = with pkgs.python3Packages; [
            bibtexparser2
            watchdog
            pyzotero
            py-markdown-table
            pygls
            tosholi
            mdformat
            ripgrepy
            typing-extensions
          ];

          nativeBuildInputs = with pkgs.python3Packages; [
            setuptools
            pip
            wheel
          ];

          doCheck = false;

          meta = with pkgs.lib; {
            description = "A simple LSP server for your bibliographies";
            homepage = "https://pypi.org/project/bibli-ls/";
            license = licenses.mit; # Adjust according to your license
            maintainers = with maintainers; [ ];
          };
        };

        defaultPackage = self.packages.${system}.default;
      }
    );
}
