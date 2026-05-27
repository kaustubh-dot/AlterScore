# AlterScore Frontend

The frontend is a React/Vite application for the borrower flow plus the evaluator dashboard. It talks to the backend API.

## Working State

- **Borrower flow**: Fully implemented (landing, assessment, processing, results, sharing).
- **Evaluator dashboard**: Fully implemented, including:
  - Confusion matrix rendering a 2x2 decision grid.
  - Independent loading/error/empty states per panel via async components and error boundary wrappers.
  - Standard analytics charts (model stats, baseline, fairness, drift, global importance, score distribution, ROC, PR, calibration curves).
- Recommended local Node.js: `18+`
- Recommended local npm: `9+`

## Frontend Quick Start

You can start both the backend and frontend together using the root orchestrator script:
```powershell
# From the repository root
.\scripts\setup\start_alterscore.ps1
```

Or run the frontend service independently (ensure the backend is already running first):

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

The app expects the backend at `http://127.0.0.1:8000/api` unless the `VITE_API_BASE_URL` environment variable is overridden.

## Connectivity Check

Before validating the borrower flow, confirm:

- `GET /api/health` returns 200 from the backend.
- `frontend/src/services/api.js` points to the same backend origin.
- CORS configuration includes `http://localhost:5173` and `http://127.0.0.1:5173`.

## Current Frontend Gaps / Open Items

- Deeper/focused frontend tests (unit and component test coverage) are lighter compared with backend coverage.
- The production build can emit a bundle size warning because of the WebGL/R3F (React Three Fiber) stack.
- Fresh `npm install` reports a few dependency vulnerabilities in transitive packages.

## Read Next

- [`README.md`](../README.md)
- [`docs/SETUP.md`](../docs/SETUP.md)
- [`docs/FRONTEND_INTEGRATION_GUIDE.md`](../docs/FRONTEND_INTEGRATION_GUIDE.md)
- [`docs/API_CONTRACTS.md`](../docs/API_CONTRACTS.md)

