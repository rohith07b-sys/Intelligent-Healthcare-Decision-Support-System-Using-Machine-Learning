import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.feature_schemas import FEATURE_SCHEMAS


def evaluate(y_true, predictions, probabilities):
    return {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, probabilities)) if len(np.unique(y_true)) == 2 else None,
        "sample_count": int(len(y_true)),
    }


def train_model(assessment_type, data_path, feature_names, target_name, output_dir, positive_mapping, zero_missing=()):
    data = pd.read_csv(data_path, header=None, na_values=["?", "NA", ""])
    expected_columns = len(feature_names) + 1
    if data.shape[1] != expected_columns:
        raise ValueError(f"Expected {expected_columns} columns, found {data.shape[1]}. Check the documented CSV format.")
    data.columns = feature_names + [target_name]
    for name in feature_names + [target_name]:
        data[name] = pd.to_numeric(data[name], errors="coerce")
    data = data.dropna(subset=[target_name]).copy()
    for name in zero_missing:
        data.loc[data[name] == 0, name] = np.nan
    empty_features = [name for name in feature_names if not data[name].notna().any()]
    if empty_features:
        raise ValueError(f"Dataset has no observed values for feature(s): {', '.join(empty_features)}.")
    for specification in FEATURE_SCHEMAS[assessment_type]["features"]:
        name = specification["name"]
        observed = data[name].dropna()
        out_of_range = (observed < specification["minimum"]) | (observed > specification["maximum"])
        if out_of_range.any():
            raise ValueError(f"Feature {name} has values outside the documented input range.")
        if "options" in specification:
            allowed = {option["value"] for option in specification["options"]}
            if not observed.isin(allowed).all():
                raise ValueError(f"Feature {name} contains values outside its documented dataset codes.")
        elif specification["step"] == 1 and not np.equal(observed, np.floor(observed)).all():
            raise ValueError(f"Feature {name} must contain whole-number values.")
    target = data[target_name].map(positive_mapping)
    if target.isna().any():
        values = sorted(data.loc[target.isna(), target_name].unique().tolist())
        raise ValueError(f"Unexpected target labels: {values}")
    features = data[feature_names]
    if len(features) < 20 or target.nunique() != 2 or target.value_counts().min() < 2:
        raise ValueError("Dataset must have at least 20 usable rows and at least two examples of each class.")

    X_train, X_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, random_state=42, stratify=target
    )
    candidates = {
        "logistic_regression": LogisticRegression(max_iter=2000, class_weight=None, random_state=42),
        "random_forest": RandomForestClassifier(n_estimators=300, min_samples_leaf=2, random_state=42, n_jobs=-1),
    }
    results = {}
    fitted = {}
    folds = min(5, int(y_train.value_counts().min()))
    for name, estimator in candidates.items():
        pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("scaler", StandardScaler()),
            ("classifier", estimator),
        ])
        cv_scores = cross_val_score(pipeline, X_train, y_train, scoring="f1", cv=folds)
        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_test)
        probabilities = pipeline.predict_proba(X_test)[:, 1]
        results[name] = {
            "selection_metric": "mean stratified training-fold F1",
            "cross_validation_f1_mean": float(cv_scores.mean()),
            "cross_validation_f1_std": float(cv_scores.std()),
            "test_metrics": evaluate(y_test, predictions, probabilities),
        }
        fitted[name] = pipeline
    selected_name = max(results, key=lambda name: results[name]["cross_validation_f1_mean"])
    now = datetime.now(timezone.utc)
    if assessment_type == "diabetes":
        dataset_source = {
            "citation": "Pima Indians Diabetes Dataset; historically used in Smith et al., Using the ADAP learning algorithm to forecast the onset of diabetes mellitus (1988).",
            "license": "Not asserted here; the user must verify terms for the specific dataset source before use.",
        }
    else:
        dataset_source = {
            "citation": "Janosi, A., Steinbrunn, W., Pfisterer, M., & Detrano, R. (1989). Heart Disease. UCI Machine Learning Repository.",
            "documentation_url": "https://archive.ics.uci.edu/dataset/45/heart+disease",
            "license": "CC BY 4.0, as stated by the UCI Machine Learning Repository.",
        }
    metadata = {
        "assessment_type": assessment_type,
        "model_version": f"{assessment_type}-v1-{now.strftime('%Y%m%dT%H%M%SZ')}",
        "training_status": "trained_and_evaluated",
        "selected_model": selected_name,
        "features": feature_names,
        "target": target_name,
        "target_mapping": {str(label): int(mapped) for label, mapped in positive_mapping.items()},
        "positive_class_definition": (
            f"{target_name} values mapped to class 1: "
            f"{[label for label, mapped in positive_mapping.items() if mapped == 1]}"
        ),
        "dataset": str(data_path.name),
        "dataset_source": dataset_source,
        "dataset_rows_used": int(len(data)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "split": {"strategy": "stratified train/test split", "test_size": 0.2, "random_state": 42},
        "selection_criteria": "Highest mean stratified cross-validation F1 on training data; test split is reserved for final evaluation.",
        "missing_values": {
            "method": "Median imputation fitted within each training-fold pipeline.",
            "zero_as_missing_features": list(zero_missing),
        },
        "explanation_baseline": {
            name: float(X_train[name].median()) for name in feature_names
        },
        "explanation_baseline_method": "Feature-wise median from the training split; contributions explain model behavior relative to this reference, not medical causation.",
        "evaluation": results,
        "trained_at": now.isoformat(),
        "limitations": [
            "Dataset performance is not evidence of clinical performance or clinical calibration.",
            "The dataset population, collection process, and target coding limit generalizability.",
        ],
    }
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_stem = assessment_type.replace("-", "_")
    joblib.dump(fitted[selected_name], output_dir / f"{artifact_stem}_pipeline.joblib")
    metadata_path = output_dir / f"{artifact_stem}_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, allow_nan=False), encoding="utf-8")
    return metadata
