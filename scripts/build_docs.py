#!/usr/bin/env python3
"""
Build docs/ HTML from REPORT.md and experiment results.

Generates:
  - docs/report.html from REPORT.md (full content, all experiments)
  - Updates experiment count in docs/index.html, findings.html
  - Updates docs/llms.txt, llms-full.txt, sitemap.xml

Run from repo root: python3 scripts/build_docs.py
"""
import os
import re
import json
import html
import glob
from pathlib import Path
from datetime import date

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"
REPORT_MD = ROOT / "REPORT.md"
STYLE_CSS = "style.css"


def count_experiments():
    """Count experiment directories."""
    return len(glob.glob(str(ROOT / "experiments" / "*_*" / "run.py")))


def count_findings():
    """Count finding files."""
    return len(glob.glob(str(ROOT / "findings" / "*.md")))


def md_to_html_body(md_text: str) -> str:
    """Convert markdown to HTML. Simple converter for the report structure."""
    lines = md_text.split("\n")
    html_parts = []
    in_table = False
    in_code = False
    in_blockquote = False
    table_rows = []

    for line in lines:
        # Code blocks
        if line.strip().startswith("```"):
            if in_code:
                html_parts.append("</code></pre>")
                in_code = False
            else:
                lang = line.strip().lstrip("`").strip()
                html_parts.append(f"<pre><code>")
                in_code = True
            continue
        if in_code:
            html_parts.append(html.escape(line))
            continue

        # Blockquotes
        if line.startswith("> "):
            if not in_blockquote:
                html_parts.append('<blockquote style="border-left:3px solid var(--border);padding-left:1rem;color:var(--text-muted);font-style:italic;">')
                in_blockquote = True
            html_parts.append(f"<p>{_inline(line[2:])}</p>")
            continue
        elif in_blockquote and not line.startswith(">"):
            html_parts.append("</blockquote>")
            in_blockquote = False

        # Tables
        if "|" in line and line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue  # separator row
            if not in_table:
                html_parts.append("<table><thead><tr>")
                for c in cells:
                    html_parts.append(f"<th>{_inline(c)}</th>")
                html_parts.append("</tr></thead><tbody>")
                in_table = True
            else:
                html_parts.append("<tr>")
                for c in cells:
                    html_parts.append(f"<td>{_inline(c)}</td>")
                html_parts.append("</tr>")
            continue
        elif in_table:
            html_parts.append("</tbody></table>")
            in_table = False

        # Headers
        if line.startswith("# "):
            html_parts.append(f"<h1>{_inline(line[2:])}</h1>")
        elif line.startswith("## "):
            anchor = re.sub(r'[^a-z0-9]+', '-', line[3:].lower()).strip('-')
            html_parts.append(f'<h2 id="{anchor}">{_inline(line[3:])}</h2>')
        elif line.startswith("### "):
            html_parts.append(f"<h3>{_inline(line[4:])}</h3>")
        elif line.startswith("#### "):
            html_parts.append(f"<h4>{_inline(line[5:])}</h4>")
        elif line.startswith("---"):
            html_parts.append("<hr>")
        elif line.startswith("- "):
            html_parts.append(f"<li>{_inline(line[2:])}</li>")
        elif re.match(r'^\d+\.\s', line):
            html_parts.append(f"<li>{_inline(re.sub(r'^\d+\.\s', '', line))}</li>")
        elif line.strip() == "":
            html_parts.append("")
        else:
            html_parts.append(f"<p>{_inline(line)}</p>")

    if in_table:
        html_parts.append("</tbody></table>")
    if in_blockquote:
        html_parts.append("</blockquote>")

    return "\n".join(html_parts)


def _inline(text: str) -> str:
    """Convert inline markdown: bold, italic, code, links."""
    text = html.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    return text


