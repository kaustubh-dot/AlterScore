# AlterScore Frontend

React/Vite single-page app for the anonymous v2 assessment, explainable
results, session-only dashboard, and static offline Research Lab.

Use Node.js `20.19.x` or `>=22.12.0`; the locked Vite toolchain does not
support Node 18.

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

The v2 assessment form and score routes require HTTPS for every remote and
production-like request. Loopback HTTP is accepted only when the backend is in
local/test/development mode; a client-supplied forwarded-protocol header does
not bypass the remote transport boundary.

## Production

Vercel builds the app from this directory. `frontend/.env.production` points
the deployed SPA at the Hugging Face Spaces backend. Each production build
must receive the exact backend release SHA through `VITE_RELEASE_SHA`; the
release gate rejects missing or local values.

Useful checks:

```bash
npm run lint
VITE_RELEASE_SHA=<40-character-reviewed-sha> npm run build
npm run test:trial
npm run test:phase5
npm run test:phase6
npm run test:phase7
npm run test:phase8
npm run test:all
```

The inline assignment uses POSIX shell syntax. For PowerShell, set
`$env:VITE_RELEASE_SHA = '<40-character-reviewed-sha>'` before running
`npm.cmd run build`.
