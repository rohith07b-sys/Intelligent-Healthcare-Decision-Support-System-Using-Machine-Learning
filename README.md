# Intelligent Healthcare Decision Support System Using Machine Learning

An academic demonstration application with a React dashboard, Flask REST API, SQLite assessment history, and separate diabetes and heart-disease training pipelines. This project is an **educational decision-support tool, not a medical diagnostic system**. It does not prescribe medicines and must not replace professional medical evaluation.

The repository contains no datasets, patient records, pre-trained model artifacts, generated predictions, or example performance figures. A model remains unavailable until its dataset is supplied and the corresponding training command completes successfully.

## What is implemented

- Responsive React/Vite dashboard with overview, assessment, report, history, and model-performance pages.
- Flask JSON API with schema-based validation, model availability reporting, pagination/filtering, informative errors, and CORS restricted to the configured frontend origin.
- SQLite initialization and parameterized persistence of pseudonymous references, submitted features, model output/version, explanation (when available), and timestamp.
- Separate Logistic Regression and Random Forest training/evaluation for each dataset; selection uses mean stratified training-fold F1 and reports held-out test metrics.
- Shared saved preprocessing pipeline, model metadata, inference feature-order checks, and optional SHAP KernelExplainer contributions relative to training-set feature medians.
- Cautious non-prescriptive follow-up text based only on the model's dataset-positive/negative output.
- Automated backend checks for health, unavailable models, validation, feature order, persistence, retrieval, filtering, and pagination.

## Limitations and safeguards

- Predictions are only available after local model training. The app does not simulate a successful prediction if artifacts are missing.
- The Pima dataset is a limited historical cohort and the processed Cleveland dataset is small. Neither establishes general-population nor clinical performance. The output classes reflect each dataset's target coding.
- `predict_proba` is displayed as **model probability**, not clinically calibrated risk. It must not be interpreted as a diagnosis.
- SHAP is optional at runtime. If it cannot compute an explanation, the report explicitly shows an unavailable state. Contributions explain model behavior relative to a feature-wise median reference; they do not imply medical causation.
- No clinical thresholds or risk bands are used. Training metrics are actual results from the local data, and remain “Not evaluated yet” until training succeeds.
- Follow-up wording is generic, non-prescriptive text triggered by the model's dataset-positive/negative label; it does not apply a clinical rule or imply a treatment recommendation. No external clinical guideline or threshold is encoded.
- Form ranges are input sanity checks, not clinical thresholds. UCI categorical codes and feature meanings are shown in the assessment form.
- The zero values in Pima `Glucose`, `BloodPressure`, `SkinThickness`, `Insulin`, and `BMI` are treated as missing by the training script, then imputed with a median learned within the training pipeline. The UI requires positive values for these inputs so an assessment value cannot be silently treated differently from a missing training value. Other missing feature values are median-imputed by the saved pipeline.
- This local demonstration is **not automatically compliant with HIPAA, GDPR, or other healthcare privacy regulations**. Use only pseudonymous demonstration data; do not enter direct identifiers or real patient records.
- SQLite is suitable for a local academic prototype, not concurrent production healthcare workloads.

## Project layout

```text
backend/
  app.py
  config.py
  database.py
  routes/api.py
  ml/feature_schemas.py
  ml/train_common.py
  ml/train_diabetes.py
  ml/train_heart_disease.py
  ml/explain.py
  services/model_registry.py
  data/README.md
  tests/test_api.py
frontend/
  src/components/
  src/layouts/
  src/pages/
  src/services/api.js
```

## Prerequisites

- Windows 10/11 with PowerShell
- Python 3.10 or later (64-bit recommended)
- Node.js 20 LTS and npm
- Dataset files obtained from a source whose terms permit your intended academic use

## Dataset preparation and training

Review [backend/data/README.md](backend/data/README.md) before acquiring data. Training scripts do not download data. Obtain the datasets from a trusted source, inspect their documentation and licensing, and put the files in the exact headerless CSV formats described there.

From the project root, in PowerShell:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m ml.train_diabetes
python -m ml.train_heart_disease
```

If PowerShell prevents environment activation, either adjust the execution policy for your user according to your organization's guidance or invoke the environment's executable directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m ml.train_diabetes
.\.venv\Scripts\python.exe -m ml.train_heart_disease
```

