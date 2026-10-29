import { Activity, Info } from "lucide-react";
import { useEffect, useState } from "react";
import EmptyState from "../components/EmptyState";
import Loading from "../components/Loading";
import Notice from "../components/Notice";
import { api } from "../services/api";

const names = { diabetes: "Diabetes", "heart-disease": "Heart disease" };
const metricLabels = [["accuracy", "Accuracy"], ["precision", "Precision"], ["recall", "Recall"], ["f1", "F1-score"], ["roc_auc", "ROC-AUC"]];

export default function Performance() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { api.performance().then(setData).catch((e) => setError(e.message)); }, []);
  return <>
    <div className="page-heading"><div><div className="eyebrow">VALIDATION</div><h1>Model performance</h1><p>Evaluation metrics recorded during local model training.</p></div></div>
    <div className="performance-note"><Info size={18} /><p>Test-set performance on a particular dataset does not establish clinical performance, calibration, or suitability for individual care.</p></div>
    {error ? <Notice>{error}</Notice> : !data ? <Loading label="Loading model evaluation…" /> : <div className="performance-grid">
      {Object.entries(data.models).map(([key, item]) => <section className="panel performance-card" key={key}>
        <div className="panel-heading"><div><span className="performance-icon"><Activity size={18} /></span><h2>{names[key]}</h2></div><span className={`status-pill ${item.available ? "available" : "unavailable"}`}><i />{item.available ? "Evaluated" : "Not evaluated yet"}</span></div>
        {!item.available || !item.metadata?.evaluation ? <EmptyState title="Not evaluated yet">Supply the documented dataset and run its training script to create actual evaluation metrics.</EmptyState> : <>
          <p className="model-selection">Selected {item.metadata.selected_model.replaceAll("_", " ")} · version {item.metadata.model_version}</p>
          <div className="table-scroll"><table className="metrics-table"><thead><tr><th>Candidate</th><th>CV F1</th>{metricLabels.map(([, label]) => <th key={label}>{label}</th>)}</tr></thead><tbody>{Object.entries(item.metadata.evaluation).map(([candidate, evaluation]) => <tr key={candidate}><td>{candidate.replaceAll("_", " ")}{candidate === item.metadata.selected_model ? <span className="selected-tag">Selected</span> : null}</td><td>{(evaluation.cross_validation_f1_mean * 100).toFixed(1)}%</td>{metricLabels.map(([metric]) => <td key={metric}>{evaluation.test_metrics[metric] == null ? "—" : `${(evaluation.test_metrics[metric] * 100).toFixed(1)}%`}</td>)}</tr>)}</tbody></table></div>
          <p className="model-selection metrics-caption">CV F1 is the training-fold mean used for selection. Other metrics are computed on the held-out test split; em dash means not available.</p>
          <div className="metadata-list"><div><span>Dataset</span><strong>{item.metadata.dataset}</strong></div><div><span>Training rows</span><strong>{item.metadata.train_rows}</strong></div><div><span>Test rows</span><strong>{item.metadata.test_rows}</strong></div><div><span>Training timestamp</span><strong>{new Date(item.metadata.trained_at).toLocaleString()}</strong></div></div>
          <p className="model-selection">{item.metadata.selection_criteria}</p>
        </>}
      </section>)}
    </div>}
  </>;
}
