# Services website

A static page (`index.html` + `style.css`) with no build step and no paid services.

## Before publishing
1. Replace `YOUR_EMAIL@gmail.com` (twice) and `YOUR_LINKEDIN` in `index.html`.
2. Re-read the About section; every line must still be true.
3. Preview locally: `python -m http.server 8090 --directory site`, then open http://localhost:8090.

## Publish free on GitHub Pages
GitHub Pages serves a repo named `<username>.github.io` at `https://<username>.github.io/`.
1. On github.com create a public repo named `Nishanth-nishu.github.io`.
2. Copy `index.html` and `style.css` into it and push.
3. Repo → Settings → Pages → Source: "Deploy from a branch", branch `main`, folder `/`.
4. The site is live at `https://nishanth-nishu.github.io/` within a few minutes.

Use that URL as `SENDER_SITE` for the outreach bot and on your LinkedIn profile. A custom domain (~₹800/year)
can come later; it is a paid step, so it waits for your approval.
