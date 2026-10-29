import json
from pathlib import Path

import joblib

from ml.feature_schemas import FEATURE_SCHEMAS


def load_model(model_dir, assessment_type):
    directory = Path(model_dir)
    pipeline_path = directory / f"{assessment_type.replace('-', '_')}_pipeline.joblib"
    metadata_path = directory / f"{assessment_type.replace('-', '_')}_metadata.json"
    if not pipeline_path.is_file() or not metadata_path.is_file():
        return None
    with metadata_path.open("r", encoding="utf-8") as file:
        metadata = json.load(file)
    pipeline = joblib.load(pipeline_path)
    expected = [feature["name"] for feature in FEATURE_SCHEMAS[assessment_type]["features"]]
    if metadata.get("features") != expected:
        raise ValueError(f"Model metadata feature order does not match the {assessment_type} schema.")
    if not hasattr(pipeline, "predict") or not hasattr(pipeline, "predict_proba"):
        raise ValueError(f"The {assessment_type} model must expose predict and predict_proba.")
    return {"pipeline": pipeline, "metadata": metadata, "version": metadata["model_version"]}
