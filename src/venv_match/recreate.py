"""Safe virtual environment creation and requirements export from a Snapshot."""

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from venv_match.exceptions import CollectionError, SnapshotFormatError
from venv_match.snapshot import Snapshot

DEFAULT_EXCLUDED_PACKAGES: frozenset[str] = frozenset(
    {"pip", "setuptools", "wheel", "distribute"}
)

_SAFE_PKG_NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?$")
_SAFE_VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.+!_~-]*$")


@dataclass(frozen=True)
class CreateVenvResult:
    """Result details from creating or dry-running a virtual environment from a snapshot."""

    target_dir: Path
    python_executable: str
    venv_python: Path
    installed_packages: tuple[str, ...]
    python_version_warning: str | None
    dry_run: bool


def _validate_safe_package_spec(name: str, version: str) -> str:
    """Ensure package name and version cannot inject flags or shell/pip options."""
    if (
        not _SAFE_PKG_NAME_RE.match(name)
        or name.startswith("-")
        or not _SAFE_VERSION_RE.match(version)
        or version.startswith("-")
    ):
        raise SnapshotFormatError(
            f"Unsafe or invalid package specification in snapshot: '{name}=={version}'."
        )
    return f"{name}=={version}"


def export_requirements(
    snapshot: Snapshot,
    *,
    include_build_tools: bool = False,
) -> list[str]:
    """Return a deterministic list of 'package==version' requirement specifiers."""
    if not isinstance(snapshot, Snapshot):
        raise SnapshotFormatError("Expected a validated Snapshot instance.")

    sections = snapshot.sections
    if "packages" not in snapshot.completed_sections or "packages" not in sections:
        raise SnapshotFormatError(
            "Snapshot does not contain a collected 'packages' section."
        )

    raw_packages: dict[str, str] = sections["packages"]
    specs: list[str] = []
    for pkg_name in sorted(raw_packages.keys()):
        if not include_build_tools and pkg_name in DEFAULT_EXCLUDED_PACKAGES:
            continue
        pkg_version = raw_packages[pkg_name]
        specs.append(_validate_safe_package_spec(pkg_name, pkg_version))

    return specs


def _resolve_venv_python_path(target_dir: Path) -> Path:
    if os.name == "nt":
        return target_dir / "Scripts" / "python.exe"
    return target_dir / "bin" / "python"


def _query_interpreter_version(python_bin: str) -> str | None:
    try:
        res = subprocess.run(
            [
                python_bin,
                "-c",
                "import platform; print(platform.python_version())",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip() or None
    except Exception:
        return None


def create_venv(
    snapshot: Snapshot,
    target_dir: str | Path,
    *,
    python_executable: str | None = None,
    include_build_tools: bool = False,
    overwrite: bool = False,
    dry_run: bool = False,
) -> CreateVenvResult:
    """Create a virtual environment and install packages recorded in a Snapshot."""
    specs = export_requirements(snapshot, include_build_tools=include_build_tools)
    target = Path(target_dir)
    py_exe = python_executable if python_executable is not None else sys.executable

    if target.exists() and not overwrite:
        raise CollectionError(
            f"Refusing to overwrite existing directory '{target}'. "
            "Pass overwrite=True or --overwrite to replace it."
        )

    snap_py_ver = str(snapshot.sections.get("python", {}).get("version", ""))
    local_py_ver = _query_interpreter_version(py_exe)
    version_warning: str | None = None
    if snap_py_ver and local_py_ver and snap_py_ver != local_py_ver:
        version_warning = (
            f"Snapshot was captured with Python {snap_py_ver}, "
            f"but target environment uses Python {local_py_ver}."
        )

    venv_python = _resolve_venv_python_path(target)

    if dry_run:
        return CreateVenvResult(
            target_dir=target,
            python_executable=py_exe,
            venv_python=venv_python,
            installed_packages=tuple(specs),
            python_version_warning=version_warning,
            dry_run=True,
        )

    if target.exists() and overwrite:
        try:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        except OSError as exc:
            raise CollectionError(
                f"Failed to remove existing target '{target}': {exc}"
            ) from exc

    # Step 1: Create the virtual environment
    try:
        subprocess.run(
            [py_exe, "-m", "venv", str(target)],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr_msg = (exc.stderr or "").strip()
        raise CollectionError(
            f"Failed to create virtual environment at '{target}': {stderr_msg or exc}"
        ) from exc
    except OSError as exc:
        raise CollectionError(
            f"Failed to execute Python interpreter '{py_exe}': {exc}"
        ) from exc

    if not venv_python.exists():
        raise CollectionError(
            f"Virtual environment created at '{target}', but interpreter '{venv_python}' was not found."
        )

    # Step 2: Install pinned packages if any exist
    if specs:
        try:
            subprocess.run(
                [
                    str(venv_python),
                    "-m",
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    "--",
                    *specs,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            stderr_msg = (exc.stderr or "").strip()
            raise CollectionError(
                f"Failed to install packages into '{target}': {stderr_msg or exc}"
            ) from exc

    return CreateVenvResult(
        target_dir=target,
        python_executable=py_exe,
        venv_python=venv_python,
        installed_packages=tuple(specs),
        python_version_warning=version_warning,
        dry_run=False,
    )
