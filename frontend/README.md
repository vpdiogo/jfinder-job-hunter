# JFinder frontend

Browser UI for the JFinder job-management workflow. It is built with React,
TypeScript, and Vite, and consumes the FastAPI backend.

## Development

Start the API from the repository root:

```bash
uvicorn app.main:app --reload
```

In another terminal, start the frontend:

```bash
npm install
npm run dev
```

The UI is available at `http://localhost:5173`. By default it calls
`http://127.0.0.1:8000`. Copy `.env.example` to `.env` and set `VITE_API_URL`
when the API uses another address.

## Checks

```bash
npm run build
npm run lint
```
