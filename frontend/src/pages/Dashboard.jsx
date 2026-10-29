import { Activity, ArrowRight, ClipboardCheck, HeartPulse, Plus, Stethoscope } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import AssessmentTable from "../components/AssessmentTable";
import EmptyState from "../components/EmptyState";
import Loading from "../components/Loading";
import Notice from "../components/Notice";
import { api } from "../services/api";

const displayNames = { diabetes: "Diabetes", "heart-disease": "Heart disease" };

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { api.dashboard().then(setData).catch((e) => setError(e.message)); }, []);

  if (error) return <><PageHeading /><Notice>{error}</Notice></>;
  if (!data) return <><PageHeading /><Loading label="Loading dashboard data…" /></>;
  const chartData = Object.keys(displayNames).map((type) => ({
    name: displayNames[type],
    "Dataset-positive": data.counts[type].positive,
    "Dataset-negative": data.counts[type].negative,
  }));
  const modelList = Object.entries(data.models);

  return (
    <>
      <PageHeading />
      <div className="stat-grid">
        <StatCard icon={ClipboardCheck} label="Completed assessments" value={data.total_assessments} detail="Saved in this local database" />
        <StatCard icon={Activity} label="Diabetes outputs" value={data.counts.diabetes.positive + data.counts.diabetes.negative} detail={`${data.counts.diabetes.positive} dataset-positive · ${data.counts.diabetes.negative} dataset-negative`} />
        <StatCard icon={HeartPulse} label="Heart disease outputs" value={data.counts["heart-disease"].positive + data.counts["heart-disease"].negative} detail={`${data.counts["heart-disease"].positive} dataset-positive · ${data.counts["heart-disease"].negative} dataset-negative`} />
      </div>
      <div className="dashboard-grid">
        <section className="panel chart-panel">
          <div className="panel-heading"><div><h2>Assessment distribution</h2><p>Saved model outputs, grouped by dataset class</p></div></div>
          {data.total_assessments === 0 ? <EmptyState title="No assessment data yet">Once a model has been trained and an assessment is saved, its output will appear here.</EmptyState> : (
            <div className="chart-wrap"><ResponsiveContainer width="100%" height="100%"><BarChart data={chartData} barGap={9} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}><CartesianGrid stroke="#e9eef2" vertical={false} /><XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: "#718096", fontSize: 12 }} /><YAxis allowDecimals={false} axisLine={false} tickLine={false} tick={{ fill: "#718096", fontSize: 12 }} /><Tooltip /><Bar dataKey="Dataset-positive" fill="#287d83" radius={[5, 5, 0, 0]} /><Bar dataKey="Dataset-negative" fill="#a9cbd0" radius={[5, 5, 0, 0]} /></BarChart></ResponsiveContainer></div>
          )}
        </section>
        <section className="panel model-panel">
          <div className="panel-heading"><div><h2>Model availability</h2><p>Local artifacts and training status</p></div></div>
          <div className="model-list">{modelList.map(([key, model]) => <div className="model-row" key={key}><span className="model-icon">{key === "diabetes" ? <Activity size={18} /> : <HeartPulse size={18} />}</span><div className="model-info"><strong>{displayNames[key]}</strong><small>{model.version || model.training_status.replaceAll("_", " ")}</small></div><span className={`status-pill ${model.available ? "available" : "unavailable"}`}><i />{model.available ? "Ready" : "Unavailable"}</span></div>)}</div>
          <div className="model-footnote">Models are loaded from locally trained artifacts. An unavailable model cannot produce an assessment.</div>
        </section>
      </div>
      <section className="panel recent-panel">
        <div className="panel-heading"><div><h2>Recent assessments</h2><p>The latest records saved in this installation</p></div><Link className="text-link" to="/history">View history <ArrowRight size={15} /></Link></div>
        {data.recent_assessments.length ? <AssessmentTable items={data.recent_assessments} /> : <EmptyState title="Your assessment history is empty">No patient records are created for this demo. Train a model to begin saving real assessment outputs.</EmptyState>}
      </section>
      <section className="callout"><div className="callout-icon"><Stethoscope size={20} /></div><div><strong>Use model outputs with care</strong><p>Predicted classes and probabilities reflect model behavior on particular datasets, not an individual's clinical diagnosis or calibrated clinical risk.</p></div><Link to="/assess">Start assessment <ArrowRight size={15} /></Link></section>
    </>
  );
}

function PageHeading() {
  return <div className="page-heading"><div><div className="eyebrow">OVERVIEW</div><h1>Decision support dashboard</h1><p>Monitor assessments and locally trained model availability.</p></div><Link className="button button-primary" to="/assess"><Plus size={17} /> New assessment</Link></div>;
}

function StatCard({ icon: Icon, label, value, detail }) {
  return <div className="stat-card"><span className="stat-icon"><Icon size={19} /></span><span className="stat-label">{label}</span><strong>{value}</strong><small>{detail}</small></div>;
}
