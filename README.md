# Nanalytics

A ripening banana as a status glyph. 35 photographic frames, 10 named stages, served by URL, CC0.

```html
<img src="https://nanalytics.dev/v1/banana?value=0.72" alt="stage 9 of 10, brown">
```

Why would you want this? Because a number in a dashboard looks more certain than it usually is, and a banana doesn't. Read [SPEC.md](SPEC.md) for the argument and the vocabulary.

## Layout

```
public/v1/stages/{size}/{1..10 | slug | unknown}.{webp,png}
public/v1/frames/{size}/{01..35}.{webp,png}
public/v1/dark/...                       rimmed variant for dark backgrounds
public/v1/manifest.json
src/index.js        Cloudflare Worker: resolves ?value= to a file, serves shields JSON
demo/               a dashboard shown twice, once with numbers, once with bananas
```

## Deploy

```
npm install
npx wrangler login
npx wrangler deploy
```

Static files under `public/` are served by Cloudflare's asset layer, free and unlimited. The Worker only runs for `/v1/banana` and `/v1/shields`.

## License

Images CC0 1.0 (see LICENSE-IMAGES). Code MIT.
