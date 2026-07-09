# AlterScore Frontend

React/Vite single-page app for the borrower assessment flow, score results,
and evaluator dashboard.

## Local Development

Run from `frontend/`:

```bash
npm install
npm run dev
```

The app reads `VITE_API_BASE_URL` for backend calls. For local development,
create `frontend/.env.local` if you need to override the default:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

## Production

Vercel builds the app from this directory. `frontend/.env.production` points
the deployed SPA at the Hugging Face Spaces backend.

Useful checks:

```bash
npm run lint
npm run build
```
