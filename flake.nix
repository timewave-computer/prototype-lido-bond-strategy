{
  description = "A simple Python 3.11 environment using Nix Flakes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
      pkgsForSystem = system: import nixpkgs { inherit system; };
    in {
      devShells = forAllSystems (system: {
        default = let pkgs = pkgsForSystem system; in pkgs.mkShell {
          buildInputs = with pkgs; [
            python311
            python311Packages.pip
            python311Packages.virtualenv
          ];
          shellHook = ''
            # Create and activate virtual environment if it doesn't exist
            VENV=.venv
            if [ ! -d "$VENV" ]; then
              python -m venv "$VENV"
            fi
            source "$VENV/bin/activate"
            
            # Install required packages
            pip install web3
          '';
        };
      });
    };
}