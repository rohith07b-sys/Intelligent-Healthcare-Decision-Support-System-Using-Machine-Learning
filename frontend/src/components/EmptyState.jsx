import { ClipboardList } from "lucide-react";

export default function EmptyState({ title, children }) {
  return <div className="empty-state"><span className="empty-icon"><ClipboardList size={22} /></span><h3>{title}</h3><p>{children}</p></div>;
}
