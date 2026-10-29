FEATURE_SCHEMAS = {
    "diabetes": {
        "title": "Diabetes assessment",
        "dataset": "Pima Indians Diabetes Dataset",
        "features": [
            {"name": "Pregnancies", "label": "Pregnancies", "unit": "count", "minimum": 0, "maximum": 20, "step": 1},
            {"name": "Glucose", "label": "Plasma glucose", "unit": "mg/dL", "minimum": 1, "maximum": 500, "step": 1},
            {"name": "BloodPressure", "label": "Diastolic blood pressure", "unit": "mm Hg", "minimum": 1, "maximum": 300, "step": 1},
            {"name": "SkinThickness", "label": "Triceps skin-fold thickness", "unit": "mm", "minimum": 1, "maximum": 150, "step": 1},
            {"name": "Insulin", "label": "2-hour serum insulin", "unit": "mu U/mL", "minimum": 1, "maximum": 3000, "step": 1},
            {"name": "BMI", "label": "Body mass index", "unit": "kg/m2", "minimum": 0.1, "maximum": 150, "step": 0.1},
            {"name": "DiabetesPedigreeFunction", "label": "Diabetes pedigree function", "unit": "dataset score", "minimum": 0, "maximum": 10, "step": 0.001},
            {"name": "Age", "label": "Age", "unit": "years", "minimum": 18, "maximum": 120, "step": 1},
        ],
    },
    "heart-disease": {
        "title": "Heart disease assessment",
        "dataset": "UCI Heart Disease (processed Cleveland subset)",
        "features": [
            {"name": "age", "label": "Age", "unit": "years", "minimum": 18, "maximum": 120, "step": 1},
            {"name": "sex", "label": "Sex code", "unit": "0 = female, 1 = male (dataset coding)", "minimum": 0, "maximum": 1, "step": 1, "options": [{"value": 0, "label": "0 — female"}, {"value": 1, "label": "1 — male"}]},
            {"name": "cp", "label": "Chest pain type", "unit": "dataset code", "minimum": 1, "maximum": 4, "step": 1, "options": [{"value": 1, "label": "1 — typical angina"}, {"value": 2, "label": "2 — atypical angina"}, {"value": 3, "label": "3 — non-anginal pain"}, {"value": 4, "label": "4 — asymptomatic"}]},
            {"name": "trestbps", "label": "Resting blood pressure", "unit": "mm Hg", "minimum": 50, "maximum": 300, "step": 1},
            {"name": "chol", "label": "Serum cholesterol", "unit": "mg/dL", "minimum": 50, "maximum": 1000, "step": 1},
            {"name": "fbs", "label": "Fasting blood sugar > 120 mg/dL", "unit": "dataset code", "minimum": 0, "maximum": 1, "step": 1, "options": [{"value": 0, "label": "0 — no"}, {"value": 1, "label": "1 — yes"}]},
            {"name": "restecg", "label": "Resting ECG", "unit": "dataset code", "minimum": 0, "maximum": 2, "step": 1, "options": [{"value": 0, "label": "0 — normal"}, {"value": 1, "label": "1 — ST-T abnormality"}, {"value": 2, "label": "2 — probable/definite left ventricular hypertrophy"}]},
            {"name": "thalach", "label": "Maximum heart rate achieved", "unit": "beats/min", "minimum": 40, "maximum": 300, "step": 1},
            {"name": "exang", "label": "Exercise-induced angina", "unit": "dataset code", "minimum": 0, "maximum": 1, "step": 1, "options": [{"value": 0, "label": "0 — no"}, {"value": 1, "label": "1 — yes"}]},
            {"name": "oldpeak", "label": "ST depression induced by exercise", "unit": "dataset score", "minimum": 0, "maximum": 20, "step": 0.1},
            {"name": "slope", "label": "Slope of peak exercise ST segment", "unit": "dataset code", "minimum": 1, "maximum": 3, "step": 1, "options": [{"value": 1, "label": "1 — upsloping"}, {"value": 2, "label": "2 — flat"}, {"value": 3, "label": "3 — downsloping"}]},
            {"name": "ca", "label": "Major vessels colored by fluoroscopy", "unit": "count", "minimum": 0, "maximum": 3, "step": 1},
            {"name": "thal", "label": "Thalassemia", "unit": "dataset code", "minimum": 3, "maximum": 7, "step": 1, "options": [{"value": 3, "label": "3 — normal"}, {"value": 6, "label": "6 — fixed defect"}, {"value": 7, "label": "7 — reversible defect"}]},
        ],
    },
}


def validate_inputs(assessment_type, payload):
    schema = FEATURE_SCHEMAS[assessment_type]
    errors = {}
    validated = {}
    expected_names = [feature["name"] for feature in schema["features"]]
    if not isinstance(payload, dict):
        return None, {"input_values": "Expected an object containing all model features."}

    extra = set(payload) - set(expected_names)
    missing = set(expected_names) - set(payload)
    if extra:
        errors["input_values"] = "Unexpected feature(s): " + ", ".join(sorted(extra))
    if missing:
        errors["input_values"] = "Missing feature(s): " + ", ".join(sorted(missing))
    if errors:
        return None, errors

    for feature in schema["features"]:
        name = feature["name"]
        value = payload[name]
        if isinstance(value, bool):
            errors[name] = "Enter a numeric value."
            continue
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            errors[name] = "Enter a numeric value."
            continue
        if not (numeric_value == numeric_value and abs(numeric_value) != float("inf")):
            errors[name] = "Enter a finite numeric value."
            continue
        if numeric_value < feature["minimum"] or numeric_value > feature["maximum"]:
            errors[name] = f"Enter a value from {feature['minimum']} to {feature['maximum']} {feature['unit']}."
            continue
        if "options" in feature and numeric_value not in [option["value"] for option in feature["options"]]:
            errors[name] = "Select one of the defined dataset codes."
            continue
        if feature["step"] == 1 and not numeric_value.is_integer():
            errors[name] = "Enter a whole number."
            continue
        validated[name] = int(numeric_value) if numeric_value.is_integer() else numeric_value
    if errors:
        return None, errors
    return {name: validated[name] for name in expected_names}, None
