# RadBuild CLI Usage

This file covers direct CLI usage. For server/database/worker usage, see
`radserver/README.md` and `radserver/DATABASEUSAGE.md`.

## Source-Tree Mode

```bash
source <RadBuild-source-path>/radbuild/radbuild.sh
```

After sourcing:

```bash
radsetup
build_vivado
build_petalinux
radbuildserver.py
```

## Installed Frozen Mode

```bash
source <radbuild-install-prefix>/radbuild.sh
```

After sourcing:

```bash
radsetup
build_vivado
build_petalinux
radserver
raddb
radbuildserver
radclient
radworker
radcodex_worker
radllm
```

The installed release keeps runtime state in:

```text
<radbuild-install-prefix>/radserver_data/
```

## Workspace Setup

Register or create a workspace:

```bash
radsetup <radbuild-workspace>
```

Create a workspace symlink:

```bash
radsetup <radbuild-workspace> --link-target <real-workspace-path>
```

Fail instead of prompting for missing toolchains:

```bash
radsetup <radbuild-workspace> --non-interactive
```

Refresh this machine's profile:

```bash
radsetup <radbuild-workspace> --force
```

`radsetup` writes machine-local toolchain data to:

```text
radbuild-workspace/.userconfig/<username>-<hostname>.json
```

The RadBuild source/release registry is stored under `.radmeta/`.

## Project Settings

Most commands run from a project directory containing `settings.json`, or from a
child directory below it. You can also pass an explicit settings file:

```bash
build_vivado --settings <project-path>/settings.json --list
build_petalinux --settings <project-path>/settings.json --dry-run
```

Minimal shape:

```json
{
  "radbuild_version": "v1.0.0",
  "vendor": "xilinx",
  "modelseries": "zynq7",
  "projects": {
    "vivado": {
      "version": "2024.1",
      "project_name": "example_hw",
      "part_number": "xc7z020clg400-1"
    },
    "petalinux": {
      "version": "2024.1",
      "project_name": "example_linux",
      "template": "zynq",
      "bsp_release_dir": "bsp_release"
    }
  }
}
```

The top-level dispatchers load the requested implementation from:

```text
radbuild/.tools/v1.0.0/
```

## Vivado Commands

List discovered IP package scripts and testbenches:

```bash
build_vivado --list
```

Run package scripts and testbenches:

```bash
build_vivado
```

Run package scripts, testbenches, and the project design build:

```bash
build_vivado --build-design
```

After a successful design build, RadBuild runs `bootgen` to create an
FPGA-manager-ready `.bit.bin` next to the Vivado `.bit` file. Use
`--skip-bitbin` when only the raw Vivado bitstream is needed.

Package IP only:

```bash
build_vivado --skip-testbenches
```

Run testbenches only:

```bash
build_vivado --skip-packages
```

Run one target:

```bash
build_vivado --skip-packages tb_example.vhd
build_vivado example_ip/package_example_ip.tcl
```

Launch a generated Vivado testbench GUI project:

```bash
build_vivado --skip-packages --launch-testbench-gui tb_example.vhd
```

Generated outputs are normally under:

```text
hdl/testbench/
hdl/iprepo/
```

Package scripts receive:

```text
RADBUILD_VIVADO_PART
```

## PetaLinux Commands

Dry run:

```bash
build_petalinux --dry-run
```

Build/package:

```bash
build_petalinux
```

Build one PetaLinux component:

```bash
build_petalinux --component <recipe-name>
build_petalinux -c <recipe-name>
build_petalinux -c <recipe-name> --clean-component
```

Force rebuild:

```bash
build_petalinux --force
```

Deploy fast-update artifacts:

```bash
build_petalinux --deploy
```

Build SDK/sysroot:

```bash
build_petalinux --sdk-only
build_petalinux --sdk --sdk-dir <sdk-output-dir>
```

For PetaLinux 2024.1, RadBuild uses:

```text
petalinux-build --sdk
petalinux-package sysroot --sdk <sdk.sh> --dir <sdk_dir>
```

## Build Monitor

The branch monitor can run from source or installed release.

Source-tree mode:

```bash
radbuildserver.py --config <radbuildserver-config-path> --once
```

Installed mode:

```bash
radbuildserver --config <radbuild-install-prefix>/radserver_data/radbuildserver.json --once
```

When `workspace_dir` is configured, the monitor verifies setup first by running
`radsetup <workspace_dir> --non-interactive` through `radbuild.sh`. Build steps
run in a shell that has sourced `radbuild.sh`, so configs should prefer command
names such as `build_vivado` and `build_petalinux`.

Example:

```json
{
  "workspace_dir": "<radbuild-workspace>",
  "radbuild_dir": "<radbuild-install-prefix>",
  "auto_radsetup": true,
  "use_radbuild_shell": true,
  "review_db_cli": "<radbuild-install-prefix>/raddb",
  "projects": [
    {
      "name": "example",
      "path": "<project-path>",
      "remote": "origin",
      "branch": "main",
      "enabled": true,
      "build_steps": [
        {
          "name": "vivado",
          "issue_type": "hdl",
          "command": ["build_vivado", "--skip-testbenches"]
        }
      ]
    }
  ]
}
```

## Toolchain Resolution

RadBuild resolves toolchains using:

1. The active project's `vendor`, `modelseries`, and requested tool version.
2. The current machine's `.userconfig/<profile>.json`.
3. Typical install locations.
4. An interactive prompt, unless `--non-interactive` is used.

Typical Vivado locations:

```text
<vivado-install-root>/<version>
<vivado-install-root>/<version>
<vivado-install-root>/<version>
<vivado-install-root>/<version>
```

Typical PetaLinux locations:

```text
<petalinux-install-root>/<version>
<petalinux-install-root>/<version>
<petalinux-install-root>/<version>
<petalinux-install-root>/<version>
```
