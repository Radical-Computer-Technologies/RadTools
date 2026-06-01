# RadBuild Database Usage

RadBuild stores curated build evidence in SQLite and treats JSON files as the
portable evidence format. Automation should add `pending` evidence; humans move
records to `verified` or `rejected`.

## Start And Review

Installed release:

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
https://SERVER:8767/pending
https://SERVER:8767/verified
```

Fresh install starts at `/setup`. Default login is `admin` / `admin`, followed
by forced password change.

## CLI Basics

Installed release:

```bash
raddb init
raddb stats
raddb list --status pending
```

Source tree:

```bash
python3 radserver/raddb.py init
python3 radserver/raddb.py stats
python3 radserver/raddb.py list --status pending
```

Add a record:

```bash
raddb add \
  --issue-type hdl \
  --build-stage testbench \
  --result success \
  --status pending \
  --repo-path <project-path> \
  --tags '["vivado","testbench"]' \
  --retrieval-summary "Self-checking VHDL testbench passed" \
  --principles '{"summary":"Testbench passed","impact":"HDL behavior is ready for review"}' \
  --build '{"tool":"vivado-xsim","command":"build_vivado --skip-packages tb_example.vhd"}'
```

Approve/reject:

```bash
raddb approve 12 --note "reviewed logs"
raddb reject 13 --note "missing artifact link"
```

## Evidence Fields

Required core fields:

- `issue_type`: `hdl`, `fsbl`, `uboot`, `kdriver`, `userspace`, or
  `hardware_test`
- `build_stage`: `static_analysis`, `elaboration`, `testbench`, `full_build`,
  `unit_test`, `integration_test`, `package_build`, `smoke_test`,
  `hardware_smoke`, `hardware_loop`, `live_verification`, or `unspecified`
- `result`: `success` or `fail`
- `principles`: short JSON explanation of the issue/result
- `build`: JSON details including command, tool, exit code, artifact/log paths

Retrieval fields:

- `repo_path`, `repo_url`, `branch`
- `commit_before`, `commit_after`
- `git_current`, `git_previous`, `git_future`
- `previous_task_id`, `future_task_id`
- `changed_files`, `artifact_paths`, `log_paths`
- `tool_version`, `migration_from`, `migration_to`
- `tags`, `retrieval_summary`, `human_status`
- `live` for live hardware-loop evidence

Use git fields only for real git repository state. Use task/subtask IDs for
workflow ordering when no real git repo applies.

## JSON Import, Export, And Compression

Import JSON or `.json.gz` evidence:

```bash
raddb import-files build_results_json
raddb import-files exported_results/result-12.json.gz
```

Export rows to portable JSON files:

```bash
raddb export-files --out-dir exported_results
```

Compress individual files:

```bash
raddb compress-json --source build_results_json --out-dir build_results_json_gz
```

Create one archive:

```bash
raddb archive-json --source build_results_json --out backups/build-results-json.tar.gz
```

## SQLite Backup And Migration

Backup:

```bash
raddb backup
```

Installed runtime DB:

```text
<radbuild-install-prefix>/radserver_data/build_review.sqlite3
```

Source-tree runtime DB:

```text
RadBuild/radserver/build_review.sqlite3
```

For migration to a fresh machine, copy either:

- the SQLite DB or a backup from `backups/`
- exported JSON evidence files
- uploaded logs if those links matter

Then use `/setup` in the browser to import a local database, or:

```bash
raddb init
raddb import-files exported_results
raddb stats
```

## Tasks

Tasks are orchestration state; build results are evidence.

Humans create top-level tasks. Agents/workers create subtasks, append events,
upload logs, and link evidence.

```bash
raddb task-add \
  --title "Run Vivado smoke test" \
  --objective "Build and record HDL testbench result" \
  --status queued \
  --project-path <project-path> \
  --assigned-agent command-local \
  --tags '["hdl","vivado"]'

raddb task-event 1 \
  --event-type progress \
  --progress 50 \
  --message "simulation running" \
  --agent command-local

raddb task-link 1 \
  --link-type log \
  --path <build-log-path> \
  --note "full build log"
```

The web UI shows compact task cards at `/tasks` and full hierarchy at
`/tasks/<id>`.

## API And Logs

API write calls use a bearer token from `/account`:

```bash
curl -k -X POST https://SERVER:8767/api/tasks/1/events \
  -H "Authorization: Bearer $RADDB_API_TOKEN" \
  -H "content-type: application/json" \
  -d '{"event_type":"progress","message":"worker heartbeat","progress":50}'
```

Upload a large log:

```bash
curl -k -X POST "https://SERVER:8767/api/logs/upload?task_id=1&note=worker-log" \
  -H "Authorization: Bearer $RADDB_API_TOKEN" \
  -F "file=@<build-log-path>"
```

The `/logs` page browses the configured temporary log directory hierarchy.

## AI CLI Rules

AI agents using `raddb` must follow these rules:

1. Query before repeating work.
2. Prefer source JSON evidence plus `raddb import-files`.
3. Never mark automation output as `verified`.
4. Always set precise `issue_type`, `build_stage`, and `result`.
5. Report every error with command, exit code, log path, and error lines.
6. Never overwrite historical JSON evidence.
7. Check prior failures before repeating a known-bad build path.
8. Use task hierarchy for workflow order.
9. Keep pending and verified separate.
10. Store large logs as files and link them.
11. Backup/export before migration or destructive local changes.
