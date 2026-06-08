#!/usr/bin/env python3
from __future__ import annotations

import argparse
import curses
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = SCRIPT_DIR / "installer_manifest.json"


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def component_map(manifest: dict) -> dict[str, dict]:
    return {item["id"]: item for item in manifest["components"]}


def detect_platform() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    machine_aliases = {
        "amd64": "x86_64",
        "x64": "x86_64",
        "aarch64": "aarch64",
        "arm64": "aarch64",
    }
    return f"{system}-{machine_aliases.get(machine, machine)}"


def filter_manifest_for_platform(manifest: dict, host_platform: str) -> dict:
    filtered = dict(manifest)
    filtered["components"] = [
        item for item in manifest["components"]
        if host_platform in item.get("platforms", [manifest["release"].get("platform", host_platform)])
    ]
    return filtered


def validate_manifest_platform(manifest: dict, host_platform: str, allow_mismatch: bool) -> dict:
    filtered = filter_manifest_for_platform(manifest, host_platform)
    if not filtered["components"] and not allow_mismatch:
        supported = sorted({p for item in manifest["components"] for p in item.get("platforms", [])})
        raise SystemExit(f"no installable components for host platform {host_platform}; supported: {', '.join(supported)}")
    return filtered


def have_whiptail() -> bool:
    term = os.environ.get("TERM", "")
    return shutil.which("whiptail") is not None and sys.stdin.isatty() and sys.stdout.isatty() and term not in {"", "dumb"}


def have_curses() -> bool:
    term = os.environ.get("TERM", "")
    return sys.stdin.isatty() and sys.stdout.isatty() and term not in {"", "dumb"}


def whiptail(args: list[str], capture_value: bool = False) -> subprocess.CompletedProcess:
    cmd = ["whiptail", *args]
    if capture_value:
        cmd = ["whiptail", "--output-fd", "1", *args]

    try:
        tty_in = open("/dev/tty", "r", encoding="utf-8")
        tty_err = open("/dev/tty", "w", encoding="utf-8")
    except OSError:
        tty_in = None
        tty_err = None

    try:
        return subprocess.run(
            cmd,
            text=True,
            stdin=tty_in,
            stderr=tty_err,
            stdout=subprocess.PIPE if capture_value else None,
        )
    finally:
        if tty_in is not None:
            tty_in.close()
        if tty_err is not None:
            tty_err.close()


def prompt_input(title: str, label: str, default: str, use_whiptail: bool) -> str:
    if use_whiptail:
        result = whiptail(["--title", title, "--inputbox", label, "10", "78", default], capture_value=True)
        if result.returncode != 0:
            raise SystemExit(1)
        return result.stdout.strip() or default
    value = input(f"{label} [{default}]: ").strip()
    return value or default


def prompt_components(manifest: dict, selected: set[str], use_whiptail: bool) -> set[str]:
    optional = [c for c in manifest["components"] if not c.get("required")]
    title = f'{manifest["release"]["name"]} {manifest["release"]["version"]} - {manifest["release"]["codename"]}'
    if use_whiptail:
        args = ["--title", title, "--checklist", "Select optional components", "20", "84", str(len(optional))]
        for comp in optional:
            state = "ON" if comp["id"] in selected or comp.get("default") else "OFF"
            args.extend([comp["id"], comp["name"], state])
        result = whiptail(args, capture_value=True)
        if result.returncode != 0:
            raise SystemExit(1)
        return {item.strip('"') for item in result.stdout.split()}

    out = set()
    for comp in optional:
        default_yes = comp["id"] in selected or bool(comp.get("default"))
        suffix = "Y/n" if default_yes else "y/N"
        answer = input(f'Install {comp["name"]}? [{suffix}] ').strip().lower()
        if not answer:
            answer = "y" if default_yes else "n"
        if answer.startswith("y"):
            out.add(comp["id"])
    return out


def settings_candidates(tool: str, install_dir: Path) -> list[Path]:
    if install_dir.is_file():
        return [install_dir]
    if tool == "vivado":
        return [
            install_dir / "settings64.sh",
            install_dir / "settings.sh",
            install_dir.parent / "settings64.sh",
            install_dir.parent / "settings.sh",
        ]
    if tool == "petalinux":
        return [
            install_dir / "settings.sh",
            install_dir.parent / "settings.sh",
        ]
    return [install_dir / "settings.sh"]


