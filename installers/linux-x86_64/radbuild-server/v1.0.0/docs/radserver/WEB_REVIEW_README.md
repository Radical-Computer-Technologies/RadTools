# RadBuild Web Review UI

The web UI is served by `radserver`. It is the human-facing console for setup,
task assignment, evidence review, log browsing, user management, and API token
access.

## Start

Installed:

```bash
<radbuild-install-prefix>/radserver serve --host 0.0.0.0 --port 8767
```

Source tree:

```bash
python3 radserver/radserver.py serve --host 0.0.0.0 --port 8767
```

Open:

```text
https://SERVER:8767/
```

The server uses HTTPS by default with a self-signed certificate. Use `--http`
only for local debugging.

## First Run

Open `/setup`. Until setup is complete, only setup/docs/static assets and setup
APIs are available.

Setup configures:

- LAN base URL
- one or more build servers
- temporary uploaded-log folder
- log retention and cleanup interval
- dark/light theme
- API token generation
- optional existing SQLite database migration

Default browser login is `admin` / `admin`; password change is required on
first login.

Installed runtime files are under:

```text
<radbuild-install-prefix>/radserver_data/
```

## Pages

- `/` main navigation.
- `/setup` server configuration and database migration.
- `/pending` unreviewed build evidence.
- `/verified` human-approved build evidence.
- `/tasks` compact task list, grouped to reduce review fatigue.
- `/tasks/<id>` full task/subtask tree with events and links.
- `/logs` browses uploaded logs.
- `/account` token display and user administration.
- `/docs` built-in documentation.

## Task Model

- Humans create top-level tasks.
- Agents/workers create subtasks.
- Events are append-only progress/status records.
- Evidence links connect tasks to build result rows, logs, artifacts, or URLs.
- Git fields are only for real git state.
- Non-git workflow order uses task IDs and subtask relationships.

## Users

Roles:

- `admin`: full control.
- `reviewer`: approve/reject pending evidence within scopes.
- `developer`: token/client/worker usage, no review approval.

Admins can create users from `/account` or CLI:

```bash
raddb user-add \
  --username reviewer01 \
  --role reviewer \
  --password temporary-password \
  --scopes '["<project-path>"]'
```

## API

Read examples:

```bash
curl -k https://SERVER:8767/api/tasks/tree
curl -k https://SERVER:8767/api/results?status=pending
curl -k https://SERVER:8767/api/results/12
```

Write examples use `/account` token:

```bash
curl -k -X POST https://SERVER:8767/api/tasks/1/events \
  -H "Authorization: Bearer $RADDB_API_TOKEN" \
  -H "content-type: application/json" \
  -d '{"event_type":"progress","message":"heartbeat","progress":50}'
```

Upload log:

```bash
curl -k -X POST "https://SERVER:8767/api/logs/upload?task_id=1&note=worker-log" \
  -H "Authorization: Bearer $RADDB_API_TOKEN" \
  -F "file=@<build-log-path>"
```

## Client And Worker Flow

```bash
radclient discover
radclient configure --server https://SERVER:8767
radclient register --name command-local --type command --capability shell
radworker --name command-local --server https://SERVER:8767
```

Codex:

```bash
radclient register --name codex-local --type codex --capability codex-cli
radcodex_worker --agent codex-local --server https://SERVER:8767
```

LLM helper:

```bash
radllm draft-result --task-id 1 --log <build-log-path> --notes "summary" --out draft.json
radllm validate-result-json draft.json
raddb import-files draft.json
```

Use `radclient task-summary <id>` for token-efficient status before retrieving
full logs.
