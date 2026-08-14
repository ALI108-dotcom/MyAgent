import React from "react";

interface StatusCardProps {
  title: string;
  value: string;
  status: "success" | "warning" | "error" | "info";
  subtitle?: string;
}

export function StatusCard({ title, value, status, subtitle }: StatusCardProps) {
  const getBadgeStyle = () => {
    switch (status) {
      case "success":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
      case "warning":
        return "bg-amber-500/10 text-amber-400 border-amber-500/30";
      case "error":
        return "bg-rose-500/10 text-rose-400 border-rose-500/30";
      case "info":
      default:
        return "bg-cyan-500/10 text-cyan-400 border-cyan-500/30";
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur-sm">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider">{title}</h3>
        <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${getBadgeStyle()}`}>
          {value}
        </span>
      </div>
      {subtitle && <p className="text-xs text-slate-500 mt-2 font-mono">{subtitle}</p>}
    </div>
  );
}
