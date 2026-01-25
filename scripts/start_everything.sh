#!/bin/bash
# Start hybrid server, context websocket, and web UI/bridge together.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WHISPER_SCRIPTS_DIR="$ROOT_DIR/scripts"
UI_DIR="$ROOT_DIR/web-ui"
PID_CONTEXT="/tmp/hypr-voice-context-ws.pid"
PID_UI_WRAPPER="/tmp/hypr-voice-ui-wrapper.pid"
PID_ORCHESTRATOR="/tmp/hypr-voice-orchestrator.pid"

log() { printf "[start-all] %s\n" "$*"; }

# Load environment variables once for all services
MODE="LOCAL"
if [ -f "$ROOT_DIR/.env" ]; then
  set -a
  source "$ROOT_DIR/.env"
  set +a
  MODE="${MODE:-LOCAL}"
  log "Loaded .env file (MODE=$MODE)"
fi
MODE="${MODE:-LOCAL}"
MODE_UPPER="${MODE^^}"
export MODE

# Optional: Wispr Flow API server (9095)
start_flow() {
  log "Starting Wispr Flow API server (9095)..."
  (cd "$ROOT_DIR" && ./scripts/start_wispr_flow.sh start)
}

# 1) Hybrid Whisper server (9099)
start_hybrid() {
  log "Starting hybrid server (9099)..."
  (cd "$ROOT_DIR" && "$WHISPER_SCRIPTS_DIR/start_hybrid_server.sh" start)
}

# 2) Context WebSocket (9091)
start_context_ws() {
  if [ -f "$PID_CONTEXT" ] && kill -0 "$(cat "$PID_CONTEXT")" 2>/dev/null; then
    log "Context WS already running (pid $(cat "$PID_CONTEXT"))."
    return
  fi

  # Ensure venv exists
  if [ ! -d "$ROOT_DIR/.venv" ]; then
    log "Creating .venv at $ROOT_DIR/.venv"
    python -m venv "$ROOT_DIR/.venv"
  fi
  source "$ROOT_DIR/.venv/bin/activate"

  log "Starting context_websocket_server.py (9091)..."
  # Run from project root for module imports - file moved to src/hypr_voice/whisper/context/
  # Run directly as script to avoid parent package import issues
  cd "$ROOT_DIR"
  export PYTHONPATH="$ROOT_DIR/src:$PYTHONPATH"
  nohup python "$ROOT_DIR/src/hypr_voice/whisper/context/context_websocket_server.py" > /tmp/hypr-voice-context-ws.log 2>&1 &
  echo $! > "$PID_CONTEXT"
  log "Context WS pid $(cat "$PID_CONTEXT"), logs: /tmp/hypr-voice-context-ws.log"
}

# 3) Agent Orchestrator (9093)
start_orchestrator() {
  if [ -f "$PID_ORCHESTRATOR" ] && kill -0 "$(cat "$PID_ORCHESTRATOR")" 2>/dev/null; then
    log "Orchestrator already running (pid $(cat "$PID_ORCHESTRATOR"))."
    return
  fi

  # Ensure venv exists
  if [ ! -d "$ROOT_DIR/.venv" ]; then
    log "Creating .venv at $ROOT_DIR/.venv"
    python -m venv "$ROOT_DIR/.venv"
  fi
  source "$ROOT_DIR/.venv/bin/activate"

  log "Starting Agent Orchestrator (9093)..."
  cd "$ROOT_DIR"
  
  # Load environment variables from .env
  if [ -f "$ROOT_DIR/.env" ]; then
    set -a
    source "$ROOT_DIR/.env"
    set +a
    log "Loaded .env file"
  fi
  
  # Set orchestrator port
  export ORCHESTRATOR_PORT=9093
  export PYTHONPATH="$ROOT_DIR/src"
  
  # Use the main venv python which has anthropic installed
  nohup /home/mewtwo/.venv/bin/python -c "
import uvicorn
import sys
sys.path.insert(0, '$ROOT_DIR/src')
from hypr_voice.server import app
uvicorn.run(app, host='0.0.0.0', port=9093, log_level='info')
" > /tmp/hypr-voice-orchestrator.log 2>&1 &
  echo $! > "$PID_ORCHESTRATOR"
  log "Orchestrator pid $(cat "$PID_ORCHESTRATOR"), logs: /tmp/hypr-voice-orchestrator.log"
}

