// Nanalytics resolver. Static files under /v1/ are served by Cloudflare's asset layer
// (free, unlimited). This Worker only answers the dynamic routes:
//   /v1/banana?value=0.72[&min=0&max=1][&scale=freshness|readiness][&mode=stage|frame][&size=128][&format=webp][&theme=light|dark]
//   /v1/shields?value=...   -> shields.io endpoint JSON
//   /v1/banana?value=       -> "unknown" image (never defaults to fresh)

const SIZES = [32, 64, 128, 256, 512, 1024];
const FRAMES = 35;
const STAGES = 10;

function clamp(x, lo, hi) { return Math.min(hi, Math.max(lo, x)); }
function pickSize(s) { const n = parseInt(s || "128", 10); return SIZES.includes(n) ? n : 128; }
function pickFormat(f) { return f === "png" ? "png" : "webp"; }
function pickTheme(t) { return t === "dark" ? "dark/" : ""; }

// Map a normalised t in [0,1] to a frame (1..35) or a stage (1..10).
// Stage boundaries mirror manifest.json: frames per stage are uneven on purpose
// because the ripening curve is uneven in time.
const STAGE_LAST_FRAME = [4, 6, 8, 9, 10, 11, 16, 22, 28, 35];
function frameFor(t) { return clamp(Math.round(t * (FRAMES - 1)) + 1, 1, FRAMES); }
function stageFor(frame) { return STAGE_LAST_FRAME.findIndex(last => frame <= last) + 1; }

function normalise(params) {
  const raw = params.get("value");
  if (raw === null || raw === "" || Number.isNaN(parseFloat(raw))) return null;
  const v = parseFloat(raw);
  const min = parseFloat(params.get("min") ?? "0");
  const max = parseFloat(params.get("max") ?? "1");
  let t = max === min ? 0 : (v - min) / (max - min);
  t = clamp(t, 0, 1);
  // `scale` (freshness | readiness) does not change the mapping, it documents which
  // end the caller considers "good". See SPEC.md.
  const scale = params.get("scale") || "freshness";
  if (params.get("invert") === "true") t = 1 - t;
  return { t, scale };
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const p = url.pathname.replace(/\/+$/, "");

    if (p === "/v1/banana" || p === "/v1/shields") {
      const size = pickSize(url.searchParams.get("size"));
      const fmt = pickFormat(url.searchParams.get("format"));
      const mode = url.searchParams.get("mode") === "frame" ? "frame" : "stage";
      const theme = pickTheme(url.searchParams.get("theme"));
      const n = normalise(url.searchParams);

      let target, label;
      if (n === null) {
        target = `/v1/${theme}stages/${size}/unknown.${fmt}`;
        label = "unknown";
      } else {
        const frame = frameFor(n.t);
        const stage = stageFor(frame);
        target = mode === "frame"
          ? `/v1/${theme}frames/${size}/${String(frame).padStart(2, "0")}.${fmt}`
          : `/v1/${theme}stages/${size}/${stage}.${fmt}`;
        label = `stage ${stage}/${STAGES}`;
      }

      if (p === "/v1/shields") {
        return new Response(JSON.stringify({
          schemaVersion: 1, label: url.searchParams.get("label") || "banana",
          message: label, logoSvg: null, color: "lightgrey",
          // consumers that support it can use the image directly:
          image: `${url.origin}${target}`
        }), { headers: { "content-type": "application/json", "cache-control": "public, max-age=300" } });
      }

      // 302 so the browser caches the immutable file, not the computed redirect
      return Response.redirect(`${url.origin}${target}`, 302);
    }

    // Everything else: let the static layer answer, with long immutable caching on versioned files
    const res = await env.ASSETS.fetch(request);
    if (res.ok && p.startsWith("/v1/")) {
      const h = new Headers(res.headers);
      h.set("cache-control", "public, max-age=31536000, immutable");
      h.set("access-control-allow-origin", "*");
      return new Response(res.body, { status: res.status, headers: h });
    }
    return res;
  }
};
