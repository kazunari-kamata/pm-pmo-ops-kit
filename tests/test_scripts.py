from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args], cwd=ROOT, text=True, capture_output=True, check=False
    )


def test_generate_requirements_checklist() -> None:
    result = run_script("scripts/generate_project_checklist.py", "requirements")
    assert result.returncode == 0
    assert "受入条件" in result.stdout


def test_generate_rejects_unknown_phase() -> None:
    result = run_script("scripts/generate_project_checklist.py", "unknown")
    assert result.returncode != 0


def test_templates_validate() -> None:
    result = run_script("scripts/validate_templates.py", "templates")
    assert result.returncode == 0
    assert "validated" in result.stdout