def common_tool_roots(tool: str) -> list[Path]:
    home = Path.home()
    sudo_user = os.environ.get("SUDO_USER")
    homes = [home]
    if sudo_user:
        homes.append(Path("/home") / sudo_user)
    if tool == "vivado":
        return [
            *(base / "xilinx" / "Vivado" for base in homes),
            *(base / "Xilinx" / "Vivado" for base in homes),
            Path("/opt/Xilinx/Vivado"),
            Path("/tools/Xilinx/Vivado"),
        ]
    if tool == "petalinux":
        return [
            *(base / "xilinx" / "petalinux" for base in homes),
            *(base / "Xilinx" / "petalinux" for base in homes),
            Path("/opt/pkg/petalinux"),
            Path("/opt/Xilinx/petalinux"),
        ]
    return []


def discover_toolchains() -> list[dict[str, str]]:
    discovered: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for tool in ("vivado", "petalinux"):
        for root in common_tool_roots(tool):
            if not root.exists():
                continue
            candidates = [root] if any(path.exists() for path in settings_candidates(tool, root)) else []
            candidates.extend(path for path in sorted(root.iterdir()) if path.is_dir())
            for install_dir in candidates:
                for settings in settings_candidates(tool, install_dir):
                    if not settings.exists():
                        continue
                    version = install_dir.name
                    key = (tool, version, str(settings.resolve()))
                    if key in seen:
                        continue
                    seen.add(key)
                    discovered.append(
                        {
                            "id": f"{tool}:{version}:{settings.resolve()}",
                            "tool": tool,
                            "version": version,
                            "install_dir": str(install_dir.resolve()),
                            "settings": str(settings.resolve()),
                        }
                    )
                    break
    return discovered


def manual_toolchain(title: str, use_whiptail: bool = False) -> dict[str, str] | None:
    tool = prompt_input(title, "Tool name (vivado or petalinux, blank to stop)", "", use_whiptail).strip().lower()
    if not tool:
        return None
    if tool not in {"vivado", "petalinux"}:
        print(f"Unknown tool: {tool}", file=sys.stderr)
        return None
    version = prompt_input(title, f"{tool} version", "2023.1" if tool == "vivado" else "2023.2", use_whiptail).strip()
    settings = Path(prompt_input(title, f"{tool} settings script", "", use_whiptail)).expanduser().resolve()
    if not settings.exists():
        print(f"Skipping missing settings script: {settings}", file=sys.stderr)
        return None
    install_dir = settings.parent
    return {
        "id": f"{tool}:{version}:{settings}",
        "tool": tool,
        "version": version,
        "install_dir": str(install_dir),
        "settings": str(settings),
    }


def prompt_toolchains_text(title: str, selected: list[dict[str, str]]) -> list[dict[str, str]]:
    detected = discover_toolchains()
    by_id = {item["id"]: item for item in selected}
    for item in detected:
        default_yes = item["id"] in by_id
        suffix = "Y/n" if default_yes else "y/N"
        answer = input(f'Link {item["tool"]} {item["version"]} at {item["settings"]}? [{suffix}] ').strip().lower()
        if not answer:
            answer = "y" if default_yes else "n"
        if answer.startswith("y"):
            by_id[item["id"]] = item
        else:
            by_id.pop(item["id"], None)

    while True:
        answer = input("Add a manual toolchain path? [y/N] ").strip().lower()
        if not answer.startswith("y"):
            break
        item = manual_toolchain(title, False)
        if item:
            by_id[item["id"]] = item
    return list(by_id.values())


def prompt_whiptail_install_options(
    manifest: dict,
    selected: set[str],
    install_root: Path,
    bindir: Path,
) -> tuple[Path, Path, set[str], list[dict[str, str]]]:
    title = f'{manifest["release"]["name"]} {manifest["release"]["version"]} - {manifest["release"]["codename"]}'
    message = (
        "RadBuild Tools are always installed.\n\n"
        "Use Configure Paths to choose where payload binaries are installed and where command wrappers are linked."
    )

    while True:
        result = whiptail(
            [
                "--title", title,
                "--default-item", "install",
                "--menu", message,
                "18", "86", "6",
                "paths", f"Configure paths: install={install_root}, wrappers={bindir}",
                "components", "Select optional components",
                "toolchains", "Link detected Vivado/PetaLinux installs",
                "install", "Install selected RadTools components",
                "cancel", "Exit without installing",
            ],
            capture_value=True,
        )
        if result.returncode != 0:
            raise SystemExit(1)
        choice = result.stdout.strip().strip('"')

        if choice == "paths":
            install_root = Path(prompt_input(title, "Install payload root", str(install_root), True))
            bindir = Path(prompt_input(title, "Command wrapper directory", str(bindir), True))
        elif choice == "components":
            selected = prompt_components(manifest, selected, True)
        elif choice == "toolchains":
            toolchains = prompt_toolchains_text(title, [])
        elif choice == "install":
            return install_root, bindir, selected, locals().get("toolchains", [])
        elif choice == "cancel":
            raise SystemExit(1)


