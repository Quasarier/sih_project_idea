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

    def test_curved_paths_keep_endpoints_and_bend_midpoint(self):
        path = forecast((18.72, 72.10), (0.1, 0.2), 4, curve_strength=0.1)
        self.assertEqual(path[0], (18.72, 72.1))
        self.assertEqual(path[-1], (19.12, 72.9))
        self.assertNotEqual(path[2], (18.92, 72.5))

    def test_curved_hindcast_and_forecast_join_smoothly(self):
        hindcast = backtrack((18.72, 72.10), (0.1, 0.2), 4, curve_strength=0.1)
        forecast_path = forecast((18.72, 72.10), (0.1, 0.2), 4, curve_strength=0.1)
        incoming = (hindcast[0][0] - hindcast[1][0], hindcast[0][1] - hindcast[1][1])
        outgoing = (forecast_path[1][0] - forecast_path[0][0], forecast_path[1][1] - forecast_path[0][1])
        self.assertAlmostEqual(incoming[0], outgoing[0], places=5)
        self.assertAlmostEqual(incoming[1], outgoing[1], places=5)


if __name__ == "__main__":
    unittest.main()
