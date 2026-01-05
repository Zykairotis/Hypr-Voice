import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";

type Props = {
  event: {
    event_type: string;
    severity?: string;
    ts?: string;
    session_id?: string;
    payload?: Record<string, unknown>;
    source_app?: string;
  };
};

const severityColor: Record<string, string> = {
  info: "bg-blue-500/20 text-blue-100 border-blue-500/40",
  warn: "bg-amber-500/20 text-amber-100 border-amber-500/40",
  error: "bg-red-500/20 text-red-100 border-red-500/40",
  debug: "bg-slate-500/20 text-slate-100 border-slate-500/40",
};

export function EventRow({ event }: Props) {
  const ts = event.ts ? new Date(event.ts) : undefined;
  const sev = event.severity || "info";
  return (
    <div className="flex items-start justify-between rounded-xl border border-white/5 bg-white/5 px-4 py-3 hover:border-white/10 transition">
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2 text-sm text-white/80">
          <Badge variant="outline" className={cn("border-white/10", severityColor[sev] || "")}>{sev}</Badge>
          <span className="font-semibold text-white">{event.event_type}</span>
          {event.source_app && <span className="text-xs text-white/60">{event.source_app}</span>}
          {event.session_id && <span className="text-xs text-white/60">session {event.session_id}</span>}
        </div>
        {event.payload && (
          <pre className="max-h-24 overflow-y-auto text-xs text-white/70 whitespace-pre-wrap leading-relaxed">
            {JSON.stringify(event.payload, null, 2)}
          </pre>
        )}
      </div>
      <div className="text-xs text-white/60 whitespace-nowrap ml-4">
        {ts ? formatDistanceToNow(ts, { addSuffix: true }) : "just now"}
      </div>
    </div>
  );
}

export default EventRow;

