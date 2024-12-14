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

        # Helper function for wheel packages
        buildWheel =
          {
            pname,
            version,
            url,
            sha256,
            propagatedBuildInputs ? [ ],
          }:
          pkgs.python3Packages.buildPythonPackage {
            inherit pname version propagatedBuildInputs;
            format = "wheel";
            src = pkgs.fetchurl {
              inherit url sha256;
            };
            doCheck = false;
          };

        # Custom Python packages
        customPythonPackages = with pkgs.python3Packages; {
          bibtexparser2 = buildWheel {
            pname = "bibtexparser";
            version = "2.0.0b4";
            url = "https://files.pythonhosted.org/packages/3f/64/6eda019a3b0d3aa6834865c126b66cfd442f56829befdca571c40662f8a6/bibtexparser-2.0.0b4-py3-none-any.whl";
            sha256 = "sha256-FOWMfvltp4z2dce7LPFbA2E9Rj737c09ruIPU7SJzoM=";
            propagatedBuildInputs = [ pylatexenc ];
          };

          pyzotero = buildWheel {
            pname = "pyzotero";
            version = "1.5.25";
            url = "https://files.pythonhosted.org/packages/cb/3c/717f90930fbba6ec433a8b6eb9c8854089b7cd54118fb3dd5822d53bdfc7/pyzotero-1.5.25-py3-none-any.whl";
            sha256 = "sha256-ZSkTDLfH53OWPZLbfnoYtpipesgVZ2YyC1Xr1MfpTtU=";
            propagatedBuildInputs = [
              # bibtexparser2
              feedparser
              pytz
              requests
            ];
          };

          lsprotocol = buildWheel {
            pname = "lsprotocol";
            version = "2024.0.0b1";
            url = "https://files.pythonhosted.org/packages/4d/1b/526af91cd43eba22ac7d9dbdec729dd9d91c2ad335085a61dd42307a7b35/lsprotocol-2024.0.0b1-py3-none-any.whl";
            sha256 = "sha256-k3hQUKwVWuK+FrHr+9dMIU/rPT73exA5nOlB5czvbr0=";
            propagatedBuildInputs = [
              attrs
              cattrs
              jsonschema
            ];
          };

          pygls = buildWheel {
            pname = "pygls";
            version = "2.0.0a2";
            url = "https://files.pythonhosted.org/packages/f8/47/7d7b3911fbd27153ee38a1a15e3977c72733a41ee8d7f6ce6dca65843fe9/pygls-2.0.0a2-py3-none-any.whl";
            sha256 = "sha256-sgI2kyFAk0OqZEDXMRHZ+gwi5YBGb/HHaWuDWLuR8kM=";
            propagatedBuildInputs = [ lsprotocol ];
          };

          mdformat = buildWheel {
            pname = "mdformat";
            version = "0.7.19";
            url = "https://files.pythonhosted.org/packages/a5/7e/a7a904ec104e21c85333a02dd54456f53d5be31bee716217a1450844a044/mdformat-0.7.19-py3-none-any.whl";
            sha256 = "sha256-XDYJkq3BGM8Uecu+krs71m3NfxpaOirWZ1kVYixnjPE=";
            propagatedBuildInputs = [ markdown-it-py ];
          };

          # PyPI packages that use setuptools/pyproject
          py-markdown-table = buildPythonPackage {
            pname = "py-markdown-table";
            version = "1.2.0";
            format = "pyproject";
            src = fetchPypi {
              pname = "py_markdown_table";
              version = "1.2.0";
              sha256 = "sha256-uuMMqX274UT/phiXlsi+1kWV6kyqTUI3nhFY3Y0myHM=";
            };
            nativeBuildInputs = [ poetry-core ];
            doCheck = false;
          };

          tosholi = buildPythonPackage {
            pname = "tosholi";
            version = "0.1.0";
            format = "pyproject";
            src = fetchPypi {
              pname = "tosholi";
              version = "0.1.0";
              sha256 = "sha256-MmykuNgxCzKvmei+c6O2Yosw88i027jnvGDkKiWpGlI=";
            };
            nativeBuildInputs = [
              setuptools
              setuptools_scm
            ];
            propagatedBuildInputs = [
              dacite
              tomli-w
            ];
            doCheck = false;
          };

          typing-extensions = buildPythonPackage {
            pname = "typing_extensions";
            version = "4.12.2";
            format = "pyproject";
            src = fetchPypi {
              pname = "typing_extensions";
              version = "4.12.2";
              sha256 = "sha256-Gn6tVcflWd1N7ohW46iLQSJav+HOjfV7fBORX+Eh/7g=";
            };
            nativeBuildInputs = with pkgs.python3Packages; [
              flit-core
            ];
            doCheck = false;
          };

          ripgrepy = buildPythonPackage {
            pname = "ripgrepy";
            version = "2.0.0";
            format = "setuptools";
            src = fetchPypi {
              pname = "ripgrepy";
              version = "2.0.0";
              sha256 = "sha256-bdhxuv6FkwEJc1TR8XFUD7yb040/j1L4oZbcKFIghdo=";
            };
            doCheck = false;
          };

          watchdog = buildPythonPackage {
            pname = "watchdog";
            version = "6.0.0";
            format = "setuptools";
            src = fetchPypi {
              pname = "watchdog";
              version = "6.0.0";
              sha256 = "sha256-nd98gv2jro4k3s2hM47eZuHJmIPbk3Edj7lB6qLYwoI=";
            };
            doCheck = false;
          };
        };
      in
      {
        packages.default = pkgs.python3Packages.buildPythonPackage {
          pname = "bibli-ls";
          version = "0.1.6.2";
          src = ./.;
          format = "pyproject";

          propagatedBuildInputs = with customPythonPackages; [
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
            # pip
            # wheel
          ];

          doCheck = false;

          meta = with pkgs.lib; {
            description = "A simple LSP server for your bibliographies";
            homepage = "https://pypi.org/project/bibli-ls/";
            license = licenses.mit;
          };
        };

        defaultPackage = self.packages.${system}.default;
      }
    );
}
