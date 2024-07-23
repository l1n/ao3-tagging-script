{ pkgs ? import <nixpkgs> {} }:

let
  pythonPackages = ps: with ps; [
    pip
    virtualenv
    setuptools
    wheel
    black
    flake8
    mypy
    pytest
    ipython
    requests
    pyyaml
    pandas
    numpy
    matplotlib
    google-auth-oauthlib
    google-auth-httplib2
    google-api-python-client
    beautifulsoup4
    lxml
  ];
  pythonEnv = pkgs.python3.withPackages pythonPackages;
in pkgs.mkShell {
  buildInputs = [
    pythonEnv
    pkgs.nodePackages.pyright
    pkgs.gcc
    pkgs.gnumake
    pkgs.git
  ];

  shellHook = ''
    # Create a virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
      echo "Creating virtual environment..."
      ${pythonEnv}/bin/virtualenv venv
    fi

    # Activate the virtual environment
    source venv/bin/activate

    # Ensure all packages are installed in the virtual environment
    pip install --no-deps --no-index --no-cache-dir --find-links=${pythonEnv}/lib/python*/site-packages $(python -c "import site; print(' '.join([p.split('-')[0] for p in site.getsitepackages()[0].split('/')[-1].split('_')]))")

    # Set up any environment variables you need
    export PIP_DISABLE_PIP_VERSION_CHECK=1
    export PYTHONPATH="$PWD:$PYTHONPATH"

    echo "Python development environment activated!"
    echo "Python version: $(python --version)"
    echo "Pip version: $(pip --version)"
  '';
}
