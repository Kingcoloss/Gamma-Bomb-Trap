# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Identity

**Gamma Bomb Trap (GBT)** — Streamlit dashboard for institutional quant analysis of Gold Futures (GC) options using CME data. Combines Gamma Hedging and Block Trading strategies.

## Tech Stack

- Python 3.13 · Streamlit 1.55.0 · Plotly · Pandas · NumPy
- Timezone: Asia/Bangkok (session boundary at 10:00 local)
- Data source: CME options data versioned via GitHub commits

## Architecture — Clean Architecture (4 layers)

```
streamlit_app.py              ← Thin entry point (~200 lines), orchestration only
core/
├── domain/                   ← Pure business logic, ZERO framework dependencies
│   ├── black76.py            ← Black-76 pricing engine (Gamma, Vanna, Volga, Theta)
│   ├── models.py             ← Dataclasses: GexResult, GtbrResult, VannaVolgaGtbrResult
│   └── constants.py          ← Named constants (no magic numbers)
├── use_cases/                ← Application logic, depends only on domain
│   ├── gex_analysis.py       ← calculate_gex_analysis(), get_atm_iv()
│   ├── gtbr.py               ← GTBR + Vanna-Volga adjusted GTBR (Carr & Wu 2020)
│   └── data_helpers.py       ← extract_atm/dte, filter_session_data, session date
├── infrastructure/           ← External services (GitHub API, Streamlit state)
│   ├── github_client.py      ← fetch_github_history(), get_latest_commit_sha()
│   └── session_manager.py    ← SessionManager class (Streamlit session lifecycle)
└── presentation/             ← UI layer (Streamlit + Plotly)
    ├── styles.py             ← CSS injection, styled header builder
    ├── legend.py             ← Thai hover-tooltip legend (8 entries)
    ├── chart_helpers.py      ← Plotly vline helpers (ATM, GEX, GTBR)
    ├── tab_gbt.py            ← Tab 1: GBT Composite Analysis
    ├── tab_intraday.py       ← Tab 2: Intraday Volume (γ-Flow)
    ├── tab_oi.py             ← Tab 3: Open Interest (GEX)
    └── tab_guide.py          ← Tab 4: Thai accordion guide (7 sections)
```

### Dependency Rules

- **domain/** → imports nothing external (pure math + stdlib)
- **use_cases/** → imports from domain/ only
- **infrastructure/** → imports from domain/ and use_cases/
- **presentation/** → imports from all layers
- **streamlit_app.py** → imports from all layers, wires everything together

## Key Domain Concepts

### Black-76 Model (r = 0)

All Greeks use Black-76 (options on futures, no cost-of-carry):

- `d1 = [ln(F/K) + ½σ²T] / (σ√T)`
- `Gamma = N'(d1) / (F · σ · √T)`
- `Vanna = −N'(d1) · d2 / σ`
- `Volga = Vega · (d1 · d2) / σ`

### Net Exposure Conventions

- `Net GEX = Γ × (Call − Put) × F² × 0.01` — directional
- `Net Vanna = Vanna × (Call − Put)` — directional
- `Net Volga = Volga × (Call + Put)` — symmetric

### GEX Flip Detection

1. Filter active strikes only (OI/Volume > 0)
2. Cumulative sum of Net GEX
3. Find ALL zero-crossings via linear interpolation
4. Pick nearest to ATM

### Vanna-Volga Adjusted GTBR (Carr & Wu 2020)

Quadratic in ΔF: `a(ΔF)² + b(ΔF) + c = 0` where a=½Γ, b=Vanna·Δσ, c=θ/365+½Volga·(Δσ)²

## Commands

```bash
# Activate virtualenv (all commands below assume this)
source .virtenv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run streamlit_app.py

# Compile check (fast verification)
python3 -c "import py_compile; py_compile.compile('streamlit_app.py', doraise=True)"

# Run unit tests
# Note: test_black76.py re-implements Black-76 math inline (does NOT import from core/)
python3 test_black76.py

# Verify all module imports (non-Streamlit layers)
python3 -c "
from core.domain.black76 import b76_gamma, b76_vanna, b76_volga
from core.use_cases.gex_analysis import calculate_gex_analysis
from core.use_cases.gtbr import calculate_gamma_theta_breakeven, calculate_vanna_adjusted_gtbr
from core.use_cases.data_helpers import extract_atm, extract_dte
from core.infrastructure.github_client import fetch_github_history
from core.presentation.chart_helpers import add_gex_vlines
print('All imports OK')
"
```

## Secrets

`.streamlit/secrets.toml` (gitignored):

```toml
[github]
access_token = "ghp_..."
data_source_repo = "owner/repo"
```

## Data Format

GitHub repo contains two CSV files committed by CME data pipeline:

- `IntradayData.txt` — intraday option volume snapshots (multiple per day)
- `OIData.txt` — end-of-day open interest (1 snapshot per day)

CSV format: 2-line header then standard CSV. Header line 1 contains ATM price (`vs 3,015.50`) and DTE (`(25.00 DTE)`), parsed by `extract_atm()` and `extract_dte()`.

## Session Date Logic

```
Bangkok time < 10:00 → session_date = yesterday
Bangkok time ≥ 10:00 → session_date = today
```

Staleness: `last_fetch_datetime < session_start_10am` triggers re-fetch. Weekend/holiday fallback: if no commits for session_date, fetch latest available.

## Code Style

- UI text is Thai; code comments mix English/Thai
- Use dataclasses for function return types (GexResult, GtbrResult, etc.)
- Constants in `core/domain/constants.py` — no magic numbers in logic
- All new Greek functions go in `core/domain/black76.py`
- All new analysis use cases go in `core/use_cases/`
- Presentation modules are per-tab — add new tabs as `core/presentation/tab_*.py`

## Known Patterns

- `calculate_gex_analysis()` returns `GexResult` dataclass — access via `.flip`, `.pos_wall`, `.gex_df`, etc.
- `calculate_gamma_theta_breakeven()` returns `GtbrResult` — access via `.lo_daily`, `.hi_daily`, etc.
- `calculate_vanna_adjusted_gtbr()` returns `VannaVolgaGtbrResult` — access via `.lo_daily`, `.shift_daily`, etc.
- `SessionManager` handles all `st.session_state` lifecycle — don't manipulate session state keys directly from tabs
- IV normalization: values > 1.0 are treated as percentages and divided by 100

## Files NOT to Edit

- `.streamlit/secrets.toml` — contains credentials
- `streamlit_app_backup.py` — pre-refactoring backup (reference only)
- `Integration/Github.py` — standalone helper, NOT used by main app