# 4) Web UI + bridge (8933/8934)
start_ui_bridge() {
  if [ -f "$PID_UI_WRAPPER" ] && kill -0 "$(cat "$PID_UI_WRAPPER")" 2>/dev/null; then
    log "UI wrapper already running (pid $(cat "$PID_UI_WRAPPER"))."
    return
  fi

  log "Starting web UI + bridge (8933/8934)..."
  cd "$UI_DIR"
  # Ensure env to point to upstream context ws
  CONTEXT_WS_UPSTREAM=${CONTEXT_WS_UPSTREAM:-ws://localhost:9091}
  export CONTEXT_WS_UPSTREAM
  export NEXT_PUBLIC_CONTEXT_WS=${NEXT_PUBLIC_CONTEXT_WS:-ws://localhost:9091/ws}

  nohup bash ./start-ui.sh > /tmp/hypr-voice-ui.log 2>&1 &
  echo $! > "$PID_UI_WRAPPER"
  log "UI wrapper pid $(cat "$PID_UI_WRAPPER"), logs: /tmp/hypr-voice-ui.log"
}

case "${1:-start}" in
  start)
    if [ "$MODE_UPPER" = "FLOW" ]; then
      start_flow
    fi
    start_hybrid
    start_context_ws
    start_orchestrator
    start_ui_bridge
    log "All services started."
    log "Hybrid:      http://localhost:9099  (WS ws://localhost:9099/ws/{session_id})"
    if [ "$MODE_UPPER" = "FLOW" ]; then
      log "Wispr Flow:  http://localhost:${WISPR_FLOW_PORT:-9095}  (API /transcribe)"
    fi
    log "Context:     ws://localhost:9091/ws"
    log "Orchestrator: http://localhost:9093  (Agent SDK orchestrator)"
    log "Bridge:      http://localhost:8934  (WS proxy /ws/context, /ws/orchestrator)"
    log "Frontend:    http://localhost:8933"
    ;;
  stop)
    log "Stopping services..."
    # stop UI wrapper
    if [ -f "$PID_UI_WRAPPER" ]; then
      kill "$(cat "$PID_UI_WRAPPER")" 2>/dev/null || true
      rm -f "$PID_UI_WRAPPER"
      log "Stopped UI wrapper"
    fi
    # stop orchestrator
    if [ -f "$PID_ORCHESTRATOR" ]; then
      kill "$(cat "$PID_ORCHESTRATOR")" 2>/dev/null || true
      rm -f "$PID_ORCHESTRATOR"
      log "Stopped orchestrator"
    fi
    # stop context ws
    if [ -f "$PID_CONTEXT" ]; then
      kill "$(cat "$PID_CONTEXT")" 2>/dev/null || true
      rm -f "$PID_CONTEXT"
      log "Stopped context WS"
    fi
    # stop hybrid server
    (cd "$ROOT_DIR" && "$WHISPER_SCRIPTS_DIR/start_hybrid_server.sh" stop) || true
    if [ "$MODE_UPPER" = "FLOW" ]; then
      (cd "$ROOT_DIR" && ./scripts/start_wispr_flow.sh stop) || true
    fi
    ;;
  status)
    log "Hybrid server status:"; (cd "$ROOT_DIR" && "$WHISPER_SCRIPTS_DIR/start_hybrid_server.sh" status || true)
    if [ "$MODE_UPPER" = "FLOW" ]; then
      log "Wispr Flow server status:"; (cd "$ROOT_DIR" && ./scripts/start_wispr_flow.sh status || true)
    fi
    if [ -f "$PID_CONTEXT" ] && kill -0 "$(cat "$PID_CONTEXT")" 2>/dev/null; then
      log "Context WS running (pid $(cat "$PID_CONTEXT"))"
    else
      log "Context WS not running"
    fi
    if [ -f "$PID_ORCHESTRATOR" ] && kill -0 "$(cat "$PID_ORCHESTRATOR")" 2>/dev/null; then
      log "Orchestrator running (pid $(cat "$PID_ORCHESTRATOR"))"
    else
      log "Orchestrator not running"
    fi
    if [ -f "$PID_UI_WRAPPER" ] && kill -0 "$(cat "$PID_UI_WRAPPER")" 2>/dev/null; then
      log "UI wrapper running (pid $(cat "$PID_UI_WRAPPER"))"
    else
      log "UI wrapper not running"
    fi
    ;;
  *)
    echo "Usage: $0 {start|stop|status}"
    exit 1
    ;;
esac