You can select alternate dataset/output paths:

```powershell
python -m ml.train_diabetes --data .\data\diabetes.csv --output .\artifacts\models
python -m ml.train_heart_disease --data .\data\heart_disease.csv --output .\artifacts\models
```

Each successful run writes a scikit-learn pipeline (`*_pipeline.joblib`) and JSON metadata (`*_metadata.json`) beneath `backend/artifacts/models/`. Artifacts are ignored by git. Training exits with an explicit error if file schema, labels, or class counts do not satisfy the script. It does not claim success or report metrics before those checks pass.

## Configure and run

Open two PowerShell terminals from the project root. Backend and frontend commands are intentionally separate.

### Backend terminal

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

If you already created the virtual environment and installed requirements during training, skip those steps. The Flask service listens at `http://127.0.0.1:5000`. It initializes the local SQLite database at `backend/instance/healthcare.db` and loads model artifacts if present. Set optional configuration by defining environment variables in the terminal before `python app.py`; see `backend/.env.example`. The example `.env` is informational; Flask does not automatically load it.

### Frontend terminal

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Open the Vite URL printed in the terminal (normally `http://127.0.0.1:5173`). `VITE_API_BASE_URL` in `frontend/.env` can point at a different backend API URL. Restart Vite after changing environment variables.

## API examples

Health and model availability:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/health
```

Diabetes request (all required feature names and values are validated):

```powershell
$diabetes = @{
  patient_ref = "demo-001"
  input_values = @{
    Pregnancies = 2
    Glucose = 110
    BloodPressure = 70
    SkinThickness = 20
    Insulin = 80
    BMI = 25.4
    DiabetesPedigreeFunction = 0.5
    Age = 42
  }
} | ConvertTo-Json -Depth 4
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/assessments/diabetes -ContentType "application/json" -Body $diabetes
```

Heart disease request. Codes are those of the processed Cleveland dataset; see the form/schema and dataset documentation:

```powershell
$heart = @{
  patient_ref = "demo-002"
  input_values = @{
    age = 54; sex = 1; cp = 2; trestbps = 130; chol = 240
    fbs = 0; restecg = 0; thalach = 150; exang = 0; oldpeak = 1.0
    slope = 2; ca = 0; thal = 3
  }
} | ConvertTo-Json -Depth 4
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/assessments/heart-disease -ContentType "application/json" -Body $heart
```

Both POST requests return HTTP 503 with an explanatory error if the corresponding model has not been trained. Additional endpoints:

- `GET /api/dashboard/stats`
- `GET /api/models/schema`
- `GET /api/assessments?page=1&per_page=10&type=diabetes&category=positive&search=demo`
- `GET /api/assessments/<id>`
- `GET /api/models/performance`

## Testing

From a backend terminal with its virtual environment active:

```powershell
cd backend
python -m pytest -q
```

Build the frontend separately:

```powershell
cd frontend
npm run build
```

The backend tests use temporary SQLite databases and mock model inference; they do not assert fabricated model performance. To verify actual model outputs, supply the documented datasets, run the training commands, start the API, and submit the sample requests.

## Troubleshooting

- **Model unavailable:** Check `GET /api/health`. Confirm the relevant `*_pipeline.joblib` and `*_metadata.json` exist in the configured model directory and rerun that training command if needed.
- **Dataset schema error:** The training scripts expect headerless rows in the exact column order documented in `backend/data/README.md`. Unknown heart-disease feature values may be `?`; target labels must be valid.
- **Cannot reach API / CORS error:** Start Flask at the API URL in `frontend/.env`; ensure `FRONTEND_ORIGIN` matches the Vite origin and restart Flask after changing it.
- **SHAP explanation unavailable:** Prediction remains available if model inference succeeds, but no explanation is shown. Check backend logs and SHAP/scikit-learn compatibility; the application does not invent an explanation.
- **SQLite or artifact path:** `DATABASE_PATH` and `MODEL_DIR` can be set as environment variables. Relative paths resolve from the backend process working directory.
- **Dependency installation failure:** Confirm supported Python/Node versions and retry in a fresh virtual environment. Do not mix package installs across Python environments.