def prompt_text_install_options(
    manifest: dict,
    selected: set[str],
    install_root: Path,
    bindir: Path,
) -> tuple[Path, Path, set[str], list[dict[str, str]]]:
    title = f'{manifest["release"]["name"]} {manifest["release"]["version"]} - {manifest["release"]["codename"]}'
    toolchains: list[dict[str, str]] = []
    while True:
        print(f"\n{title}")
        print("RadBuild Tools are always installed.")
        print(f"  1. Configure paths: install={install_root}, wrappers={bindir}")
        print(f"  2. Select optional components: {', '.join(sorted(selected)) if selected else 'none'}")
        print(f"  3. Link toolchains: {len(toolchains)} selected")
        print("  4. Install selected RadTools components")
        print("  5. Exit without installing")
        choice = input("Selection [4]: ").strip() or "4"

        if choice == "1":
            install_root = Path(prompt_input(title, "Install payload root", str(install_root), False))
            bindir = Path(prompt_input(title, "Command wrapper directory", str(bindir), False))
        elif choice == "2":
            selected = prompt_components(manifest, selected, False)
        elif choice == "3":
            toolchains = prompt_toolchains_text(title, toolchains)
        elif choice == "4":
            return install_root, bindir, selected, toolchains
        elif choice == "5":
            raise SystemExit(1)
        else:
            print(f"Unknown selection: {choice}", file=sys.stderr)


