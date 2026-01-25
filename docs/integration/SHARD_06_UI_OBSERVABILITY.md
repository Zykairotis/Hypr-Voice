# SHARD 06 — Web UI Observability Timeline

Goal: add a live event timeline page to `web-ui` showing Claude hook + Hypr-Voice events.

Layout
- Route: `/observability`
- Components:
  - `EventFeed` (virtualized list)
  - `EventRow` (type badge, summary, time ago, session link)
  - `FilterBar` (agent, event type, severity)
  - `LivePill` (WS connection status)

Data
- WebSocket to existing WS bridge (ports 8933/8934) or direct to Bun server if allowed.
- Fallback REST: `/api/events?since=` to hydrate on load.

Actions
- Clicking an event opens drawer with payload JSON and related audio file (if present).

Styling
- Tailwind; use chips + subtle gradients; no purple bias.

Testing
- Storybook-lite: mock provider with static events.
- Live test: trigger a query; observe TTS/route events append in near real-time.
