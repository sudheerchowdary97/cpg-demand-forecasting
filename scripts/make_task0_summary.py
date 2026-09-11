"""Generate the Task 0 summary workbook — PepsiCo client-styled.

Produces ``docs/Task0_Summary.xlsx`` with audience-specific sheets (business +
developer), PepsiCo-themed styling, and a product-portfolio sheet with generated
brand icons.

See ``scripts/branding.py`` for the important trademark disclaimer: this is an
independent learning project and uses stylized, ORIGINAL brand representations,
not official PepsiCo assets.

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

# ---- Shared styling (PepsiCo palette) -------------------------------------
TITLE_FONT = Font(bold=True, size=14, color=B.WHITE)
HEADER_FONT = Font(bold=True, size=11, color=B.WHITE)
HEADER_FILL = PatternFill("solid", fgColor=B.PEPSI_BLUE)
TITLE_FILL = PatternFill("solid", fgColor=B.PEPSI_BLUE_DARK)
WRAP = Alignment(wrap_text=True, vertical="top")
WRAP_CENTER = Alignment(wrap_text=True, vertical="center", horizontal="center")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
DONE_FILL = PatternFill("solid", fgColor=B.DONE_GREEN)

ICONS: dict[str, Path] = {}


def _xl_image(path: Path, px: int) -> XLImage:
    img = XLImage(str(path))
    img.width = px
    img.height = px
    return img


def _branded_title(ws: Worksheet, title: str, span: int) -> None:
    """Row 1 = PepsiCo-blue title bar with the tricolor roundel accent."""
    for col in range(1, span + 1):
        ws.cell(row=1, column=col).fill = TITLE_FILL
    ws.merge_cells(start_row=1, start_column=2, end_row=1, end_column=span)
    cell = ws.cell(row=1, column=2, value=title)
    cell.font = TITLE_FONT
    cell.alignment = Alignment(vertical="center", horizontal="left", indent=1)
    ws.row_dimensions[1].height = 30
    ws.add_image(_xl_image(ICONS["_roundel"], 26), "A1")


def _write_table(
    ws: Worksheet,
    title: str,
    headers: list[str],
    rows: list[list[str]],
    widths: list[int],
) -> None:
    """Titled, PepsiCo-styled table: row 1 title bar, row 2 header, row 3+ data."""
    _branded_title(ws, title, len(headers))

    for col, (head, width) in enumerate(zip(headers, widths, strict=True), start=1):
        cell = ws.cell(row=2, column=col, value=head)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = WRAP_CENTER
        cell.border = BORDER
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.row_dimensions[2].height = 22

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


# ---- Sheet content --------------------------------------------------------
def build() -> Workbook:
    wb = Workbook()

    # 1) Overview -----------------------------------------------------------
    ws = wb.active
    ws.title = "Overview"
    _write_table(
        ws,
        "PepsiCo Demand Forecasting — Project Overview",
        ["Field", "Detail"],
        [
            ["Client (illustrative)", "PepsiCo, Inc. — global food & beverage leader"],
            ["Project", "End-to-end SKU-level demand forecasting with time-series deep learning"],
            [
                "Purpose",
                "Learning project: master the full deep-learning ladder end to end (data -> deployment)",
            ],
            [
                "Portfolio in scope",
                "Beverages (Pepsi, Mtn Dew, Gatorade, Tropicana, Aquafina, 7UP) + Frito-Lay snacks (Lay's, Doritos, Cheetos, Ruffles) + Quaker foods",
            ],
            [
                "Data (proxy)",
                "M5 Forecasting - Accuracy (Walmart, Kaggle) used as a realistic stand-in for PepsiCo's SKU x store x day sales; a real engagement would use PepsiCo shipment / POS / Nielsen data",
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
                "Independent learning project; NOT affiliated with or endorsed by PepsiCo. Brand icons/colors are stylized, original representations — not official assets. All trademarks belong to their owners.",
            ],
        ],
        [24, 95],
    )

    # 2) Business summary ---------------------------------------------------
    ws = wb.create_sheet("Business Summary")
    _write_table(
        ws,
        "Business View — PepsiCo Objectives, Pain Points & Solution",
        ["Topic", "Detail", "Why it matters to PepsiCo"],
        [
            [
                "Business objective",
                "Forecast demand accurately at store level so the right pack is on the right shelf at the right time across Pepsi, Frito-Lay and Quaker.",
                "Directly drives net revenue, availability, and working capital.",
            ],
            [
                "Scale of the problem",
                "~$91B annual net revenue, 20+ billion-dollar brands, products sold in 200+ countries/territories.",
                "Tiny % accuracy gains compound into very large absolute value.",
            ],
            [
                "Pain point 1 — Stockouts",
                "Empty shelves lose the sale and push shoppers to competitor brands.",
                "Lost sales estimated at ~4% of revenue for typical retailers.",
            ],
            [
                "Pain point 2 — Waste / freshness",
                "Frito-Lay snacks and chilled Tropicana are freshness-critical; overstock becomes stale/expired.",
                "Waste and markdowns directly erode margin.",
            ],
            [
                "Pain point 3 — DSD complexity",
                "Direct-Store-Delivery routes must be stocked per store per day without over/under-loading trucks.",
                "Route efficiency and service level depend on the forecast.",
            ],
            [
                "Pain point 4 — Promotions & events",
                "Promos, price changes, holidays, sports events and heatwaves cause large demand swings.",
                "Missed spikes = stockouts; over-forecast = waste.",
            ],
            [
                "Pain point 5 — New product launches",
                "Constant limited-time flavors and NPI have little/no history.",
                "Cold-start forecasting is hard and high-stakes.",
            ],
            [
                "Proposed solution",
                "Deep-learning time-series models forecasting SKU x store x day demand with uncertainty, feeding replenishment, DSD, production and promo planning.",
                "Captures seasonality, promotions, weather and cross-brand patterns automatically.",
            ],
            [
                "Business value",
                "Fewer stockouts, less waste, higher service levels, tighter DSD, and data-driven, auditable planning.",
                "Improves both top line (sales) and bottom line (margin).",
            ],
            [
                "Pathway to impact",
                "Forecasts -> safety stock & replenishment -> DSD route loads -> production plans -> promo planning; served via a live API + planner dashboard.",
                "Turns model output into daily operational decisions.",
            ],
            [
                "Task 0 in business terms",
                "Built a trustworthy, reproducible, vendor-neutral foundation before any modeling.",
                "Ensures results are credible and auditable — reduces project risk.",
            ],
        ],
        [24, 64, 42],
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
                "Create a reproducible, industry-standard project skeleton before any DL code.",
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
                "Reusable PepsiCo-styled icon/theme module powering all task workbooks.",
                "scripts/branding.py (Pillow)",
            ],
            [
                "Data / model hygiene",
                "data/ and models/ git-ignored (DVC-tracked later); folders kept via .gitkeep.",
                ".gitignore + DVC intent",
            ],
            [
                "Version control",
                "Standalone git repo, personal (non-Apple) identity, pushed to GitHub.",
                "git + GitHub CLI",
            ],
            [
                "Docs",
                "README with full Task 0-18 roadmap; MIT license; this branded summary workbook.",
                "README.md, LICENSE",
            ],
            [
                "Deliberately NOT done",
                "No neural networks yet — Task 0 is tooling only.",
                "DL starts at Task 5",
            ],
        ],
        [22, 62, 40],
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
                "Data/model separation",
                "Keeping large data & artifacts out of git (DVC later).",
                "Keeps repo small; data versioned properly.",
            ],
            [
                "Reproducibility",
                "Pinned Python + pinned deps + scripted setup.",
                "Anyone can rebuild the exact environment.",
            ],
        ],
        [24, 55, 45],
    )

    # 5) PepsiCo product portfolio -----------------------------------------
    ws = wb.create_sheet("PepsiCo Portfolio")
    _branded_title(ws, "PepsiCo Portfolio in Scope — Brands & Forecasting Relevance", 4)
    headers = ["Icon", "Brand", "Category", "Forecasting relevance"]
    for col, (head, width) in enumerate(zip(headers, [8, 22, 26, 60], strict=True), start=1):
        cell = ws.cell(row=2, column=col, value=head)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = WRAP_CENTER
        cell.border = BORDER
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.row_dimensions[2].height = 22

    for i, (name, cat, _color, _initials, _tcolor, emoji, note) in enumerate(B.BRANDS):
        r = 3 + i
        ws.row_dimensions[r].height = 34
        ws.add_image(_xl_image(ICONS[name], 30), f"A{r}")
        for c, value in enumerate(["", f"{emoji} {name}", cat, note], start=1):
            cell = ws.cell(row=r, column=c, value=value)
            cell.alignment = WRAP
            cell.border = BORDER
    ws.freeze_panes = "A3"
    ws.sheet_view.showGridLines = False

    # 6) Roadmap 0-18 -------------------------------------------------------
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
            "windowing, embeddings",
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
            "self-attention, interpretability",
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
            "mixed precision, checkpointing",
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
        ["16", "Monitoring, drift & retraining", "distribution shift", "observability", "Planned"],
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
        "Full Roadmap — Task 0 to 18",
        ["Task", "Name", "Core DL concept", "Engineering skill", "Status"],
        roadmap,
        [7, 38, 32, 34, 12],
    )

    # 7) Task 0 checklist ---------------------------------------------------
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
            ["PepsiCo-styled branding module (icons/theme)", "Done ✅"],
            ["Business + developer summary workbook (this file)", "Done ✅"],
        ],
        [65, 14],
    )

    return wb


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
