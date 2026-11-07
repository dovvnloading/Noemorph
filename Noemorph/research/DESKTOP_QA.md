# Desktop bootstrap quality invariants

Noemorph's launcher builds an application-owned frontend unless `--skip-build`
is provided. Its build-cache fingerprint must include package manifests, Vite
config, **all root `tsconfig*.json` files**, index.html, and the source tree.
A TypeScript configuration edit must trigger a rebuild rather than silently
reuse a stale bundle.

The launcher accepts `--host ::1`. That path must reserve an IPv6 socket and
construct an HTTP URL using bracket notation (`http://[::1]:PORT`), including
for the server readiness check.

To verify on supported Python platforms:

```sh
cd Noemorph
python -m unittest tests.test_launcher -v
```

These lightweight unit tests do not replace the planned clean-install,
WebView2, offline bootstrap, recovery and packaged release tests on Windows.
