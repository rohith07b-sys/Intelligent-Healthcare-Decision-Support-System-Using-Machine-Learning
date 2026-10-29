import { AlertCircle, CheckCircle2 } from "lucide-react";

export default function Notice({ children, tone = "error" }) {
  const Icon = tone === "success" ? CheckCircle2 : AlertCircle;
  return <div className={`notice notice-${tone}`} role={tone === "error" ? "alert" : "status"}><Icon size={18} /> <span>{children}</span></div>;
}
