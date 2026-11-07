# Noemorph Windows portable package (Python 3.14 x64)

This is a **versioned, unsigned portable source-and-wheel bundle**, not a Windows
installer, signed executable or certified offline WebView2 package. It contains
the prebuilt Vite desktop UI, the curated research catalog, tracked application
sources, and Python wheels downloaded for 64-bit Windows Python 3.14.

## Requirements

- Windows x64.
- **Python 3.14 x64** installed and available as `python` (or specify `-Python`).
- **Microsoft Edge WebView2 Evergreen Runtime** installed already.
- PowerShell to run the contained launch script.

## Start

1. Extract the complete `Noemorph-Windows-vVERSION-SHA.zip` into a *new* directory.
2. From PowerShell inside that directory run
   `& .\Start-Noemorph.ps1`.
3. The first run creates `.runtime\venv` beside the launcher, installs Python
   dependencies from `wheelhouse` with `--no-index` (no network fetch), then
   starts the prebuilt UI using `--skip-python-bootstrap --skip-build`.

You may specify `-Python 'C:\Path\To\Python314\python.exe'`. The app also
supports `-ServerOnly` for API-only operation without opening a WebView2 window.

## Update / rollback

Each package is independent. Extract new versions into **separate directories**
and validate them before replacing a working version. To roll back, start the
previous extracted directory. Do not overwrite a working `.runtime` in place.

**Protect local reviewer data:** `Noemorph\data\reviews`, local semantic SQLite
stores, and `.runtime\webview-profile` may contain uncommitted or sensitive
state. Back them up privately before any move; the package does not import,
publish or migrate them automatically. Never upload these local files to GitHub.

## Validation limits

The CI package job builds the Vite UI, downloads pinned Windows wheels, installs
them in a clean virtual environment **offline**, checks imports and launcher
regressions, and uploads a versioned ZIP as a GitHub Actions artifact.

It does **not** simulate an interactive WebView2 session, prove that WebView2 is
installed on a user's machine, sign software, run a Windows installer, or certify
that all research claims and external source links are independently reviewed.
These remain tracked under issues #19, #17 and #15 as appropriate.
