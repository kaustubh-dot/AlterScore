# AlterScore Frontend

The frontend is a React/Vite application for the borrower flow plus the
evaluator dashboard shell. It talks to the backend API through
`VITE_API_BASE_URL`.

## Working State

- Borrower flow implemented: landing, assessment, processing, results, sharing
- Dashboard state: shell implemented, full analytics wiring still pending
- Recommended local Node.js: `18+`
- Recommended local npm: `9+`

## Frontend Quick Start

Run these commands from the repository root after the backend is available:

```powershell
cd frontend
& 'C:\Program Files\nodejs\npm.cmd' install
& 'C:\Program Files\nodejs\npm.cmd' run dev -- --host 127.0.0.1 --port 5173
```

The app expects the backend at `http://127.0.0.1:8000/api` unless
`VITE_API_BASE_URL` is overridden.

## Connectivity Check

Before validating the borrower flow, confirm:

- `GET /api/health` returns 200 from the backend
- `frontend/src/services/api.js` points to the same backend origin as
  `VITE_API_BASE_URL`
- CORS includes `http://localhost:5173` and `http://127.0.0.1:5173`

## Current Frontend Gaps

- Dashboard panels are not fully wired to all analytics endpoints yet.
- Focused frontend tests are still thin compared with backend coverage.
- The production build can emit a large bundle warning because of the WebGL/R3F
  stack.
- Fresh `npm install` currently reports 5 dependency vulnerabilities in
  transitive packages.

## Read Next

- [`README.md`](../README.md)
- [`docs/SETUP.md`](../docs/SETUP.md)
- [`docs/FRONTEND_INTEGRATION_GUIDE.md`](../docs/FRONTEND_INTEGRATION_GUIDE.md)
- [`docs/API_CONTRACTS.md`](../docs/API_CONTRACTS.md)
