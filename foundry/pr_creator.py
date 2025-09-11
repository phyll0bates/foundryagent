"""Create remediation commits for vulnerable applications."""

from __future__ import annotations

from pathlib import Path
import shutil

from git import Repo


def create_pr(app_dir: Path, approved_dir: Path, cve: str) -> str:
    """Create a remediation commit replacing the vulnerable jar.

    Parameters
    ----------
    app_dir: Path
        Path to the vulnerable application repository.
    approved_dir: Path
        Path to the approved package directory.
    cve: str
        Identifier of the vulnerability.

    Returns
    -------
    str
        Name of the branch created.
    """

    repo = Repo(app_dir)
    branch_name = f"autopatch-{cve.lower()}"
    repo.git.checkout('-b', branch_name)

    libs = app_dir / 'libs'
    for jar in libs.glob('log4j*.jar'):
        jar.unlink()

    src_jar = approved_dir / f"{approved_dir.name}.jar"
    shutil.copy(src_jar, libs / src_jar.name)

    repo.git.add(libs)
    repo.index.commit(f"AUTO-PATCH: {cve}")
    return branch_name
