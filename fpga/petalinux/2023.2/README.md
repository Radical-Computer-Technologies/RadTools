# PetaLinux 2023.2

This folder contains public PetaLinux 2023.2 support material for RadBuild.

## Contents

- `meta-radbuild/`: minimal Yocto/PetaLinux layer skeleton for RadBuild
  projects.

`meta-radbuild` intentionally does not include board-specific device-tree
fragments, firmware recipes, kernel modules, Qt overrides, or machine
configuration. Keep those items in a private project layer such as
`meta-<project>`.

## Intended Layer Split

```text
petalinux/
  layers/
    meta-radbuild/          Generic RadBuild helper layer
    meta-<project-private>/ Board, firmware, driver, and product recipes
```

Zynq-7000 and Zynq UltraScale+ support should be added as separate generic
templates only when the recipes are portable and do not encode board-specific
hardware details.
