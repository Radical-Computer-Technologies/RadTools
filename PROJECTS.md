# RadBuild Project Creation

RadBuild v1.0.0 includes `radbuild --createproject` for creating starter
projects in the structure expected by the build tools.

## Interactive Project Wizard

```sh
radbuild --createproject .
```

The command opens a curses wizard when the terminal supports it. This works
over normal SSH sessions. Use `--ui text` if a minimal terminal cannot run
curses.

```sh
radbuild --createproject . --ui curses
radbuild --createproject . --ui text
```

The wizard asks for:

- registered workspace
- project type
- project name
- FPGA vendor
- part family
- FPGA part number
- FPGA tool and version
- Linux build system and version for FPGA-MPSoC projects

## Project Types

Implemented templates:

- `FPGA`: bare HDL project with Vivado settings.
- `FPGA-MPSoC`: HDL project with Vivado and PetaLinux settings.

Reserved project type names:

- `MCU`
- `MicroProcessor`

Those names are present in the UI for forward compatibility, but templates are
not implemented yet.

## Generated FPGA Layout

```text
<workspace>/<project-name>/
  README.md
  settings.json
  .gitignore
  hdl/
    src/top.vhd
    tcl/build.tcl
```

The generated `settings.json` follows the current RadBuild schema:

```json
{
  "radbuild_version": "v1.0.0",
  "vendor": "xilinx",
  "modelseries": "artix7",
  "projects": {
    "vivado": {
      "version": "2023.1",
      "project_name": "example_fpga",
      "part_number": "xc7a35tcsg324-1",
      "testbench_stop_time": "1us"
    }
  }
}
```

## Generated FPGA-MPSoC Layout

FPGA-MPSoC projects add PetaLinux scaffolding:

```text
<workspace>/<project-name>/
  petalinux/
    bsp_release/
    hwdef/
    fast_update/
```

The generated `projects.petalinux` block includes BSP, XSA, deploy, and
fingerprint fields used by `build_petalinux`.

`projects.petalinux.version_file` stores the last packaged BSP version relative
to the `petalinux/` folder. `build_petalinux --minor` increments the minor
number and `build_petalinux --major` increments the major number before
packaging a BSP into `petalinux/bsp_release/`. If a project already contains a
checked-in BSP such as `neuma-3eg_v1.0.bsp`, set the version file to `1.0`
before running `build_petalinux --minor`; the next BSP will be `v1.1`.

Use `build_petalinux --minor --small-bsp` when the BSP should carry source and
configuration only. This mode skips PetaLinux pre-built generation and invokes
`petalinux-package --bsp --exclude-from-file` to omit `pre-built`, generated
images, build workspaces, downloads, and sstate caches.

## Scripted FPGA Project Creation

```sh
radbuild --createproject <workspace-path> \
  --non-interactive \
  --workspace <workspace-path> \
  --project-type FPGA \
  --project-name example_fpga \
  --vendor xilinx \
  --modelseries artix7 \
  --part-number xc7a35tcsg324-1 \
  --tool vivado \
  --tool-version 2023.1
```

## Scripted FPGA-MPSoC Project Creation

```sh
radbuild --createproject <workspace-path> \
  --non-interactive \
  --workspace <workspace-path> \
  --project-type FPGA-MPSoC \
  --project-name example_mpsoc \
  --vendor xilinx \
  --modelseries zynq7 \
  --part-number xc7z020clg400-1 \
  --tool vivado \
  --tool-version 2023.1 \
  --linux-build-system petalinux \
  --linux-version 2023.2
```

## Workspace Registration

Register existing workspaces with:

```sh
radsetup <workspace-path>
```

RadBuild records workspaces in its `.radmeta/radworkspaces.json` registry and
writes per-machine toolchain config under:

```text
<workspace-path>/.userconfig/<user>-<host>.json
```

`radbuild --createproject` lists registered workspaces first. If none are
registered, it can still create a project in the path supplied to
`--createproject`.
