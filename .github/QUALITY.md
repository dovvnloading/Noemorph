# Noemorph engineering quality gates

The CI suite continues to run Python unit tests, deterministic catalog/export
checks, the frontend production build, and public JavaScript smoke tests.

Additional checks:
- **Critical Ruff checks (blocking):** Python syntax-level errors, undefined names,
  and related high-confidence diagnostics across the project. This is an initial
  baseline, not a substitute for broader lint and formatting rules.
- **CodeQL (blocking once GitHub's code scanning is available):** static security
  analysis for Python and JavaScript/TypeScript.
- **Dependency review (requires repository setup):** detects newly introduced vulnerable dependencies on PRs. It is disabled until the GitHub Dependency Graph is enabled under Settings → Security and analysis, and the repository Actions variable `NOEMORPH_DEPENDENCY_GRAPH_ENABLED` is set to `true`. An unset variable causes the job to be skipped, not passed.
- **Windows desktop smoke (blocking when enabled):** a Windows-hosted Python 3.14
  environment installs the pinned application requirements, validates CLR and
  WebView2 Python wrapper imports, and runs portable launcher regression tests.
  This verifies dependency installability, not real WebView2 UI or a packaged
  offline install; those remain tracked in #19.
- **Research dependency smoke (blocking when enabled):** independently install
  the research requirements, run `pip check`, and import NumPy, pypdf, and
  Beautiful Soup. This covers dependencies that the application-only Python
  test installation does not exercise.
- **Python and npm advisories (non-blocking baseline):** these checks deliberately
  continue on error until existing advisories have been triaged. A successful CI
  run does not mean every dependency is free of known advisories.
- **Dependabot:** staggered weekly updates with an open version-PR limit of three per
  configured ecosystem. Routine minor/patch updates are grouped where appropriate,
  React/runtime/types move together, while fixed `python-numpy` and
  `python-pypdf` groups cover both Python manifests. Other Python minor/patch
  updates use a routine group; unrelated Python major updates remain separate.
  Individual major updates still require compatibility review. Grouping is not
  an auto-merge policy. Avoid Dependabot's dynamic `group-by: dependency-name`
  until its reported rebase issue is fixed (dependabot/dependabot-core#14780).

When reviewing dependency PRs:
- Treat skipped dependency review as **not assessed**, even when CI is green.
- Revalidate against current `main`, including relevant browser/desktop or Windows
  integration tests that may not have existed when an older PR first ran.
- Review lockfile peer dependencies together; do not use `--force` or
  `--legacy-peer-deps` to conceal an incompatible React/types combination.
- Keep major UI/graph-library updates separate until their integrations are migrated,
  and verify the user-visible behavior before merging.

Before release, review non-blocking advisory output and create tracked remediation
issues for confirmed reachable vulnerabilities. Promote audit steps to blocking
after establishing a passing baseline.

## Repository settings still required

Enable GitHub's Dependency Graph and set `NOEMORPH_DEPENDENCY_GRAPH_ENABLED=true` before requiring the dependency-review job. The action fails otherwise with a repository-unsupported error.

GitHub branch rules are configured in the repository settings, not by checked-in
workflow YAML. Protect `main` by requiring:
1. PRs for changes; do not permit force pushes or branch deletion.
2. Existing Python, public export, frontend build and public-site smoke jobs,
   plus the Python quality, CodeQL, and dependency-review checks where available.
3. At least one independent approval **where a second qualified reviewer exists**.
   Do not silently treat an author's self-review as independent review.
4. Require branches to be current with `main` before merging.

Do not enable checks by guessed names; wait for the new CI workflow to finish
and select the exact check names shown in GitHub's branch rules UI.
