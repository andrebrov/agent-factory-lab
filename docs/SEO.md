# SEO & GEO Setup — Manual Steps

The static site and structured data are already in the repo. These steps
require manual action by Andrei in GitHub / Google / browser.

## 1. Enable GitHub Pages

1. Go to **Settings → Pages** in the repo.
2. Under **Source**, select **GitHub Actions**.
3. The `pages.yml` workflow will deploy `docs/` on every push to `main`.
4. After the first deploy, verify: <https://andrebrov.github.io/agent-factory-lab/>

## 2. Set Repository Description & Topics

1. On the repo main page, click the gear icon next to **About**.
2. Set the **description** to:
   > Open research lab testing techniques to make AI coding agents faster and cheaper. Real measurements: 94.5% token reduction (batching), 72% cost savings (caching), 1.83x speedup (panes).
3. Add **topics** (tags):
   ```
   ai-coding-agents, llm-optimization, token-reduction, prompt-caching,
   multi-agent-pipeline, coding-agent-research, herdr, gwaihir, landroval,
   agent-benchmarks, developer-tools
   ```
4. Set the **website** URL to: `https://andrebrov.github.io/agent-factory-lab/`

## 3. Submit to Google Search Console

1. Go to <https://search.google.com/search-console/>.
2. Add property: `https://andrebrov.github.io/agent-factory-lab/`.
3. Verify via the **URL prefix** method (GitHub Pages may need the HTML tag method
   or DNS — URL prefix with a meta tag in `index.html` is simplest).
4. Submit the sitemap: `https://andrebrov.github.io/agent-factory-lab/sitemap.xml`.
5. Request indexing for the homepage.

## 4. Submit to Bing Webmaster Tools (optional but helps Copilot/ChatGPT)

1. Go to <https://www.bing.com/webmasters/>.
2. Add site, verify, submit sitemap.
3. Bing feeds into Microsoft Copilot and some ChatGPT web-search results.

## 5. Verify Structured Data

1. Go to <https://search.google.com/test/rich-results>.
2. Test each page URL:
   - `https://andrebrov.github.io/agent-factory-lab/` — should show TechArticle + Dataset
   - `https://andrebrov.github.io/agent-factory-lab/faq.html` — should show FAQPage
   - `https://andrebrov.github.io/agent-factory-lab/report.html` — should show TechArticle
   - `https://andrebrov.github.io/agent-factory-lab/findings.html` — should show TechArticle
3. Fix any validation errors (there shouldn't be any).

## 6. Verify llms.txt

AI search engines (Perplexity, ChatGPT with browsing, Gemini) look for
`/llms.txt` at the site root. Verify it loads:
- <https://andrebrov.github.io/agent-factory-lab/llms.txt>
- <https://andrebrov.github.io/agent-factory-lab/llms-full.txt>

## 7. Share for Backlinks (optional, boosts SEO)

- Post the lab on X with a thread summarizing the results.
- Share on Hacker News, Reddit r/LocalLLaMA, r/MachineLearning.
- Link from herdr.dev and any personal blog.
- Each backlink from a relevant domain significantly boosts search ranking
  and AI-engine citation probability.

## What's Already Done (in the repo)

- [x] `docs/index.html` — landing page with meta tags, OG, Twitter cards, JSON-LD
- [x] `docs/findings.html` — findings page with TechArticle JSON-LD
- [x] `docs/report.html` — full report with TechArticle JSON-LD
- [x] `docs/faq.html` — FAQ with FAQPage JSON-LD (9 questions)
- [x] `docs/sitemap.xml` — all 4 pages
- [x] `docs/robots.txt` — allows all crawlers (GPTBot, PerplexityBot, ClaudeBot, etc.)
- [x] `docs/llms.txt` — summary for LLM crawlers
- [x] `docs/llms-full.txt` — full content for LLM crawlers
- [x] `docs/style.css` — dark-theme responsive design
- [x] `.github/workflows/pages.yml` — auto-deploy on push to main
- [x] Canonical URLs on every page
- [x] Open Graph and Twitter Card meta tags on every page
