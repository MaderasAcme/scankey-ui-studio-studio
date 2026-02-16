import express from "express";
import fetch from "node-fetch";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = Number(process.env.PORT || 8080);
const GW_URL = process.env.GW_URL;
const GW_API_KEY = process.env.GW_API_KEY;

if (!GW_URL) { console.error("Missing GW_URL"); process.exit(1); }
if (!GW_API_KEY) { console.error("Missing GW_API_KEY"); process.exit(1); }

const app = express();
app.disable("x-powered-by");

// --- health (estable, sin cache) ---
function HEALTH(_req, res) {
  res
    .set("cache-control", "no-store")
    .set("x-scankey-web", "1")
    .json({ ok: true, service: "scankey-web" });
}
// Canonical (usa este en smoke tests)
app.get("/sk-health", HEALTH);
// Alternativo seguro
app.get("/_health", HEALTH);
// Si /healthz está “raro”/interceptado, al menos aquí queda definido
app.get("/healthz", HEALTH);

// --- static (Vite dist) ---
const DIST = path.join(__dirname, "..", "dist");
app.use(express.static(DIST));

// --- path mapping hacia GW ---
function mapUpstreamPath(originalUrl) {
  if (originalUrl === "/api/openapi.json") return "/openapi.json";
  if (originalUrl === "/api/docs") return "/docs";
  if (originalUrl.startsWith("/api/docs/")) return originalUrl.replace("/api/docs", "/docs");
  if (originalUrl === "/api/redoc") return "/redoc";
  if (originalUrl === "/api/health") return "/health";
  // El gateway real usa /api/analyze-key (NO tocar)
  return originalUrl;
}

// --- API proxy: /api/* -> gateway ---
app.all("/api/*", async (req, res) => {
  try {
    const upstreamPath = mapUpstreamPath(req.originalUrl);
    const targetUrl = new URL(upstreamPath, GW_URL).toString();

    const headers = { ...req.headers };
    delete headers.host;
    delete headers.connection;
    delete headers["content-length"];
    delete headers.expect;

    headers["x-api-key"] = GW_API_KEY;

    const method = req.method.toUpperCase();
    const body = (method === "GET" || method === "HEAD") ? undefined : req;

    const gwResp = await fetch(targetUrl, { method, headers, body });

    res.status(gwResp.status);
    gwResp.headers.forEach((v, k) => {
      const kk = k.toLowerCase();
      if (kk === "transfer-encoding") return;
      if (kk === "content-encoding") return;
      res.setHeader(k, v);
    });

    if (gwResp.body) gwResp.body.pipe(res);
    else res.end();
  } catch (e) {
    console.error("proxy_error", e);
    res.status(500).type("text/plain").send("proxy_error");
  }
});

// SPA fallback (si no es /api)
app.get("*", (req, res) => {
  if (req.path.startsWith("/api")) return res.status(404).json({ detail: "Not Found" });
  res.sendFile(path.join(DIST, "index.html"));
});

app.listen(PORT, "0.0.0.0", () => console.log("scankey-web listening on", PORT));
