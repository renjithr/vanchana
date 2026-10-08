# Deploying communistvanchana.com

## GitHub Pages (current host)

`.github/workflows/pages.yml` (at the repo root) builds the site and publishes it
on every push to `main`. Nothing to run locally; push and wait about a minute.
Progress is under the repo's **Actions** tab.

### One-time setup

1. **Repo visibility.** Pages on a free account needs a public repo. Either make
   `renjithr/vanchana` public, or be on GitHub Pro.
2. **Turn Pages on.** Repo → **Settings** → **Pages** → **Source:** *GitHub Actions*.
3. **Verify the domain** (stops anyone else claiming it on GitHub). Your profile →
   **Settings** → **Pages** → **Add a domain** → `communistvanchana.com`. GitHub
   shows a TXT record; add it in GoDaddy (step 4) and click **Verify**.
4. **GoDaddy DNS.** My Products → `communistvanchana.com` → **DNS**. Delete the
   existing `A @` record (GoDaddy's "Parked" page) and any domain forwarding, then add:

   | Type  | Name | Value                   |
   |-------|------|-------------------------|
   | A     | @    | 185.199.108.153         |
   | A     | @    | 185.199.109.153         |
   | A     | @    | 185.199.110.153         |
   | A     | @    | 185.199.111.153         |
   | AAAA  | @    | 2606:50c0:8000::153     |
   | AAAA  | @    | 2606:50c0:8001::153     |
   | AAAA  | @    | 2606:50c0:8002::153     |
   | AAAA  | @    | 2606:50c0:8003::153     |
   | CNAME | www  | renjithr.github.io      |

   If a `CNAME www` record already exists, edit it rather than adding a second one.
5. **Attach the domain.** Repo → **Settings** → **Pages** → **Custom domain** →
   `communistvanchana.com` → Save. Once the DNS check passes (minutes to a few
   hours), tick **Enforce HTTPS**.

### Differences from Cloudflare

- `_headers` is ignored, so GitHub's own caching applies (10 minutes on
  everything). Fine for this site; CSS/JS changes show up sooner, scans re-download
  more often.
- `_redirects` is ignored. The build writes stub pages for `/kaalarekha/` and
  `/rekhakal/` that redirect in the browser instead.
- `CNAME` and `.nojekyll` are written into `build/` for completeness; with the
  Actions deploy, the custom domain in Settings is what counts.

---

## Cloudflare Pages (alternative)

The site is plain static HTML. **Cloudflare runs no build step** — you build locally
and upload the finished `build/` folder. That means nothing can break on their side,
and deploys take seconds.

---

## 1. Build

```bash
cd /Users/apple/Commie/communistvanchana/src
python3 build_archive.py
```

Output goes to `build/`. Expect `pages: 47` and about 28 MB.

If the scans or fonts ever need regenerating:

```bash
python3 src/fetch_fonts.py     # re-downloads and self-hosts the fonts
python3 src/build_images.py    # regenerates all responsive scan derivatives
```

---

## 2. Deploy

### Option A — Wrangler CLI (recommended)

```bash
npx wrangler pages deploy build --project-name=communistvanchana
```

First run asks you to log in and creates the project. Every later run is a new
deployment with instant rollback available in the dashboard.

### Option B — Dashboard upload

Cloudflare dashboard → **Workers & Pages** → **Create** → **Pages** →
**Upload assets** → drag in the `build` folder.

### Option C — Git

Push the repo, connect it in Pages, and set:

- **Build command:** `python3 src/build_archive.py`
- **Build output directory:** `build`

Only worth it if you want deploys on push; A is simpler.

---

## 3. Attach the domain

Pages project → **Custom domains** → **Set up a custom domain** →
`communistvanchana.com`.

Because the domain is already on Cloudflare, the DNS record is created for you and
the certificate issues automatically, usually within a couple of minutes. Add
`www.communistvanchana.com` as a second custom domain if you want it to resolve;
Cloudflare will redirect it to the apex.

---

## 4. What is already configured

**`build/_headers`** — sets caching and security headers:

- fonts and scans: immutable, one-year cache (they never change under the same name)
- CSS/JS: one-week cache
- `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options`, `Permissions-Policy`
  on every route

**`build/_redirects`** — normalises `/index.html` to `/`.

**`build/404.html`** — Cloudflare serves this automatically on unmatched routes.

**`build/robots.txt`** and **`build/sitemap.xml`** — 47 URLs, all with `lastmod`.

---

## 5. After the first deploy

1. **Google Search Console** — add the property, verify by DNS (fastest, since the
   domain is on Cloudflare), then submit `https://communistvanchana.com/sitemap.xml`.
2. **Bing Webmaster Tools** — same sitemap. Worth doing; Bing feeds several other
   engines.
3. **Check the share card** — paste the URL into
   [opengraph.xyz](https://www.opengraph.xyz/) to confirm `og.jpg` renders.
4. **Cloudflare settings** — Speed → Optimization: leave Auto Minify **off**. The
   HTML is already tight and minifying can corrupt the `<pre>` transcript blocks,
   where whitespace is meaningful.

---

## 6. Things to know before launch

- **The Malayalam has not been proofread.** It was written to be checked. Every
  Malayalam string lives in `src/content_ml.py` and `src/ml_labels.py` — edit those
  two files and rebuild; you never need to touch HTML.
- **Cache busting.** Filenames are not content-hashed. If you change `site.css` or
  `site.js`, returning visitors may hold the old copy for up to a week. For a
  significant change, either rename the file or purge the cache in the Cloudflare
  dashboard.
- **The scans are the heavy part** (27 MB of the 28 MB). They are cached
  immutably, so this costs first-time visitors only, and each page loads just the
  few images it needs.
