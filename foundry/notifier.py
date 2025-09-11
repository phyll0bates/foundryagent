"""Simple webhook notifier."""

from __future__ import annotations

import os
from typing import Any, Dict

import requests


def notify(status: str, detail: str) -> None:
    """Send a POST request with the operation status.

    Parameters
    ----------
    status: str
        Status string.
    detail: str
        Additional information.
    """

    url = os.environ.get("AUTOPATCH_WEBHOOK")
    if not url:
        return

    payload: Dict[str, Any] = {"status": status, "detail": detail}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass
