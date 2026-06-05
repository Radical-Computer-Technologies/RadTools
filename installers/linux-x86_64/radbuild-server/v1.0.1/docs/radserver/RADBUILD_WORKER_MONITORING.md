# RadBuild Worker Monitoring

Workers are long-running processes that poll a RadBuild server, execute assigned
work, upload logs, and append task events. They should not approve evidence.

## Worker Loop

1. Start `radserver` first.
2. Configure/register a client with `radclient`.
3. Worker polls for a queued task assigned to its name/machine.
4. Worker starts only one task unless the task explicitly allows safe parallel
   work.
5. Worker emits `started`, `progress`, `passed`, `failed`, or `blocked` events.
6. Worker uploads full logs through `/api/logs/upload`.
7. Worker links build evidence before marking task complete.

## Commands

Installed release:

```bash
radclient configure --server https://SERVER:8767
radclient register --name command-local --type command --capability shell
radworker --name command-local --server https://SERVER:8767
```

Codex worker:

```bash
radclient register --name codex-local --type codex --capability codex-cli
radcodex_worker --agent codex-local --server https://SERVER:8767
```

Source tree:

```bash
python3 radserver/radclient.py configure --server https://SERVER:8767
python3 radserver/radworker.py --name command-local --server https://SERVER:8767
python3 radserver/radcodex_worker.py --agent codex-local --server https://SERVER:8767
```

## Build Monitor

The Git branch monitor is `radbuildserver`. It is separate from `radworker`.

Installed release:

```bash
nohup /home/jvincent/RadBuild/radbuildserver \
  --config /home/jvincent/RadBuild/radserver_data/radbuildserver.json \
  > /home/jvincent/RadBuild/radserver_data/radbuildserver.nohup.log 2>&1 &
```

Source tree:

```bash
nohup python3 radserver/radbuildserver.py \
  --config radserver/radbuildserver.json \
  > radbuildserver.nohup.log 2>&1 &
```

When `workspace_dir` is configured, the monitor runs `radsetup <workspace_dir>
--non-interactive` through `radbuild.sh` before building. Build steps should use
`build_vivado`, `build_litex`, and `build_petalinux` command names where possible.

## Systemd Example

```ini
[Unit]
Description=RadBuild server
After=network-online.target

[Service]
WorkingDirectory=/home/jvincent/RadBuild
ExecStart=/home/jvincent/RadBuild/radserver serve --host 0.0.0.0 --port 8767
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Guardrails

- Do not modify RadBuild tooling unless Joseph Vincent explicitly asks.
- Do not interrupt a running build unless cleanup/retry is requested or the
  build clearly failed.
- Do not mark a task complete until logs/evidence are linked.
- Do not create fake git fields for non-git work; use task/subtask IDs.
- Do not use `parallel_ok` to touch the same active project tree.
- Send heartbeat progress at least every five minutes during long work.
- Report all errors with command, exit code, log path, and relevant output.
