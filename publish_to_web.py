"""
publish_to_web.py — Publishes daily market reports to the PrudentSigma GitHub Pages site.

Steps:
  1. Convert the .md report to a styled HTML page (matching PrudentSigma design)
  2. Update reports/index.json with the new entry
  3. Push both files to the gh-pages branch via git worktree
"""

import os
import json
import shutil
import subprocess
import re
from datetime import datetime

PROJECT_DIR = r"C:\Users\Pavlos Elpidorou\Documents\AI_Project"
WEB_DIR = os.path.join(PROJECT_DIR, "Web_design")
WORKTREE_PATH = r"C:\Users\Pavlos Elpidorou\AppData\Local\Temp\ps-ghpages"
LOG_FILE = os.path.join(PROJECT_DIR, "reports", "generation.log")


def _log(msg):
    print(msg)
    today = datetime.now().strftime("%Y-%m-%d")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{today} [web] {msg}\n")


def _run(args, cwd=None):
    return subprocess.run(
        args, cwd=cwd or PROJECT_DIR,
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )


def _format_display_date(date_str):
    """Format '2026-04-05' -> 'April 5, 2026'"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%B %-d, %Y") if os.name != "nt" else dt.strftime("%B %d, %Y").replace(" 0", " ")


def _strip_report_text(md_text):
    """Strip Claude preamble and code fence wrappers from the report."""
    lines = md_text.split("\n")

    # Find start: first line with ════ or PRUDENTSIGMA
    start = 0
    for i, line in enumerate(lines):
        if "════" in line or "PRUDENTSIGMA" in line:
            # Check if the preceding line was a ``` fence
            if i > 0 and lines[i - 1].strip().startswith("```"):
                start = i  # skip the fence, start at ════
            else:
                start = i
            break

    lines = lines[start:]

    # Strip trailing ``` fence
    while lines and not lines[-1].strip():
        lines.pop()
    if lines and lines[-1].strip().startswith("```"):
        lines.pop()

    return "\n".join(lines)


def _escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _apply_inline_formatting(text):
    """Convert **bold** and section titles to styled HTML within escaped text."""
    # **bold** → <strong>
    text = re.sub(r"\*\*(.+?)\*\*", r'<strong style="color:var(--text-1);font-weight:500;">\1</strong>', text)
    return text


def _convert_report_to_html_body(report_text):
    """
    Convert the stripped report text to HTML body content.
    Uses <pre> for monospace alignment + applies inline formatting.
    Section headers (──── SECTION N ────) get highlighted.
    """
    lines = report_text.split("\n")
    html_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # ════ header line → report title block
        if "════" in stripped and "PRUDENTSIGMA" not in stripped:
            html_lines.append('<span class="rpt-rule">════════════════════════════════════════════════════════════════════════════════</span>')
            i += 1
            continue

        # PRUDENTSIGMA header line
        if "PRUDENTSIGMA" in stripped and "════" not in stripped:
            escaped = _escape_html(stripped)
            html_lines.append(f'<span class="rpt-header">{escaped}</span>')
            i += 1
            continue

        # ──── lines — section separators
        if stripped.startswith("────") and len(stripped) > 20:
            # Check if next non-empty line is a section title
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and not lines[j].strip().startswith("────"):
                # This is the opening separator of a section
                section_line = lines[j].strip()
                escaped_section = _escape_html(section_line)
                html_lines.append('<span class="rpt-sep">────────────────────────────────────────────────────────────────────────────────</span>')
                html_lines.append(f'<span class="rpt-section">{escaped_section}</span>')
                i = j + 1
                # Skip the closing ──── line
                if i < len(lines) and lines[i].strip().startswith("────"):
                    html_lines.append('<span class="rpt-sep">────────────────────────────────────────────────────────────────────────────────</span>')
                    i += 1
                continue
            else:
                html_lines.append('<span class="rpt-sep">────────────────────────────────────────────────────────────────────────────────</span>')
                i += 1
                continue

        # Normal line — escape + apply inline formatting
        escaped = _escape_html(line)
        formatted = _apply_inline_formatting(escaped)
        html_lines.append(formatted)
        i += 1

    return "\n".join(html_lines)


def build_report_html(md_text, date, display_date):
    """Build a full HTML page for the report."""
    report_text = _strip_report_text(md_text)
    body_html = _convert_report_to_html_body(report_text)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Market Report {display_date} — PrudentSigma</title>
  <meta name="description" content="PrudentSigma Daily Market Report for {display_date}. Macro analysis, technical snapshot, investment ideas.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;1,300;1,400&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../style.css">
  <style>
    .report-wrapper {{
      background: var(--navy-800);
      border: 1px solid var(--navy-600);
      border-radius: var(--radius-md);
      padding: 40px;
      overflow-x: auto;
    }}
    .report-pre {{
      font-family: 'DM Mono', 'Courier New', monospace;
      font-size: 0.8125rem;
      font-weight: 300;
      line-height: 1.7;
      color: var(--text-2);
      white-space: pre-wrap;
      word-wrap: break-word;
      margin: 0;
    }}
    .rpt-rule {{
      color: var(--gold-deep);
      opacity: 0.6;
      display: block;
    }}
    .rpt-header {{
      color: var(--gold-warm);
      font-weight: 400;
      letter-spacing: 0.02em;
      display: block;
    }}
    .rpt-sep {{
      color: var(--navy-600);
      display: block;
    }}
    .rpt-section {{
      color: var(--gold-mid);
      font-weight: 400;
      letter-spacing: 0.05em;
      display: block;
      padding: 4px 0;
    }}
    .back-link {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--gold-mid);
      font-family: 'DM Sans', sans-serif;
      font-size: 0.875rem;
      font-weight: 400;
      text-decoration: none;
      letter-spacing: 0.04em;
      transition: color var(--transition-fast);
      margin-bottom: 48px;
      display: block;
    }}
    .back-link:hover {{ color: var(--gold-warm); }}
    .report-meta {{
      display: flex;
      align-items: center;
      gap: 24px;
      margin-bottom: 32px;
      flex-wrap: wrap;
    }}
    .report-meta-badge {{
      font-family: 'DM Mono', monospace;
      font-size: 0.75rem;
      color: var(--text-3);
      letter-spacing: 0.1em;
      text-transform: uppercase;
    }}
  </style>
</head>
<body>

<!-- NAV -->
<nav class="nav" id="main-nav">
  <div class="container">
    <a href="../index.html" class="nav-logo">
      <svg width="28" height="28" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="60" cy="60" r="56" stroke="url(#rpt-nfg)" stroke-width="1" opacity="0.35"/>
        <path d="M28 32 L92 32 L57 59 L92 86 L28 86" stroke="url(#rpt-nsg)" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round" fill="none"/>
        <defs>
          <linearGradient id="rpt-nsg" x1="28" y1="32" x2="92" y2="86" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stop-color="#C5923A"/>
            <stop offset="50%" stop-color="#DFB06A"/>
            <stop offset="100%" stop-color="#C5923A"/>
          </linearGradient>
          <linearGradient id="rpt-nfg" x1="4" y1="4" x2="116" y2="116" gradientUnits="userSpaceOnUse">
            <stop stop-color="#C5923A" stop-opacity="0.6"/>
            <stop offset="1" stop-color="#C5923A" stop-opacity="0.1"/>
          </linearGradient>
        </defs>
      </svg>
      PrudentSigma
    </a>
    <div class="nav-links">
      <a href="../about.html">About</a>
      <a href="../newsletter.html" class="active">Financial News</a>
      <a href="../consulting.html">Consulting</a>
      <a href="../insights.html">Insights</a>
      <a href="../tools.html">Tools</a>
    </div>
    <div class="nav-cta">
      <a href="../contact.html" class="btn btn-primary">Book a Call</a>
      <button class="nav-burger" id="nav-burger" aria-label="Toggle menu">
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
</nav>

<!-- TICKER BAR -->
<div class="ticker-bar">
  <div class="tradingview-widget-container" style="height:100%;width:100%;">
    <div class="tradingview-widget-container__widget" style="height:100%;"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
    {{
      "symbols": [
        {{"proName": "TVC:SPX", "title": "S&P 500"}},
        {{"proName": "TVC:NDX", "title": "Nasdaq 100"}},
        {{"description": "DXY", "proName": "TVC:DXY"}},
        {{"description": "Gold", "proName": "TVC:GOLD"}},
        {{"description": "Silver", "proName": "TVC:SILVER"}},
        {{"description": "WTI Crude", "proName": "TVC:USOIL"}},
        {{"description": "BTC/USD", "proName": "BITSTAMP:BTCUSD"}},
        {{"description": "EUR/USD", "proName": "FX:EURUSD"}},
        {{"description": "GBP/USD", "proName": "FX:GBPUSD"}},
        {{"description": "USD/JPY", "proName": "FX:USDJPY"}}
      ],
      "showSymbolLogo": false,
      "isTransparent": true,
      "displayMode": "adaptive",
      "colorTheme": "dark",
      "locale": "en"
    }}
    </script>
  </div>
</div>

<!-- PAGE HERO -->
<section class="page-hero">
  <div class="container">
    <span class="label anim-1">Daily Market Report</span>
    <h1 class="display anim-2" style="max-width:700px;">{display_date}</h1>
    <p class="subtitle anim-3" style="max-width:500px; margin-top:16px;">PrudentSigma Market Intelligence — Macro, Technicals, and Ideas.</p>
  </div>
</section>

<!-- REPORT CONTENT -->
<section class="section">
  <div class="container">
    <a href="../newsletter.html" class="back-link">&#8592; Back to all reports</a>
    <div class="report-meta">
      <span class="report-meta-badge">Date: {date}</span>
      <span class="report-meta-badge">Source: PrudentSigma AI Research</span>
    </div>
    <div class="report-wrapper reveal">
      <pre class="report-pre">{body_html}</pre>
    </div>
  </div>
</section>

<!-- FOOTER -->
<footer class="footer">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-col">
        <div class="footer-logo">
          <svg width="24" height="24" viewBox="0 0 120 120" fill="none">
            <path d="M28 32 L92 32 L57 59 L92 86 L28 86" stroke="url(#rpt-ffg)" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round" fill="none"/>
            <defs>
              <linearGradient id="rpt-ffg" x1="28" y1="32" x2="92" y2="86" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stop-color="#C5923A"/>
                <stop offset="50%" stop-color="#DFB06A"/>
                <stop offset="100%" stop-color="#C5923A"/>
              </linearGradient>
            </defs>
          </svg>
          PrudentSigma
        </div>
        <p class="footer-tagline">A finance and decision-intelligence platform for serious people.</p>
      </div>
      <div class="footer-col">
        <h4>Navigate</h4>
        <ul>
          <li><a href="../index.html">Home</a></li>
          <li><a href="../about.html">About</a></li>
          <li><a href="../newsletter.html">Financial News</a></li>
          <li><a href="../insights.html">Insights</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>Services</h4>
        <ul>
          <li><a href="../consulting.html">Consulting</a></li>
          <li><a href="../tools.html">Tools</a></li>
          <li><a href="../contact.html">Contact</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>Philosophy</h4>
        <div class="footer-beliefs">
          <div class="footer-belief"><span class="footer-belief-num">01</span><span class="footer-belief-text">Risk comes before return</span></div>
          <div class="footer-belief"><span class="footer-belief-num">02</span><span class="footer-belief-text">Clarity beats complexity</span></div>
          <div class="footer-belief"><span class="footer-belief-num">03</span><span class="footer-belief-text">Discipline compounds</span></div>
        </div>
      </div>
    </div>
    <div class="footer-bottom">
      <p class="footer-bottom-copy">&copy; 2025 PrudentSigma. All rights reserved.</p>
      <div class="footer-bottom-links">
        <a href="#">Privacy Policy</a>
        <a href="#">Terms of Use</a>
        <a href="#">Disclaimer</a>
      </div>
    </div>
  </div>
</footer>

<script>
  const reveals = document.querySelectorAll('.reveal');
  const ro = new IntersectionObserver((entries) => {{
    entries.forEach(e => {{ if (e.isIntersecting) {{ e.target.classList.add('visible'); ro.unobserve(e.target); }}}});
  }}, {{ threshold: 0.1 }});
  reveals.forEach(r => ro.observe(r));

  const burger = document.getElementById('nav-burger');
  const nav = document.getElementById('main-nav');
  if (burger) burger.addEventListener('click', () => nav.classList.toggle('nav-open'));
</script>
</body>
</html>"""


