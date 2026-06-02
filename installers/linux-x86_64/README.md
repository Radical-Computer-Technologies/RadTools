# RadTools v1.0.0 - Crimson Linux Installer

Use `install.py` as the main Linux installer for RadTools Crimson. `install.sh` is a thin compatibility wrapper around it.

```sh
sudo ./install.py
```

The installer reads `installer_manifest.json` to discover release metadata, available component versions, payload paths, commands, and service templates.

The manifest also lists supported platforms for each component. The installer detects the host OS/architecture and only presents matching components. This release currently lists `linux-x86_64` components.

When run interactively, the installer uses a curses terminal menu by default when the SSH/session terminal supports it. It falls back to a plain numbered text menu if curses is unavailable. It presents:

- RadTools version: `v1.0.0 - Crimson`
- install payload root
- command wrapper directory
- optional components

UI backends:

- `--ui auto`: curses when supported, otherwise the plain text menu.
- `--ui curses`: force the curses menu.
- `--ui text`: force the plain numbered menu.
- `--ui whiptail`: force the legacy whiptail dialogs.

RadBuild tools are always installed:

- `radbuild`
- `build_vivado`
- `build_petalinux`
- `radsetup`

The installer can also link local FPGA toolchains. It searches common Vivado
and PetaLinux locations under `/opt`, `/tools`, and the invoking user's home
directory. Linked tools are written to:

```text
<install-root>/RadBuild/v1.0.0/.radmeta/toolchains.json
```

Scripted toolchain links use:

```sh
sudo ./install.py install \
  --toolchain vivado:2023.1:/opt/Xilinx/Vivado/2023.1/settings64.sh \
  --toolchain petalinux:2023.2:/opt/pkg/petalinux/2023.2/settings.sh
```

Optional components:

- `radclient`
- RadBuild server and worker commands
- `radbuild-server.service`
- RadFPGA Debug Hub

RadFPGA Debug Hub is an installable release payload. The corresponding
RadILA/RadDebugHub source lives in `../../RadHDL/debug/radila/` from the
repository root.

The top-level installer is versioned as:

```text
RadTools v1.0.0 - Crimson
```

## Layout

The default system layout keeps payload binaries outside `/usr/bin`:

```text
/opt/radtools/RadBuild/v1.0.0/bin/              RadBuild payload binaries
/opt/radtools/RadFPGA-Debug-Hub/v0.1.0/bin/    RadFPGA Debug Hub payload binaries
/usr/bin/<command>                              Thin command wrappers only
```

The wrappers dispatch RadBuild commands to the version requested by the nearest `settings.json`.

See also:

- [../../INSTALL.md](../../INSTALL.md) for full install options.
- [../../PROJECTS.md](../../PROJECTS.md) for `radbuild --createproject`.
- [../../RELEASES.md](../../RELEASES.md) for archive and release policy.

## Scripted Installs

Tools only:

```sh
sudo ./install.py install --non-interactive
```

Create a starter FPGA project after install:

```sh
radbuild --createproject .
```

Tools and client:

```sh
sudo ./install.py install --component radbuild-client --non-interactive
```

Everything:

```sh
sudo ./install.py install --all
```

Full server install without starting the service immediately:

```sh
sudo ./install.py install \
  --component radbuild-client \
  --component radbuild-server \
  --component radbuild-service \
  --no-start
```

Current-user test install:

```sh
./install.py install \
  --install-root "$HOME/.local/opt/radtools" \
  --bindir "$HOME/.local/bin" \
  --component radbuild-client \
  --non-interactive
```

## Uninstall

```sh
sudo ./install.py uninstall
```

Preserve RadBuild server data by default; pass `--remove-data` to delete it.

To remove everything installed by the release:

```sh
sudo ./install.py uninstall --all --remove-data
```
