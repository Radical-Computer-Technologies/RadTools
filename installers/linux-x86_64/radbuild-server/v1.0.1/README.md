# RadBuild

RadBuild is an embedded-systems build toolset with two normal operating modes:

- **Local CLI mode:** source `radbuild.sh`, then run `radsetup`,
  `build_vivado`, `build_litex`, `build_petalinux`, and `radbuildserver` by hand.
- **Server/worker mode:** run the RadBuild web/API server, assign tasks in the
  browser, and let registered clients, workers, Codex, or local LLM helpers
  report progress and database evidence.

The current implementation focuses on Xilinx Vivado, LiteX, and PetaLinux
flows, plus a SQLite-backed review database for curated
build/test/live-verification evidence.

## Repository Layout

```text
RadBuild/
  build_release.py       Builds native PyInstaller executables.
  radbuildinstall.py     Installs a frozen release into a chosen directory.
  RadTools/              Public release repository submodule.
  radbuild/
    radbuild.sh          Source-tree shell entry point.
    USAGE.md             CLI and build-monitor usage.
    .tools/              Dispatchers and versioned build scripts.
    .tools/v1.0.1/       Current RadBuild implementation.
    .radmeta/            Local workspace registry metadata.
  radserver/
    app.py               HTTPS web UI and API.
    raddb.py             SQLite database CLI.
    radbuildserver.py    Git branch monitor/build runner.
    radclient.py         Client API wrapper.
    radworker.py         Generic command worker.
    radcodex_worker.py   Codex CLI worker.
    radllm.py            Local LLM JSON drafting/validation helper.
```

Generated release folders contain native executables at the install root and
runtime state under `radserver_data/`.

## Build A Native Release

PyInstaller is required for frozen native executables:

```bash
python3 -m pip install --user --upgrade pyinstaller
cd /mnt/TEAMV_FILES/radbuild_workspace/RadBuild
python3 build_release.py --mode native
```

This writes:

```text
/mnt/TEAMV_FILES/radbuild_workspace/radbuild-release1v01/
RadBuild/release/radbuild-release1v01/
RadBuild/release/radbuild-release1v01-native.tar.gz
RadBuild/RadTools/installers/linux-x86_64/radbuild-server/v1.0.1/
```

Executables currently produced:

```text
radbuild
build_vivado
build_petalinux
build_litex
radsetup
radserver
raddb
radbuildserver
radclient
radworker
radcodex_worker
radllm
```

When the `RadTools` submodule is present, `build_release.py` also republishes
the RadBuild payload, docs, and runtime templates into the public RadTools
installer tree. To publish the release repository in the same command:

```bash
python3 build_release.py --mode native --radtools-commit --radtools-push
```

Use `--no-radtools-publish` to build only the local release directory and
`RadBuild/release` mirror.

The release builder intentionally excludes live SQLite databases, uploaded logs,
worker logs, private TLS keys, and machine-specific server config from the
embedded payload. Fresh runtime config is created in `radserver_data/`.

## Install A Frozen Release

Flat install target:

```bash
cd /mnt/TEAMV_FILES/radbuild_workspace/RadBuild
python3 radbuildinstall.py \
  --source /mnt/TEAMV_FILES/radbuild_workspace/radbuild-release1v01 \
  --install-dir /home/jvincent/RadBuild
```

Versioned install target with `/usr/bin`-style dispatch wrappers:

```bash
python3 radbuildinstall.py \
  --source /mnt/TEAMV_FILES/radbuild_workspace/radbuild-release1v01 \
  --install-dir /home/jvincent/RadTools/RadBuild/v1.0.1 \
  --layout versioned \
  --wrapper-dir /usr/bin \
  --radbuild-root /home/jvincent/RadTools/RadBuild
```

The installer preserves existing `radserver_data/server_config.json`,
`radserver_data/radbuildserver.json`, `.radmeta/toolchains.json`, and runtime
data unless `--overwrite-config` is passed. The versioned layout places
executables under `bin/`, runtime state under `radserver_data/`, and the global
tool registry under `.radmeta/toolchains.json`.

After install:

```bash
source /home/jvincent/RadBuild/radbuild.sh
radsetup /path/to/radbuild-workspace
build_vivado --help
build_litex --help
build_petalinux --help
radserver serve --host 0.0.0.0 --port 8767
```

When `/usr/bin` wrappers are installed, commands such as `build_litex` dispatch
through `RADBUILD_ROOT/<radbuild_version>/bin/<tool>`, defaulting to the
configured install root.

Open:

```text
https://SERVER:8767/setup
```

On a fresh install, login is `admin` / `admin`; the server requires changing the
password before write actions.

## Source-Tree CLI Usage

Without frozen executables:

```bash
source /mnt/TEAMV_FILES/radbuild_workspace/RadBuild/radbuild/radbuild.sh
radsetup /mnt/TEAMV_FILES/radbuild_workspace/radbuild_workspace --non-interactive
cd /path/to/project-with-settings-json
build_vivado
build_litex --list
build_petalinux --dry-run
```

Project settings select tool versions, vendor/model family, Vivado part number,
and PetaLinux project details. See [radbuild/USAGE.md](radbuild/USAGE.md).

## Server Usage

Installed executable:

```bash
/home/jvincent/RadBuild/radserver serve --host 0.0.0.0 --port 8767
```

Source tree:

```bash
python3 radserver/radserver.py serve --host 0.0.0.0 --port 8767
```

The server provides:

- HTTPS web UI
- setup page and database migration
- pending/verified build evidence review
- task hierarchy with subtasks and events
- client/worker registration
- uploaded log storage and cleanup
- role-based users: `admin`, `reviewer`, `developer`
- API tokens for clients/workers

See [radserver/README.md](radserver/README.md) and
[radserver/DATABASEUSAGE.md](radserver/DATABASEUSAGE.md).

## Client, Worker, And LLM Driver

Clients discover/configure a server and register themselves:

```bash
radclient discover
radclient configure --server https://SERVER:8767
radclient register --name codex-local --type codex --capability codex-cli
radclient tasks
radclient task-summary 1
```

Generic command worker:

```bash
radworker --name command-local --server https://SERVER:8767
```

Codex CLI worker:

```bash
radcodex_worker --agent codex-local --server https://SERVER:8767
```

Local LLM helper for Qwen/Ollama-style intake:

```bash
radllm draft-result --task-id 1 --log /path/to/build.log --notes "summary" --out draft.json
radllm validate-result-json draft.json
raddb import-files draft.json
```

Automation should create pending evidence and task events. Human reviewers
approve or reject evidence in the browser or with `raddb`.

## Guardrails

- Do not modify RadBuild tooling unless Joseph Vincent explicitly requests it.
- Do not approve evidence from automation.
- Use git fields only when real git state exists.
- Use task/subtask IDs for workflow order when no real git repo applies.
- Store large logs as files and link paths; keep database rows concise.
- Record failures with command, exit code, log path, and relevant error lines.
