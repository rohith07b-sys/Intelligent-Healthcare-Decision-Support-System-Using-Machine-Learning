import { ArrowUpRight } from "lucide-react";
import { Link } from "react-router-dom";

const typeLabels = { diabetes: "Diabetes", "heart-disease": "Heart disease" };

export default function AssessmentTable({ items }) {
  if (!items.length) return null;
  return (
    <div className="table-scroll">
      <table>
        <thead><tr><th>Reference</th><th>Assessment</th><th>Model output</th><th>Assessed</th><th /></tr></thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td className="reference-cell">{item.patient_ref}</td>
              <td>{typeLabels[item.assessment_type] || item.assessment_type}</td>
              <td><span className={`badge ${item.output_category}`}>{item.output_category === "positive" ? "Dataset-positive" : "Dataset-negative"}</span></td>
              <td>{new Date(item.created_at).toLocaleString()}</td>
              <td><Link className="icon-link" aria-label={`Open assessment ${item.id}`} to={`/assessments/${item.id}`}><ArrowUpRight size={17} /></Link></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
