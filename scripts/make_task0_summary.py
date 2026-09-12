"""Generate the Task 0 summary workbook — PepsiCo client-styled, multi-geo scope.

Produces ``docs/Task0_Summary.xlsx``: audience-specific sheets (business +
developer), PepsiCo theming with the real logo, a global brand matrix across
geographies, a per-brand portfolio with icons, and the portfolio infographic.

See ``scripts/branding.py`` for the trademark disclaimer.

Run with:  make summary   (or)   python scripts/make_task0_summary.py
"""

from __future__ import annotations

from pathlib import Path

import branding as B
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

OUT_PATH = Path(__file__).resolve().parents[1] / "docs" / "Task0_Summary.xlsx"

# ---- Styling --------------------------------------------------------------
TITLE_FONT = Font(bold=True, size=14, color=B.PEPSI_BLUE)  # navy on white bar
HEADER_FONT = Font(bold=True, size=11, color=B.WHITE)
HEADER_FILL = PatternFill("solid", fgColor=B.PEPSI_BLUE)
TITLE_FILL = PatternFill("solid", fgColor=B.WHITE)
WRAP = Alignment(wrap_text=True, vertical="top")
WRAP_CENTER = Alignment(wrap_text=True, vertical="center", horizontal="center")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
DONE_FILL = PatternFill("solid", fgColor=B.DONE_GREEN)

ICONS: dict[str, Path] = {}


def _xl_image(path: Path, height: int, width: int | None = None) -> XLImage:
    img = XLImage(str(path))
    if width is None:
        w, h = B.image_size(path)
        width = max(1, round(height * w / h))
    img.width = width
    img.height = height
    return img


def _branded_title(ws: Worksheet, title: str, span: int) -> None:
    """Row 1 = white title bar with the real PepsiCo logo + navy title text."""
    span = max(span, 2)  # need col 1 for the logo + col 2+ for the title
    for col in range(1, span + 1):
        ws.cell(row=1, column=col).fill = TITLE_FILL
    ws.merge_cells(start_row=1, start_column=2, end_row=1, end_column=span)
    cell = ws.cell(row=1, column=2, value=title)
    cell.font = TITLE_FONT
    cell.alignment = Alignment(vertical="center", horizontal="left", indent=1)
    ws.row_dimensions[1].height = 34
    if "_logo" in ICONS:
        ws.add_image(_xl_image(ICONS["_logo"], height=30), "A1")


def _headers(ws: Worksheet, headers: list[str], widths: list[int]) -> None:
    for col, (head, width) in enumerate(zip(headers, widths, strict=True), start=1):
        cell = ws.cell(row=2, column=col, value=head)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = WRAP_CENTER
        cell.border = BORDER
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.row_dimensions[2].height = 22


def _write_table(
    ws: Worksheet,
    title: str,
    headers: list[str],
    rows: list[list[str]],
    widths: list[int],
) -> None:
    _branded_title(ws, title, len(headers))
    _headers(ws, headers, widths)
    for r, row in enumerate(rows, start=3):
        for c, value in enumerate(row, start=1):
            cell = ws.cell(row=r, column=c, value=value)
            cell.alignment = WRAP
            cell.border = BORDER
        if "Status" in headers:
            status_idx = headers.index("Status")
            if str(row[status_idx]).lower().startswith(("done", "✅")):
                for cc in range(1, len(headers) + 1):
                    ws.cell(row=r, column=cc).fill = DONE_FILL
    ws.freeze_panes = "A3"
    ws.sheet_view.showGridLines = False


