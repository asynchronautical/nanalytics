# Nanalytics: the spec

Version 1 (draft, October 2026)

## Why

Good communication requires a judicious balancing of ambiguity and clarity. Sometimes being a bit ambiguous delivers more clarity than if you rely on the thing everyone thinks is the definition of clear - numbers. After all, a 2, is always a 2? But the apparent clarity of numbers is a bit of a cognitive honey trap and so the idea of using a clearly ambiguous inference, is way of trying to tell the evaluative gray mush between your ears, to slow it's roll.

To be clear about what it is and isn't: the service is still called with a number and maps it deterministically to a frame. The ambiguity isn't in the encoding, it's in the reading only. The number stays in your system. The human gets the banana, and has to interpret it. That's the point.

Use it where a number would overstate your confidence: data freshness, how long a project has been sitting unloved, how many miles your car has moved beyond it's change oil marker, basically anything that ages. Don't use it where someone needs the number. While I think it would be funny to deliver everyone their bank statements with banana math, it's probably not respectful of their needs. Things are funny when everyone is laughing, as Nana used to say.

## The vocabulary

One banana, photographed on a fixed rig over roughly four weeks as it went from green to black. 35 frames. Ten named stages on top of them. Stages 1 to 7 align with the USDA / Von Loesecke commercial colour index. No commercial scale goes past "yellow flecked with brown," so stages 8 to 10 are this project's own convention and are labelled as such.

| Stage | Slug | Reference | Description | Frames |
|---|---|---|---|---|
| 1 | green | USDA 1 | all green | 1–4 |
| 2 | breaking | USDA 2 | green, first traces of yellow | 5–6 |
| 3 | turning | USDA 3 | more green than yellow | 7–8 |
| 4 | yellow-green | USDA 4 | more yellow than green | 9 |
| 5 | ripe | USDA 5 | yellow with green tips | 10 |
| 6 | yellow | USDA 6 | all yellow | 11 |
| 7 | flecked | USDA 7 | yellow flecked with brown | 12–16 |
| 8 | spotted | ext. | heavily spotted, yellow still dominant | 17–22 |
| 9 | brown | ext. | brown dominant, yellow in patches | 23–28 |
| 10 | black | ext. | black, matte | 29–35 |

The frames per stage are uneven because ripening is uneven in time. That's kept, not smoothed. The fruit also visibly shrinks; all frames share one scale so that's kept too.

Two reading conventions, because a green banana means two different things:

- **freshness** (default): stage 1 is best. Use for staleness, SLA age, ticket age, anything that decays.
- **readiness**: stages 5–6 are best, below is "not yet," above is "past it." Use for launch readiness, maturity, anything that ripens.

The `scale` parameter doesn't change which image you get. It documents which end you consider good, so a reader of your URL (or your code) knows.

There is an explicit **unknown** image. The service never defaults to fresh when it has no value. Badges that quietly show green because nothing was measured are a known failure mode and this is the fix.

## URLs

Versioned, static, immutable. Same URL, same bytes, forever. A re-shoot would go to `/v2/`.

```
/v1/stages/{size}/{stage}.{ext}      stage = 1..10 or slug      e.g. /v1/stages/128/7.webp
/v1/frames/{size}/{frame}.{ext}      frame = 01..35             e.g. /v1/frames/64/23.png
/v1/stages/{size}/unknown.{ext}
/v1/dark/...                         same tree, with a faint light rim for dark backgrounds
/v1/manifest.json                    stage table, frame table, colours, alt text
```

size = 32 | 64 | 128 | 256 | 512 | 1024. ext = webp | png. Fixed buckets, not arbitrary dimensions, so the cacheable surface stays tiny.

One dynamic route, for callers that have a number and don't want to do the mapping:

```
/v1/banana?value=0.72                        -> 302 to /v1/stages/128/8.webp
/v1/banana?value=37&min=0&max=90             -> normalised, then mapped
/v1/banana?value=...&mode=frame              -> one of the 35 frames instead of a stage
/v1/banana?value=...&size=64&format=png
/v1/banana?value=...&scale=readiness         -> documentation only, same image
/v1/banana?value=...&theme=dark              -> rimmed variant for dark UIs
/v1/banana?value=...&invert=true             -> flips the mapping
/v1/banana                                   -> unknown
/v1/shields?value=...                        -> shields.io endpoint-compatible JSON
```

The dynamic route answers with a redirect so browsers cache the immutable file, not the computation.

## Images

Square, transparent canvas, no plate or drop shadow: the fruit floats. The banana fills 92% of the height at stage 1 and the same absolute scale thereafter. Supplied as WebP (default) and PNG.

Two themes. The default has no treatment and sits on anything light. `dark/` adds a faint warm-grey rim around the silhouette so the brown and black stages don't vanish on a dark UI. Same frames, same mapping, same filenames. Every frame and stage in `manifest.json` carries alt text ("Banana, frame 23 of 35, stage 9 of 10 (brown)") because a colour-only decay cue fails for colour-blind readers and screen readers. Ship the alt text.

## Licensing

Images: CC0 1.0. Code: MIT. No attribution required anywhere, that would be silly.

## Self-hosting

The whole thing is static files plus one small Worker. Clone it, run `wrangler deploy`, done. Or install the npm package and serve `public/v1/` from wherever you already serve images. Heavy users should self-host; the public endpoint is a convenience, not a guarantee.
