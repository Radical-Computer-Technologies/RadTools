# RadTools Releases

## v1.0.0 - Crimson

Crimson is the first RadTools release branch.

```text
Release: RadTools v1.0.0 - Crimson
Platform: linux-x86_64
Installer: installers/linux-x86_64/install.py
```

Included payloads:

- RadBuild v1.0.0 command tools
- RadBuild client/server/worker executables
- RadFPGA Debug Hub Linux payload
- RadHDL submodule with RadILA/RadDebugHub HDL, bridge source, and host-tool source
- PetaLinux 2023.2 `meta-radbuild` template layer

## Packaging Policy

Track release payload directories and documentation:

```text
installers/linux-x86_64/radbuild-server/v1.0.0/
installers/linux-x86_64/radfpga-debug-hub/v0.1.0/
fpga/
raddebug/
```

Do not duplicate RadILA/RadDebugHub source in RadTools. Source belongs under
`RadHDL/debug/radila/`; RadTools only tracks compiled release payloads and
installer metadata.

Do not track generated release archives such as:

```text
*.tar.gz
*.tgz
*.zip
```

The current RadBuild aggregate archives are larger than GitHub's ordinary
single-file limit. They should be regenerated from tracked payload directories
for distribution or attached to GitHub Releases outside the git tree.

## Regenerating Archives

From the repository root:

```sh
cd installers/linux-x86_64/radbuild-server
tar --exclude='__pycache__' -czf radbuild-server-v1.0.0-linux-x86_64.tar.gz v1.0.0

cd ../radfpga-debug-hub
tar --exclude='__pycache__' -czf radfpga-debug-hub-v0.1.0-linux-x86_64.tar.gz v0.1.0

cd ..
tar --exclude='*.tar.gz' --exclude='__pycache__' \
  -czf radtools-v1.0.0-crimson-linux-x86_64.tar.gz \
  RELEASE README.md installer_manifest.json install.py install.sh uninstall.sh \
  radbuild-server radfpga-debug-hub
```

## Smoke Tests

Install tools only into a temporary root:

```sh
installers/linux-x86_64/install.py install \
  --non-interactive \
  --install-root /tmp/radtools-test \
  --bindir /tmp/radtools-bin-test
```

Create a temporary project through the installed wrapper:

```sh
/tmp/radtools-bin-test/radbuild --createproject /tmp/radbuild-create-test \
  --non-interactive \
  --workspace /tmp/radbuild-create-test \
  --project-type FPGA \
  --project-name smoke_fpga \
  --vendor xilinx \
  --modelseries artix7 \
  --part-number xc7a35tcsg324-1 \
  --tool vivado \
  --tool-version 2023.1
```

Uninstall:

```sh
installers/linux-x86_64/install.py uninstall \
  --all \
  --install-root /tmp/radtools-test \
  --bindir /tmp/radtools-bin-test \
  --remove-data
```
