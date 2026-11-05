"""Noemorph desktop bootstrap and application entry point.

Running this file creates an isolated Python runtime when necessary, installs the
locked frontend dependencies, builds the Vite application, starts the local API,
and hosts the interface in an application-owned WebView2 window.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import venv
import zipfile
from pathlib import Path
from typing import Sequence


APP_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = APP_DIR / "frontend"
RUNTIME_DIR = APP_DIR / ".runtime"
VENV_DIR = RUNTIME_DIR / "venv"
BUILD_MARKER = RUNTIME_DIR / "frontend-build.json"
NPM_INSTALL_MARKER = RUNTIME_DIR / "frontend-dependencies.json"
LOGGER = logging.getLogger("noemorph")
BOOTSTRAP_ENV = "NOEMORPH_RUNTIME_BOOTSTRAPPED"
NODE_VERSION = "24.20.0"
NODE_WINDOWS_ARCHIVE = f"node-v{NODE_VERSION}-win-x64.zip"
NODE_WINDOWS_SHA256 = "6cac9ffbca8f6a47091e4b5c772e0606049c3871cb67d900c0cedde630e545ba"
NODE_WINDOWS_URL = f"https://nodejs.org/dist/v{NODE_VERSION}/{NODE_WINDOWS_ARCHIVE}"
PORTABLE_NODE_DIR = RUNTIME_DIR / f"node-v{NODE_VERSION}-win-x64"


def _configure_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="[Noemorph] %(message)s",
    )


def _venv_python() -> Path:
    return VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _bootstrap_python_runtime(arguments: Sequence[str], *, skip: bool) -> None:
    """Create a project-local environment, install dependencies, and re-launch."""
    if skip or os.environ.get(BOOTSTRAP_ENV) == "1":
        return

    runtime_python = _venv_python()
    requirements = APP_DIR / "requirements.txt"
    requirements_fingerprint = hashlib.sha256(requirements.read_bytes()).hexdigest()
    dependency_marker = VENV_DIR / ".requirements.sha256"
    current_fingerprint = (
        dependency_marker.read_text(encoding="utf-8").strip()
        if dependency_marker.exists()
        else ""
    )

    if not runtime_python.exists():
        LOGGER.info("Preparing the isolated Python runtime…")
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        venv.EnvBuilder(with_pip=True, clear=False).create(VENV_DIR)

    if current_fingerprint != requirements_fingerprint:
        LOGGER.info("Installing Python application dependencies…")
        subprocess.run(
            [
                str(runtime_python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-input",
                "-r",
                str(requirements),
            ],
            cwd=APP_DIR,
            check=True,
        )
        dependency_marker.write_text(requirements_fingerprint, encoding="utf-8")

    child_environment = os.environ.copy()
    child_environment[BOOTSTRAP_ENV] = "1"
    try:
        completed = subprocess.run(
            [str(runtime_python), str(Path(__file__).resolve()), *arguments],
            cwd=APP_DIR,
            env=child_environment,
        )
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    raise SystemExit(completed.returncode)


def _frontend_fingerprint() -> str:
    hasher = hashlib.sha256()
    inputs = [
        FRONTEND_DIR / "package-lock.json",
        FRONTEND_DIR / "package.json",
        FRONTEND_DIR / "index.html",
        FRONTEND_DIR / "vite.config.ts",
    ]
    inputs.extend(sorted((FRONTEND_DIR / "src").rglob("*")))
    for path in inputs:
        if path.is_file():
            hasher.update(path.relative_to(FRONTEND_DIR).as_posix().encode("utf-8"))
            hasher.update(path.read_bytes())
    return hasher.hexdigest()


def _compatible_node_for_npm(npm: str) -> bool:
    npm_path = Path(npm).resolve()
    sibling = npm_path.parent / ("node.exe" if os.name == "nt" else "node")
    node = str(sibling) if sibling.exists() else shutil.which("node")
    if not node:
        return False
    try:
        version_text = subprocess.run(
            [node, "--version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip().lstrip("v")
        major, minor, *_ = (int(part) for part in version_text.split("."))
    except (OSError, ValueError, subprocess.SubprocessError):
        return False
    return major > 22 or (major == 22 and minor >= 12) or (major == 20 and minor >= 19)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _install_portable_node() -> str:
    """Install an application-owned Node/npm runtime when the host has none."""
    if os.name != "nt" or platform.machine().lower() not in {"amd64", "x86_64"}:
        raise RuntimeError(
            "No compatible Node.js runtime was found. Automatic Node bootstrap is "
            "currently available for 64-bit Windows; install Node.js 22.12 or newer."
        )

    npm = PORTABLE_NODE_DIR / "npm.cmd"
    if npm.exists() and _compatible_node_for_npm(str(npm)):
        return str(npm)

    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    LOGGER.info("Downloading the contained Node.js %s build runtime…", NODE_VERSION)
    with tempfile.TemporaryDirectory(prefix="node-bootstrap-", dir=RUNTIME_DIR) as temporary:
        temporary_dir = Path(temporary)
        archive_path = temporary_dir / NODE_WINDOWS_ARCHIVE
        try:
            with urllib.request.urlopen(NODE_WINDOWS_URL, timeout=45) as response, archive_path.open("wb") as output:
                shutil.copyfileobj(response, output)
        except (OSError, urllib.error.URLError) as exc:
            raise RuntimeError(
                "Noemorph could not download its pinned Node.js runtime from nodejs.org. "
                "Check the network connection and run the application again."
            ) from exc

        actual_hash = _sha256_file(archive_path)
        if actual_hash.lower() != NODE_WINDOWS_SHA256.lower():
            raise RuntimeError(
                "The downloaded Node.js archive failed SHA-256 verification; it was not installed."
            )

        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(temporary_dir)
        extracted = temporary_dir / f"node-v{NODE_VERSION}-win-x64"
        if not (extracted / "npm.cmd").exists() or not (extracted / "node.exe").exists():
            raise RuntimeError("The verified Node.js archive did not contain the expected runtime files.")

        if PORTABLE_NODE_DIR.exists():
            expected_parent = RUNTIME_DIR.resolve()
            if PORTABLE_NODE_DIR.resolve().parent != expected_parent:
                raise RuntimeError("Refusing to replace a Node runtime outside Noemorph's runtime directory.")
            shutil.rmtree(PORTABLE_NODE_DIR)
        shutil.move(str(extracted), str(PORTABLE_NODE_DIR))

    LOGGER.info("Contained Node.js runtime is ready.")
    return str(PORTABLE_NODE_DIR / "npm.cmd")


def _find_npm() -> str:
    executable = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if executable and _compatible_node_for_npm(executable):
        return executable
    return _install_portable_node()


def _run_frontend_command(npm: str, *arguments: str) -> None:
    subprocess.run(
        [npm, *arguments],
        cwd=FRONTEND_DIR,
        check=True,
        env={**os.environ, "CI": "true"},
    )


def _bootstrap_frontend(*, skip_install: bool, skip_build: bool) -> None:
    if skip_build:
        return
    npm = _find_npm()
    node_modules = FRONTEND_DIR / "node_modules"
    lockfile = FRONTEND_DIR / "package-lock.json"
    if not lockfile.exists():
        raise RuntimeError(
            "The locked frontend manifest is missing. Restore frontend/package-lock.json; "
            "Noemorph will not create an unreviewed dependency graph."
        )

    lock_hash = hashlib.sha256(lockfile.read_bytes()).hexdigest()
    installed_lock_hash = ""
    if NPM_INSTALL_MARKER.exists():
        try:
            installed_lock_hash = json.loads(
                NPM_INSTALL_MARKER.read_text(encoding="utf-8")
            ).get("package_lock_sha256", "")
        except (json.JSONDecodeError, OSError):
            installed_lock_hash = ""

    if not skip_install and (not node_modules.exists() or installed_lock_hash != lock_hash):
        LOGGER.info("Downloading the locked web-interface dependencies…")
        _run_frontend_command(npm, "ci", "--no-audit", "--no-fund")
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        NPM_INSTALL_MARKER.write_text(
            json.dumps(
                {
                    "package_lock_sha256": lock_hash,
                    "installed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    if not node_modules.exists():
        raise RuntimeError(
            "Frontend dependencies are absent. Run without --skip-install to bootstrap them."
        )

    fingerprint = _frontend_fingerprint()
    recorded_fingerprint = ""
    if BUILD_MARKER.exists():
        try:
            recorded_fingerprint = json.loads(
                BUILD_MARKER.read_text(encoding="utf-8")
            ).get("fingerprint", "")
        except (json.JSONDecodeError, OSError):
            recorded_fingerprint = ""

    dist_index = FRONTEND_DIR / "dist" / "index.html"
    if recorded_fingerprint == fingerprint and dist_index.exists():
        LOGGER.info("Web interface is already up to date.")
        return

    LOGGER.info("Building the web interface…")
    _run_frontend_command(npm, "run", "build")
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    BUILD_MARKER.write_text(
        json.dumps(
            {
                "fingerprint": fingerprint,
                "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _reserve_socket(host: str, port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if os.name == "nt" and hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        else:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
    except Exception:
        sock.close()
        raise
    return sock


def _start_server(host: str, port: int, *, serve_frontend: bool):
    import uvicorn

    from backend.api import create_app

    app = create_app(APP_DIR, serve_frontend=serve_frontend)
    server_socket = _reserve_socket(host, port)
    selected_port = int(server_socket.getsockname()[1])
    config = uvicorn.Config(
        app,
        host=host,
        port=selected_port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    server_errors: list[BaseException] = []

    def run_server() -> None:
        try:
            server.run(sockets=[server_socket])
        except BaseException as exc:  # surfaced by the owning launcher thread
            server_errors.append(exc)

    thread = threading.Thread(
        target=run_server,
        name="noemorph-api",
        daemon=False,
    )
    try:
        thread.start()
    except Exception:
        server_socket.close()
        raise
    return server, thread, selected_port, server_errors


def _wait_for_server(
    url: str,
    server_thread: threading.Thread,
    server_errors: list[BaseException],
    timeout_seconds: float = 15.0,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
        if server_errors:
            raise RuntimeError("The local API stopped during startup.") from server_errors[0]
        if not server_thread.is_alive():
            raise RuntimeError("The local API stopped before it became ready.")
        time.sleep(0.1)
    raise RuntimeError(f"The local API did not become ready: {last_error}")


class DesktopBridge:
    """The deliberately small JavaScript surface exposed to the contained UI."""

    def open_source(self, url: str, title: str = "Research source") -> dict[str, object]:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc:
            return {"ok": False, "error": "Only HTTPS research sources can be opened."}

        import webview

        safe_title = " ".join(str(title).split())[:120] or "Research source"
        webview.create_window(
            f"Noemorph Source · {safe_title}",
            url,
            width=1180,
            height=820,
            min_size=(760, 520),
            background_color="#0a0c10",
            text_select=True,
            zoomable=True,
        )
        return {"ok": True}


def _run_desktop(url: str, *, debug: bool) -> None:
    import webview

    webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = False
    webview.settings["ALLOW_FILE_URLS"] = False
    webview.settings["ALLOW_DOWNLOADS"] = False
    window = webview.create_window(
        "Noemorph · Consciousness Research Atlas",
        url,
        width=1440,
        height=900,
        min_size=(960, 640),
        background_color="#070A11",
        text_select=True,
        zoomable=True,
        js_api=DesktopBridge(),
    )
    LOGGER.info("Opening the contained research workspace…")
    try:
        webview.start(
            gui="edgechromium" if os.name == "nt" else None,
            debug=debug,
            private_mode=False,
            storage_path=str(RUNTIME_DIR / "webview-profile"),
        )
    except Exception as exc:
        if os.name == "nt":
            raise RuntimeError(
                "The Microsoft WebView2 application runtime is unavailable. "
                "Noemorph does not use Chrome or an external browser; install the "
                "Evergreen WebView2 Runtime and run the application again."
            ) from exc
        raise
    finally:
        del window


def _parse_arguments(arguments: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch the Noemorph research atlas")
    parser.add_argument("--server-only", action="store_true", help="Run the API without a desktop window")
    parser.add_argument("--api-only", action="store_true", help="Run API endpoints without serving the built UI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0, help="Port; zero chooses an available local port")
    parser.add_argument("--skip-python-bootstrap", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--skip-install", action="store_true", help="Do not install frontend dependencies")
    parser.add_argument("--skip-build", action="store_true", help="Use the existing frontend build")
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args(arguments)


def main(arguments: Sequence[str] | None = None) -> int:
    raw_arguments = list(arguments if arguments is not None else sys.argv[1:])
    preliminary = _parse_arguments(raw_arguments)
    _configure_logging(preliminary.debug)
    _bootstrap_python_runtime(
        raw_arguments,
        skip=preliminary.skip_python_bootstrap,
    )

    if preliminary.host not in {"127.0.0.1", "localhost", "::1"} and not preliminary.api_only:
        raise RuntimeError(
            "Desktop mode is restricted to the local machine. Use --api-only only when "
            "an explicitly networked API is intended."
        )

    if not preliminary.api_only:
        _bootstrap_frontend(
            skip_install=preliminary.skip_install,
            skip_build=preliminary.skip_build,
        )

    server = None
    server_thread = None
    try:
        server, server_thread, selected_port, server_errors = _start_server(
            preliminary.host,
            preliminary.port,
            serve_frontend=not preliminary.api_only,
        )
        base_url = f"http://{preliminary.host}:{selected_port}"
        _wait_for_server(f"{base_url}/api/health", server_thread, server_errors)
        LOGGER.info("Research API ready at %s", base_url)

        if preliminary.server_only or preliminary.api_only:
            while server_thread.is_alive():
                server_thread.join(timeout=0.5)
                if server_errors:
                    raise RuntimeError("The local API stopped unexpectedly.") from server_errors[0]
        else:
            _run_desktop(base_url, debug=preliminary.debug)
    except KeyboardInterrupt:
        LOGGER.info("Stopping…")
    finally:
        if server is not None:
            server.should_exit = True
        if server_thread is not None:
            server_thread.join(timeout=5)
            if server_thread.is_alive() and server is not None:
                server.force_exit = True
                server_thread.join(timeout=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
