import unittest

from simulation.hindcast.drift import backtrack, forecast, origin_window


class DriftTests(unittest.TestCase):
    def test_backtrack_moves_against_current(self):
        path = backtrack((18.72, 72.10), (0.1, 0.2), 2)
        self.assertEqual(path, [(18.72, 72.1), (18.62, 71.9), (18.52, 71.7)])

    def test_forecast_moves_with_current(self):
        path = forecast((18.72, 72.10), (0.1, 0.2), 2)
        self.assertEqual(path, [(18.72, 72.1), (18.82, 72.3), (18.92, 72.5)])

    def test_origin_window_contains_requested_hours(self):
        result = origin_window((18.72, 72.10), (0.1, 0.2), 6)
        self.assertEqual(result["hours"], 6)
        self.assertEqual(len(result["path"]), 7)
        self.assertEqual(result["start"], (18.12, 70.9))
        self.assertEqual(result["end"], (18.72, 72.1))


if __name__ == "__main__":
    unittest.main()
