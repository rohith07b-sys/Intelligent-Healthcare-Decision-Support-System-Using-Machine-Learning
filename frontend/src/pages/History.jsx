import { Search } from "lucide-react";
import { useEffect, useState } from "react";
import AssessmentTable from "../components/AssessmentTable";
import EmptyState from "../components/EmptyState";
import Loading from "../components/Loading";
import Notice from "../components/Notice";
import { api } from "../services/api";

export default function History() {
  const [search, setSearch] = useState("");
  const [type, setType] = useState("");
  const [category, setCategory] = useState("");
  const [page, setPage] = useState(1);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    setResult(null);
    api.assessments({ search, type, category, page: String(page), per_page: "10" })
      .then(setResult).catch((e) => setError(e.message));
  }, [search, type, category, page]);

  return <>
    <div className="page-heading"><div><div className="eyebrow">RECORDS</div><h1>Assessment history</h1><p>Search saved assessments and open a complete report.</p></div></div>
    <section className="panel history-panel">
      <div className="filter-bar">
        <label className="search-field"><Search size={17} /><input value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} placeholder="Search reference…" aria-label="Search patient reference" /></label>
        <select className="filter-select" aria-label="Filter by assessment" value={type} onChange={(e) => { setType(e.target.value); setPage(1); }}><option value="">All assessments</option><option value="diabetes">Diabetes</option><option value="heart-disease">Heart disease</option></select>
        <select className="filter-select" aria-label="Filter by model output" value={category} onChange={(e) => { setCategory(e.target.value); setPage(1); }}><option value="">All outputs</option><option value="positive">Dataset-positive</option><option value="negative">Dataset-negative</option></select>
      </div>
      {error ? <Notice>{error}</Notice> : !result ? <Loading label="Loading assessment history…" /> : result.items.length ? <>
        <AssessmentTable items={result.items} />
        <div className="pagination"><span>{result.total} {result.total === 1 ? "assessment" : "assessments"} · Page {result.page} of {Math.max(result.pages, 1)}</span><div><button className="button button-secondary button-small" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>Previous</button><button className="button button-secondary button-small" disabled={page >= result.pages} onClick={() => setPage((value) => value + 1)}>Next</button></div></div>
      </> : <EmptyState title="No matching assessments">Saved assessments will appear here. No demo records are generated.</EmptyState>}
    </section>
  </>;
}
