import { ArrowLeft, CalendarDays, Info } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import Loading from "../components/Loading";
import Notice from "../components/Notice";
import { api } from "../services/api";

const titles = { diabetes: "Diabetes", "heart-disease": "Heart disease" };

export default function AssessmentDetail() {
  const { id } = useParams();
  const [assessment, setAssessment] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { api.assessment(id).then((result) => setAssessment(result.assessment)).catch((e) => setError(e.message)); }, [id]);

  return <>
    <div className="page-heading"><div><div className="eyebrow">ASSESSMENT REPORT</div><h1>Assessment details</h1><p>Saved model output and submitted values.</p></div><Link className="button button-secondary" to="/history"><ArrowLeft size={16} /> Back to history</Link></div>
    {error ? <Notice>{error}</Notice> : !assessment ? <Loading label="Loading assessment report…" /> : <>
      <section className="result-hero panel">
        <div><span className={`result-mark ${assessment.output_category}`}>{assessment.output_category === "positive" ? "P" : "N"}</span></div>
        <div className="result-copy"><div className="eyebrow">{titles[assessment.assessment_type]} · {assessment.patient_ref}</div><h2>{assessment.output_category === "positive" ? "Dataset-positive class" : "Dataset-negative class"}</h2><p>This is the model's predicted dataset class, not a medical diagnosis.</p></div>
        <div className="probability"><span>Model probability</span><strong>{assessment.probability == null ? "Unavailable" : `${(assessment.probability * 100).toFixed(1)}%`}</strong><small>Not clinically calibrated risk</small></div>
      </section>
      <div className="detail-meta"><span><CalendarDays size={16} />{new Date(assessment.created_at).toLocaleString()}</span><span>Model version: <strong>{assessment.model_version}</strong></span><span>Assessment ID: <strong>#{assessment.id}</strong></span></div>
      <div className="detail-grid">
        <section className="panel detail-panel"><div className="panel-heading"><div><h2>Recorded inputs</h2><p>Values submitted for this assessment</p></div></div><dl className="value-list">{Object.entries(assessment.input_values).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl></section>
        <section className="panel detail-panel"><div className="panel-heading"><div><h2>Feature contributions</h2><p>SHAP explanation of model behavior</p></div></div>
          {assessment.explanation ? <><div className="explanation-note"><Info size={16} /> {assessment.explanation.method} contributions relative to a feature-wise training reference. They describe statistical model behavior, not medical causation. {assessment.explanation.reference}</div><div className="contribution-list">{assessment.explanation.features.map((item) => <div className="contribution-row" key={item.feature}><div><strong>{item.feature}</strong><small>{item.direction} the positive-class model output</small></div><span className={item.contribution >= 0 ? "contribution-positive" : "contribution-negative"}>{item.contribution > 0 ? "+" : ""}{item.contribution}</span></div>)}</div></> : <div className="unavailable-box"><Info size={18} /><span>A feature explanation is unavailable for this assessment. No contribution values have been fabricated.</span></div>}
        </section>
      </div>
      <section className="panel guidance-panel"><div className="panel-heading"><div><h2>General follow-up</h2><p>Separate from the model prediction</p></div></div><ul>{assessment.guidance.map((item) => <li key={item}>{item}</li>)}</ul><div className="disclaimer-inline">Educational decision support only. Not a diagnosis, prescription, or substitute for professional evaluation.</div></section>
    </>}
  </>;
}
