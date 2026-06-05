# RadBuild CLI Usage

This file covers direct CLI usage. For server/database/worker usage, see
`radserver/README.md` and `radserver/DATABASEUSAGE.md`.

## Source-Tree Mode

```bash
source /path/to/RadBuild/radbuild/radbuild.sh
```

After sourcing:

```bash
radbuild
radsetup
build_vivado
build_petalinux
build_litex
radbuildserver.py
```

## Installed Frozen Mode

```bash
source /home/jvincent/RadBuild/radbuild.sh
```

For versioned installs, source the versioned install root or use the generated
`/usr/bin` wrappers:

```bash
source /home/jvincent/RadTools/RadBuild/v1.0.1/radbuild.sh
build_litex --help
```

After sourcing:

```bash
radbuild
radsetup
build_vivado
build_petalinux
build_litex
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
/home/jvincent/RadBuild/radserver_data/
```

Versioned installs keep the same state under the version root:

```text
/home/jvincent/RadTools/RadBuild/v1.0.1/radserver_data/
```

## Workspace Setup

Register or create a workspace:

```bash
radsetup /path/to/radbuild-workspace
```

Create a workspace symlink:

```bash
radsetup /path/to/radbuild-workspace --link-target /real/workspace/path
```

Fail instead of prompting for missing toolchains:

```bash
radsetup /path/to/radbuild-workspace --non-interactive
```

Refresh this machine's profile:

```bash
radsetup /path/to/radbuild-workspace --force
```

`radsetup` writes machine-local toolchain data to:

```text
radbuild-workspace/.userconfig/<username>-<hostname>.json
```

The RadBuild source/release registry is stored under `.radmeta/`. Versioned
installs use `.radmeta/toolchains.json` for global toolchain defaults and
`.radmeta/radworkspaces.json` for registered workspaces.

## Project Creation

Open the curses project wizard:

```bash
radbuild --createproject .
```

The wizard supports FPGA and FPGA-MPSoC templates. It lists registered
workspaces, asks for project name, vendor, part family, FPGA part number,
Vivado version, and for FPGA-MPSoC projects also asks for PetaLinux version.

Force the curses UI or plain text fallback:

```bash
radbuild --createproject . --ui curses
radbuild --createproject . --ui text
```

Create a project noninteractively:

```bash
radbuild --createproject /path/to/radbuild-workspace \
  --non-interactive \
  --workspace /path/to/radbuild-workspace \
  --project-type FPGA \
  --project-name example_fpga \
  --vendor xilinx \
  --modelseries artix7 \
  --part-number xc7a35tcsg324-1 \
  --tool vivado \
  --tool-version 2023.1
```

Create an FPGA-MPSoC project:

```bash
radbuild --createproject /path/to/radbuild-workspace \
  --non-interactive \
  --workspace /path/to/radbuild-workspace \
  --project-type FPGA-MPSoC \
  --project-name example_mpsoc \
  --vendor xilinx \
  --modelseries zus+ \
  --part-number xczu3eg-sfvc784-1-e \
  --tool vivado \
  --tool-version 2023.1 \
  --linux-build-system petalinux \
  --linux-version 2023.2
```

## Project Settings

Most commands run from a project directory containing `settings.json`, or from a
child directory below it. You can also pass an explicit settings file:

```bash
build_vivado --settings /path/to/project/settings.json --list
build_petalinux --settings /path/to/project/settings.json --dry-run
build_litex --settings /path/to/project/settings.json --list
```

Minimal shape:

```json
{
  "radbuild_version": "v1.0.1",
  "vendor": "xilinx",
  "modelseries": "zus+",
  "projects": {
    "vivado": {
      "version": "2024.1",
      "project_name": "example_hw",
      "part_number": "xczu3eg-sbva484-1-e"
    },
    "petalinux": {
      "version": "2024.1",
      "project_name": "example_linux",
      "template": "zynqMP",
      "bsp_release_dir": "bsp_release"
    },
    "litex": {
      "version": "local",
      "project_name": "example_litex",
      "source_dir": ".",
      "script": "litex_m2sdr.py",
      "backend_tool": "vivado",
      "default_args": ["--variant=m2"],
      "build_args": ["--build"]
    }
  }
}
```

The top-level dispatchers load the requested implementation from:

