# meta-radbuild

`meta-radbuild` is a minimal PetaLinux/Yocto layer template for RadBuild
projects.

This layer intentionally contains no board-specific device-tree fragments,
firmware payloads, kernel modules, Qt overrides, or machine configuration. Use
it as a neutral starting point for public RadBuild examples and add
project-specific recipes in a private project layer.

## Scope

- Compatible layer skeleton for PetaLinux 2023.2 based flows.
- No default recipes.
- No board, carrier, RF, firmware, or module assumptions.

## Suggested Project Layout

```text
<workspace>/<project>/
  petalinux/
    layers/
      meta-radbuild/
      meta-<project-private>/
```

Keep generic RadBuild helper recipes in `meta-radbuild` only when they are
portable across boards. Put Zynq-7000, Zynq UltraScale+, board-specific
device-tree, firmware, and driver recipes in separate private layers.
