# DMS Web UI

## Local development

```bash
npm install
npm run dev
```

The dev server runs on http://localhost:5173 and proxies `/api` to `http://localhost:8081` (the REST API running via `docker compose up rest-api postgres-db`, or override with `VITE_API_PROXY_TARGET` in environment variables.).

## Production build

```bash
npm run build   # outputs static files to dist/
```

The Docker image (`Dockerfile`) builds this and serves `dist/` with nginx using `nginx.conf`.
