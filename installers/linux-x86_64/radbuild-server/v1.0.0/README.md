# RadBuild Server v1.0.0 Linux Installer

This directory contains the Linux x86_64 installer payload for the compiled RadBuild v1.0.0 release.

## Install

Install RadBuild tools only with the release-level installer:

```sh
../../../install.py install --non-interactive
```

Install RadBuild tools, client, server, and systemd service from this component directory:

```sh
sudo ./install.sh
```

Install to a custom payload root and command wrapper directory:

```sh
../../../install.py install \
  --install-root "$HOME/.local/opt/radtools" \
  --bindir "$HOME/.local/bin" \
  --component radbuild-client \
  --non-interactive
```

When selected, the service installer writes, enables, and starts:

```text
/etc/systemd/system/radbuild-server.service
```

That service starts automatically on boot. To install server files without the service:

```sh
sudo ../../../install.py install \
  --component radbuild-client \
  --component radbuild-server \
  --non-interactive
```

To run the service as a specific user:

```sh
sudo ./install.sh --service-user <user>
```

The default system layout is:

```text
/opt/radtools/RadBuild/v1.0.0/bin/      Compiled RadBuild executables
/usr/bin/build_vivado                    Version-routing wrapper
/usr/bin/build_petalinux                 Version-routing wrapper
/usr/bin/radserver                       Version-routing wrapper
/usr/bin/<tool>-v1.0.0                   Version-routing wrapper pinned to this release
```

The unversioned wrappers inspect `--settings <project-path>/settings.json` or the nearest parent `settings.json`. If that file contains `"radbuild_version": "v1.0.0"`, the wrapper dispatches to `<radbuild-install-prefix>/bin/<tool>`. This keeps shell usage simple while still allowing multiple RadBuild versions to coexist.

## Programs

The payload includes compiled release executables:

- `radbuild`
- `radserver`
- `raddb`
- `radclient`
- `radworker`
- `radcodex_worker`
- `radbuildserver`
- `radllm`
- `radsetup`
- `build_vivado`
- `build_petalinux`

Create a starter project:

```sh
radbuild --createproject .
```

Scripted FPGA project creation:

```sh
radbuild --createproject <workspace-path> \
  --non-interactive \
  --workspace <workspace-path> \
  --project-type FPGA \
  --project-name <project-name> \
  --vendor xilinx \
  --modelseries artix7 \
  --part-number <fpga-part> \
  --tool vivado \
  --tool-version <vivado-version>
```

## Start Server

```sh
radserver serve --host 0.0.0.0 --port 8767
```

Service control:

```sh
sudo systemctl status radbuild-server
sudo systemctl restart radbuild-server
sudo systemctl disable --now radbuild-server
```

Runtime data is stored under:

```text
<radbuild-install-prefix>/radserver_data
```

## Project Commands

Prefer explicit project settings paths in automation:

```sh
build_vivado --settings <project-path>/settings.json --build-design
build_petalinux --settings <project-path>/settings.json
```

For interactive use, you may run commands from inside `<project-path>`:

```sh
cd <project-path>
build_vivado --list
build_petalinux --dry-run
```

Package a versioned BSP release:

```sh
build_petalinux --minor
build_petalinux --major
```

Package a smaller source/config BSP without generated pre-built images:

```sh
build_petalinux --minor --small-bsp
build_petalinux --minor --no-prebuilt
```

These commands update the configured PetaLinux `version_file` and write the BSP
under `petalinux/bsp_release/`. Keep the version file aligned with the latest
checked-in BSP; `1.0` plus `--minor` creates `v1.1`.

The small BSP mode skips `petalinux-package --prebuilt` and uses PetaLinux
`--exclude-from-file` during BSP packaging to omit `pre-built`, generated
images, build workspaces, downloads, and sstate caches.

Directly call this release if you need to bypass wrapper selection:

```sh
build_vivado-v1.0.0 --settings <project-path>/settings.json --list
```

Configure a RadBuild client:

```sh
radclient configure --server https://<server-host>:8767
radclient status
```

## Docs

Sanitized RadBuild documentation is copied under `docs/`. Paths use placeholders such as `<radbuild-install-prefix>`, `<project-path>`, and `<radbuild-workspace>`.
