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
- **Python and npm advisories (non-blocking baseline):** these checks deliberately
  continue on error until existing advisories have been triaged. A successful CI
  run does not mean every dependency is free of known advisories.
- **Dependabot:** weekly update proposals, requiring ordinary CI and review.

Before release, review non-blocking advisory output and create tracked remediation
issues for confirmed reachable vulnerabilities. Promote audit steps to blocking
after establishing a passing baseline.

## Repository settings still required

Enable GitHub's Dependency Graph and set `NOEMORPH_DEPENDENCY_GRAPH_ENABLED=true` before requiring the dependency-review job. The action fails otherwise with a repository-unsupported error.\n\nGitHub branch rules are configured in the repository settings, not by checked-in
workflow YAML. Protect `main` by requiring:
1. PRs for changes; do not permit force pushes or branch deletion.
2. Existing Python, public export, frontend build and public-site smoke jobs,
   plus the Python quality, CodeQL, and dependency-review checks where available.
3. At least one independent approval **where a second qualified reviewer exists**.
   Do not silently treat an author's self-review as independent review.
4. Require branches to be current with `main` before merging.

Do not enable checks by guessed names; wait for the new CI workflow to finish
and select the exact check names shown in GitHub's branch rules UI.
