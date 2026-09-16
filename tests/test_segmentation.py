import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from ml.segmentation.segment_slick import segment_tiff


class SegmentationTests(unittest.TestCase):
    def write_raster(self, directory: str, values: np.ndarray) -> tuple[Path, Path]:
        input_path = Path(directory) / "input.tif"
        output_path = Path(directory) / "mask.tif"
        with rasterio.open(
            input_path,
            "w",
            driver="GTiff",
            width=values.shape[1],
            height=values.shape[0],
            count=1,
            dtype=str(values.dtype),
            transform=from_origin(72.0, 19.0, 0.01, 0.01),
            crs="EPSG:4326",
        ) as dataset:
            dataset.write(values, 1)
        return input_path, output_path

    def test_binary_mask_uses_positive_class(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path, output_path = self.write_raster(directory, np.array([[0, 1], [1, 0]], dtype="uint8"))
            result = segment_tiff(input_path, output_path, 15)
            self.assertEqual(result["method"], "binary-positive-class")
            self.assertEqual(result["positive_pixels"], 2)

    def test_binary_mask_counts_connected_regions(self):
        with tempfile.TemporaryDirectory() as directory:
            values = np.array([[1, 0, 1], [0, 0, 0], [1, 0, 0]], dtype="uint8")
            input_path, output_path = self.write_raster(directory, values)
            result = segment_tiff(input_path, output_path, 15)
            self.assertEqual(result["regions"], 3)

    def test_continuous_raster_uses_backscatter_threshold(self):
        with tempfile.TemporaryDirectory() as directory:
            values = np.arange(16, dtype="float32").reshape(4, 4)
            input_path, output_path = self.write_raster(directory, values)
            result = segment_tiff(input_path, output_path, 25)
            self.assertEqual(result["method"], "lower-backscatter-percentile")
            self.assertEqual(result["positive_pixels"], 4)


if __name__ == "__main__":
    unittest.main()
