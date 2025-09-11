"""Utilities to parse Tenable JSON reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel


class TenableVulnerability(BaseModel):
    """Representation of a vulnerability entry."""

    pkg: str
    version: str
    hosts: List[str]
    cve: str


def parse_tenable(file_path: str) -> List[Dict[str, Any]]:
    """Parse a Tenable JSON file.

    Parameters
    ----------
    file_path: str
        Path to the Tenable report.

    Returns
    -------
    list of dict
        List of vulnerabilities with keys ``pkg``, ``version``, ``hosts`` and ``cve``.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    """

    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Tenable file not found: {file_path}")

    data = json.loads(path.read_text())
    vulnerabilities = [
        TenableVulnerability(**item).model_dump()
        for item in data.get("vulnerabilities", [])
    ]
    return vulnerabilities
