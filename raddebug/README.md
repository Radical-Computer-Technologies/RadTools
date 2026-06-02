# RadFPGA Debug Hub Releases

This folder is for RadDebug release notes, packaging notes, and installer-facing documentation.

RadILA/RadDebugHub source is owned by the RadHDL submodule:

```text
RadHDL/debug/radila/
```

The installable RadFPGA Debug Hub payload is packaged under:

```text
installers/linux-x86_64/radfpga-debug-hub/v0.1.0/
```

The current installer payload contains:

- `radfpga_debug_hub`: Qt desktop UI.
- `radfpga_debug_hubd`: local daemon/service endpoint used by the UI.

The daemon supports RadBuild connection settings through `RADBUILD_ROOT`, `RADBUILD_RADCLIENT`, and `RADBUILD_SERVER_CONFIG`.
