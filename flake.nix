{
  description = "A simple LSP server for your bibliographies";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      uv2nix,
      pyproject-nix,
      pyproject-build-systems,
      ...
    }:
    let
      inherit (nixpkgs) lib;
      forAllSystems = lib.genAttrs lib.systems.flakeExposed;

      # Load workspace from current directory
      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

      # Create package overlay from workspace
      overlay = workspace.mkPyprojectOverlay {
        sourcePreference = "wheel";
      };

      # Python sets grouped per system
      pythonSets = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};

          # Base Python package set from pyproject.nix
          baseSet = pkgs.callPackage pyproject-nix.build.packages {
            python = pkgs.python312;
          };

          # Build fixups for problematic packages
          # Those packages are using setuptools, so we need to pass setuptools
          # as a build input
          pyprojectOverrides = final: prev: {
            sgmllib3k = prev.sgmllib3k.overrideAttrs (old: {
              nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [
                final.setuptools
              ];
            });

            ripgrepy = prev.ripgrepy.overrideAttrs (old: {
              nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [
                final.setuptools
              ];
            });

            docstring-parser = prev.docstring-parser.overrideAttrs (old: {
              nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [
                final.setuptools
              ];
            });
          };

        in
        baseSet.overrideScope (
          lib.composeManyExtensions [
            pyproject-build-systems.overlays.default
            overlay
            pyprojectOverrides
          ]
        )
      );

    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          pythonSet = pythonSets.${system};
          inherit (pkgs.callPackages pyproject-nix.build.util { }) mkApplication;
        in
        {
          default = mkApplication {
            venv = pythonSet.mkVirtualEnv "bibli-ls-env" workspace.deps.default;
            package = pythonSet.bibli-ls;
          };
        }
      );

      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/bibli_ls";
        };
      });

      devShells = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};

          # Create editable overlay for development
          editableOverlay = workspace.mkEditablePyprojectOverlay {
            root = "$REPO_ROOT";
          };

          editablePythonSet = pythonSets.${system}.overrideScope editableOverlay;

          # Create development environment with all dependencies
          venv = editablePythonSet.mkVirtualEnv "bibli-ls-dev-env" workspace.deps.all;
        in
        {
          default = pkgs.mkShell {
            packages = [
              venv
              pkgs.uv
            ];

            env =
              {
                UV_NO_SYNC = "1";
                UV_PYTHON = "${venv}/bin/python";
                UV_PYTHON_DOWNLOADS = "never";
              }
              // lib.optionalAttrs pkgs.stdenv.isLinux {
                # Add library path for Linux systems
                LD_LIBRARY_PATH = lib.makeLibraryPath pkgs.pythonManylinuxPackages.manylinux1;
              };

            shellHook = ''
              unset PYTHONPATH
              export REPO_ROOT=$(git rev-parse --show-toplevel)
            '';
          };
        }
      );
    };
}
