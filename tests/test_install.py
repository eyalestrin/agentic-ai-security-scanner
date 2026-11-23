import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("installer", ROOT / "install.py")
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class InstallationTests(unittest.TestCase):
    def test_installs_without_copying_local_environment(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(installer.Path, "home", return_value=Path(tmp)), \
             patch.object(installer.subprocess, "run") as run:
            installer.install()
            destination = Path(tmp) / ".copilot" / "skills" / installer.NAME
            self.assertTrue((destination / "SKILL.md").is_file())
            self.assertTrue((destination / "references" / "maestro.md").is_file())
            self.assertFalse((destination / ".venv").exists())
            self.assertEqual((destination / "python-interpreter.txt").read_text().strip(),
                             installer.sys.executable)
            self.assertIn("--target", run.call_args.args[0])

    def test_failure_does_not_leave_partial_installation(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(installer.Path, "home", return_value=Path(tmp)), \
             patch.object(installer.subprocess, "run",
                          side_effect=subprocess.CalledProcessError(1, "pip")):
            with self.assertRaises(subprocess.CalledProcessError):
                installer.install()
            skills = Path(tmp) / ".copilot" / "skills"
            self.assertEqual(list(skills.iterdir()), [])

    def test_existing_installation_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(installer.Path, "home", return_value=Path(tmp)), \
             patch.object(installer.subprocess, "run") as run:
            destination = Path(tmp) / ".copilot" / "skills" / installer.NAME
            destination.mkdir(parents=True)
            marker = destination / "marker"
            marker.write_text("keep", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                installer.install()
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
