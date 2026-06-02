# RadTools

RadTools is the release repository for RadBuild, RadFPGA Debug Hub, reusable
FPGA debug HDL, and PetaLinux support layers.

This repository is intentionally biased toward installable artifacts and
release collateral. Desktop application source belongs in a separate tool
source repository. HDL and PetaLinux layer sources may live here because they
are directly consumed by FPGA and PetaLinux builds.

## Current Release

`crimson` is the first release branch.

```text
RadTools v1.0.0 - Crimson
Platform: linux-x86_64
Installer: installers/linux-x86_64/install.py
```

Install interactively:

```sh
cd installers/linux-x86_64
sudo ./install.py install
```

The installer uses a curses terminal UI over SSH when available and falls back
to a numbered text menu. RadBuild tools are always installed; the client,
server, systemd service, and RadFPGA Debug Hub are selectable components.

## Repository Layout

```text
installers/
  linux-x86_64/                RadTools Crimson Linux installer and payloads
fpga/
  hdl/radila/                  RadILA and RadDebugHub HDL
  petalinux/2023.2/            PetaLinux 2023.2 meta-radbuild template layer
raddebug/                      RadFPGA Debug Hub release notes and packaging docs
INSTALL.md                     Installation guide
PROJECTS.md                    RadBuild project creation guide
RELEASES.md                    Release and packaging notes
```

## Installed Commands

The RadBuild tools component installs wrappers for:

- `radbuild`
- `build_vivado`
- `build_petalinux`
- `radsetup`

Optional components add:

- `radclient`
- `radserver`
- `raddb`
- `radbuildserver`
- `radworker`
- `radcodex_worker`
- `radllm`
- `radfpga_debug_hub`
- `radfpga_debug_hubd`

## Common Workflows

Create a starter FPGA or FPGA-MPSoC project:

```sh
radbuild --createproject .
```

Register an existing workspace:

```sh
radsetup <workspace-path>
```

Run a Vivado flow from a project directory:

```sh
build_vivado --list
build_vivado --build-design
```

Run a PetaLinux flow from a project directory:

```sh
build_petalinux --dry-run
build_petalinux
```

Package a new BSP release from the PetaLinux project:

```sh
build_petalinux --minor
build_petalinux --major
```

Package a smaller source/config BSP without generated pre-built images:

```sh
build_petalinux --minor --small-bsp
build_petalinux --minor --no-prebuilt
```

`--minor` and `--major` update the project's configured PetaLinux
`version_file` before writing a BSP into `petalinux/bsp_release/`. Keep that
file aligned with the latest checked-in BSP version; for example, set it to
`1.0` before using `--minor` to create `neuma-3eg_v1.1.bsp`.

`--small-bsp` uses PetaLinux BSP packaging with `--exclude-from-file` and skips
`petalinux-package --prebuilt`, keeping `pre-built`, generated images, build
workspaces, downloads, and sstate caches out of the BSP.

See [INSTALL.md](INSTALL.md), [PROJECTS.md](PROJECTS.md), and
[RELEASES.md](RELEASES.md) for detailed usage.

## Dependencies

For the current Linux x86_64 RadFPGA Debug Hub payload on Ubuntu 22.04:

```sh
sudo apt-get update
sudo apt-get install -y libqt5widgets5 libqt5network5 libqt5serialport5
```
