# Skills & Capabilities Reference

This file tracks skills, tools, MCP servers, and techniques needed for this project.

There are two ways to extend Claude Code:
- **MCP Servers** — Give Claude real new tool capabilities (databases, APIs, file processing)
- **Custom Skills** — Give Claude workflow templates and domain knowledge via slash commands

---

## How to Add MCP Servers (Real Tool Capabilities)

```bash
# General pattern (Windows requires cmd /c for local servers)
claude mcp add --transport stdio <name> -- cmd /c npx -y <package>
claude mcp add --transport http <name> <url>

# List configured servers
claude mcp list
```

---

## Skill Map: What You Need & How to Add It

### 1. Reading Excel (.xlsx)

| Type | MCP Server / Tool |
|------|------------------|
| Requirement | Python (real install) + openpyxl/pandas |
| Install | `pip install openpyxl pandas` |
| MCP option | Look for: `excel-mcp-server` on GitHub |

**Workaround until Python is installed:** Ask Claude to generate a Python script, run it, and read the output.

---

### 2. Reading Word (.docx) / PowerPoint (.pptx)

| Type | Tool |
|------|------|
| Requirement | Python + python-docx + python-pptx |
| Install | `pip install python-docx python-pptx` |
| MCP option | Community servers exist (search: `docx mcp server` on GitHub) |

---

### 3. SQL Databases

| Type | MCP Server |
|------|-----------|
| SQLite | `claude mcp add --transport stdio sqlite -- cmd /c npx -y @modelcontextprotocol/server-sqlite --db-path ./data.db` |
| PostgreSQL | `claude mcp add --transport stdio postgres -- cmd /c npx -y @bytebase/dbhub --dsn "postgresql://user:pass@host:5432/db"` |

---

### 4. Financial Data & Market APIs

| Source | Notes |
|--------|-------|
| Yahoo Finance (`yfinance`) | **Primary source** — free, no API key. Prices, OHLCV, technicals, fundamentals (P/E, EPS, analyst targets, earnings history). Used in `market_data_fetcher.py` |
| Exa MCP | **Configured** ✓ — semantic news search for Claude. Key saved as `EXA_API_KEY` env var. Free tier: 1,000 searches/month (~250 used by daily report). Add via: `claude mcp add exa --transport http https://mcp.exa.ai/mcp --header "x-api-key: <KEY>"` |
| financialdatasets.ai | API key saved as `FINANCIAL_DATASETS_API_KEY` env var. **Free tier has no API access** — all endpoints return 403. Paid plan required (~$29/mo). Not currently used; yfinance covers the same data for free. REST API works (tested): `https://api.financialdatasets.ai/financials/income-statements/?ticker=AAPL&period=ttm&limit=1` |
| Alpha Vantage | Free tier available. Search GitHub: `alpha-vantage mcp server` |
| Polygon.io | Search GitHub: `polygon mcp server` |
| News API | Search GitHub: `newsapi mcp server` |

**Install Python approach:**
```bash
pip install yfinance pandas requests
```

---

### 5. API Connections (News & Market Data)

- Built-in `WebFetch` tool can already hit any public REST API
- **Exa MCP** is the preferred news source — use `exa_search` tool in Claude for financial content
- For persistent integrations, create MCP servers wrapping specific APIs
- Key APIs to connect: Alpha Vantage, Polygon.io, NewsAPI, FRED (Federal Reserve data)

---

### 6. Data Analytics

- Powered by Python (pandas, numpy, scipy, matplotlib, seaborn)
- Install: `pip install pandas numpy scipy matplotlib seaborn`
- Claude can write, run, and interpret analytics scripts
- Combine with SQL MCP for database-driven analytics

---

### 7. n8n Workflow Creation

| Type | Approach |
|------|---------|
| Knowledge-based | Claude already knows n8n workflow JSON schema |
| MCP option | Search GitHub: `n8n mcp server` |
| Best approach | Claude generates workflow JSON → import into n8n UI |

Claude can design and write full n8n workflows (JSON) for you to import directly.

---

### 8. Live Dashboards

| Tool | Approach |
|------|---------|
| Streamlit (Python) | Fastest — Claude writes app, you run it locally |
| Grafana | Connect to data sources, Claude generates dashboard JSON |
| Power BI | Claude can generate DAX formulas and layout guidance |
| HTML/JS | Claude writes self-contained dashboard pages |

---

### 9. Portfolio, Asset Valuation & Risk Assessment

- Claude has strong built-in knowledge of: VaR, Greeks, Sharpe ratio, CAPM, Black-Scholes, duration/convexity, stress testing
- Python libraries: `yfinance`, `quantlib`, `pyfolio`, `empyrical`, `scipy`
- Install: `pip install yfinance pyfolio empyrical`
- Combine with market data APIs for live valuations

---

### 10. Workflow Automation

| Tool | Notes |
|------|-------|
| n8n | Claude generates workflow JSON |
| Python scripts | Claude writes and runs automation scripts |
| Playwright MCP | `claude mcp add --transport stdio playwright -- cmd /c npx -y @playwright/mcp@latest` (browser automation) |

---

## Priority Setup Steps

To unlock most of the above, do these in order:

1. **Install Python properly** (not Windows Store stub)
   - Download from python.org
   - Verify: `python --version`

2. **Install core Python packages**
   ```bash
   pip install pandas openpyxl python-docx python-pptx yfinance numpy scipy matplotlib seaborn requests pyfolio
   ```

3. **Add SQL MCP server (SQLite)**
   ```bash
   claude mcp add --transport stdio sqlite -- cmd /c npx -y @modelcontextprotocol/server-sqlite --db-path ./data.db
   ```

4. **Add Playwright for browser automation**
   ```bash
   claude mcp add --transport stdio playwright -- cmd /c npx -y @playwright/mcp@latest
   ```

5. **API keys configured** — `EXA_API_KEY` (Exa MCP, active) and `FINANCIAL_DATASETS_API_KEY` (paid plan needed to activate)

---

## Useful GitHub Search Terms for MCP Servers

- `mcp-server excel`
- `mcp-server financial`
- `mcp-server n8n`
- `mcp-server alpha-vantage`
- `mcp-server polygon`
- `modelcontextprotocol/servers` (official list)

---

## Environment Status

| Item | Status |
|------|--------|
| Python | Installed (3.14.3) — use `py` command |
| pandas | 2.3.3 |
| openpyxl | 3.1.5 — Excel |
| python-docx | 1.2.0 — Word |
| python-pptx | 1.0.2 — PowerPoint |
| yfinance | 1.2.0 — live market data |
| numpy | 2.4.3 |
| matplotlib | 3.10.8 |
| seaborn | 0.13.2 |
| scipy | 1.17.1 |
| scikit-learn | 1.8.0 |
| pyfolio-reloaded | 0.9.9 — portfolio analytics |
| empyrical-reloaded | 0.5.12 — risk/return metrics |
| pandoc | Not installed |
| Node.js/npx | v24.14.0 / v11.9.0 — installed |
| MCP servers configured | sqlite, fetch, playwright, filesystem, exa ✓ — all connected. financial-datasets configured but needs paid plan for API access. |
| EXA_API_KEY | Set permanently via setx — Exa MCP news search |
| FINANCIAL_DATASETS_API_KEY | Set permanently via setx — free tier is 403 on all endpoints; paid plan needed |

### Note on pyfolio
The original `pyfolio` package is broken on Python 3.12+. Use `pyfolio-reloaded` instead — same API, maintained fork.
