{
  description = "Run stash query Python script";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
      pythonEnv = pkgs.python3.withPackages (ps: with ps; [ requests ]);
    in {
      packages.${system}.default = pkgs.writeShellApplication {
        name = "stash-query";
        runtimeInputs = [ pythonEnv ];
        text = ''
          exec python ./main.py "$@"
        '';
      };

      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [ pythonEnv ];
      };
    };
}