# ---- Sheets ---------------------------------------------------------------
def build() -> Workbook:
    wb = Workbook()

    n_geos = len(B.GEOS)
    n_brands = len(B.BRAND_INFO)

    # 1) Overview -----------------------------------------------------------
    ws = wb.active
    ws.title = "Overview"
    _write_table(
        ws,
        "PepsiCo Global Demand Forecasting — Project Overview",
        ["Field", "Detail"],
        [
            ["Client (illustrative)", "PepsiCo, Inc. — global food & beverage leader"],
            ["Project", "End-to-end SKU-level demand forecasting with time-series deep learning"],
            [
                "Purpose",
                "Learning project: master the full deep-learning ladder end to end (data -> deployment)",
            ],
            [
                "Scope",
                f"ALL PepsiCo food & beverage brands across geographies. Illustrative markets: {', '.join(B.GEOS)} ({n_geos} shown, {n_brands} distinct brands) — extensible to PepsiCo's 200+ markets.",
            ],
            [
                "Scaling approach",
                "One GLOBAL model with market x brand x category x store embeddings; transfers learning across geos and cold-starts new-market / new-product launches.",
            ],
            [
                "Data (proxy)",
                "M5 Forecasting - Accuracy (Walmart, Kaggle) as a realistic stand-in for PepsiCo's SKU x store x day sales; a real engagement would use PepsiCo shipment / POS / Nielsen data per market.",
            ],
            [
                "Forecast target",
                "Units sold per SKU x store x day, 28-day horizon, with uncertainty intervals",
            ],
            ["Primary metric", "WRMSSE (M5 metric) + MAE / RMSE / pinball loss"],
            [
                "Repository",
                "github.com/sudheerchowdary97/cpg-demand-forecasting (public, personal)",
            ],
            [
                "Guardrails",
                "No Apple ecosystem; heavy training on cloud GPU only; Mac used for light dev",
            ],
            [
                "This workbook",
                "Summary of Task 0 (Foundations & Environment) — business + developer views",
            ],
            [
                "DISCLAIMER",
                "Independent learning project; NOT affiliated with or endorsed by PepsiCo. Generated brand tiles are stylized originals; logo/infographic are user-supplied. All trademarks belong to their owners.",
            ],
        ],
        [24, 100],
    )

    # 2) Business summary ---------------------------------------------------
    ws = wb.create_sheet("Business Summary")
    _write_table(
        ws,
        "Business View — Scaling PepsiCo Forecasting Across Geographies",
        ["Topic", "Detail", "Why it matters to PepsiCo"],
        [
            [
                "Business objective",
                "Forecast demand accurately at store level for every food & beverage brand in every market, so the right pack is on the right shelf at the right time.",
                "Directly drives net revenue, availability, and working capital worldwide.",
            ],
            [
                "Scale of the problem",
                "~$91B net revenue, 20+ billion-dollar brands, products in 200+ countries/territories; thousands of SKUs x thousands of stores x many markets.",
                "Tiny % accuracy gains compound into very large absolute value.",
            ],
            [
                "Why multi-geo is hard",
                "Hemisphere-flipped seasons (Australia summer = Dec-Feb), local festivals (Diwali, Ramadan/Eid, Christmas), local brands (Walkers, Smith's, Kurkure, Sting), currencies, prices and weather.",
                "A single generic model fails; forecasts must be locally aware.",
            ],
            [
                "Local brand portfolios",
                "Each market carries a tailored mix (e.g., UK: Walkers + Lipton; AU: Smith's + Solo + Sobe; India/Pakistan: Kurkure + Sting).",
                "The model must handle market-specific catalogs, not one global list.",
            ],
            [
                "Pain point — Stockouts",
                "Empty shelves lose the sale and push shoppers to competitors.",
                "Lost sales estimated at ~4% of revenue for typical retailers.",
            ],
            [
                "Pain point — Waste / freshness",
                "Snacks and chilled juices are freshness-critical; overstock becomes stale/expired.",
                "Waste and markdowns directly erode margin.",
            ],
            [
                "Pain point — DSD complexity",
                "Direct-Store-Delivery routes must be stocked per store per day across many markets.",
                "Route efficiency and service level depend on the forecast.",
            ],
            [
                "Pain point — Promotions & events",
                "Promos, price changes, holidays, sports events and heatwaves cause large, market-specific swings.",
                "Missed spikes = stockouts; over-forecast = waste.",
            ],
            [
                "Pain point — New launches",
                "Constant limited-time flavors, new products, and new-market entries have little/no history.",
                "Cold-start forecasting is hard and high-stakes.",
            ],
            [
                "Proposed solution",
                "One GLOBAL deep-learning model with market/brand/category embeddings, forecasting SKU x store x day demand with uncertainty, feeding replenishment, DSD, production and promo planning.",
                "Learns shared patterns across markets while respecting local behavior; scales to new geos.",
            ],
            [
                "Business value",
                "Fewer stockouts, less waste, higher service levels, faster new-market rollout, and consistent, auditable planning globally.",
                "Improves both top line (sales) and bottom line (margin) at scale.",
            ],
            [
                "Task 0 in business terms",
                "Built a trustworthy, reproducible, vendor-neutral foundation designed to scale across brands and markets.",
                "De-risks the global rollout before any modeling.",
            ],
        ],
        [22, 66, 42],
    )

    # 3) Developer summary --------------------------------------------------
    ws = wb.create_sheet("Developer Summary")
    _write_table(
        ws,
        "Developer View — What Was Built in Task 0",
        ["Area", "What was done", "Tool / Detail"],
        [
            [
                "Objective",
                "Create a reproducible, industry-standard project skeleton that will scale to multi-geo, multi-brand data.",
                "Foundations first",
            ],
            [
                "Package layout",
                "src/ layout package 'cpg_forecast' installed as an editable package.",
                "src/cpg_forecast/",
            ],
            [
                "Environment",
                "Isolated virtual environment on Python 3.12 (3.14 removed — ML wheels unsupported).",
                "Python 3.12.13, .venv",
            ],
            [
                "Dependencies",
                "Single source of truth for deps + tool config; light core, DL deps deferred.",
                "pyproject.toml (dev/docs extras)",
            ],
            [
                "Code quality",
                "Auto-formatting + linting enforced automatically on every commit.",
                "ruff + black via pre-commit",
            ],
            [
                "Testing",
                "Smoke tests prove the package imports and toolchain runs green.",
                "pytest (2 passed)",
            ],
            [
                "Automation",
                "One-command workflows for setup, lint, format, test, summary.",
                "Makefile",
            ],
            [
                "Branding",
                "Reusable module: real PepsiCo logo + generated brand icons + geo/brand data model driving all task workbooks.",
                "scripts/branding.py (Pillow)",
            ],
            [
                "Scale-ready data model",
                "Brand/geo master data (kind, market coverage) encoded now to seed market x brand x category features later.",
                "BRAND_INFO / GEOS",
            ],
            [
                "Version control",
                "Standalone git repo, personal (non-Apple) identity, pushed to GitHub.",
                "git + GitHub CLI",
            ],
            [
                "Docs",
                "README roadmap; MIT license; this branded, multi-geo summary workbook.",
                "README.md, LICENSE",
            ],
            [
                "Deliberately NOT done",
                "No neural networks yet — Task 0 is tooling only.",
                "DL starts at Task 5",
            ],
        ],
        [22, 64, 38],
    )

    # 4) Concepts covered ---------------------------------------------------
    ws = wb.create_sheet("Concepts Covered")
    _write_table(
        ws,
        "Concepts & Developer Skills Covered in Task 0",
        ["Concept / Skill", "What it is", "Why it matters"],
        [
            [
                "src/ layout",
                "Keeping importable code under src/ separate from tests/notebooks.",
                "Prevents import bugs; industry-standard packaging.",
            ],
            [
                "Editable install",
                "Installing the project with `pip install -e` so code changes apply instantly.",
                "Real package imports without path hacks.",
            ],
            [
                "Virtual environment",
                "An isolated Python env per project.",
                "Reproducibility; no dependency clashes across projects.",
            ],
            [
                "pyproject.toml",
                "Single file for dependencies + tool config (black, ruff, pytest).",
                "One source of truth; modern Python standard.",
            ],
            [
                "Linting (ruff)",
                "Static checks for errors, bugs, unused imports, import order.",
                "Catches issues before runtime.",
            ],
            [
                "Formatting (black)",
                "Deterministic, opinionated code formatting.",
                "Consistent style; zero style debates.",
            ],
            [
                "pre-commit hooks",
                "Checks that run automatically before each commit.",
                "Bad code never enters git history.",
            ],
            [
                "Testing (pytest)",
                "Automated tests, starting with smoke tests.",
                "Confidence that the base works before building on it.",
            ],
            [
                "Makefile",
                "Named shortcuts for common commands.",
                "One-command, self-documenting workflows.",
            ],
            [
                "git + remote",
                "Version control with a GitHub remote.",
                "History, backup, collaboration, portfolio.",
            ],
            [
                "Master data modeling",
                "Encoding brand/geo attributes (kind, market coverage) up front.",
                "Seeds the embeddings that let one model scale across geos.",
            ],
            [
                "Reproducibility",
                "Pinned Python + pinned deps + scripted setup + regenerable assets.",
                "Anyone can rebuild the exact environment and docs.",
            ],
        ],
        [24, 55, 45],
    )

    # 5) Global brand matrix ------------------------------------------------
    ws = wb.create_sheet("Global Brand Matrix")
    _branded_title(ws, "Global Brand Matrix — Brands by Market (Food + Beverage)", 3)
    _headers(ws, ["Market", "Food Brands (5)", "Beverage Brands (5)"], [22, 52, 52])
    r = 3
    for geo, (flag, tagline, food, bev) in B.GEOS.items():
        ws.cell(row=r, column=1, value=f"{flag} {geo}\n{tagline}").alignment = WRAP
        ws.cell(row=r, column=2, value=", ".join(food)).alignment = WRAP
        ws.cell(row=r, column=3, value=", ".join(bev)).alignment = WRAP
        for c in range(1, 4):
            ws.cell(row=r, column=c).border = BORDER
        ws.row_dimensions[r].height = 34
        r += 1
    note = ws.cell(
        row=r,
        column=1,
        value="Illustrative 4 of PepsiCo's 200+ markets. One global model scales to new markets via market/brand/category embeddings + hierarchical forecasting.",
    )
    note.alignment = WRAP
    note.font = Font(italic=True, color=B.PEPSI_BLUE)
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
    ws.row_dimensions[r].height = 30
    ws.freeze_panes = "A3"
    ws.sheet_view.showGridLines = False

    # 6) Brand portfolio (with icons) --------------------------------------
    ws = wb.create_sheet("Brand Portfolio")
    _branded_title(ws, f"Brand Portfolio in Scope — {n_brands} Brands Across Markets", 5)
    _headers(ws, ["Icon", "Brand", "Type", "Category", "Markets in scope"], [8, 20, 12, 24, 34])
    r = 3
    for name, (kind, _color, _initials, _tcolor, emoji) in B.BRAND_INFO.items():
        ws.row_dimensions[r].height = 34
        if name in ICONS:
            ws.add_image(_xl_image(ICONS[name], height=30, width=30), f"A{r}")
        markets = ", ".join(B.markets_for(name))
        for c, value in enumerate(["", f"{emoji} {name}", kind, _category(name), markets], start=1):
            cell = ws.cell(row=r, column=c, value=value)
            cell.alignment = WRAP
            cell.border = BORDER
        r += 1
    ws.freeze_panes = "A3"
    ws.sheet_view.showGridLines = False

    # 7) Global portfolio map (infographic) --------------------------------
    ws = wb.create_sheet("Global Portfolio Map")
    _branded_title(ws, "Loved Brands. Local Markets. — Global Portfolio Map", 1)
    cap = ws.cell(
        row=2,
        column=1,
        value="Source: user-supplied PepsiCo portfolio infographic (docs/brands_icons/Brands_Geos.png).",
    )
    cap.font = Font(italic=True, size=9, color="808080")
    ws.column_dimensions["A"].width = 20
    if "_infographic" in ICONS:
        w, h = B.image_size(ICONS["_infographic"])
        disp_w = min(1040, w)
        img = _xl_image(ICONS["_infographic"], height=round(disp_w * h / w), width=disp_w)
        ws.add_image(img, "A4")
    ws.sheet_view.showGridLines = False

    # 8) Roadmap 0-18 -------------------------------------------------------
    roadmap = [
        [
            "0",
            "Foundations & environment",
            "— (tooling)",
            "repo layout, venv, linting, tests",
            "Done ✅",
        ],
        [
            "1",
            "Problem framing & data (DVC)",
            "forecast task formulation",
            "data versioning",
            "Next",
        ],
        [
            "2",
            "EDA & time-series understanding",
            "seasonality, stationarity",
            "reproducible notebooks",
            "Planned",
        ],
        [
            "3",
            "Data pipeline & feature engineering",
            "windowing, market/brand embeddings",
            "leakage-free ETL as code",
            "Planned",
        ],
        [
            "4",
            "Classical baselines & eval harness",
            "why baselines matter",
            "WRMSSE, backtesting, tracking",
            "Planned",
        ],
        [
            "5",
            "MLP forecaster",
            "MLPs, backprop, regularization",
            "Lightning training loop",
            "Planned",
        ],
        ["6", "RNN -> LSTM -> GRU", "recurrence, gating", "GPU training discipline", "Planned"],
        [
            "7",
            "Seq2Seq + Attention",
            "attention, multi-horizon",
            "attention visualization",
            "Planned",
        ],
        [
            "8",
            "Temporal Conv Nets (TCN)",
            "dilated causal convolution",
            "architecture ablation",
            "Planned",
        ],
        [
            "9",
            "Transformer / TFT",
            "self-attention, static covariates (geo/brand)",
            "large-model training",
            "Planned",
        ],
        [
            "10",
            "Probabilistic (DeepAR / N-BEATS)",
            "uncertainty, intermittency",
            "calibration",
            "Planned",
        ],
        [
            "11",
            "Tracking, HPO & model selection",
            "HPO, bias/variance",
            "Optuna + MLflow",
            "Planned",
        ],
        [
            "12",
            "Cloud full-scale training",
            "global model across all markets",
            "training-as-code",
            "Planned",
        ],
        [
            "13",
            "Export & optimize (ONNX / quantize)",
            "graph export, quantization",
            "perf benchmarking",
            "Planned",
        ],
        [
            "14",
            "Serving API (FastAPI + Docker)",
            "inference-time preprocessing",
            "API design, containers",
            "Planned",
        ],
        [
            "15",
            "Cloud deploy + CI/CD",
            "production readiness",
            "Cloud Run/Render, GitHub Actions",
            "Planned",
        ],
        [
            "16",
            "Monitoring, drift & retraining",
            "distribution shift per market",
            "observability",
            "Planned",
        ],
        [
            "17",
            "Demo app + LLM insight layer",
            "communicating uncertainty",
            "Streamlit, prompt design",
            "Planned",
        ],
        [
            "18",
            "Docs, presentation & portfolio",
            "synthesis",
            "technical writing, Keynote-HTML",
            "Planned",
        ],
    ]
    ws = wb.create_sheet("Roadmap 0-18")
    _write_table(
        ws,
        "Full Roadmap — Task 0 to 18 (multi-geo, multi-brand)",
        ["Task", "Name", "Core DL concept", "Engineering skill", "Status"],
        roadmap,
        [7, 38, 36, 32, 12],
    )

    # 9) Task 0 checklist ---------------------------------------------------
    ws = wb.create_sheet("Task 0 Checklist")
    _write_table(
        ws,
        "Task 0 — Deliverables Checklist",
        ["Deliverable", "Status"],
        [
            ["src/ layout package (cpg_forecast) installed editable", "Done ✅"],
            ["Python 3.12 virtual environment", "Done ✅"],
            ["pyproject.toml with dev + docs extras", "Done ✅"],
            ["ruff + black wired via pre-commit", "Done ✅"],
            ["Passing smoke tests (pytest)", "Done ✅"],
            ["Makefile (setup/lint/format/test/summary)", "Done ✅"],
            [".gitignore + DVC-ready data/model folders", "Done ✅"],
            ["README with full roadmap + MIT LICENSE", "Done ✅"],
            ["Personal (non-Apple) git identity", "Done ✅"],
            ["Repo created & pushed to personal GitHub", "Done ✅"],
            ["PepsiCo branding: real logo + generated brand icons", "Done ✅"],
            ["Multi-geo, multi-brand scope defined (matrix + portfolio)", "Done ✅"],
            ["Business + developer summary workbook (this file)", "Done ✅"],
        ],
        [65, 14],
    )

    return wb


