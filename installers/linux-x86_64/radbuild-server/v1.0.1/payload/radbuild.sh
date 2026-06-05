            #!/usr/bin/env bash

            RADBUILD_RELEASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
            export RADBUILD_RELEASE_DIR
            RADBUILD_BIN_DIR="$RADBUILD_RELEASE_DIR/bin"
            if [[ ! -d "$RADBUILD_BIN_DIR" ]]; then
                RADBUILD_BIN_DIR="$RADBUILD_RELEASE_DIR"
            fi
            export RADBUILD_BIN_DIR
            export PATH="$RADBUILD_BIN_DIR:$PATH"

            radbuild() {
    "$RADBUILD_BIN_DIR/radbuild" "$@"
}

build_vivado() {
    "$RADBUILD_BIN_DIR/build_vivado" "$@"
}

build_petalinux() {
    "$RADBUILD_BIN_DIR/build_petalinux" "$@"
}

build_litex() {
    "$RADBUILD_BIN_DIR/build_litex" "$@"
}

radsetup() {
    "$RADBUILD_BIN_DIR/radsetup" "$@"
}

radserver() {
    "$RADBUILD_BIN_DIR/radserver" "$@"
}

raddb() {
    "$RADBUILD_BIN_DIR/raddb" "$@"
}

radbuildserver() {
    "$RADBUILD_BIN_DIR/radbuildserver" "$@"
}

radclient() {
    "$RADBUILD_BIN_DIR/radclient" "$@"
}

radworker() {
    "$RADBUILD_BIN_DIR/radworker" "$@"
}

radcodex_worker() {
    "$RADBUILD_BIN_DIR/radcodex_worker" "$@"
}

radllm() {
    "$RADBUILD_BIN_DIR/radllm" "$@"
}

            alias radbuild="$RADBUILD_BIN_DIR/radbuild"
alias build_vivado="$RADBUILD_BIN_DIR/build_vivado"
alias build_petalinux="$RADBUILD_BIN_DIR/build_petalinux"
alias build_litex="$RADBUILD_BIN_DIR/build_litex"
alias radsetup="$RADBUILD_BIN_DIR/radsetup"
alias radserver="$RADBUILD_BIN_DIR/radserver"
alias raddb="$RADBUILD_BIN_DIR/raddb"
alias radbuildserver="$RADBUILD_BIN_DIR/radbuildserver"
alias radclient="$RADBUILD_BIN_DIR/radclient"
alias radworker="$RADBUILD_BIN_DIR/radworker"
alias radcodex_worker="$RADBUILD_BIN_DIR/radcodex_worker"
alias radllm="$RADBUILD_BIN_DIR/radllm"
