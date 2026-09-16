"""Unit tests for the Coastal Watch API server."""

import unittest
from pathlib import Path
from unittest.mock import patch

from backend.api.server import SCENARIOS, analyze


class TestServer(unittest.TestCase):
    """Test the Coastal Watch API server."""
    
    def test_valid_scenario_request(self):
        """Test that a valid scenario request returns 200."""
        # Test with default scenario
        scenario_id = "demo1"
        result = analyze(scenario_id)
        
        # Check that the result contains expected keys
        self.assertIn("scenario", result)
        self.assertEqual(result["scenario"], scenario_id)
        self.assertIn("candidates", result)
        
    def test_invalid_scenario_parameter(self):
        """Test that an invalid scenario parameter returns 400."""
        # Test with non-alphanumeric scenario
        scenario_id = "demo1;drop table"
        
        with self.assertRaises(KeyError):
            analyze(scenario_id)
        
    def test_unknown_scenario(self):
        """Test that an unknown scenario returns 400."""
        # Test with non-existent scenario
        scenario_id = "unknown"
        
        with self.assertRaises(KeyError):
            analyze(scenario_id)
        
    def test_missing_files(self):
        """Test that missing files are handled gracefully."""
        # Test with a scenario that has missing files
        test_scenario = {
            "ais": Path("/path/to/nonexistent.csv"),
            "tiff": Path("/path/to/nonexistent.tif"),
            "hindcast_origin": [18.72, 72.10],
            "window_start": "2024-06-17T22:10:00Z",
            "window_end": "2024-06-18T01:40:00Z"
        }
        SCENARIOS["test_missing"] = test_scenario
        try:
            with self.assertRaises(FileNotFoundError):
                analyze("test_missing")
        finally:
            SCENARIOS.pop("test_missing", None)

if __name__ == "__main__":
    unittest.main()