def _category(name: str) -> str:
    """Human-friendly sub-category for the portfolio sheet."""
    mapping = {
        "Lay's": "Salty snacks (Frito-Lay)",
        "Walkers": "Salty snacks (Frito-Lay)",
        "Smith's": "Salty snacks (Frito-Lay)",
        "Doritos": "Salty snacks (Frito-Lay)",
        "Cheetos": "Salty snacks (Frito-Lay)",
        "Ruffles": "Salty snacks (Frito-Lay)",
        "Red Rock Deli": "Premium salty snacks",
        "Kurkure": "Salty snacks (local)",
        "Quaker": "Foods / oats",
        "Pepsi": "Carbonated soft drinks",
        "Pepsi Max": "Carbonated soft drinks",
        "7UP": "Carbonated soft drinks",
        "Mountain Dew": "Carbonated soft drinks",
        "Solo": "Carbonated soft drinks",
        "Tropicana": "Juices",
        "Lipton": "Ready-to-drink tea",
        "Sobe": "Enhanced / flavored drinks",
        "Gatorade": "Sports drinks",
        "Sting": "Energy drinks",
        "Aquafina": "Bottled water",
    }
    return mapping.get(name, "")


def main() -> None:
    global ICONS
    ICONS = B.generate_all()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    wb = build()
    wb.save(OUT_PATH)
    rel = OUT_PATH.relative_to(OUT_PATH.parents[1])
    print(f"Wrote {rel} with sheets: {wb.sheetnames}")


if __name__ == "__main__":
    main()
