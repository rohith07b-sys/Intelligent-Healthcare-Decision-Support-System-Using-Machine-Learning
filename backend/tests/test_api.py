import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from ml.feature_schemas import FEATURE_SCHEMAS
import routes.api as api_routes


class FakePipeline:
    def __init__(self):
        self.received = None

    def predict(self, values):
        self.received = values.copy()
        return [1]

    def predict_proba(self, values):
        return [[0.2, 0.8]]


@pytest.fixture
def app(tmp_path, monkeypatch):
    database_path = tmp_path / "test.sqlite"
    application = create_app({
        "TESTING": True,
        "DATABASE_PATH": database_path,
        "MODEL_DIR": tmp_path / "missing-models",
        "FRONTEND_ORIGIN": "http://localhost:5173",
    })
    monkeypatch.setattr(api_routes, "explain_prediction", lambda *args: None)
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def valid_diabetes_values():
    return {
        "Pregnancies": 2,
        "Glucose": 110,
        "BloodPressure": 70,
        "SkinThickness": 20,
        "Insulin": 80,
        "BMI": 25.4,
        "DiabetesPedigreeFunction": 0.5,
        "Age": 42,
    }


def valid_heart_values():
    return {
        "age": 54,
        "sex": 1,
        "cp": 2,
        "trestbps": 130,
        "chol": 240,
        "fbs": 0,
        "restecg": 0,
        "thalach": 150,
        "exang": 0,
        "oldpeak": 1.0,
        "slope": 2,
        "ca": 0,
        "thal": 3,
    }


def install_fake_model(app, assessment_type="diabetes"):
    pipeline = FakePipeline()
    app.extensions["loaded_models"] = {
        "diabetes": None,
        "heart-disease": None,
    }
    app.extensions["loaded_models"][assessment_type] = {
        "pipeline": pipeline,
        "version": "test-model-v1",
        "metadata": {
            "model_version": "test-model-v1",
            "features": [field["name"] for field in FEATURE_SCHEMAS[assessment_type]["features"]],
            "explanation_baseline": {},
            "training_status": "trained_and_evaluated",
            "selected_model": "test",
            "evaluation": {},
        },
    }
    return pipeline


def test_health_reports_missing_model_artifacts(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    result = response.get_json()
    assert result["status"] == "ok"
    assert result["models"]["diabetes"]["available"] is False
    assert result["models"]["heart-disease"]["available"] is False


def test_schema_returns_ordered_model_features(client):
    result = client.get("/api/models/schema").get_json()["models"]
    assert [feature["name"] for feature in result["diabetes"]["features"]] == [
        "Pregnancies", "Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI",
        "DiabetesPedigreeFunction", "Age",
    ]


def test_performance_is_not_evaluated_without_model(client):
    models = client.get("/api/models/performance").get_json()["models"]
    assert models["diabetes"]["status"] == "not_evaluated_yet"
    assert models["diabetes"]["metadata"] is None


def test_prediction_without_model_returns_unavailable_and_does_not_save(app, client):
    response = client.post("/api/assessments/diabetes", json={
        "patient_ref": "case-01",
        "input_values": valid_diabetes_values(),
    })
    assert response.status_code == 503
    assert "unavailable" in response.get_json()["error"]
    assert client.get("/api/assessments").get_json()["total"] == 0


def test_invalid_inputs_are_rejected(app, client):
    install_fake_model(app)
    values = valid_diabetes_values()
    values["Age"] = "not-a-number"
    response = client.post("/api/assessments/diabetes", json={
        "patient_ref": "case-02",
        "input_values": values,
    })
    assert response.status_code == 400
    assert "Age" in response.get_json()["field_errors"]
    assert client.get("/api/assessments").get_json()["total"] == 0


def test_feature_order_prediction_and_sqlite_retrieval(app, client):
    pipeline = install_fake_model(app)
    reversed_values = dict(reversed(list(valid_diabetes_values().items())))
    response = client.post("/api/assessments/diabetes", json={
        "patient_ref": "case-03",
        "input_values": reversed_values,
    })
    assert response.status_code == 201
    created = response.get_json()["assessment"]
    assert list(pipeline.received.columns) == [
        feature["name"] for feature in FEATURE_SCHEMAS["diabetes"]["features"]
    ]
    assert created["output_category"] == "positive"
    assert created["probability"] == pytest.approx(0.8)
    assert created["explanation"] is None

    listing = client.get("/api/assessments").get_json()
    assert listing["total"] == 1
    assert listing["items"][0]["patient_ref"] == "case-03"
    assert listing["items"][0]["input_values"]["Glucose"] == 110

    detail = client.get(f"/api/assessments/{created['id']}").get_json()["assessment"]
    assert detail["model_version"] == "test-model-v1"
    assert detail["guidance"]
    assert client.get("/api/dashboard/stats").get_json()["total_assessments"] == 1


def test_heart_disease_prediction_uses_its_own_feature_order(app, client):
    pipeline = install_fake_model(app, "heart-disease")
    values = dict(reversed(list(valid_heart_values().items())))
    response = client.post("/api/assessments/heart-disease", json={
        "patient_ref": "case-heart",
        "input_values": values,
    })
    assert response.status_code == 201
    assert list(pipeline.received.columns) == [
        feature["name"] for feature in FEATURE_SCHEMAS["heart-disease"]["features"]
    ]
    assert response.get_json()["assessment"]["assessment_type"] == "heart-disease"


def test_assessment_not_found_is_404(client):
    assert client.get("/api/assessments/999").status_code == 404


def test_patient_reference_and_unknown_features_are_rejected(app, client):
    install_fake_model(app)
    values = valid_diabetes_values()
    values["unknown"] = 1
    response = client.post("/api/assessments/diabetes", json={
        "patient_ref": "patient name",
        "input_values": values,
    })
    assert response.status_code == 400
    assert "patient_ref" in response.get_json()["error"]


def test_history_filters_and_pagination(app, client):
    install_fake_model(app)
    for reference in ("search-a", "other-b"):
        response = client.post("/api/assessments/diabetes", json={
            "patient_ref": reference,
            "input_values": valid_diabetes_values(),
        })
        assert response.status_code == 201
    result = client.get("/api/assessments?search=search-&page=1&per_page=1").get_json()
    assert result["total"] == 1
    assert result["pages"] == 1
    assert result["items"][0]["patient_ref"] == "search-a"
