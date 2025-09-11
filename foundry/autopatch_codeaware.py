#!/usr/bin/env python3
"""
AutoPatch‐CodeAware
Reemplaza librerías vulnerables solo si el proyecto realmente las usa.
"""

from __future__ import annotations
import json, subprocess, shutil, hashlib, sys
from pathlib import Path
from typing import List, Dict, Any
import yaml

ROOT = Path(__file__).resolve().parents[1]          # asume foundry/ dentro del repo
PACK_DIR = ROOT / "approved-packages"
PROJ_DIR = ROOT / "vulnerable-app"
LIB_DIR  = PROJ_DIR / "libs"

### ---------- 1. Parse Tenable report ----------

def parse_report(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text("utf-8"))
    return [
        i for i in data
        if i.get("severity") == "critical"
    ]

### ---------- 2. Verificar uso real en proyecto ----------

def project_uses(pkg_name: str, bad_version: str) -> bool:
    """Busca JARs o DLLs con nombre+versión en árbol del proyecto."""
    pattern = f"{pkg_name}-{bad_version}"
    for p in PROJ_DIR.rglob("*"):
        if pattern in p.name:
            return True
    return False

### ---------- 3. Aplicar parche según AGENT.yaml ----------

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def apply_patch(pkg: str, target_version: str) -> None:
    pkg_folder = PACK_DIR / f"{pkg}-{target_version}"
    agent_file = pkg_folder / "AGENT.yaml"
    spec = yaml.safe_load(agent_file.read_text("utf-8"))

    # checksum básico
    jar = pkg_folder / f"{pkg}-{target_version}.jar"
    if sha256(jar) != spec["checksum"].split(":")[1]:
        sys.exit(f"Checksum mismatch for {jar}")

    # steps — solo soportamos remove/copy directo para mantenerlo simple
    for step in spec["steps"]:
        cmd = step["shell"].replace("{{ playbook_dir }}", str(pkg_folder))
        completed = subprocess.run(cmd, shell=True, cwd=ROOT)
        if completed.returncode != 0:
            sys.exit(f"Step failed: {cmd}")

    # validación
    for check in spec["validate"]:
        completed = subprocess.run(check["shell"], shell=True, cwd=ROOT)
        if completed.returncode != 0:
            sys.exit("Validation failed")

    print(f"OK: {pkg}-{target_version} aplicado")

### ---------- 4. Orquestación ----------

def main(report_path: str):
    findings = parse_report(Path(report_path))
    if not findings:
        print("No critical findings.")
        return
    
    for f in findings:
        pkg = f["package"]
        vuln_ver = f["current_version"]
        fixed_ver = f["fixed_version"]

        if not project_uses(pkg, vuln_ver):
            print(f"Skip {pkg}-{vuln_ver}: no está en proyecto")
            continue
        
        apply_patch(pkg, fixed_ver)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: autopatch_codeaware.py <report.json>")
    main(sys.argv[1])
