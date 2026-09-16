# Machine Learning

`segmentation/` owns SAR/EO probable-oil-slick models.

`ranking/` owns calibrated candidate-vessel ranking and behavioral anomaly features.

Model outputs should include confidence and provenance so the UI never presents an attribution score as legal proof.

## Run the AIS MVP model

From the repository root:

```powershell
python ml/ranking/rank_vessels.py --ais data/raw/ais_synthetic.csv --output data/processed_rankings.json
```

The output contains ranked candidates, distances, time offsets, priors, likelihood ratios, and evidence flags. The current input is synthetic. On the current scenario, the model ranks `MT Konkan Pride` highest because it is closer to the configured offshore origin; this is a model result, not a factual accusation.

For a correlated end-to-end demo, use `data/raw/synthetic_spills.json` with `data/raw/ais_synthetic_correlated.csv`. The synthetic ground-truth vessel is `MT Samudra Shakti`; the ranker returns it first with a 96.9 posterior relevance because its generated track crosses the generated origin during the generated time window. This validates the pipeline mechanics only, not the model's real-world accuracy.

## Run the GeoTIFF baseline

Install the optional dependencies first:

```powershell
pip install -r ml/requirements.txt
python ml/segmentation/segment_slick.py data/raw/oil_spill.tif data/processed_slick_mask.tif
```

The segmentation script is a lower-backscatter baseline, not a trained deep-learning model. It also detects 0/1 binary masks like `data/raw/01339.tif` and preserves the positive class. The uploaded TIFF has no CRS or geotransform, so its pixels can be analyzed but cannot be placed at real latitude/longitude until scene georeferencing metadata is supplied.
