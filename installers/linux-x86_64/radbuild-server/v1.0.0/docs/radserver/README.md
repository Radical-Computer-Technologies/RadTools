# RadBuild Server

`radserver` is the web/API side of RadBuild. It owns task state, pending and
verified build evidence, users, API tokens, uploaded logs, and client/worker
registration.

## Start The Server

Installed release:

```bash
<radbuild-install-prefix>/radserver serve --host 0.0.0.0 --port 8767
```

Source tree:

```bash
python3 radserver/radserver.py serve --host 0.0.0.0 --port 8767
```

HTTPS is enabled by default with a self-signed certificate generated under the
runtime data directory. Use `--http` only for local debugging.

Fresh install:

```text
https://SERVER:8767/setup
```

Default login is `admin` / `admin`; first login requires a password change.

## Runtime Layout

Installed release:

```text
<radbuild-install-prefix>/
  radserver                 Frozen server executable.
  raddb                     Frozen DB CLI.
  radclient                 Frozen API client.
  radworker                 Generic task worker.
  radcodex_worker           Codex CLI worker.
  radllm                    Local LLM helper.
  radserver_data/
    build_review.sqlite3
    server_config.json
    radbuildserver.json
    certs/
    uploaded_logs/
```

Source tree defaults to `radserver/` for code and local runtime files unless
`RADSERVER_HOME` is set.

## Pages

- `/` main console.
- `/setup` first-run and server configuration.
- `/pending` unreviewed build evidence.
- `/verified` human-approved build evidence.
- `/tasks` compact task index.
- `/tasks/<id>` top-level task plus full subtask tree.
- `/logs` uploaded-log browser.
- `/account` current user, token, and user administration for admins.
- `/docs` built-in usage and API reference.

## Roles

- `admin`: full control, user creation/update, unrestricted project access, and
  evidence approval/rejection.
- `reviewer`: can approve/reject pending evidence inside configured project
  scopes.
- `developer`: token-oriented client/worker access; cannot approve evidence or
  create users.

Create users:

```bash
raddb user-add \
  --username developer01 \
  --role developer \
  --password temporary-password \
  --scopes '["/mnt/buildspace/project-a"]'

raddb user-list
raddb user-update developer01 --rotate-token
```

Scopes are path prefixes. Admins bypass scopes. Empty non-admin scopes mean
unrestricted non-admin visibility.

## Clients And Workers

Configure/register a client:

```bash
radclient discover
radclient configure --server https://SERVER:8767
radclient register --name codex-local --type codex --capability codex-cli
radclient clients
```

Generic command worker:

```bash
radworker --name command-local --server https://SERVER:8767
```

Codex CLI worker:

```bash
radcodex_worker --agent codex-local --server https://SERVER:8767
```

Workers should upload full logs and emit concise events. Humans review pending
database evidence afterward.

## Build Monitor

The Git branch build monitor is separate from the web server:

```bash
radbuildserver --config <radbuild-install-prefix>/radserver_data/radbuildserver.json
```

When configured with a `workspace_dir`, the monitor runs `radsetup
<workspace_dir> --non-interactive` through `radbuild.sh`, then executes build
steps from a sourced RadBuild shell. Build steps should use `build_vivado` and
`build_petalinux` command names where possible.

## Local LLM Helper

`radllm` drafts and validates JSON evidence or task-event JSON. It does not
approve records and does not run arbitrary shell commands.

```bash
export RADDB_OLLAMA_MODEL=qwen2.5-coder:7b
radllm draft-result --task-id 1 --log <build-log-path> --notes "summary" --out draft.json
radllm validate-result-json draft.json
raddb import-files draft.json
```
