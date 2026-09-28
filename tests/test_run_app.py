"""Tests for launcher paths and environment setup without starting Gradio."""
import os
from pathlib import Path

import run_app


def test_project_venv_python_path_and_interpreter_check(tmp_path):
    expected = tmp_path / ".venv" / "Scripts" / "python.exe"
    assert run_app.project_venv_python(tmp_path) == expected.resolve()
    assert run_app.is_project_venv_python(expected, tmp_path)
    assert not run_app.is_project_venv_python(tmp_path / "python.exe", tmp_path)


def test_configure_environment_sets_expected_values_and_path(tmp_path):
    env = {"PATH": os.pathsep.join(["C:\\Windows\\System32", "C:\\Tools"])}

    result = run_app.configure_environment(tmp_path, env)

    assert env["JAVA_HOME"] == r"C:\Program Files\Java\jdk-23"
    assert env["HADOOP_HOME"] == r"C:\hadoop"
    assert env["PYSPARK_PYTHON"] == str(
        Path(tmp_path).resolve() / ".venv" / "Scripts" / "python.exe"
    )
    assert env["PATH"].split(os.pathsep)[0] == r"C:\hadoop\bin"
    assert result["HADOOP_BIN"] == r"C:\hadoop\bin"
    assert "COHERE_API_KEY" not in env


def test_configure_environment_does_not_duplicate_hadoop_bin(tmp_path):
    env = {"PATH": os.pathsep.join([r"C:\hadoop\bin", r"C:\Windows\System32"])}

    run_app.configure_environment(tmp_path, env)

    assert env["PATH"].split(os.pathsep).count(r"C:\hadoop\bin") == 1


def test_main_delegates_to_existing_gradio_entrypoint(monkeypatch):
    monkeypatch.setattr(run_app, "is_project_venv_python", lambda executable: True)
    configured = {}
    monkeypatch.setattr(run_app, "configure_environment", lambda: configured.update({"done": True}))
    launched = {}
    monkeypatch.setattr(run_app.runpy, "run_path", lambda path, run_name: launched.update({"path": path, "run_name": run_name}))

    assert run_app.main() == 0
    assert configured["done"] is True
    assert launched["path"] == str(run_app.PROJECT_ROOT / "app" / "gradio_app.py")
    assert launched["run_name"] == "__main__"
