# Contribution Guide

## Required Tools and Dependencies

The backend of FreeDATA is built with python, with a couple dependencies written
in C/C++, and the frontend is build with VueJS, so you will need Python (from
3.10 to 3.13) to work on the backend, and node+npm to work on the frontend.

System dependencies required:
  - python3 (with virtual environment support)
  - portaudio
  - hamlib (optional, there is a vendored version bundled with the freedata
    server, or you can build it from source)
  - nodejs + npm

Example for debian trixie: `sudo apt update && sudo apt install python3
python3-venv nodejs npm portaudio19-dev`

Example for MacOS: `brew install python pyenv-virtualenv npm node@24 portaudio`

To fetch the python dependencies create a virtual environment and next use pip:

- Create a virtual environment: `python -m venv venv`
- Load the virtual environment `source venv/bin/activate`
- There are several sets of dependencies you can install:
  - `pip install .` installs only the libraries required to run freedata
  - `pip install .[test]` installs the libraries required for running and testing
    freedata
  - `pip install .[dev]` installs the libraries required for running, testing
    and linting/checking freedata
  - `pip install .[build]` installs only the libraries required to run and build
    the freedata pip module
  - `pip install .[nuitka]` installs only the libraries required to run and
    build the freedata windows executable

To fetch the `npm` dependencies go inside `./freedata_gui` and run `npm
install`. See `./freedata_gui/README.md` for additional informations.

## Linting and Formatting (python-only)
The python sources must be formatted and checked using `ruff`. There is a CI
workflow that block all PRs that do not pass the linter/formatter checks.

- To check formatting run `ruff format --check` (lists file that needs formatting)
- To see what the automatic formatter will change run `ruff format --preview
--diff` (shows diff-style changes).
- To automatically format files run `ruff format --preview`

NOTE: the `--preview` enables new auto-formatting actions and enables a feature
usefull in the CI. In the future it will no longer be necessary

- To run the checker/linter execute `ruff check`
- Some errors can be automatically fixed running `ruff check --fix`, but always
  check and test the changes made by ruff. There are errors that ruff cannot safely
  fix automatically, you must fix them manually.

## Testing backend
To run the backend tests run inside the virtual environment `python -m unittest
discover tests`
