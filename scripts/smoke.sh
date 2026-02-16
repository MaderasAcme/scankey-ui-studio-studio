#!/usr/bin/env bash
set -Eeuo pipefail

REGION="${REGION:-europe-southwest1}"
WEB_URL="${1:-${WEB_URL:-}}"

if [[ -z "${WEB_URL}" ]]; then
  WEB_URL="$(gcloud run services describe scankey-web --region "$REGION" --format='value(status.url)')"
fi

echo "WEB=${WEB_URL}"
test -n "${WEB_URL}" || { echo "FAIL: WEB_URL vacío"; exit 1; }

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
ts="$(date +%s)"

code="$(curl -sS -o "$tmpdir/sk.json" -w '%{http_code}' "${WEB_URL}/sk-health?ts=${ts}")"
[[ "$code" == "200" ]] || { echo "FAIL: /sk-health status=$code"; cat "$tmpdir/sk.json" || true; exit 1; }
grep -q '"ok":true' "$tmpdir/sk.json" || { echo "FAIL: /sk-health no devuelve ok:true"; cat "$tmpdir/sk.json"; exit 1; }
grep -q '"service":"scankey-web"' "$tmpdir/sk.json" || { echo "FAIL: /sk-health no devuelve service scankey-web"; cat "$tmpdir/sk.json"; exit 1; }

code="$(curl -sS -o "$tmpdir/gw.json" -w '%{http_code}' "${WEB_URL}/api/health")"
[[ "$code" == "200" ]] || { echo "FAIL: /api/health status=$code"; cat "$tmpdir/gw.json" || true; exit 1; }
grep -q '"ok":true' "$tmpdir/gw.json" || { echo "FAIL: /api/health no devuelve ok:true"; cat "$tmpdir/gw.json"; exit 1; }

hdr="$tmpdir/opt.hdr"
code="$(curl -sS -D "$hdr" -o /dev/null -w '%{http_code}' -X OPTIONS "${WEB_URL}/api/analyze-key" \
  -H "Origin: https://scankeyapp.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type")"
[[ "$code" == "200" ]] || { echo "FAIL: OPTIONS status=$code"; cat "$hdr" || true; exit 1; }
grep -qi '^access-control-allow-origin: https://scankeyapp.com' "$hdr" || { echo "FAIL: CORS allow-origin incorrecto"; cat "$hdr"; exit 1; }

printf '\xFF\xD8\xFF\xD9' > "$tmpdir/front.jpg"
printf '\xFF\xD8\xFF\xD9' > "$tmpdir/back.jpg"
code="$(curl -sS -o "$tmpdir/post.json" -w '%{http_code}' -X POST "${WEB_URL}/api/analyze-key" \
  -H "Origin: https://scankeyapp.com" \
  -F "front=@$tmpdir/front.jpg" \
  -F "back=@$tmpdir/back.jpg")"
[[ "$code" == "400" ]] || { echo "FAIL: POST status=$code"; cat "$tmpdir/post.json" || true; exit 1; }
grep -qi 'imagen inválida' "$tmpdir/post.json" || { echo "FAIL: POST no devuelve 'imagen inválida'"; cat "$tmpdir/post.json"; exit 1; }

echo "PASS"
