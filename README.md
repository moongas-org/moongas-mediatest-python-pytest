<img src="https://raw.githubusercontent.com/moongas-org/moongas-mediatunes-web-vue/refs/heads/main/client/public/moongas.svg" width="128" height="128">

# moongas-mediatest-python-pytest

> 🚧 **Status: Work in Progress (WIP)**  
> This project is currently under active development. Features, APIs, and documentation are subject to change.

---

## Overview

**Moongas component leveraging pytest to enforce rules on media libraries. A simple way to use PyTest to help you keep your media collections (e.g. mp3 music libraries) organized. The idea is to write tests to enforce rules for your media collection.**

### A component of the `moongas` ecosystem of media library tools

- [moongas-collection-demo](https://github.com/moongas-org/moongas-collection-demo) [![CI](https://github.com/moongas-org/moongas-collection-demo/actions/workflows/ci.yml/badge.svg)](https://github.com/moongas-org/moongas-collection-demo/actions/workflows/ci.yml) - Example Moongas media collection (metadata only)
- [moongas-mediatunes-web-vue](https://github.com/moongas-org/moongas-mediatunes-web-vue) [![CI](https://github.com/moongas-org/moongas-mediatunes-web-vue/actions/workflows/ci.yml/badge.svg)](https://github.com/moongas-org/moongas-mediatunes-web-vue/actions/workflows/ci.yml) - A Deno-tooled TypeScript/Vue SPA for Moongas hybrid media collections, pairing with the separate moongas-mediatunes-svc-python-blacksheep backend to seemlessly blend offline and streaming playback
- [moongas-mediatunes-svc-python-blacksheep](https://github.com/moongas-org/moongas-mediatunes-svc-python-blacksheep) [![CI](https://github.com/moongas-org/moongas-mediatunes-svc-python-blacksheep/actions/workflows/ci.yml/badge.svg)](https://github.com/moongas-org/moongas-mediatunes-svc-python-blacksheep/actions/workflows/ci.yml) - Python+BlackSheep implementation of API service for Moongas hybrid media collections—backend for Moongas mediatunes web application (moongas-mediatunes-web-vue)
- [moongas-mediatunes-svc-java-javalin](https://github.com/moongas-org/moongas-mediatunes-svc-java-javalin) [![CI](https://github.com/moongas-org/moongas-mediatunes-svc-python-blacksheep/actions/workflows/ci.yml/badge.svg)](https://github.com/moongas-org/moongas-mediatunes-svc-java-javalin/actions/workflows/ci.yml) - Java+Javalin implementation of API service for Moongas hybrid media collections—backend for Moongas mediatunes web application (moongas-mediatunes-web-vue)
- [moongas-mediascan-go](https://github.com/moongas-org/moongas-mediascan-go) [![CI](https://github.com/moongas-org/moongas-mediascan-go/actions/workflows/ci.yml/badge.svg)](https://github.com/moongas-org/moongas-mediascan-go/actions/workflows/ci.yml) - Golang module to scan media collections and Moongas Yaml metatadata, outputs Moongas database
- [moongas-mediascan-python](https://github.com/moongas-org/moongas-mediascan-python) [![CI](https://github.com/moongas-org/moongas-mediascan-python/actions/workflows/ci.yml/badge.svg)](https://github.com/moongas-org/moongas-mediascan-python/actions/workflows/ci.yml) - Python library with data classes for loading Moongas mediascan databases and Yaml metadata files
- [moongas-mediascripts-python](https://github.com/moongas-org/moongas-mediascripts-python) [![CI](https://github.com/moongas-org/moongas-mediascripts-python/actions/workflows/ci.yml/badge.svg)](https://github.com/moongas-org/moongas-mediascripts-python/actions/workflows/ci.yml) - Python scripts for working with Moongas media collections.
- [moongas-mediatest-python-pytest](https://github.com/moongas-org/moongas-mediatest-python-pytest) [![CI](https://github.com/moongas-org/moongas-mediatest-python-pytest/actions/workflows/ci.yml/badge.svg)](https://github.com/moongas-org/moongas-mediatest-python-pytest/actions/workflows/ci.yml) - Python tool for enforcing media collection rules (implemented with `pytest`)

# Quick Start

### (User) Install from GitHub repo

```bash
pip install "git+https://github.com/moongas-org/moongas-mediatest-python-pytest.git"
```

### (Developer) Clone GitHub repo and install (editable)

```bash
git clone git@github.com:moongas-org/moongas-mediatest-python-pytest.git
cd moongas-mediatest-python-pytest
python -m pip install -e .[dev]
```

## Concept

The main (source) entry point of mediatest invokes pytest to run the tests under the `tests/mediatests` path. This allows mediatest to load its Yaml configuration file. 

## Usage

Modify settings in [mediatest-config.yml](./mediatest-config.yml) as needed, then run `mediatest`:

```bash
python -m mediatest mediatest-config.yml
```

Only test artist.yml:

```bash
python -m mediatest -k test_media_artist_dirs mediatest-config.yml
```

## Help

```bash
$ python -m mediatest --help
usage: python -m mediatest [-h] [--version] [--log-level LEVEL] [--ignore PATH] [-k EXPRESSION] [-m MARKEXPR] [--lf] [--pdb] [-v] [-s]
                           [-x] [--ff] [--maxfail NUM] [--durations NUM] [--durations-min SECONDS]
                           config_path

Run mediatest media tests using the provided config YAML file

positional arguments:
  config_path           Path to the mediatest config YAML file.

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --log-level LEVEL     Logging level (default: INFO).
  --ignore PATH         Path to ignore when collecting pytest tests; may be repeated.
  -k, --keyword EXPRESSION
                        Only run tests matching the pytest expression.
  -m MARKEXPR           Only run tests matching the pytest marker expression.
  --lf, --last-failed   Re-run only tests that failed during the previous execution.
  --pdb                 Drop into the Python debugger when a test fails.
  -v, --verbose         Increase pytest output details.
  -s, --capture=no      Disable pytest output capture.
  -x, --exitfirst       Stop the test suite after the first failure.
  --ff, --failed-first  Run previously failed tests first, then the remaining tests.
  --maxfail NUM         Stop after NUM test failures or errors.
  --durations NUM       Report the NUM slowest test durations.
  --durations-min SECONDS
                        Only report test durations at least SECONDS long.

```


## Development

For development purposes, if you just want to run pytest on the internal unit-tests for this package, run pytest with an `--ignore` argument to exclude the `tests/mediatests` path e.g.

```bash
python -m pytest -vv -s --log-cli-level=DEBUG --ignore tests/media
```

## Example Test Failure

```bash
tests/test_media_lib_counts.py:97: AssertionError
======================================================= short test summary info ========================================================
FAILED tests/test_media_artist_dirs.py::test_artist_yaml_exists[artist_path2151] - AssertionError: assert False
 +  where False = exists()
 +    where exists = PosixPath('/data/Music/Various Artists/artist.yml').exists
FAILED tests/test_media_files_yaml.py::test_mediafile_albumartist_matches_artist_directory_name - AssertionError: File (path=/data/Music/Crosby, Stills and Nash/Crosby, Stills and Nash - Crosby, Stills and Nash [1969]/01.01 - Suite_ Judy Blue Eyes.mp3) albumartist 'Crosby, Stills & Nash' (escaped=Crosby, Stills & Nash)  does not match artist directory name 'Crosby, Stills and Nash'
assert 'David Crosby & Stephen Stills' == 'Crosby, Stills & Nash'
  
  - Crosby, Stills & Nash
  + David Crosby & Stephen Stills

```


## Advanced Usage

Only run filesystem tests (and not the slower files yaml tests):

```bash
pytest -k filesystem
```

## Developer Usage

Only run internal unit-tests and not media library tests:

```bash
pytest --ignore tests/media
```

## Depedencies
- [moongas-mediascan-golang](https://github.com/moongas-org/moongas-mediascan-golang) [![CI](https://github.com/moongas-org/moongas-mediascan-golang/actions/workflows/ci.yml/badge.svg)](https://github.com/moongas-org/moongas-mediascan-golang/actions/workflows/ci.yml) - Golang module to scan media collections and Moongas Yaml metatadata, outputs Moongas database
- [moongas-mediascan-python](https://github.com/moongas-org/moongas-mediascan-python) [![CI](https://github.com/moongas-org/moongas-mediascan-python/actions/workflows/ci.yml/badge.svg)](https://github.com/moongas-org/moongas-mediascan-python/actions/workflows/ci.yml) - Python package for loading Moongas database and Yaml


## Rules Enforced

- Top level folders are _artist_ folders
- Inside each _artist_ folder is one or more _album_ folders
- Every _album_ folder is required to have a `cover.jpg`
- Every _album_ folder name is required to have the year in square brackets
- No empty directories
- _album_ folders must contain one or more media files
- Media files types are `.mp3` and `.m4a`
- Media file count matches expected media file count
- Folder names don't contain prohibited characters which may cause problems with other filesystems (e.g. Windows)
- etc.
- Year ID3 tag must be greater than 0 (requires mediascan)
- Year ID3 tag must be less than current year (requires mediascan)
- Genre ID3 tag must be in allowed genres (see Genres below)

Of course you can adjust the rules as desired my modifying the Python.

## Genres

This library utilizes the comprehensive [`Genre` enum provided by the Moongas `mediascan` Python package](https://github.com/moongas-org/moongas-mediascan-python/blob/main/src/mediascan/genres.py) with string values corresponding to the expected ID3 tag values. This helps avoid inconsistencies e.g. _"Post-punk"_ vs. _"Post-Punk"_ vs. _"Post punk"_ vs. _"Post Punk"_.
