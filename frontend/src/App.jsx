import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./layouts/AppLayout";
import Loading from "./components/Loading";

const Assessment = lazy(() => import("./pages/Assessment"));
const AssessmentDetail = lazy(() => import("./pages/AssessmentDetail"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const History = lazy(() => import("./pages/History"));
const Performance = lazy(() => import("./pages/Performance"));

export default function App() {
  return <Suspense fallback={<Loading label="Loading page…" />}><Routes><Route element={<AppLayout />}><Route index element={<Dashboard />} /><Route path="assess" element={<Assessment />} /><Route path="history" element={<History />} /><Route path="assessments/:id" element={<AssessmentDetail />} /><Route path="performance" element={<Performance />} /><Route path="*" element={<Navigate to="/" replace />} /></Route></Routes></Suspense>;
}
