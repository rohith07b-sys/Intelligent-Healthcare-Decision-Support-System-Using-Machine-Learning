import { ArrowLeft, ArrowRight, Info } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Loading from "../components/Loading";
import Notice from "../components/Notice";
import { api } from "../services/api";

const types = [
  { id: "diabetes", title: "Diabetes", description: "Pima dataset features" },
  { id: "heart-disease", title: "Heart disease", description: "Processed Cleveland dataset features" },
];

export default function Assessment() {
  const [schemas, setSchemas] = useState(null);
  const [health, setHealth] = useState(null);
  const [type, setType] = useState("diabetes");
  const [patientRef, setPatientRef] = useState("");
  const [values, setValues] = useState({});
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([api.schema(), api.health()]).then(([schemaResult, healthResult]) => {
      setSchemas(schemaResult.models);
      setHealth(healthResult.models);
    }).catch((e) => setError(e.message));
  }, []);

  function changeType(nextType) {
    setType(nextType);
    setValues({});
    setFieldErrors({});
    setError("");
  }

  async function submit(event) {
    event.preventDefault();
    setError("");
    setFieldErrors({});
    setSubmitting(true);
    try {
      const response = await api.createAssessment(type, { patient_ref: patientRef, input_values: values });
      navigate(`/assessments/${response.assessment.id}`);
    } catch (e) {
      setError(e.message);
      setFieldErrors(e.fieldErrors || {});
    } finally {
      setSubmitting(false);
    }
  }

  if (!schemas || !health) return <><Heading /><Loading label="Loading assessment form…" />{error && <Notice>{error}</Notice>}</>;
  const modelAvailable = health[type]?.available;
  const features = schemas[type].features;

  return (
    <>
      <Heading />
      <div className="assessment-layout">
        <form className="panel assessment-form" onSubmit={submit}>
          <div className="form-section-title"><span>01</span><div><h2>Choose assessment</h2><p>Each model uses a separate dataset schema.</p></div></div>
          <div className="type-picker" role="group" aria-label="Assessment type">
            {types.map((item) => <button key={item.id} type="button" className={`type-option ${type === item.id ? "selected" : ""}`} onClick={() => changeType(item.id)}><strong>{item.title}</strong><small>{item.description}</small></button>)}
          </div>
          {!modelAvailable && <Notice>Model unavailable. This form is shown for reference, but no assessment can be performed until its dataset is supplied and the training command succeeds.</Notice>}
          <div className="form-section-title section-spaced"><span>02</span><div><h2>Assessment details</h2><p>Use a pseudonymous reference; do not enter a patient's name or contact details.</p></div></div>
          <label className="field-label" htmlFor="patient-ref">Patient reference <span>Required</span></label>
          <input id="patient-ref" className="text-input" value={patientRef} onChange={(e) => setPatientRef(e.target.value)} required maxLength={64} pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,63}" placeholder="e.g. demo-001" autoComplete="off" />
          {fieldErrors.patient_ref && <small className="field-error">{fieldErrors.patient_ref}</small>}
          <div className="feature-grid">
            {features.map((feature) => <div className="field-wrap" key={feature.name}>
              <label className="field-label" htmlFor={`field-${feature.name}`}>{feature.label}</label>
              {feature.options ? (
                <select id={`field-${feature.name}`} className="text-input" value={values[feature.name] ?? ""} required onChange={(e) => setValues((current) => ({ ...current, [feature.name]: e.target.value }))}>
                  <option value="" disabled>Select a dataset code</option>
                  {feature.options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                </select>
              ) : (
                <input id={`field-${feature.name}`} className="text-input" type="number" min={feature.minimum} max={feature.maximum} step={feature.step} required value={values[feature.name] ?? ""} onChange={(e) => setValues((current) => ({ ...current, [feature.name]: e.target.value }))} />
              )}
              <small className="field-hint">Range: {feature.minimum}–{feature.maximum} {feature.unit}</small>
              {fieldErrors[feature.name] && <small className="field-error">{fieldErrors[feature.name]}</small>}
            </div>)}
          </div>
          {fieldErrors.input_values && <Notice>{fieldErrors.input_values}</Notice>}
          {error && <Notice>{error}</Notice>}
          <div className="form-actions"><Link className="button button-secondary" to="/"><ArrowLeft size={16} /> Cancel</Link><button className="button button-primary" type="submit" disabled={submitting || !modelAvailable}>{submitting ? "Running assessment…" : "Run assessment"} <ArrowRight size={16} /></button></div>
        </form>
        <aside className="assessment-aside">
          <div className="panel aside-panel"><span className="aside-icon"><Info size={19} /></span><h3>About this assessment</h3><p>Inputs are checked against the selected dataset schema and passed to a locally trained model using its saved preprocessing pipeline.</p><ul><li>No values are guessed or filled in.</li><li>The model class is not a diagnosis.</li><li>A probability is not clinically calibrated risk.</li></ul></div>
          <div className="safety-card"><strong>Before you continue</strong><p>Use only de-identified sample values. This local academic prototype is not automatically compliant with healthcare privacy regulations.</p></div>
        </aside>
      </div>
    </>
  );
}

function Heading() {
  return <div className="page-heading"><div><div className="eyebrow">NEW RECORD</div><h1>Health assessment</h1><p>Enter measurements for one model at a time.</p></div></div>;
}
