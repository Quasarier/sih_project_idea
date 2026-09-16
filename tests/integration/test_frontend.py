"""Integration checks for the static frontend and API contract."""

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class TestFrontend(unittest.TestCase):
    def test_frontend_contains_intake_controls(self):
        document = (PROJECT_ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="tiff-file"', document)
        self.assertIn('id="ais-file"', document)
        self.assertIn("Use demo files", document)

    def test_frontend_references_api(self):
        script = (PROJECT_ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
        self.assertIn("/api/analyze?scenario=", script)
        self.assertIn("activeCandidates", script)


if __name__ == "__main__":
    unittest.main()
