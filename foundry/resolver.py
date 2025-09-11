"""Locate approved packages."""

from __future__ import annotations

from pathlib import Path


def resolve(pkg: str, version: str) -> Path:
    """Return the directory for an approved package.

    Parameters
    ----------
    pkg: str
        Package name.
    version: str
        Package version.

    Returns
    -------
    Path
        Path to the approved package directory.

    Raises
    ------
    FileNotFoundError
        If no matching directory exists.
    """

    base = Path("approved-packages")
    candidate = base / f"{pkg}-{version}"
    if candidate.is_dir():
        return candidate
    raise FileNotFoundError(f"Approved package not found for {pkg}-{version}")
