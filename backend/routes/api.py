import json
import logging
import re
import sqlite3

from flask import Blueprint, current_app, jsonify, request
import pandas as pd

from database import database_connection, serialize_assessment
from ml.explain import explain_prediction
from ml.feature_schemas import FEATURE_SCHEMAS, validate_inputs
from services.model_registry import load_model


api = Blueprint("api", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)
MODEL_TYPES = ("diabetes", "heart-disease")


def _models():
    if "loaded_models" not in current_app.extensions:
        current_app.extensions["loaded_models"] = {}
        current_app.extensions["model_load_errors"] = {}
        for assessment_type in MODEL_TYPES:
            try:
                current_app.extensions["loaded_models"][assessment_type] = load_model(
                    current_app.config["MODEL_DIR"], assessment_type
                )
            except Exception:
                logger.exception("Could not load %s model", assessment_type)
                current_app.extensions["loaded_models"][assessment_type] = None
                current_app.extensions["model_load_errors"][assessment_type] = True
    return current_app.extensions["loaded_models"]


def _guidance(predicted_class):
    if predicted_class == 1:
        return [
            "This model returned its dataset-positive class. Consider discussing this result and the recorded measurements with a qualified healthcare professional.",
            "A qualified professional can determine whether confirmatory evaluation is appropriate.",
        ]
    return [
        "This model returned its dataset-negative class. This result does not rule out a health condition or replace professional evaluation.",
        "Discuss health concerns or changing symptoms with a qualified healthcare professional.",
    ]


@api.get("/health")
def health():
    models = _models()
    return jsonify({
        "status": "ok",
        "models": {
            assessment_type: {
                "available": models[assessment_type] is not None,
                "version": models[assessment_type]["version"] if models[assessment_type] else None,
                "error": "Model artifacts could not be loaded; check backend logs."
                if current_app.extensions.get("model_load_errors", {}).get(assessment_type) else None,
            }
            for assessment_type in MODEL_TYPES
        },
    })


@api.get("/models/schema")
def model_schema():
    return jsonify({"models": FEATURE_SCHEMAS})


@api.get("/dashboard/stats")
def dashboard_stats():
    with database_connection(current_app.config["DATABASE_PATH"]) as connection:
        total = connection.execute("SELECT COUNT(*) FROM assessments").fetchone()[0]
        grouped = connection.execute(
            """
            SELECT assessment_type, output_category, COUNT(*) AS count
            FROM assessments
            GROUP BY assessment_type, output_category
            """
        ).fetchall()
        recent = connection.execute(
            "SELECT * FROM assessments ORDER BY created_at DESC, id DESC LIMIT 5"
        ).fetchall()
    counts = {assessment_type: {"positive": 0, "negative": 0} for assessment_type in MODEL_TYPES}
    for row in grouped:
        counts[row["assessment_type"]][row["output_category"]] = row["count"]
    models = _models()
    return jsonify({
        "total_assessments": total,
        "counts": counts,
        "recent_assessments": [serialize_assessment(row) for row in recent],
        "models": {
            name: {
                "available": models[name] is not None,
                "version": models[name]["version"] if models[name] else None,
                "training_status": models[name]["metadata"].get("training_status", "not_trained")
                if models[name] else "not_trained",
            }
            for name in MODEL_TYPES
        },
    })