def publish_report(report_md_path, date):
    """
    Publish a daily market report to GitHub Pages.
    Returns True on success, False on failure.
    """
    display_date = _format_display_date(date)
    report_filename = f"report_{date}.html"

    _log(f"Publishing report for {date} to GitHub Pages...")

    # 1. Read and convert the report
    try:
        with open(report_md_path, "r", encoding="utf-8", errors="replace") as f:
            md_text = f.read()
        html_content = build_report_html(md_text, date, display_date)
    except Exception as e:
        _log(f"Error converting report to HTML: {e}")
        return False

    # 2. Clean up any existing worktree
    if os.path.exists(WORKTREE_PATH):
        _run(["git", "worktree", "remove", "--force", WORKTREE_PATH])
        shutil.rmtree(WORKTREE_PATH, ignore_errors=True)

    # 3. Fetch latest gh-pages from origin
    _run(["git", "fetch", "origin", "gh-pages"])

    # 4. Create worktree for gh-pages
    result = _run(["git", "worktree", "add", WORKTREE_PATH, "gh-pages"])
    if result.returncode != 0:
        _log(f"git worktree add failed: {result.stderr.strip()}")
        return False

    try:
        reports_dir = os.path.join(WORKTREE_PATH, "reports")
        os.makedirs(reports_dir, exist_ok=True)

        # 5. Write HTML report file
        html_path = os.path.join(reports_dir, report_filename)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # 6. Update index.json
        index_path = os.path.join(reports_dir, "index.json")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                index = json.load(f)
        else:
            index = {"reports": []}

        # Remove existing entry for this date if present (idempotent)
        index["reports"] = [r for r in index["reports"] if r.get("date") != date]
        index["reports"].insert(0, {
            "date": date,
            "display_date": display_date,
            "filename": report_filename,
            "title": f"Daily Market Report — {display_date}",
        })
        # Keep last 90 reports
        index["reports"] = index["reports"][:90]

        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

        # 7. Also sync newsletter.html from Web_design (keeps it up to date)
        nl_src = os.path.join(WEB_DIR, "newsletter.html")
        nl_dst = os.path.join(WORKTREE_PATH, "newsletter.html")
        if os.path.exists(nl_src):
            shutil.copy2(nl_src, nl_dst)

        # 8. Git commit and push
        _run(["git", "add", "reports/", "newsletter.html"], cwd=WORKTREE_PATH)
        commit_result = _run(
            ["git", "commit", "-m", f"Add market report {date}"],
            cwd=WORKTREE_PATH
        )
        if "nothing to commit" in commit_result.stdout:
            _log(f"Report {date} already published (no changes).")
            return True

        push_result = _run(["git", "push", "origin", "gh-pages"], cwd=WORKTREE_PATH)
        if push_result.returncode != 0:
            _log(f"git push failed: {push_result.stderr.strip()}")
            return False

        _log(f"Report published: https://pavlise.github.io/prudentsigma-dashboard/reports/{report_filename}")
        return True

    except Exception as e:
        _log(f"Publish error: {e}")
        return False

    finally:
        _run(["git", "worktree", "remove", "--force", WORKTREE_PATH])
        shutil.rmtree(WORKTREE_PATH, ignore_errors=True)


if __name__ == "__main__":
    import sys
    # Allow manual test: python publish_to_web.py reports/report_2026-04-05.md 2026-04-05
    if len(sys.argv) == 3:
        success = publish_report(sys.argv[1], sys.argv[2])
        sys.exit(0 if success else 1)
    else:
        print("Usage: python publish_to_web.py <report.md> <YYYY-MM-DD>")
        sys.exit(1)