class CursesInstallerUI:
    def __init__(self, stdscr, manifest: dict, selected: set[str], install_root: Path, bindir: Path):
        self.stdscr = stdscr
        self.manifest = manifest
        self.selected = set(selected)
        for comp in manifest["components"]:
            if comp.get("default") and not comp.get("required"):
                self.selected.add(comp["id"])
        self.install_root = install_root
        self.bindir = bindir
        self.toolchains: list[dict[str, str]] = []
        self.title = f'{manifest["release"]["name"]} {manifest["release"]["version"]} - {manifest["release"]["codename"]}'

    def run(self) -> tuple[Path, Path, set[str]]:
        curses.curs_set(0)
        self.stdscr.keypad(True)
        curses.use_default_colors()
        try:
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
        except curses.error:
            pass

        while True:
            components = ", ".join(sorted(self.selected)) if self.selected else "none"
            items = [
                ("Configure paths", f"install={self.install_root}, wrappers={self.bindir}"),
                ("Select optional components", components),
                ("Link toolchains", f"{len(self.toolchains)} selected"),
                ("Install selected RadTools components", "continue"),
                ("Exit without installing", "cancel"),
            ]
            choice = self.menu("RadBuild Tools are always installed.", items, default_index=3)
            if choice == 0:
                self.install_root = Path(self.input_box("Install payload root", str(self.install_root)))
                self.bindir = Path(self.input_box("Command wrapper directory", str(self.bindir)))
            elif choice == 1:
                self.selected = self.component_checklist()
            elif choice == 2:
                self.toolchains = self.toolchain_checklist()
            elif choice == 3:
                return self.install_root, self.bindir, self.selected, self.toolchains
            elif choice == 4:
                raise SystemExit(1)

    def addstr(self, y: int, x: int, text: str, attr: int = 0) -> None:
        height, width = self.stdscr.getmaxyx()
        if y < 0 or y >= height or x >= width:
            return
        try:
            self.stdscr.addstr(y, x, text[: max(0, width - x - 1)], attr)
        except curses.error:
            pass

    def draw_header(self, subtitle: str = "") -> None:
        self.stdscr.erase()
        height, _width = self.stdscr.getmaxyx()
        self.addstr(1, 2, self.title, curses.A_BOLD)
        if subtitle:
            self.addstr(3, 2, subtitle)
        self.addstr(height - 2, 2, "Use arrow keys or j/k, Enter to select, q to cancel.")

    def menu(self, subtitle: str, items: list[tuple[str, str]], default_index: int = 0) -> int:
        index = default_index
        while True:
            self.draw_header(subtitle)
            top = 5
            for offset, (label, detail) in enumerate(items):
                attr = curses.color_pair(1) if offset == index else 0
                self.addstr(top + offset, 4, f"{offset + 1}. {label}: {detail}", attr)
            self.stdscr.refresh()
            key = self.stdscr.getch()
            if key in (ord("q"), 27):
                raise SystemExit(1)
            if key in (curses.KEY_UP, ord("k")):
                index = (index - 1) % len(items)
            elif key in (curses.KEY_DOWN, ord("j")):
                index = (index + 1) % len(items)
            elif key in (curses.KEY_ENTER, 10, 13):
                return index
            elif ord("1") <= key <= ord(str(len(items))):
                return key - ord("1")

    def input_box(self, label: str, default: str) -> str:
        curses.curs_set(1)
        curses.echo()
        self.draw_header(label)
        self.addstr(6, 4, f"{label}:")
        self.addstr(8, 4, f"[{default}]")
        self.addstr(10, 4, "> ")
        self.stdscr.refresh()
        raw = self.stdscr.getstr(10, 6, 240)
        curses.noecho()
        curses.curs_set(0)
        value = raw.decode("utf-8", errors="ignore").strip()
        return value or default

    def component_checklist(self) -> set[str]:
        optional = [c for c in self.manifest["components"] if not c.get("required")]
        selected = set(self.selected)
        index = 0
        while True:
            self.draw_header("Space toggles a component. Enter accepts selections.")
            top = 5
            for offset, comp in enumerate(optional):
                checked = "x" if comp["id"] in selected else " "
                attr = curses.color_pair(1) if offset == index else 0
                self.addstr(top + offset, 4, f"[{checked}] {comp['name']} ({comp['id']})", attr)
            self.stdscr.refresh()
            key = self.stdscr.getch()
            if key in (ord("q"), 27):
                raise SystemExit(1)
            if key in (curses.KEY_UP, ord("k")):
                index = (index - 1) % len(optional)
            elif key in (curses.KEY_DOWN, ord("j")):
                index = (index + 1) % len(optional)
            elif key == ord(" "):
                comp_id = optional[index]["id"]
                if comp_id in selected:
                    selected.remove(comp_id)
                else:
                    selected.add(comp_id)
            elif key in (curses.KEY_ENTER, 10, 13):
                return selected

    def toolchain_checklist(self) -> list[dict[str, str]]:
        detected = discover_toolchains()
        selected = {item["id"]: item for item in self.toolchains}
        index = 0
        items = [*detected, {"id": "manual", "tool": "manual", "version": "", "settings": "Add manual path"}]
        while True:
            self.draw_header("Space toggles detected toolchains. Enter accepts selections.")
            top = 5
            for offset, item in enumerate(items):
                if item["id"] == "manual":
                    label = "[+] Add manual Vivado/PetaLinux path"
                else:
                    checked = "x" if item["id"] in selected else " "
                    label = f"[{checked}] {item['tool']} {item['version']} - {item['settings']}"
                attr = curses.color_pair(1) if offset == index else 0
                self.addstr(top + offset, 4, label, attr)
            self.stdscr.refresh()
            key = self.stdscr.getch()
            if key in (ord("q"), 27):
                raise SystemExit(1)
            if key in (curses.KEY_UP, ord("k")):
                index = (index - 1) % len(items)
            elif key in (curses.KEY_DOWN, ord("j")):
                index = (index + 1) % len(items)
            elif key == ord(" ") and items[index]["id"] != "manual":
                item = items[index]
                if item["id"] in selected:
                    selected.pop(item["id"], None)
                else:
                    selected[item["id"]] = item
            elif key in (curses.KEY_ENTER, 10, 13):
                if items[index]["id"] == "manual":
                    item = self.manual_toolchain()
                    if item:
                        selected[item["id"]] = item
                        items.insert(-1, item)
                else:
                    return list(selected.values())

    def manual_toolchain(self) -> dict[str, str] | None:
        tool = self.input_box("Tool name (vivado or petalinux)", "vivado").strip().lower()
        if tool not in {"vivado", "petalinux"}:
            return None
        version = self.input_box(f"{tool} version", "2023.1" if tool == "vivado" else "2023.2").strip()
        settings = Path(self.input_box(f"{tool} settings script", "")).expanduser().resolve()
        if not settings.exists():
            return None
        return {
            "id": f"{tool}:{version}:{settings}",
            "tool": tool,
            "version": version,
            "install_dir": str(settings.parent),
            "settings": str(settings),
        }


def prompt_curses_install_options(
    manifest: dict,
    selected: set[str],
    install_root: Path,
    bindir: Path,
) -> tuple[Path, Path, set[str], list[dict[str, str]]]:
    def run(stdscr):
        return CursesInstallerUI(stdscr, manifest, selected, install_root, bindir).run()

    return curses.wrapper(run)


def close_requires(selected: set[str], comps: dict[str, dict]) -> set[str]:
    changed = True
    selected = set(selected)
    while changed:
        changed = False
        for comp_id in list(selected):
            for req in comps[comp_id].get("requires", []):
                if req not in selected:
                    selected.add(req)
                    changed = True
    for comp_id, comp in comps.items():
        if comp.get("required"):
            selected.add(comp_id)
    return selected


