"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import EventRow from "@/components/observability/EventRow";
import { endpoints } from "@/lib/endpoints";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, Wifi, WifiOff } from "lucide-react";

type ObsEvent = {
  event_type: string;
  severity?: string;
  ts?: string;
  session_id?: string;
  payload?: Record<string, unknown>;
  source_app?: string;
};

export default function ObservabilityPage() {
  const [events, setEvents] = useState<ObsEvent[]>([]);
  const [status, setStatus] = useState<"connecting" | "online" | "offline">("connecting");
  const wsRef = useRef<WebSocket | null>(null);

  const obsWs = endpoints.ws.observability;
  const obsHttp = endpoints.api.observabilityEvents;

  // WebSocket live stream
  useEffect(() => {
    if (!obsWs) {
      setStatus("offline");
      return;
    }
    const ws = new WebSocket(obsWs);
    wsRef.current = ws;
    ws.onopen = () => setStatus("online");
    ws.onclose = () => setStatus("offline");
    ws.onerror = () => setStatus("offline");
    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data as string);
        setEvents((prev) => [data as ObsEvent, ...prev].slice(0, 200));
      } catch (e) {
        console.warn("Bad event", e);
      }
    };
    return () => ws.close();
  }, [obsWs]);

  // Initial load via HTTP if available
  useEffect(() => {
    const fetchInitial = async () => {
      if (!obsHttp) return;
      try {
        const res = await fetch(obsHttp, { cache: "no-store" });
        if (!res.ok) return;
        const data = await res.json();
        if (Array.isArray(data)) {
          setEvents(data.reverse());
        }
      } catch (e) {
        console.warn("Failed to fetch obs events", e);
      }
    };
    fetchInitial();
  }, [obsHttp]);

  const liveBadge = useMemo(() => {
    if (status === "online") return <Badge className="bg-emerald-500/20 text-emerald-100 border-emerald-500/40"><Wifi className="h-3 w-3 mr-1" />Live</Badge>;
    if (status === "connecting") return <Badge className="bg-amber-500/20 text-amber-100 border-amber-500/40"><Loader2 className="h-3 w-3 mr-1 animate-spin" />Connecting</Badge>;
    return <Badge className="bg-rose-500/20 text-rose-100 border-rose-500/40"><WifiOff className="h-3 w-3 mr-1" />Offline</Badge>;
  }, [status]);

  return (
    <div className="min-h-screen w-full bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-white">
      <div className="container mx-auto px-6 py-10 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Observability</h1>
            <p className="text-sm text-white/70">Real-time events from hooks, whisper, TTS, and sandbox.</p>
          </div>
          <div className="flex items-center gap-3">
            {liveBadge}
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                // manual refresh via HTTP
                if (!obsHttp) return;
                fetch(obsHttp, { cache: "no-store" })
                  .then((res) => res.json())
                  .then((data) => Array.isArray(data) && setEvents(data.reverse()))
                  .catch(() => {});
              }}
            >Refresh</Button>
          </div>
        </div>

        {!obsWs && (
          <div className="rounded-xl border border-amber-500/40 bg-amber-500/10 p-4 text-amber-100 text-sm">
            Set <code className="font-mono">NEXT_PUBLIC_OBS_WS</code> (and optional <code className="font-mono">NEXT_PUBLIC_OBS_HTTP</code>) to enable live observability.
          </div>
        )}

        <div className="grid gap-3">
          {events.length === 0 ? (
            <div className="text-white/60 text-sm">No events yet.</div>
          ) : (
            events.map((ev, idx) => <EventRow key={`${ev.ts}-${idx}`} event={ev} />)
          )}
        </div>
      </div>
    </div>
  );
}