def build_report_html():
    """Build docs/report.html from REPORT.md."""
    md = REPORT_MD.read_text()
    body = md_to_html_body(md)
    exp_count = count_experiments()

    report_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Experiment Report — Agent Factory Lab</title>
  <meta name="description" content="Full experiment report: {exp_count} experiments on AI coding agent optimization. Real measurements, honest caveats, measured vs modeled clearly labeled.">
  <link rel="canonical" href="https://andrebrov.github.io/agent-factory-lab/report.html">
  <meta property="og:type" content="article">
  <meta property="og:title" content="Experiment Report — Agent Factory Lab">
  <meta property="og:description" content="Full results from {exp_count} experiments on AI coding agent optimization.">
  <meta property="og:url" content="https://andrebrov.github.io/agent-factory-lab/report.html">
  <meta property="og:site_name" content="Agent Factory Lab">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="Experiment Report — Agent Factory Lab">
  <link rel="stylesheet" href="style.css">
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "TechArticle",
    "headline": "Agent Factory Lab — Full Experiment Report ({exp_count} experiments)",
    "url": "https://andrebrov.github.io/agent-factory-lab/report.html",
    "author": {{"@type": "Person", "name": "Andrei Brov"}},
    "dateModified": "{date.today().isoformat()}"
  }}
  </script>
</head>
<body>
<nav>
  <div class="container">
    <a href="./" class="logo">Agent Factory Lab</a>
    <div class="links">
      <a href="./">Home</a>
      <a href="findings.html">Findings</a>
      <a href="report.html" class="active">Report</a>
      <a href="faq.html">FAQ</a>
      <a href="https://github.com/andrebrov/agent-factory-lab">GitHub</a>
    </div>
  </div>
</nav>
<main class="container">
{body}
</main>
<footer>
  <div class="container">
    <p>Agent Factory Lab &middot; <a href="https://github.com/andrebrov/agent-factory-lab">Source on GitHub</a> &middot; Generated {date.today().isoformat()}</p>
  </div>
</footer>
</body>
</html>"""

    (DOCS / "report.html").write_text(report_html)
    return len(report_html)


def update_counts():
    """Update experiment counts in index.html, findings.html, llms.txt, llms-full.txt."""
    exp_count = count_experiments()
    finding_count = count_findings()

    # Count real/modeled/not-run from results files
    real = modeled = not_run = 0
    for rfile in sorted(glob.glob(str(ROOT / "experiments" / "*_*" / "results.json"))):
        try:
            d = json.loads(Path(rfile).read_text())
            if d.get("could_not_run"):
                not_run += 1
            elif d.get("simulated") or d.get("fixture_modeled") or d.get("costs_modeled"):
                modeled += 1
            else:
                real += 1
        except (json.JSONDecodeError, OSError):
            pass

    # Update index.html
    idx = (DOCS / "index.html").read_text()
    idx = re.sub(r'with \d+ experiments', f'with {exp_count} experiments', idx)
    idx = re.sub(r'\d+ real measurements', f'{real} real measurements', idx)
    idx = re.sub(r'\d+ cost estimates', f'{modeled} modeled/estimated', idx)
    idx = re.sub(r'\d+ simulations', f'{not_run} could-not-run', idx)
    (DOCS / "index.html").write_text(idx)

    # Update findings.html
    findings = (DOCS / "findings.html").read_text()
    findings = re.sub(r'\d+ techniques', f'{finding_count} techniques', findings)
    findings = re.sub(r'\d+ research findings', f'{finding_count} research findings', findings)
    (DOCS / "findings.html").write_text(findings)

    # Update llms.txt header
    llms = (DOCS / "llms.txt").read_text()
    llms = re.sub(r'with \d+ experiments', f'with {exp_count} experiments', llms)
    llms = re.sub(r'\d+ real measurements', f'{real} real measurements', llms)
    (DOCS / "llms.txt").write_text(llms)

    # Update llms-full.txt header
    llms_full = (DOCS / "llms-full.txt").read_text()
    llms_full = re.sub(r'with \d+ experiments', f'with {exp_count} experiments', llms_full)
    (DOCS / "llms-full.txt").write_text(llms_full)

    # Update sitemap lastmod
    sitemap = (DOCS / "sitemap.xml").read_text()
    today = date.today().isoformat()
    sitemap = re.sub(r'<lastmod>\d{4}-\d{2}-\d{2}</lastmod>',
                     f'<lastmod>{today}</lastmod>', sitemap)
    (DOCS / "sitemap.xml").write_text(sitemap)

    return exp_count, real, modeled, not_run


def main():
    print("Building docs from REPORT.md and experiment results...")
    report_size = build_report_html()
    exp_count, real, modeled, not_run = update_counts()
    print(f"  report.html: {report_size:,} bytes")
    print(f"  Experiments: {exp_count} ({real} real, {modeled} modeled, {not_run} not-run)")
    print("  Updated: index.html, findings.html, llms.txt, llms-full.txt, sitemap.xml")
    print("Done.")


if __name__ == "__main__":
    main()
