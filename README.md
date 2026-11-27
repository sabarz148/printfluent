# PrintFluent website

Static site (no framework, no database). 60 Etsy listings, 5 categories, 69 pages, sitemap, product schema.
Buyers check out on Etsy; the site is the branded storefront that sends them there.

## Build
    python3 build.py        # writes dist/ — upload that folder

## Deploy (pick one)
- **Cloudflare Pages / Netlify (free, recommended):** push this folder to GitHub, connect it, build command `python3 build.py`, output `dist`. Add printfluent.shop as the custom domain. The `_redirects` file maps your old URLs.
- **Hostinger hosting:** upload the contents of `dist/` to `public_html`. (Hostinger Horizons itself can't import this; point the domain at the new hosting instead.)

## Automation
1. Create an Etsy app at etsy.com/developers/your-apps and copy the keystring.
2. Locally: `ETSY_API_KEY=xxxx python3 scripts/sync_etsy.py && python3 build.py` — refreshes titles, prices, categories and **downloads every listing photo**.
3. Hands-free: add `ETSY_API_KEY` as a GitHub secret. `.github/workflows/sync.yml` re-syncs and rebuilds daily, so new Etsy listings appear on the site on their own.

## Edit
- `config/site.json`: tagline, socials, GA4 id, contact email, newsletter form endpoint.
- `data/products.json`: set `"featured": true` on any listing to feature it on the home page.
- Photos can also be dropped in manually as `src/assets/products/<listing id>.jpg`.

## Direct sales (bundles) with Polar
1. Create a Polar account and connect your payout account.
2. For each bundle in `data/bundles.json`, create a product in Polar (same name, price, upload the files) and copy its checkout link.
3. Paste each link into `data/checkout_links.csv` (last column, matching the bundle id), then `python3 build.py` and upload `dist/`.
Bundles show "Coming soon" until a link is pasted. Etsy single designs keep their Etsy buttons.
