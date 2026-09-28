"""Windows-friendly launcher for the existing Document Summarizer Gradio app."""
from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path
from typing import MutableMapping

PROJECT_ROOT = Path(__file__).resolve().parent


def project_venv_python(project_root: str | Path = PROJECT_ROOT) -> Path:
    """Return the Windows Python executable belonging to this project's venv."""
    return Path(project_root).resolve() / ".venv" / "Scripts" / "python.exe"


def is_project_venv_python(
    executable: str | Path, project_root: str | Path = PROJECT_ROOT
) -> bool:
    """Whether *executable* resolves to this project's virtualenv Python."""
    return Path(executable).resolve() == project_venv_python(project_root).resolve()


def configure_environment(
    project_root: str | Path = PROJECT_ROOT,
    environ: MutableMapping[str, str] | None = None,
) -> dict[str, str]:
    """Set local Java, Hadoop, and PySpark paths in the current process env."""
    env = os.environ if environ is None else environ
    root = Path(project_root).resolve()
    java_home = Path(r"C:\Program Files\Java\jdk-23")
    hadoop_home = Path(r"C:\hadoop")
    hadoop_bin = str(hadoop_home / "bin")
    python_executable = str(project_venv_python(root))

    env["JAVA_HOME"] = str(java_home)
    env["HADOOP_HOME"] = str(hadoop_home)
    env["PYSPARK_PYTHON"] = python_executable

    path_entries = env.get("PATH", "").split(os.pathsep)
    norm_hadoop_bin = os.path.normcase(os.path.normpath(hadoop_bin))
    if not any(
        os.path.normcase(os.path.normpath(entry)) == norm_hadoop_bin
        for entry in path_entries
        if entry
    ):
        env["PATH"] = os.pathsep.join([hadoop_bin, *[entry for entry in path_entries if entry]])

    return {
        "JAVA_HOME": env["JAVA_HOME"],
        "HADOOP_HOME": env["HADOOP_HOME"],
        "PYSPARK_PYTHON": env["PYSPARK_PYTHON"],
        "HADOOP_BIN": hadoop_bin,
    }


def main() -> int:
    if not is_project_venv_python(sys.executable):
        print(
            "This project must run with its .venv Python. Activate it first, then run python run_app.py.\n"
            "PowerShell: .\\.venv\\Scripts\\Activate.ps1\n"
            "Command Prompt: .venv\\Scripts\\activate.bat"
        )
        return 1

    configure_environment()
    app_path = PROJECT_ROOT / "app" / "gradio_app.py"
    runpy.run_path(str(app_path), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
