from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "bug-bounty-report-submitter"
    / "scripts"
    / "record_asciinema_replay.py"
)
SPEC = importlib.util.spec_from_file_location("record_asciinema_replay", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RecordAsciinemaReplayTests(unittest.TestCase):
    def test_build_recorded_command_echoes_each_replay_command_before_execution(self) -> None:
        recorded_command = MODULE.build_recorded_command("python setup.py\npython exploit.py")

        self.assertIn("printf '$ %s\\n' 'python setup.py'", recorded_command)
        self.assertIn("printf '$ %s\\n' 'python exploit.py'", recorded_command)
        self.assertTrue(recorded_command.endswith("python exploit.py"))

    def test_records_uploads_and_writes_metadata_with_native_asciinema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            finding_dir = root / "audit-targets" / "demo" / "findings" / "F-001"
            workdir = root / "target-root"
            finding_dir.mkdir(parents=True)
            workdir.mkdir()

            cast_path = finding_dir / "artifacts" / "asciinema" / "reverify-session.cast"
            metadata_path = finding_dir / "artifacts" / "asciinema" / "asciinema-session.json"

            def fake_run(
                args: list[str],
                check: bool,
                capture_output: bool,
                text: bool,
                cwd: Path | None = None,
            ) -> subprocess.CompletedProcess[str]:
                if args[:2] == ["asciinema", "--version"]:
                    return subprocess.CompletedProcess(args, 0, "asciinema 2.4.0\n", "")
                if args[:2] == ["asciinema", "rec"]:
                    recorded_command = args[args.index("-c") + 1]
                    self.assertIn('echo " > Proof of Concept"', recorded_command)
                    self.assertIn('echo " > crafted by dxoth1nh"', recorded_command)
                    self.assertIn("sleep 2", recorded_command)
                    self.assertIn("set -e", recorded_command)
                    self.assertIn("printf '$ %s\\n' 'python exploit.py'", recorded_command)
                    self.assertTrue(recorded_command.endswith("python exploit.py"))
                    cast_path.parent.mkdir(parents=True, exist_ok=True)
                    cast_path.write_text("{}\n", encoding="utf-8")
                    return subprocess.CompletedProcess(args, 0, "", "")
                if args[:2] == ["asciinema", "upload"]:
                    return subprocess.CompletedProcess(args, 0, "https://asciinema.org/a/demo123\n", "")
                raise AssertionError(f"unexpected command: {args}")

            with patch.object(MODULE.subprocess, "run", side_effect=fake_run):
                result = MODULE.record_asciinema_replay(
                    finding_dir=finding_dir,
                    run_command="python exploit.py",
                    workdir=workdir,
                    title="demo replay",
                    success_signals=["[PASS] replay completed"],
                    output_dir=None,
                    force=False,
                )

            self.assertEqual(result["server_url"], "https://asciinema.org/a/demo123")
            self.assertTrue(cast_path.exists())
            self.assertTrue(metadata_path.exists())

            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(metadata["tool"], "asciinema")
            self.assertEqual(metadata["local_cast_path"], "reverify-session.cast")
            self.assertEqual(metadata["server_url"], "https://asciinema.org/a/demo123")
            self.assertIn('echo " > Proof of Concept"', metadata["recorded_command"])
            self.assertTrue(metadata["recorded_command"].endswith("python exploit.py"))
            self.assertEqual(
                metadata["link_markdown"],
                "[https://asciinema.org/a/demo123](https://asciinema.org/a/demo123)",
            )
            self.assertEqual(metadata["environment_check"]["mode"], "native")
            self.assertEqual(metadata["success_signals"], ["[PASS] replay completed"])

    def test_falls_back_to_wsl_when_native_asciinema_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            finding_dir = root / "audit-targets" / "demo" / "findings" / "F-001"
            workdir = root / "target-root"
            finding_dir.mkdir(parents=True)
            workdir.mkdir()

            cast_path = finding_dir / "artifacts" / "asciinema" / "reverify-session.cast"
            metadata_path = finding_dir / "artifacts" / "asciinema" / "asciinema-session.json"

            def fake_run(
                args: list[str],
                check: bool,
                capture_output: bool,
                text: bool,
                cwd: Path | None = None,
            ) -> subprocess.CompletedProcess[str]:
                if args[:2] == ["asciinema", "--version"]:
                    raise FileNotFoundError("asciinema")
                command = args[-1]
                if "asciinema --version" in command:
                    return subprocess.CompletedProcess(args, 0, "asciinema 2.4.0\n", "")
                if "asciinema rec" in command:
                    self.assertIn('echo " > Proof of Concept"', command)
                    self.assertIn('echo " > crafted by dxoth1nh"', command)
                    self.assertIn("sleep 2", command)
                    self.assertIn("set -e", command)
                    self.assertIn("printf", command)
                    self.assertIn("python exploit.py", command)
                    cast_path.parent.mkdir(parents=True, exist_ok=True)
                    cast_path.write_text("{}\n", encoding="utf-8")
                    return subprocess.CompletedProcess(args, 0, "", "")
                if "asciinema upload" in command:
                    return subprocess.CompletedProcess(args, 0, "https://asciinema.org/a/demo123\n", "")
                raise AssertionError(f"unexpected command: {args}")

            with patch.object(MODULE.subprocess, "run", side_effect=fake_run):
                MODULE.record_asciinema_replay(
                    finding_dir=finding_dir,
                    run_command="python exploit.py",
                    workdir=workdir,
                    title="demo replay",
                    success_signals=[],
                    output_dir=None,
                    force=False,
                )

            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(metadata["environment_check"]["mode"], "wsl")

    def test_fails_when_asciinema_is_missing_on_system(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            finding_dir = root / "audit-targets" / "demo" / "findings" / "F-001"
            workdir = root / "target-root"
            finding_dir.mkdir(parents=True)
            workdir.mkdir()

            def fake_run(
                args: list[str],
                check: bool,
                capture_output: bool,
                text: bool,
                cwd: Path | None = None,
            ) -> subprocess.CompletedProcess[str]:
                if args[:2] == ["asciinema", "--version"]:
                    raise FileNotFoundError("asciinema")
                return subprocess.CompletedProcess(args, 1, "", "not found")

            with patch.object(MODULE.subprocess, "run", side_effect=fake_run):
                with self.assertRaises(SystemExit) as exc:
                    MODULE.record_asciinema_replay(
                        finding_dir=finding_dir,
                        run_command="python exploit.py",
                        workdir=workdir,
                        title=None,
                        success_signals=[],
                        output_dir=None,
                        force=False,
                    )

            self.assertIn("Checked native PATH", str(exc.exception))
            self.assertIn("and WSL", str(exc.exception))


if __name__ == "__main__":
    unittest.main()
