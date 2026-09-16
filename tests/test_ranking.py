import csv
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from ml.ranking.config import RankingConfig
from ml.ranking.rank_vessels import behavioral_anomaly_score, likelihood_ratio, rank_vessels


class RankingTests(unittest.TestCase):
    headers = ["mmsi", "imo", "vessel_name", "timestamp", "latitude", "longitude", "speed_knots", "heading_deg", "ship_type"]

    def write_csv(self, rows: list[dict]) -> Path:
        file = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8")
        with file:
            writer = csv.DictWriter(file, fieldnames=self.headers)
            writer.writeheader()
            writer.writerows(rows)
        return Path(file.name)

    def test_closest_tanker_ranks_above_distant_decoy(self):
        path = self.write_csv([
            {"mmsi": "1", "imo": "1", "vessel_name": "Near Tanker", "timestamp": "2024-06-18T00:20:00Z", "latitude": "18.72", "longitude": "72.11", "speed_knots": "10", "heading_deg": "247", "ship_type": "tanker"},
            {"mmsi": "2", "imo": "2", "vessel_name": "Far Carrier", "timestamp": "2024-06-18T00:20:00Z", "latitude": "20.0", "longitude": "74.0", "speed_knots": "12", "heading_deg": "90", "ship_type": "container"},
        ])
        result = rank_vessels(path, 18.72, 72.10, datetime(2024, 6, 17, 22, 10, tzinfo=timezone.utc), datetime(2024, 6, 18, 1, 40, tzinfo=timezone.utc))
        self.assertEqual(result[0]["vessel_name"], "Near Tanker")

    def test_inside_time_window_has_zero_offset(self):
        path = self.write_csv([{ "mmsi": "1", "imo": "1", "vessel_name": "Timed Vessel", "timestamp": "2024-06-18T00:20:00Z", "latitude": "18.72", "longitude": "72.10", "speed_knots": "10", "heading_deg": "247", "ship_type": "tanker" }])
        result = rank_vessels(path, 18.72, 72.10, datetime(2024, 6, 17, 22, 10, tzinfo=timezone.utc), datetime(2024, 6, 18, 1, 40, tzinfo=timezone.utc))
        self.assertEqual(result[0]["time_offset_hours"], 0)
        self.assertTrue(result[0]["evidence"]["inside_time_window"])

    def test_non_tanker_gets_lower_prior(self):
        path = self.write_csv([{ "mmsi": "1", "imo": "1", "vessel_name": "Container Vessel", "timestamp": "2024-06-18T00:20:00Z", "latitude": "18.72", "longitude": "72.10", "speed_knots": "10", "heading_deg": "247", "ship_type": "container" }])
        result = rank_vessels(path, 18.72, 72.10, datetime(2024, 6, 17, 22, 10, tzinfo=timezone.utc), datetime(2024, 6, 18, 1, 40, tzinfo=timezone.utc))
        self.assertEqual(result[0]["prior"], 0.03)

    def test_behavioral_anomaly_uses_reporting_gap_and_motion_change(self):
        points = [
            {"timestamp": datetime(2024, 6, 18, 0, 0, tzinfo=timezone.utc), "heading_deg": 90, "speed_knots": 10},
            {"timestamp": datetime(2024, 6, 18, 2, 0, tzinfo=timezone.utc), "heading_deg": 180, "speed_knots": 14},
        ]
        self.assertEqual(behavioral_anomaly_score(points), 90)

    def test_invalid_coordinates_are_skipped(self):
        path = self.write_csv([{
            "mmsi": "bad", "imo": "1", "vessel_name": "Invalid", "timestamp": "2024-06-18T00:20:00Z",
            "latitude": "95", "longitude": "72.10", "speed_knots": "10", "heading_deg": "247", "ship_type": "tanker"
        }])
        result = rank_vessels(path, 18.72, 72.10, datetime(2024, 6, 17, 22, 10, tzinfo=timezone.utc), datetime(2024, 6, 18, 1, 40, tzinfo=timezone.utc))
        self.assertEqual(result, [])

    def test_likelihood_ratio_uses_runtime_configuration(self):
        config = RankingConfig()
        config.proximity_close = 100
        config.likelihood_proximity_close = 11
        ratios = likelihood_ratio(20, 0, "TANKER", 10, config)
        self.assertEqual(ratios["proximity"], 11)
        self.assertEqual(ratios["vessel_type"], config.likelihood_vessel_type_tanker)


if __name__ == "__main__":
    unittest.main()
