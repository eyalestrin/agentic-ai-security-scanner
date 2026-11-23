import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "scanner", ROOT / ".github/skills/agentic-ai-security-scanner/scanner.py"
)
scanner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scanner)


def example():
    finding = {
        "severity": "Low",
        "file": "/workspace/agent.py",
        "line": 8,
        "title": "Untrusted <tool> output",
        "description": "Untrusted data can redirect the agent beyond its read-only intent.",
        "snippet": "    run(input)",
        "recommendation": "Validate tool arguments.",
        "references": [{"title": "OWASP", "url": "https://genai.owasp.org/agentic-applications-2026/asi02-tool-misuse-and-exploitation/"}],
    }
    high = copy.deepcopy(finding)
    high.update(severity="High", title="Privileged action")
    return {
        "name": "Example agent", "description": "", "languages": ["Python"],
        "model": "Unknown (not exposed by the host)", "intent": "Read only",
        "coverage": "Reviewed agent.py; deployment permissions unavailable.",
        "findings": [finding, high],
    }


class ReportTests(unittest.TestCase):
    def test_both_reports_are_sorted_escaped_and_linked(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "findings.json"
            path.write_text(json.dumps(example()), encoding="utf-8")
            scanner.generate_report(path, tmp)
            html_path = next(Path(tmp).glob("*.html"))
            pdf_path = next(Path(tmp).glob("*.pdf"))
            self.assertEqual(html_path.stem, pdf_path.stem)
            self.assertTrue(html_path.stem.startswith("agentic-ai-scanner-report-"))
            rendered = html_path.read_text(encoding="utf-8")
            self.assertIn("Untrusted &lt;tool&gt; output", rendered)
            self.assertNotIn("Untrusted <tool> output", rendered)
            self.assertLess(rendered.index("Privileged action"), rendered.index("Untrusted &lt;tool&gt;"))
            pdf = PdfReader(str(pdf_path))
            pdf_text = "\n".join(page.extract_text() for page in pdf.pages)
            self.assertLess(pdf_text.index("Privileged action"), pdf_text.index("Untrusted <tool>"))
            self.assertIn("Unknown (not exposed by the host)", pdf_text)
            self.assertIn("deployment permissions unavailable", pdf_text)
            uris = [annotation.get_object().get("/A", {}).get("/URI")
                    for page in pdf.pages for annotation in page.get("/Annots", [])]
            self.assertIn(example()["findings"][0]["references"][0]["url"], uris)

    def test_empty_findings_are_not_presented_as_proof_of_security(self):
        data = example()
        data["findings"] = []
        rendered = scanner.report_html(scanner.validate(data), "2026-01-01")
        self.assertIn("not a guarantee of security", rendered)
        self.assertEqual(rendered.count("<td>0</td>"), 4)

    def test_invalid_finding_is_rejected_before_output(self):
        data = example()
        data["findings"][0]["references"][0]["url"] = "https://owasp.org.attacker.test/"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "findings.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                scanner.generate_report(path, tmp)
            self.assertFalse(list(Path(tmp).glob("agentic-ai-scanner-report-*")))

    def test_windows_absolute_path_and_severity_validation(self):
        data = example()
        data["findings"][0]["file"] = r"C:\agent\main.py"
        scanner.validate(data)
        data["findings"][0]["severity"] = "Unknown"
        with self.assertRaises(ValueError):
            scanner.validate(data)

    def test_temporary_findings_are_deleted_and_reports_go_to_scanned_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            findings = root / "findings.json"
            target = root / "scanned"
            target.mkdir()
            findings.write_text(json.dumps(example()), encoding="utf-8")
            with patch.object(sys, "argv", ["scanner.py", "--report", str(findings),
                                            "--output", str(target), "--delete-findings"]):
                self.assertEqual(scanner.main(), 0)
            self.assertFalse(findings.exists())
            self.assertEqual({p.suffix for p in target.iterdir()}, {".html", ".pdf"})

    def test_temporary_findings_are_deleted_on_invalid_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            findings = Path(tmp) / "findings.json"
            findings.write_text("invalid json", encoding="utf-8")
            with patch.object(sys, "argv", ["scanner.py", "--report", str(findings),
                                            "--output", tmp, "--delete-findings"]):
                self.assertEqual(scanner.main(), 1)
            self.assertFalse(findings.exists())

    def test_standalone_renderer_preserves_input_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            findings = Path(tmp) / "findings.json"
            findings.write_text(json.dumps(example()), encoding="utf-8")
            with patch.object(sys, "argv", ["scanner.py", "--report", str(findings), "--output", tmp]):
                self.assertEqual(scanner.main(), 0)
            self.assertTrue(findings.exists())

    def test_cleanup_failure_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            findings = Path(tmp) / "findings.json"
            findings.write_text(json.dumps(example()), encoding="utf-8")
            with patch.object(sys, "argv", ["scanner.py", "--report", str(findings),
                                            "--output", tmp, "--delete-findings"]), \
                 patch.object(scanner.Path, "unlink", side_effect=PermissionError("denied")):
                self.assertEqual(scanner.main(), 1)
            self.assertTrue(findings.exists())


class UpdateTests(unittest.TestCase):
    def test_download_failure_preserves_existing_snapshots(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            existing = directory / "mcp-security.md"
            existing.write_text("existing", encoding="utf-8")
            with patch.object(scanner, "REFERENCES", directory), patch.object(
                scanner, "fetch", side_effect=OSError("network unavailable")
            ):
                with self.assertRaises(OSError):
                    scanner.update_references()
            self.assertEqual(existing.read_text(encoding="utf-8"), "existing")


if __name__ == "__main__":
    unittest.main()
