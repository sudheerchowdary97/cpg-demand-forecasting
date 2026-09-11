"""Generate the Task 0 summary workbook (business- and developer-friendly).

Produces ``docs/Task0_Summary.xlsx`` with separate, audience-specific sheets so a
business stakeholder and a developer can each read what matters to them.

Run with:  make summary   (or)   python scripts/make_task0_summary.py
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

OUT_PATH = Path(__file__).resolve().parents[1] / "docs" / "Task0_Summary.xlsx"

# ---- Shared styling -------------------------------------------------------
TITLE_FONT = Font(bold=True, size=14, color="FFFFFF")
HEADER_FONT = Font(bold=True, size=11, color="FFFFFF")
HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
TITLE_FILL = PatternFill("solid", fgColor="2E75B6")
WRAP = Alignment(wrap_text=True, vertical="top")
WRAP_CENTER = Alignment(wrap_text=True, vertical="center", horizontal="center")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
DONE_FILL = PatternFill("solid", fgColor="E2EFDA")


def _title_row(ws: Worksheet, title: str, span: int) -> None:
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=span)
    cell = ws.cell(row=1, column=1, value=title)
    cell.font = TITLE_FONT
    cell.fill = TITLE_FILL
    cell.alignment = Alignment(vertical="center", horizontal="left", indent=1)
    ws.row_dimensions[1].height = 26


def _write_table(
    ws: Worksheet,
    title: str,
    headers: list[str],
    rows: list[list[str]],
    widths: list[int],
) -> None:
    """Write a titled, styled table starting at row 1 (title) / row 2 (header)."""
    _title_row(ws, title, len(headers))

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
                status_idx = headers.index("Status") + 1
                if c == status_idx and str(value).lower().startswith(("done", "✅")):
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
        "CPG Demand Forecasting — Project Overview",
        ["Field", "Detail"],
        [
            [
                "Project",
                "End-to-end CPG SKU-level demand forecasting with time-series deep learning",
            ],
            ["Domain", "Consumer Packaged Goods (CPG) / retail demand planning"],
            [
                "Purpose",
                "Learning project: master the full deep-learning ladder end to end (data -> deployment)",
            ],
            [
                "Dataset",
                "M5 Forecasting - Accuracy (Walmart, via Kaggle): 42,840 hierarchical daily series",
            ],
            [
                "Forecast target",
                "Units sold per SKU x store x day, 28-day horizon, with uncertainty intervals",
            ],
            ["Primary metric", "WRMSSE (M5 competition metric) + MAE / RMSE / pinball loss"],
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
        ],
        [22, 95],
    )

    # 2) Business summary ---------------------------------------------------
    ws = wb.create_sheet("Business Summary")
    _write_table(
        ws,
        "Business View — Objectives, Pain Points, Solution & Pathway",
        ["Topic", "Detail", "Why it matters"],
        [
            [
                "Business objective",
                "Forecast product demand accurately at store level so the right stock is in the right place at the right time.",
                "Directly drives revenue, availability, and working-capital efficiency.",
            ],
            [
                "Pain point 1 — Stockouts",
                "Running out of a product loses the sale and sends shoppers to competitors.",
                "Lost sales are estimated at ~4% of revenue for typical retailers.",
            ],
            [
                "Pain point 2 — Overstock",
                "Too much stock leads to markdowns, spoilage (perishables), and cash tied up in inventory.",
                "Waste and clearance directly erode margin.",
            ],
            [
                "Pain point 3 — Scale",
                "Manual / spreadsheet forecasting cannot cover thousands of SKUs across many stores.",
                "Human rules do not scale and are inconsistent.",
            ],
            [
                "Pain point 4 — Demand spikes",
                "Promotions, holidays, price changes, and local events cause swings classic methods miss.",
                "Missed spikes = stockouts; over-forecast = waste.",
            ],
            [
                "Proposed solution",
                "Deep-learning time-series models that forecast SKU x store x day demand with uncertainty, feeding replenishment, production, and promo planning.",
                "Captures seasonality, promotions, and cross-series patterns automatically.",
            ],
            [
                "Business value",
                "Fewer stockouts, less waste, higher service levels, and data-driven, auditable planning decisions.",
                "Improves both top line (sales) and bottom line (margin).",
            ],
            [
                "Pathway to impact",
                "Forecasts -> safety-stock & replenishment orders -> production plans -> promo planning; served via a live API + planner dashboard.",
                "Turns model output into day-to-day operational decisions.",
            ],
            [
                "Task 0 in business terms",
                "Built a trustworthy, reproducible, vendor-neutral foundation before any modeling.",
                "Ensures results are credible, auditable, and not locked to any vendor — reduces project risk.",
            ],
        ],
        [24, 62, 45],
    )

    # 3) Developer summary (Task 0) ----------------------------------------
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
                "README with full Task 0-18 roadmap; MIT license; this summary workbook.",
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

    # 4) Concepts & skills covered -----------------------------------------
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

    # 5) Roadmap 0-18 -------------------------------------------------------
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

    # 6) Task 0 checklist ---------------------------------------------------
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
            ["Business + developer summary workbook (this file)", "Done ✅"],
        ],
        [65, 14],
    )

    return wb


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    wb = build()
    wb.save(OUT_PATH)
    print(f"Wrote {OUT_PATH.relative_to(OUT_PATH.parents[1])} with sheets: {wb.sheetnames}")


if __name__ == "__main__":
    main()
