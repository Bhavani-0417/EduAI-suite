# EduAI Suite — Frontend

React 18 single-page application built with Vite.

## Requirements

- Node.js 20 or later
- npm
- The EduAI FastAPI backend running at the URL configured by `VITE_API_URL`

## Local development

From this directory:

```bash
npm ci
cp .env.example .env
npm run dev
```

On Windows PowerShell, use `Copy-Item .env.example .env`.

The default API URL is `http://localhost:8000`. Update `VITE_API_URL` in `.env` when the backend runs elsewhere.

## Available commands

| Command | Purpose |
| --- | --- |
| `npm run dev` | Start the Vite development server |
| `npm run build` | Create an optimised production build in `dist/` |
| `npm run preview` | Preview the production build locally |

## Application screens

The router exposes login, registration, dashboard, academic, notes, content, career, roadmap, chat, document-vault, and code-explainer screens.

## Notes

- The frontend is not standalone; authenticated features depend on the backend API and configured services.
- Never put server-side API keys in Vite environment variables. Variables prefixed with `VITE_` are bundled into browser code and are public.
- The root README documents backend, database, environment, and CI setup.