def os_release() -> dict[str, str]:
    release: dict[str, str] = {}
    path = Path("/etc/os-release")
    if not path.exists():
        return release
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        release[key] = value.strip().strip('"')
    return release


def dependency_keys(release: dict[str, str]) -> list[str]:
    keys: list[str] = []
    distro_id = release.get("ID", "").lower()
    if distro_id:
        keys.append(distro_id)
    keys.extend(item.lower() for item in release.get("ID_LIKE", "").split())
    keys.append("linux")
    out: list[str] = []
    for key in keys:
        if key and key not in out:
            out.append(key)
    return out


def package_manager() -> tuple[str, list[str], list[str] | None] | None:
    candidates = [
        ("apt", ["apt-get", "install", "-y"], ["apt-get", "update"]),
        ("dnf", ["dnf", "install", "-y"], None),
        ("yum", ["yum", "install", "-y"], None),
        ("zypper", ["zypper", "--non-interactive", "install"], None),
        ("pacman", ["pacman", "-Sy", "--needed", "--noconfirm"], None),
    ]
    for name, install_cmd, update_cmd in candidates:
        if shutil.which(install_cmd[0]):
            return name, install_cmd, update_cmd
    return None


def package_installed(package: str, manager: str) -> bool:
    checks = {
        "apt": ["dpkg-query", "-W", "-f=${Status}", package],
        "dnf": ["rpm", "-q", package],
        "yum": ["rpm", "-q", package],
        "zypper": ["rpm", "-q", package],
        "pacman": ["pacman", "-Q", package],
    }
    cmd = checks.get(manager)
    if cmd is None or shutil.which(cmd[0]) is None:
        return False
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def dependencies_for_components(selected: set[str], comps: dict[str, dict]) -> list[str]:
    release = os_release()
    keys = dependency_keys(release)
    packages: list[str] = []
    for comp_id in sorted(selected):
        deps = comps[comp_id].get("dependencies", {})
        for key in keys:
            for package in deps.get(key, []):
                if package not in packages:
                    packages.append(package)
    return packages


def install_dependencies(args: argparse.Namespace, selected: set[str], comps: dict[str, dict]) -> list[str]:
    packages = dependencies_for_components(selected, comps)
    if not packages:
        return []

    manager = package_manager()
    if manager is None:
        if args.install_dependencies:
            raise SystemExit(f"no supported Linux package manager found for dependencies: {', '.join(packages)}")
        print(f"Skipping dependency check; no supported package manager found. Needed packages: {', '.join(packages)}")
        return packages

    manager_name, install_cmd, update_cmd = manager
    missing = [package for package in packages if not package_installed(package, manager_name)]
    if not missing:
        print(f"Dependencies already installed: {', '.join(packages)}")
        return packages

    if args.no_install_dependencies:
        raise SystemExit(
            "missing required packages and --no-install-dependencies was requested: "
            + ", ".join(missing)
        )

    if not args.install_dependencies and os.geteuid() != 0:
        raise SystemExit(
            "missing required packages: "
            + ", ".join(missing)
            + "\nRe-run with sudo, or install them manually, or pass --no-install-dependencies only for a temporary test install."
        )

    print(f"Installing dependencies with {manager_name}: {', '.join(missing)}")
    if update_cmd is not None and not args.no_dependency_update:
        subprocess.run(update_cmd, check=True)
    subprocess.run([*install_cmd, *missing], check=True)
    return packages


