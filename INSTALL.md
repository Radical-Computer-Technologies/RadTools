# Installing RadTools Crimson

This document covers the Linux x86_64 installer for RadTools v1.0.0 -
Crimson.

## Quick Install

```sh
cd installers/linux-x86_64
sudo ./install.py install
```

The default layout keeps payload binaries outside `/usr/bin` and places only
small command wrappers on the global path:

```text
/opt/radtools/RadBuild/v1.0.0/bin/              RadBuild payload binaries
/opt/radtools/RadFPGA-Debug-Hub/v0.1.0/bin/    RadFPGA Debug Hub payload binaries
/usr/bin/<command>                              Thin command wrappers
```

The interactive installer uses a curses menu when the SSH or local terminal
supports it. If curses is unavailable, it falls back to a numbered text menu.

Force a UI backend:

```sh
sudo ./install.py install --ui curses
sudo ./install.py install --ui text
sudo ./install.py install --ui whiptail
```

## Selectable Components

RadBuild tools are always installed:

- `radbuild`
- `build_vivado`
- `build_petalinux`
- `radsetup`

Optional components:

- RadBuild client: `radclient`
- RadBuild server and workers: `radserver`, `raddb`, `radbuildserver`,
  `radworker`, `radcodex_worker`, `radllm`
- RadBuild systemd service: `radbuild-server.service`
- RadFPGA Debug Hub: `radfpga_debug_hub`, `radfpga_debug_hubd`

Install everything:

```sh
sudo ./install.py install --all
```

Install tools and client only:

```sh
sudo ./install.py install --component radbuild-client --non-interactive
```

Install server files without starting the service immediately:

```sh
sudo ./install.py install \
  --component radbuild-client \
  --component radbuild-server \
  --component radbuild-service \
  --no-start
```

## Custom Paths

Use `--install-root` for payload files and `--bindir` for command wrappers:

```sh
sudo ./install.py install \
  --install-root /opt/radtools \
  --bindir /usr/bin
```

Current-user install for testing:

```sh
./install.py install \
  --install-root "$HOME/.local/opt/radtools" \
  --bindir "$HOME/.local/bin" \
  --component radbuild-client \
  --non-interactive
```

## Toolchain Linking

The installer can link Vivado and PetaLinux toolchain settings scripts into
the installed RadBuild metadata. The interactive menu searches common locations
under `/opt`, `/tools`, and the invoking user's home directory.

Scripted examples:

```sh
sudo ./install.py install \
  --toolchain vivado:2023.1:/opt/Xilinx/Vivado/2023.1/settings64.sh
```

```sh
sudo ./install.py install \
  --toolchain petalinux:2023.2:/opt/pkg/petalinux/2023.2/settings.sh
```

Linked tools are written to:

```text
<install-root>/RadBuild/v1.0.0/.radmeta/toolchains.json
```

Project-local workspace setup still uses `radsetup <workspace-path>` to write
per-machine `.userconfig` profiles.

## Service

When selected, the RadBuild service installs:

```text
/etc/systemd/system/radbuild-server.service
```

Useful service commands:

```sh
sudo systemctl status radbuild-server
sudo systemctl restart radbuild-server
sudo systemctl disable --now radbuild-server
```

## Uninstall

Remove selected components while preserving server data:

```sh
sudo ./install.py uninstall
```

Remove all components and data:

```sh
sudo ./install.py uninstall --all --remove-data
```
