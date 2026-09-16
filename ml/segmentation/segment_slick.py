"""GeoTIFF-ready oil-slick segmentation baseline for the MVP.

Requires rasterio and numpy. It uses a conservative dark-water threshold as a
baseline until labelled Sentinel-1 slick masks are available for training.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def segment_tiff(input_path: Path, output_path: Path, threshold: float) -> dict:
    try:
        import numpy as np
        import rasterio
        from rasterio.features import shapes
    except ImportError as error:
        raise SystemExit("Install rasterio and numpy to process GeoTIFF files") from error

    with rasterio.open(input_path) as source:
        band = source.read(1, masked=True).astype("float32")
        valid = band.compressed()
        if valid.size == 0:
            raise ValueError("GeoTIFF contains no valid pixels")
        unique_values = np.unique(valid)
        if set(unique_values.tolist()).issubset({0, 1}) and len(unique_values) <= 2:
            cutoff = 1.0
            mask = (band == 1).filled(False).astype("uint8")
            method = "binary-positive-class"
        else:
            cutoff = float(np.percentile(valid, threshold))
            mask = (band <= cutoff).filled(False).astype("uint8")
            method = "lower-backscatter-percentile"
        profile = source.profile.copy()
        profile.update(count=1, dtype="uint8", nodata=0, compress="lzw")
        with rasterio.open(output_path, "w", **profile) as target:
            target.write(mask, 1)
        areas = [shape for shape, value in shapes(mask, mask=mask, transform=source.transform) if value == 1]
        return {"input": str(input_path), "mask": str(output_path), "method": method, "threshold_percentile": threshold, "pixel_cutoff": cutoff, "positive_pixels": int(mask.sum()), "regions": len(areas), "crs": str(source.crs), "bounds": list(source.bounds)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a baseline probable-slick mask from a GeoTIFF")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--threshold", type=float, default=15.0, help="Lower-backscatter percentile treated as probable slick")
    args = parser.parse_args()
    print(json.dumps(segment_tiff(args.input, args.output, args.threshold), indent=2))


if __name__ == "__main__":
    main()