def render_template(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace(key, value)
    return text


def write_executable(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def install_file(src: Path, dst: Path, mode: int | None = None) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    if mode is not None:
        dst.chmod(mode)


def install_radbuild_command(comp: dict, command: str, paths: dict[str, Path]) -> None:
    version = comp["version"]
    payload = SCRIPT_DIR / comp["payload"]
    template_dir = SCRIPT_DIR / comp["template_dir"]
    install_prefix = paths["radbuild_root"] / version
    bin_dir = install_prefix / "bin"

    install_file(payload / "bin" / command, bin_dir / command, 0o755)

    template = (template_dir / "radbuild-command-wrapper.sh").read_text(encoding="utf-8")
    values = {
        "__RADBUILD_TOOL__": command,
        "__RADBUILD_VERSION__": version,
        "__RADBUILD_ROOT__": str(paths["radbuild_root"]),
    }
    wrapper = render_template(template, values)
    write_executable(paths["bindir"] / command, wrapper)
    write_executable(paths["bindir"] / f"{command}-{version}", wrapper)


def install_radbuild_component(comp: dict, paths: dict[str, Path]) -> None:
    version = comp["version"]
    install_prefix = paths["radbuild_root"] / version
    install_prefix.mkdir(parents=True, exist_ok=True)
    (install_prefix / "bin").mkdir(parents=True, exist_ok=True)

    payload = SCRIPT_DIR / comp["payload"]
    if comp.get("docs"):
        docs_dst = install_prefix / "docs"
        if docs_dst.exists():
            shutil.rmtree(docs_dst)
        shutil.copytree(SCRIPT_DIR / comp["docs"], docs_dst)
    if (payload / "radbuild.sh").exists():
        install_file(payload / "radbuild.sh", install_prefix / "radbuild.sh", 0o644)

    for command in comp.get("commands", []):
        install_radbuild_command(comp, command, paths)

    for runtime_dir in comp.get("runtime_dirs", []):
        (install_prefix / runtime_dir).mkdir(parents=True, exist_ok=True)

    values = {"<radbuild-install-prefix>": str(install_prefix)}
    template_dir = SCRIPT_DIR / comp.get("template_dir", "")
    for item in comp.get("config_templates", []):
        dst = install_prefix / item["dst"]
        if dst.exists():
            continue
        text = render_template((template_dir / item["src"]).read_text(encoding="utf-8"), values)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text, encoding="utf-8")
        dst.chmod(int(item.get("mode", "0644"), 8))


def install_debug_hub(comp: dict, paths: dict[str, Path]) -> None:
    prefix = paths["radfpga_prefix"]
    payload = SCRIPT_DIR / comp["payload"]
    bin_dir = prefix / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    for command in comp["commands"]:
        install_file(payload / "bin" / command, bin_dir / command, 0o755)
        write_executable(paths["bindir"] / command, f'#!/usr/bin/env bash\nexec "{bin_dir / command}" "$@"\n')


def install_service(comp: dict, paths: dict[str, Path], args: argparse.Namespace) -> str:
    service = comp["service"]
    systemd_dir = Path(args.systemd_dir)
    if systemd_dir == Path("/etc/systemd/system") and os.geteuid() != 0:
        raise SystemExit("systemd service install requires root")
    template = (SCRIPT_DIR / service["template"]).read_text(encoding="utf-8")
    service_user_line = f"User={args.service_user}" if args.service_user else ""
    values = {
        "__RADBUILD_VERSION__": comp["version"],
        "__RADBUILD_PREFIX__": str(paths["radbuild_root"] / comp["version"]),
        "__RADBUILD_ROOT__": str(paths["radbuild_root"]),
        "__RADBUILD_HOST__": args.service_host or service.get("host", "0.0.0.0"),
        "__RADBUILD_PORT__": str(args.service_port or service.get("port", "8767")),
        "__SERVICE_USER_LINE__": service_user_line,
    }
    unit_name = args.service_name or service.get("name", "radbuild-server")
    unit_path = systemd_dir / f"{unit_name}.service"
    unit_path.parent.mkdir(parents=True, exist_ok=True)
    unit_path.write_text(render_template(template, values), encoding="utf-8")
    unit_path.chmod(0o644)
    if systemd_dir == Path("/etc/systemd/system"):
        subprocess.run(["systemctl", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "enable", f"{unit_name}.service"], check=True)
        if not args.no_start:
            subprocess.run(["systemctl", "restart", f"{unit_name}.service"], check=True)
        return f"installed and enabled at {unit_path}"
    return f"installed at {unit_path}"


def parse_toolchain_arg(value: str) -> dict[str, str]:
    parts = value.split(":", 2)
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("toolchain must be TOOL:VERSION:SETTINGS_SCRIPT")
    tool, version, settings_text = parts
    if tool not in {"vivado", "petalinux"}:
        raise argparse.ArgumentTypeError("toolchain TOOL must be vivado or petalinux")
    settings = Path(settings_text).expanduser().resolve()
    if not settings.exists():
        raise argparse.ArgumentTypeError(f"settings script does not exist: {settings}")
    return {
        "id": f"{tool}:{version}:{settings}",
        "tool": tool,
        "version": version,
        "install_dir": str(settings.parent),
        "settings": str(settings),
    }


def write_toolchain_registry(paths: dict[str, Path], version: str, toolchains: list[dict[str, str]]) -> Path | None:
    if not toolchains:
        return None
    registry = paths["radbuild_root"] / version / ".radmeta" / "toolchains.json"
    data = {"schema": "radbuild-toolchains-v1", "tools": {}}
    if registry.exists():
        try:
            existing = json.loads(registry.read_text(encoding="utf-8"))
            if isinstance(existing, dict):
                data.update(existing)
                data.setdefault("tools", {})
        except json.JSONDecodeError:
            pass

    tools = data.setdefault("tools", {})
    for item in toolchains:
        tool_versions = tools.setdefault(item["tool"], {})
        tool_versions[item["version"]] = {
            "install_dir": item["install_dir"],
            "settings": item["settings"],
        }
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    registry.chmod(0o644)
    return registry


def install(args: argparse.Namespace) -> None:
    raw_manifest = load_manifest()
    host_platform = args.host_platform or detect_platform()
    manifest = validate_manifest_platform(raw_manifest, host_platform, args.allow_platform_mismatch)
    comps = component_map(manifest)
    title = f'{manifest["release"]["name"]} {manifest["release"]["version"]} - {manifest["release"]["codename"]}'
    ui = args.ui
    if ui == "auto":
        ui = "curses" if have_curses() else "text"

    install_root = Path(args.install_root or manifest["defaults"]["install_root"])
    bindir = Path(args.bindir or manifest["defaults"]["bindir"])
    selected_toolchains = list(args.toolchain or [])

    selected = set(args.component or [])
    if args.all:
        selected.update(comps)
    if not args.non_interactive and not args.component and not args.all:
        if ui == "curses":
            if not have_curses():
                raise SystemExit("curses UI requires an interactive terminal with TERM set; use --ui text for plain prompts")
            try:
                install_root, bindir, selected, selected_toolchains = prompt_curses_install_options(manifest, selected, install_root, bindir)
            except curses.error as exc:
                if args.ui == "curses":
                    raise SystemExit(f"curses UI failed: {exc}; use --ui text") from exc
                print(f"curses UI unavailable ({exc}); falling back to text menu", file=sys.stderr)
                install_root, bindir, selected, selected_toolchains = prompt_text_install_options(manifest, selected, install_root, bindir)
        elif ui == "whiptail":
            if not have_whiptail():
                raise SystemExit("whiptail UI requires whiptail and an interactive terminal with TERM set; use --ui text")
            install_root, bindir, selected, selected_toolchains = prompt_whiptail_install_options(manifest, selected, install_root, bindir)
        else:
            install_root, bindir, selected, selected_toolchains = prompt_text_install_options(manifest, selected, install_root, bindir)

    selected = close_requires(selected, comps)
    install_dependencies(args, selected, comps)
    paths = {
        "install_root": install_root,
        "bindir": bindir,
        "radbuild_root": Path(args.radbuild_root) if args.radbuild_root else install_root / "RadBuild",
        "radfpga_prefix": Path(args.radfpga_prefix) if args.radfpga_prefix else install_root / "RadFPGA-Debug-Hub" / "v0.1.0",
    }

    bindir.mkdir(parents=True, exist_ok=True)
    service_status = "not installed"
    installed = []
    for comp_id in ["radbuild-tools", "radbuild-client", "radbuild-server"]:
        if comp_id in selected:
            install_radbuild_component(comps[comp_id], paths)
            installed.append(comp_id)
    if "radbuild-service" in selected:
        service_status = install_service(comps["radbuild-service"], paths, args)
        installed.append("radbuild-service")
    if "radfpga-debug-hub" in selected:
        install_debug_hub(comps["radfpga-debug-hub"], paths)
        installed.append("radfpga-debug-hub")
    toolchain_registry = write_toolchain_registry(paths, comps["radbuild-tools"]["version"], selected_toolchains)

    print(f"Installed {title}")
    print(f"  Host platform: {host_platform}")
    print(f"  Payload root: {install_root}")
    print(f"  Command wrappers: {bindir}")
    print(f"  Components: {', '.join(installed)}")
    print(f"  Service: {service_status}")
    if toolchain_registry:
        print(f"  Toolchains: {toolchain_registry}")


def uninstall(args: argparse.Namespace) -> None:
    raw_manifest = load_manifest()
    host_platform = args.host_platform or detect_platform()
    manifest = validate_manifest_platform(raw_manifest, host_platform, args.allow_platform_mismatch)
    comps = component_map(manifest)
    install_root = Path(args.install_root or manifest["defaults"]["install_root"])
    bindir = Path(args.bindir or manifest["defaults"]["bindir"])
    radbuild_root = Path(args.radbuild_root) if args.radbuild_root else install_root / "RadBuild"
    radfpga_prefix = Path(args.radfpga_prefix) if args.radfpga_prefix else install_root / "RadFPGA-Debug-Hub" / "v0.1.0"

    selected = close_requires(set(args.component or comps), comps)
    if "radbuild-service" in selected:
        service = comps["radbuild-service"]["service"]
        unit_name = args.service_name or service.get("name", "radbuild-server")
        unit_path = Path(args.systemd_dir) / f"{unit_name}.service"
        if unit_path.exists():
            if Path(args.systemd_dir) == Path("/etc/systemd/system") and os.geteuid() != 0:
                raise SystemExit("systemd service removal requires root")
            if Path(args.systemd_dir) == Path("/etc/systemd/system"):
                subprocess.run(["systemctl", "disable", "--now", f"{unit_name}.service"], check=False)
            unit_path.unlink()
            if Path(args.systemd_dir) == Path("/etc/systemd/system"):
                subprocess.run(["systemctl", "daemon-reload"], check=False)

    radbuild_commands = []
    radbuild_versions = set()
    for comp_id in ["radbuild-tools", "radbuild-client", "radbuild-server"]:
        if comp_id in selected:
            radbuild_commands.extend(comps[comp_id].get("commands", []))
            radbuild_versions.add(comps[comp_id]["version"])
    for command in radbuild_commands:
        paths = [bindir / command]
        paths.extend(bindir / f"{command}-{version}" for version in sorted(radbuild_versions))
        for path in paths:
            path.unlink(missing_ok=True)

    if any(comp_id in selected for comp_id in ["radbuild-tools", "radbuild-client", "radbuild-server"]):
        for version in sorted(radbuild_versions):
            radbuild_prefix = radbuild_root / version
            if args.remove_data:
                shutil.rmtree(radbuild_prefix, ignore_errors=True)
            elif radbuild_prefix.exists():
                for item in radbuild_prefix.iterdir():
                    if item.name != "radserver_data":
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()

    if "radfpga-debug-hub" in selected:
        for command in comps["radfpga-debug-hub"].get("commands", []):
            (bindir / command).unlink(missing_ok=True)
        shutil.rmtree(radfpga_prefix, ignore_errors=True)

    for path in [radbuild_root, radfpga_prefix.parent, install_root]:
        try:
            path.rmdir()
        except OSError:
            pass

    print("Removed selected RadTools components.")


def parse_args() -> argparse.Namespace:
    raw_manifest = load_manifest()
    host_platform = detect_platform()
    manifest = validate_manifest_platform(raw_manifest, host_platform, True)
    parser = argparse.ArgumentParser(description=f'{manifest["release"]["name"]} {manifest["release"]["version"]} - {manifest["release"]["codename"]} installer')
    sub = parser.add_subparsers(dest="action")
    install_cmd = sub.add_parser("install")
    uninstall_cmd = sub.add_parser("uninstall")
    for cmd in [install_cmd, uninstall_cmd]:
        cmd.add_argument("--install-root")
        cmd.add_argument("--radbuild-root")
        cmd.add_argument("--radfpga-prefix")
        cmd.add_argument("--bindir")
        cmd.add_argument("--component", action="append", choices=[c["id"] for c in manifest["components"]])
        cmd.add_argument("--systemd-dir", default=manifest["defaults"]["systemd_dir"])
        cmd.add_argument("--service-name")
        cmd.add_argument("--host-platform", help=f"Override detected platform. Detected default: {host_platform}")
        cmd.add_argument("--allow-platform-mismatch", action="store_true", help="Show/install manifest components even when host platform does not match.")
    install_cmd.add_argument("--all", action="store_true")
    install_cmd.add_argument("--non-interactive", action="store_true")
    install_cmd.add_argument("--ui", choices=["auto", "curses", "whiptail", "text"], default="auto")
    install_cmd.add_argument("--install-dependencies", action="store_true", help="Install missing OS packages for selected components with the host package manager.")
    install_cmd.add_argument("--no-install-dependencies", action="store_true", help="Do not install OS packages; fail if selected component dependencies are missing.")
    install_cmd.add_argument("--no-dependency-update", action="store_true", help="Skip package-manager update steps such as apt-get update.")
    install_cmd.add_argument("--service-user", default="")
    install_cmd.add_argument("--service-host", default="")
    install_cmd.add_argument("--service-port", default="")
    install_cmd.add_argument("--no-start", action="store_true")
    install_cmd.add_argument(
        "--toolchain",
        action="append",
        type=parse_toolchain_arg,
        help="Link a toolchain as TOOL:VERSION:SETTINGS_SCRIPT, e.g. vivado:2023.1:/opt/Xilinx/Vivado/2023.1/settings64.sh.",
    )
    uninstall_cmd.add_argument("--all", action="store_true", help="Remove all manifest components. This is the default when no --component is supplied.")
    uninstall_cmd.add_argument("--remove-data", action="store_true")
    args = parser.parse_args()
    if args.action is None:
        args.action = "install"
    return args


def main() -> int:
    args = parse_args()
    if args.action == "install":
        install(args)
    elif args.action == "uninstall":
        uninstall(args)
    else:
        raise SystemExit(f"unknown action: {args.action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
