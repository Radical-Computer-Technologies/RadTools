# RadBuild

RadBuild is a workspace-oriented build toolset for FPGA/Linux projects. It
keeps project intent in each project's `settings.json`, keeps machine-local
toolchain paths in a per-PC workspace profile, and exposes short commands for
common Vivado and PetaLinux flows.

The current toolset targets Xilinx projects and supports:

- Vivado IP packaging from `hdl/**/package_*_ip.tcl`.
- Vivado VHDL testbench staging, batch simulation, and GUI launch helpers.
- Full Vivado design builds through `hdl/tcl/build.tcl`.
- PetaLinux project initialization from BSP releases.
- PetaLinux build, package, BSP versioning, and fast-update deploy flows.
- Per-project RadBuild implementation selection with `radbuild_version`.
- Per-PC toolchain profiles keyed by username, hostname, and machine identity.

## Layout

```text
RadBuild/
  radbuild/
    radbuild.sh          Source this when running from source.
    README.md            Toolset overview.
    USAGE.md             Command-line usage guide.
    .tools/              Command dispatchers.
    .tools/v1.0.0/       Current implementation.
    .radmeta/            Local RadBuild metadata, ignored by git.

radbuild-workspace/
  .userconfig/           Per-PC toolchain settings, ignored by git.
  <project>/             Project folders with settings.json.
```

Release bundles contain the same command names as executables:

```text
<radbuild-install-prefix>/
  build_vivado
  build_petalinux
  radsetup
  radbuild.sh
  README.md
  USAGE.md
```

## Requirements

- Linux shell environment with Bash.
- Python 3.10 or newer when running from source.
- PyInstaller only if you want to build native release executables.
- Vivado installed for IP packaging, testbenches, and full HDL builds.
- PetaLinux installed for PetaLinux project flows.
- Standard Unix tools used by deploy/package paths, including `scp`, `ssh`,
  and `tar`.
- Project-local `settings.json` files that describe the requested vendor,
  model series, RadBuild version, tool versions, and Vivado part number.

## Install From Source

Source the shell entrypoint:

```bash
source <RadBuild-source-path>/radbuild/radbuild.sh
```

For convenience, add that line to your shell startup file.

Then register or create a workspace:

```bash
radsetup <radbuild-workspace>
```

`radsetup` scans project `settings.json` files in the workspace, locates the
requested toolchains in typical install locations, and writes a local profile:

```text
radbuild-workspace/.userconfig/<username>-<hostname>.json
```

If two PCs share the same username and hostname, RadBuild adds a machine
fingerprint suffix so both profiles can coexist.

## Install From A Release

Unpack or copy a release directory, then either source its shell entrypoint:

```bash
source <radbuild-install-prefix>/radbuild.sh
```

or place the release directory on `PATH` and call the executables directly:

```bash
export PATH=<radbuild-install-prefix>:$PATH
build_vivado --list
```

The release executables contain the RadBuild Python payload. They still read
project settings and workspace `.userconfig` files at runtime.

When `build_vivado --build-design` completes successfully, RadBuild also runs
`bootgen` and writes an FPGA-manager `.bit.bin` beside the generated `.bit`.
Pass `--skip-bitbin` to keep the design build from running that conversion.

## Project Settings

Each project should contain a top-level `settings.json`. Example:

```json
{
  "radbuild_version": "v1.0.0",
  "vendor": "xilinx",
  "modelseries": "zynq7",
  "projects": {
    "vivado": {
      "version": "2023.1",
      "project_name": "example_hw",
      "part_number": "xc7z020clg400-1",
      "testbench_stop_time": "8ms"
    },
    "petalinux": {
      "version": "2023.2",
      "project_name": "example_linux",
      "target_ip": "192.168.2.10",
      "modules": [],
      "firmware": [],
      "xsa_dir": "hwdef",
      "default_deploy": false,
      "build_sdk": false,
      "template": "zynq",
      "bsp_release_dir": "bsp_release",
      "version_file": ".version",
      "fingerprint_file": ".last_build_fingerprint",
      "fast_update_dir": "fast_update"
    }
  }
}
```

`projects.petalinux` paths are resolved under the project's `petalinux/`
folder. For example, `"xsa_dir": "hwdef"` means
`<project>/petalinux/hwdef`.

See [USAGE.md](USAGE.md) for command examples.
