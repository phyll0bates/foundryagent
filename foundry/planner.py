"""Build an Ansible playbook from AGENT.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml


def build_plan(agent_dir: Path) -> List[Dict[str, Any]]:
    """Create a playbook with canary and batch phases.

    Parameters
    ----------
    agent_dir: Path
        Directory containing ``AGENT.yaml``.

    Returns
    -------
    list of dict
        Ansible playbook represented as Python structures.
    """

    agent_path = agent_dir / "AGENT.yaml"
    data = yaml.safe_load(agent_path.read_text())
    tasks = [{"name": step["name"], "shell": step["shell"]} for step in data.get("steps", [])]

    canary = {"hosts": "all", "serial": "10%", "tasks": tasks}
    batch = {"hosts": "all", "serial": "30%", "tasks": tasks}
    return [canary, batch]
