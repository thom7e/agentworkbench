import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "desktop"))

import awb_run  # noqa: E402


def test_prompt_is_a_fixed_template_and_rejects_bad_input():
    assert "Todo #12" in awb_run.build_prompt("hsbau-backup", "12")
    assert "Briefing des Dashboard-Projekts holtei" in awb_run.build_prompt("holtei", "")
    for slug, todo in (("../x", "1"), ("holtei", "1;calc"), ("Holtei", "1"), ("a b", "")):
        assert awb_run.build_prompt(slug, todo) is None


def test_projects_root_comes_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("AWB_PROJECTS_ROOT", str(tmp_path))
    (tmp_path / "My-App").mkdir()
    assert awb_run.project_dir("my-app") == tmp_path / "My-App"
    assert awb_run.project_dir("unknown") == tmp_path
