from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

SCRIPT = Path(__file__).parents[1] / "scripts" / "download_roboflow_dataset.py"
SPEC = importlib.util.spec_from_file_location("download_roboflow_dataset", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
DOWNLOADER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DOWNLOADER)


def _install_fake_roboflow(monkeypatch, download):
    class FakeProjectVersion:
        def download(self, *args, **kwargs):
            return download(*args, **kwargs)

    fake_module = ModuleType("roboflow")
    fake_module.Roboflow = lambda **kwargs: SimpleNamespace(  # type: ignore[attr-defined]
        workspace=lambda name: SimpleNamespace(
            project=lambda project: SimpleNamespace(
                version=lambda version: FakeProjectVersion()
            )
        )
    )
    monkeypatch.setitem(sys.modules, "roboflow", fake_module)


def test_downloader_reports_cli_metadata_without_sdk_attributes(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("ROBOFLOW_API_KEY=test-secret\n")
    output_dir = tmp_path / "download"
    _install_fake_roboflow(monkeypatch, lambda *args, **kwargs: object())

    result = DOWNLOADER.main(
        [
            "--env-file", str(env_file),
            "--workspace", "example-workspace",
            "--project", "example-project",
            "--version", "32",
            "--output-dir", str(output_dir),
        ]
    )

    summary = json.loads(capsys.readouterr().out)
    assert result == 0
    assert summary == {
        "location": str(output_dir.resolve()),
        "version": 32,
        "format": "yolov8",
    }


def test_downloader_masks_api_key_in_sdk_error(tmp_path: Path, monkeypatch, capsys) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("ROBOFLOW_API_KEY=test-secret\n")

    def fail(*args, **kwargs):
        raise RuntimeError("request failed api_key=test-secret")

    _install_fake_roboflow(monkeypatch, fail)
    result = DOWNLOADER.main(
        [
            "--env-file", str(env_file),
            "--workspace", "example-workspace",
            "--project", "example-project",
            "--version", "32",
            "--output-dir", str(tmp_path / "download"),
        ]
    )

    output = capsys.readouterr().out
    assert result == 1
    assert "test-secret" not in output
    assert 'api_key=***' in output
