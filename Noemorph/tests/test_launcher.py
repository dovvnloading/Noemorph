"""Launcher regression checks that do not download dependencies or start WebView2."""
from __future__ import annotations

import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import Noemorph as launcher


class DesktopLauncherQualityTests(unittest.TestCase):
    def test_frontend_cache_fingerprint_tracks_typescript_and_source_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            for name, content in {
                "package.json": "{}",
                "package-lock.json": "{}",
                "index.html": "<html></html>",
                "vite.config.ts": "export default {}",
                "tsconfig.json": '{"compilerOptions":{}}',
                "tsconfig.app.json": '{"compilerOptions":{}}',
                "tsconfig.node.json": '{"compilerOptions":{}}',
                "src/main.tsx": "export default 1",
            }.items():
                (root / name).write_text(content, encoding="utf-8")
            with patch.object(launcher, "FRONTEND_DIR", root):
                initial = launcher._frontend_fingerprint()
                self.assertEqual(initial, launcher._frontend_fingerprint())
                for config in ("tsconfig.json", "tsconfig.app.json", "tsconfig.node.json"):
                    path = root / config
                    before = path.read_text(encoding="utf-8")
                    path.write_text(before + " ", encoding="utf-8")
                    self.assertNotEqual(initial, launcher._frontend_fingerprint())
                    path.write_text(before, encoding="utf-8")
                    self.assertEqual(initial, launcher._frontend_fingerprint())

                source = root / "src/main.tsx"
                source.write_text("export default 2", encoding="utf-8")
                self.assertNotEqual(initial, launcher._frontend_fingerprint())

    def test_api_urls_support_ipv4_hostname_and_ipv6(self) -> None:
        self.assertEqual(launcher._api_base_url("127.0.0.1", 8765), "http://127.0.0.1:8765")
        self.assertEqual(launcher._api_base_url("localhost", 8765), "http://localhost:8765")
        self.assertEqual(launcher._api_base_url("::1", 8765), "http://[::1]:8765")

    def test_loopback_port_reservation_selects_correct_socket_family(self) -> None:
        with launcher._reserve_socket("127.0.0.1", 0) as listener:
            self.assertEqual(listener.family, socket.AF_INET)
            self.assertGreater(listener.getsockname()[1], 0)
        if not socket.has_ipv6:
            self.skipTest("IPv6 is unavailable on this host")
        try:
            with launcher._reserve_socket("::1", 0) as listener:
                self.assertEqual(listener.family, socket.AF_INET6)
                self.assertGreater(listener.getsockname()[1], 0)
        except OSError as exc:
            self.skipTest(f"IPv6 loopback is unavailable: {exc}")


if __name__ == "__main__":
    unittest.main()
