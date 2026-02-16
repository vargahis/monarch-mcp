# Releasing

This document covers the release process for the Monarch MCP Server package.

## Version Scheme

Versions follow [PEP 440](https://peps.python.org/pep-0440/) and are derived automatically from git tags via [setuptools-scm](https://setuptools-scm.readthedocs.io/). No version numbers are hardcoded in source files.

| Stage | Tag pattern | Example | Purpose |
|---|---|---|---|
| Dev | `vX.Y.Z.devN` | `v1.0.0.dev1` | Early development builds |
| Alpha | `vX.Y.ZaN` | `v1.0.0a1` | Feature-incomplete previews |
| Beta | `vX.Y.ZbN` | `v1.0.0b1` | Feature-complete, testing |
| Release candidate | `vX.Y.ZrcN` | `v1.0.0rc1` | Final validation before stable |
| Stable | `vX.Y.Z` | `v1.0.0` | Production release |

## Publish Routing

The CI pipeline automatically routes packages based on the tag:

| Target | Versions | Index URL |
|---|---|---|
| **TestPyPI** | dev, alpha, beta | https://test.pypi.org/project/monarch-mcp/ |
| **PyPI** | rc, stable | https://pypi.org/project/monarch-mcp/ |

This lets contributors test pre-release packages from TestPyPI without polluting the production PyPI index. Once a version reaches RC quality, it goes straight to PyPI.

## How to Release

1. **Ensure `main` is up to date** with all changes you want to release.

2. **Create and push a tag**:
   ```bash
   git tag v1.0.0b1
   git push origin v1.0.0b1
   ```

3. **CI runs automatically**:
   - Pylint and pytest must pass (CI gate)
   - Package is built (sdist + wheel)
   - Tag pattern determines TestPyPI or PyPI target
   - Package is published via OIDC trusted publishing

4. **GitHub Release is created** with the `.mcpb` bundle attached. Dev/alpha/beta tags are automatically marked as pre-releases.

## Installing Pre-release Versions

To install a pre-release version from TestPyPI for testing:

```bash
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ monarch-mcp
```

The `--extra-index-url` flag ensures dependencies are still resolved from PyPI.

## CI Gate

Every publish (TestPyPI or PyPI) requires the CI workflow to pass first. This includes:

- `pylint` scoring 10.00/10
- `pytest` with 90%+ coverage

The publish workflow reuses `ci.yml` via `workflow_call`.

## MCP Bundle

The `.mcpb` bundle is built for every tagged version and attached to the GitHub Release. Pre-release tags (dev, alpha, beta) are automatically flagged as pre-releases on GitHub.

## GitHub Repository Setup

For trusted publishing (OIDC) to work, the repository needs two GitHub Environments configured:

### 1. Create Environments

In **Settings > Environments**, create:

- **`testpypi`** — used for dev/alpha/beta publishes
- **`pypi`** — used for rc/stable publishes (optionally add a required reviewer for extra safety)

### 2. Configure Trusted Publishers

#### TestPyPI

At https://test.pypi.org/manage/project/monarch-mcp/settings/publishing/:

| Field | Value |
|---|---|
| Owner | `vargahis` |
| Repository | `monarch-mcp` |
| Workflow name | `publish.yml` |
| Environment name | `testpypi` |

#### PyPI

At https://pypi.org (use "Add a new pending publisher" if the project doesn't exist yet):

| Field | Value |
|---|---|
| Owner | `vargahis` |
| Repository | `monarch-mcp` |
| Workflow name | `publish.yml` |
| Environment name | `pypi` |