```text
radbuild/.tools/v1.0.1/
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

## LiteX Commands

Print the resolved LiteX command, backend settings, and configured artifact
copies:

```bash
build_litex --list
```

Run the configured LiteX command:

```bash
build_litex
```

Print the command without running it:

```bash
build_litex --dry-run
```

Append one-off LiteX arguments:

```bash
build_litex --extra-arg --with-pcie-dma-probe
build_litex -- --with-pcie-dma-probe
```

Run the SoC script without the configured `--build` argument:

```bash
build_litex --no-build
```

The `projects.litex` settings object supports:

```json
{
  "version": "local",
  "project_name": "litex_m2sdr_m2_pcie_x1_neuma_spi_hopper_neuma_axi_ila_no_jtagbone",
  "source_dir": ".",
  "script": "litex_m2sdr.py",
  "backend_tool": "vivado",
  "default_args": [
    "--variant=m2",
    "--with-pcie",
    "--pcie-lanes=1",
    "--without-jtagbone",
    "--with-neuma-native-spi-hopper",
    "--with-neuma-axi-ila"
  ],
  "build_args": ["--build"],
  "copy_bitstreams": [
    {
      "source": "build/{build_name}/gateware/{build_name}.bin",
      "dest": "host/litex-m2sdr-base-macos-port/neuma_litexm2sdr_operational.bin"
    }
  ]
}
```

`backend_tool` defaults to `vivado`; keep a matching `projects.vivado` section
in the same `settings.json` so RadBuild can source Vivado before invoking the
LiteX script. Set `backend_tool` to `false` only for non-synthesis utility
flows that do not need a vendor backend.

## PetaLinux Commands

Dry run:

```bash
build_petalinux --dry-run
```

Build/package:

```bash
build_petalinux
```

Package a BSP release:

```bash
build_petalinux --minor
build_petalinux --major
```

Package a smaller BSP without PetaLinux pre-built images:

```bash
build_petalinux --minor --small-bsp
build_petalinux --minor --no-prebuilt
```

`--small-bsp` and `--no-prebuilt` skip `petalinux-package --prebuilt` and pass
an exclude file to `petalinux-package --bsp --exclude-from-file`. This keeps
generated `pre-built`, `images`, `build`, workspace, download, and sstate cache
payloads out of the BSP while preserving the source/config project content.

Build one PetaLinux component:

```bash
build_petalinux --component ad9363-neuma-fasthop
build_petalinux -c ad9363-neuma-fasthop-spifix
build_petalinux -c ad9363-neuma-fasthop-spifix --clean-component
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
build_petalinux --sdk --sdk-dir /tmp/example-sdk
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
radbuildserver.py --config /path/to/radbuildserver.json --once
```

Installed mode:

```bash
radbuildserver --config /home/jvincent/RadBuild/radserver_data/radbuildserver.json --once
```

When `workspace_dir` is configured, the monitor verifies setup first by running
`radsetup <workspace_dir> --non-interactive` through `radbuild.sh`. Build steps
run in a shell that has sourced `radbuild.sh`, so configs should prefer command
names such as `build_vivado`, `build_litex`, and `build_petalinux`.

Example:

```json
{
  "workspace_dir": "/path/to/radbuild-workspace",
  "radbuild_dir": "/home/jvincent/RadBuild",
  "auto_radsetup": true,
  "use_radbuild_shell": true,
  "review_db_cli": "/home/jvincent/RadBuild/raddb",
  "projects": [
    {
      "name": "example",
      "path": "/path/to/project",
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
~/xilinx/Vivado/<version>
~/Xilinx/Vivado/<version>
/opt/Xilinx/Vivado/<version>
/tools/Xilinx/Vivado/<version>
```

Typical PetaLinux locations:

```text
~/xilinx/petalinux/<version>
~/Xilinx/petalinux/<version>
/opt/pkg/petalinux/<version>
/tools/Xilinx/petalinux/<version>
```

LiteX normally uses the active Python environment. RadBuild records it under
the `litex` tool entry with a `/bin/true` settings placeholder unless a global
toolchain registry overrides it. Xilinx LiteX bitstream builds still source the
configured Vivado backend through `projects.vivado`.

## Publishing The RadTools Release

`build_release.py` builds native PyInstaller executables and, when the
`RadTools` submodule exists, republishes the RadBuild payload into:

```text
RadTools/installers/linux-x86_64/radbuild-server/v1.0.1/
```

The RadTools payload layout is installer-native:

```text
payload/bin/<radbuild-command>
payload/radbuild.sh
docs/
templates/server_config.json
templates/radbuildserver.json
```

Build and publish into the submodule without committing:

```sh
python3 build_release.py --mode native
```

Build, commit the updated RadTools payload from inside the submodule, and push
that public release repository:

```sh
python3 build_release.py --mode native --radtools-commit --radtools-push
```

Useful options:

```text
--radtools-dir <path>       Use a RadTools checkout outside ./RadTools.
--no-radtools-publish      Skip RadTools publishing.
--radtools-commit-message  Override the RadTools release commit message.
```
