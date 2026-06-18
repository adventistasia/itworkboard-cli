---
lorespec: "0.1"
id: "2026061803"
date: "2026-06-18"
source: "opencode"
topic: "Windows CLI discoverability — self-path and PATH self-registration for pip-installed tools"
tags: [cli, packaging, windows, path, user-experience, typer]
classification:
  type: technical
  secondary_type: operational
  domains: [python-packaging, windows-administration, cli-tooling]
  value: medium
trails: [cli-installation, windows-tooling]
---

## Session Arc

### Started
User ran `workboard --help` and got "not recognized" — the CLI was installed but not on PATH.

### Pivots
- **Tooling → Packaging knowledge**: Diagnosing why `workboard.exe` wasn't found led into understanding pip's script-installation behavior on Windows.
- **Knowledge → Implementation**: Discussion of Python packaging defaults evolved into building a self-diagnosis and self-remediation feature directly into the tool.

### Ended
Two new commands added (`workboard self path`, `workboard self install`) that let the tool report its location and add itself to the User PATH. PATH was modified and verified.

## Artifacts

### A1 — `self` command group in `workboard-cli`

Two new commands added to `src/workboard_cli/cli.py`:

**`workboard self path`** — prints the absolute path of the entry-point executable:
```python
@self_app.command("path")
def self_path():
    print(Path(sys.argv[0]).resolve())
```

**`workboard self install`** — adds the Scripts directory to the User PATH via PowerShell's `[Environment]::SetEnvironmentVariable`:
```python
@self_app.command("install")
def self_install():
    scripts_dir = Path(sys.argv[0]).resolve().parent
    path_entry = str(scripts_dir)
    env_path = os.environ.get("PATH", "")
    if path_entry in env_path.split(os.pathsep):
        print(f"Already on PATH: {path_entry}")
        return
    import subprocess
    subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         f"[Environment]::SetEnvironmentVariable('Path', ... + ';{path_entry}', 'User')"],
        ...
    )
    os.environ["PATH"] = env_path + os.pathsep + path_entry
```

Also added `self_app` Typer sub-app and registered it as the `self` command group. Added `import os` and `import sys` to imports.

## Insights

### I1 — pip script destination varies by install scope on Windows

On Windows, `pip install` places console scripts (defined in `[project.scripts]` in `pyproject.toml`) into:

- **Per-user install** → `%APPDATA%\Python\Python{ver}\Scripts\`
- **System-wide install** → `{Python_root}\Scripts\`

These directories are often not on the user's PATH by default, especially the per-user one. pip warns about this during install but the message is easy to miss.

### I2 — Virtual environments isolate Scripts but sacrifice global discoverability

A venv's `Scripts\` folder is not on the system PATH unless explicitly added. Activating the venv adds it temporarily. This is by design — isolation vs. discoverability trade-off.

### I3 — No standard cross-platform self-discovery API for pip-installed CLIs

There is no single reliable way to determine at install time where a console script will land. The package author cannot control the destination — pip/sysconfig determines it. Runtime detection via `sys.argv[0]` (entry point) or `Path(__file__)` (module location) is the pragmatic fallback.

## Decisions

### D1 — Add runtime `self install` command for PATH registration

- **Decision**: Build PATH self-registration into the tool via `workboard self install`, rather than a pip post-install script or instructing users to add the directory manually.
- **Issue**: How should users fix the "not on PATH" problem after a per-user pip install?
- **Positions**: (1) pip post-install hook, (2) documentation-only, (3) runtime self-help command.
- **Arguments**: Post-install hooks are fragile across pip versions and build backends. Documentation is passive (users may not read it). A runtime command is discoverable (`--help`), self-contained, repeatable, and can update both the persistent User PATH and the current session's PATH atomically.
- **Warrant**: The tool is the most reliable source of truth for its own location — it can read `sys.argv[0]` at runtime. The user asked the tool "why can't I find you?" so the tool should answer and fix itself.
- **Qualifier**: in this case
- **Status**: settled

## Patterns

### P1 — CLI self-diagnosis command group

A CLI tool can expose a `self` or `doctor` command group for installation diagnostics. Useful patterns:

- `workboard self path` — prints the entry-point exe/script location
- `workboard self install` — adds the Scripts dir to User PATH (Windows only)
- Idempotent: `self install` checks if already on PATH before modifying

Scope: **local** (Windows Python CLI tools installed via pip).

## Connections

- D1 —[led_to]→ A1
- I1 —[informed_by]→ D1
- I3 —[informed_by]→ D1
- D1 —[instance_of]→ P1

## Trail Updates

- **cli-installation**: Added runtime self-diagnosis patterns for Windows CLI discoverability.
- **windows-tooling**: Documented pip script destination behavior per install scope; added self-registration pattern.
