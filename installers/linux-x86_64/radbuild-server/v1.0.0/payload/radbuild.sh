#!/usr/bin/env bash

RADBUILD_RELEASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export RADBUILD_RELEASE_DIR
export PATH="$RADBUILD_RELEASE_DIR:$PATH"

build_vivado() {
    "$RADBUILD_RELEASE_DIR/build_vivado" "$@"
}

radbuild() {
    "$RADBUILD_RELEASE_DIR/radbuild" "$@"
}

build_petalinux() {
    "$RADBUILD_RELEASE_DIR/build_petalinux" "$@"
}

radsetup() {
    "$RADBUILD_RELEASE_DIR/radsetup" "$@"
}

radserver() {
    "$RADBUILD_RELEASE_DIR/radserver" "$@"
}

raddb() {
    "$RADBUILD_RELEASE_DIR/raddb" "$@"
}

radbuildserver() {
    "$RADBUILD_RELEASE_DIR/radbuildserver" "$@"
}

alias build_vivado="$RADBUILD_RELEASE_DIR/build_vivado"
alias radbuild="$RADBUILD_RELEASE_DIR/radbuild"
alias build_petalinux="$RADBUILD_RELEASE_DIR/build_petalinux"
alias radsetup="$RADBUILD_RELEASE_DIR/radsetup"
alias radserver="$RADBUILD_RELEASE_DIR/radserver"
alias raddb="$RADBUILD_RELEASE_DIR/raddb"
alias radbuildserver="$RADBUILD_RELEASE_DIR/radbuildserver"