def _create_assessment(assessment_type):
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400
    patient_ref = body.get("patient_ref")
    if not isinstance(patient_ref, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", patient_ref.strip()):
        return jsonify({"error": "patient_ref must be a pseudonymous reference of 1–64 letters, numbers, dots, underscores, or hyphens."}), 400
    values, errors = validate_inputs(assessment_type, body.get("input_values"))
    if errors:
        return jsonify({"error": "Input validation failed.", "field_errors": errors}), 400
    model = _models()[assessment_type]
    if model is None:
        if current_app.extensions.get("model_load_errors", {}).get(assessment_type):
            return jsonify({"error": f"The {assessment_type} model artifacts could not be loaded. Check backend logs; no assessment was performed."}), 503
        return jsonify({"error": f"The {assessment_type} model is unavailable. Provide the documented dataset and train the model before assessing."}), 503

    feature_names = [feature["name"] for feature in FEATURE_SCHEMAS[assessment_type]["features"]]
    try:
        prediction_input = pd.DataFrame(
            [[values[name] for name in feature_names]],
            columns=feature_names,
        )
        predicted_class = int(model["pipeline"].predict(prediction_input)[0])
        probability = float(model["pipeline"].predict_proba(prediction_input)[0][1])
    except Exception:
        logger.exception("Model inference failed for %s", assessment_type)
        return jsonify({"error": "The model could not process this assessment. No result was saved."}), 500
    explanation_features = explain_prediction(
        model["pipeline"], values, feature_names, model["metadata"].get("explanation_baseline", {})
    ) if model["metadata"].get("explanation_baseline") else None
    explanation = {
        "method": "SHAP KernelExplainer",
        "reference": model["metadata"].get("explanation_baseline_method"),
        "features": explanation_features,
    } if explanation_features is not None else None
    category = "positive" if predicted_class == 1 else "negative"
    guidance = _guidance(predicted_class)
    try:
        with database_connection(current_app.config["DATABASE_PATH"]) as connection:
            cursor = connection.execute(
                """
                INSERT INTO assessments (
                    patient_ref, assessment_type, input_values, predicted_class,
                    output_category, probability, model_version, explanation, guidance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    patient_ref.strip(),
                    assessment_type,
                    json.dumps(values, allow_nan=False),
                    predicted_class,
                    category,
                    probability,
                    model["version"],
                    json.dumps(explanation, allow_nan=False) if explanation is not None else None,
                    json.dumps(guidance, allow_nan=False),
                ),
            )
            row = connection.execute("SELECT * FROM assessments WHERE id = ?", (cursor.lastrowid,)).fetchone()
    except sqlite3.Error:
        logger.exception("Could not persist assessment")
        return jsonify({"error": "The assessment was computed but could not be saved."}), 500
    return jsonify({"assessment": serialize_assessment(row)}), 201


@api.post("/assessments/diabetes")
def assess_diabetes():
    return _create_assessment("diabetes")


@api.post("/assessments/heart-disease")
def assess_heart_disease():
    return _create_assessment("heart-disease")


@api.get("/assessments")
def list_assessments():
    try:
        page = max(1, int(request.args.get("page", "1")))
        per_page = min(100, max(1, int(request.args.get("per_page", "10"))))
    except ValueError:
        return jsonify({"error": "page and per_page must be integers."}), 400
    assessment_type = request.args.get("type")
    category = request.args.get("category")
    search = request.args.get("search", "").strip()
    if assessment_type and assessment_type not in MODEL_TYPES:
        return jsonify({"error": "Unknown assessment type."}), 400
    if category and category not in ("positive", "negative"):
        return jsonify({"error": "category must be positive or negative."}), 400

    clauses, parameters = [], []
    if assessment_type:
        clauses.append("assessment_type = ?")
        parameters.append(assessment_type)
    if category:
        clauses.append("output_category = ?")
        parameters.append(category)
    if search:
        clauses.append("instr(lower(patient_ref), lower(?)) > 0")
        parameters.append(search)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with database_connection(current_app.config["DATABASE_PATH"]) as connection:
        total = connection.execute("SELECT COUNT(*) FROM assessments" + where, parameters).fetchone()[0]
        rows = connection.execute(
            "SELECT * FROM assessments" + where +
            " ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
            parameters + [per_page, (page - 1) * per_page],
        ).fetchall()
    return jsonify({
        "items": [serialize_assessment(row) for row in rows],
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": (total + per_page - 1) // per_page,
    })


@api.get("/assessments/<int:assessment_id>")
def get_assessment(assessment_id):
    with database_connection(current_app.config["DATABASE_PATH"]) as connection:
        row = connection.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,)).fetchone()
    if row is None:
        return jsonify({"error": "Assessment not found."}), 404
    return jsonify({"assessment": serialize_assessment(row)})


@api.get("/models/performance")
def model_performance():
    models = _models()
    result = {}
    for assessment_type in MODEL_TYPES:
        model = models[assessment_type]
        result[assessment_type] = (
            {
                "available": True,
                "metadata": model["metadata"],
            }
            if model else {
                "available": False,
                "status": "unavailable" if current_app.extensions.get("model_load_errors", {}).get(assessment_type) else "not_evaluated_yet",
                "error": "Model artifacts could not be loaded; check backend logs."
                if current_app.extensions.get("model_load_errors", {}).get(assessment_type) else None,
                "metadata": None,
            }
        )
    return jsonify({"models": result})
