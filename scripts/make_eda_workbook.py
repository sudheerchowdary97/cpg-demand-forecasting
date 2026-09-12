"""Generate docs/EDA.xlsx — comprehensive, market-wise EDA tables.

PepsiCo-styled (reuses scripts/branding.py). Sheets:
  - Overview            : dataset stats + market summary
  - <one per market>    : channel share, category split, weekday & monthly
                          seasonality, uplift, top brands, intermittency
  - Cross-market sheets : channel mix, uplift-by-market, weather-by-market

Run with:  make eda   (or)   python scripts/make_eda_workbook.py
"""

from __future__ import annotations

from pathlib import Path

import branding as B
import pandas as pd
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from cpg_forecast import eda

OUT_PATH = Path(__file__).resolve().parents[1] / "docs" / "EDA.xlsx"

TITLE_FONT = Font(bold=True, size=14, color=B.PEPSI_BLUE)
SUB_FONT = Font(bold=True, size=11, color=B.PEPSI_BLUE_DARK)
HEADER_FONT = Font(bold=True, size=10, color=B.WHITE)
HEADER_FILL = PatternFill("solid", fgColor=B.PEPSI_BLUE)
TITLE_FILL = PatternFill("solid", fgColor=B.WHITE)
WRAP = Alignment(wrap_text=True, vertical="top")
WRAP_CENTER = Alignment(wrap_text=True, vertical="center", horizontal="center")
THIN = Side(style="thin", color="D6DEE8")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def _logo(height: int) -> XLImage | None:
    if not B.LOGO_SMALL.exists():
        return None
    img = XLImage(str(B.LOGO_SMALL))
    w, h = B.image_size(B.LOGO_SMALL)
    img.width = max(1, round(height * w / h))
    img.height = height
    return img


def _title(ws: Worksheet, title: str, span: int = 5) -> None:
    for col in range(1, span + 1):
        ws.cell(row=1, column=col).fill = TITLE_FILL
    ws.merge_cells(start_row=1, start_column=2, end_row=1, end_column=span)
    c = ws.cell(row=1, column=2, value=title)
    c.font = TITLE_FONT
    c.alignment = Alignment(vertical="center", horizontal="left", indent=1)
    ws.row_dimensions[1].height = 34
    logo = _logo(30)
    if logo is not None:
        ws.add_image(logo, "A1")
    ws.sheet_view.showGridLines = False


def _block(ws: Worksheet, start: int, subtitle: str, df: pd.DataFrame, widths: list[int]) -> int:
    """Write a subtitle + a DataFrame table starting at row `start`; return next free row."""
    ws.cell(row=start, column=1, value=subtitle).font = SUB_FONT
    hdr = start + 1
    for j, (col, width) in enumerate(zip(df.columns, widths, strict=False), start=1):
        cell = ws.cell(row=hdr, column=j, value=str(col))
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = WRAP_CENTER
        cell.border = BORDER
        if width:
            ws.column_dimensions[get_column_letter(j)].width = width
    for r in range(len(df)):
        for j, col in enumerate(df.columns, start=1):
            val = df.iloc[r][col]
            val = val.item() if hasattr(val, "item") else val
            cell = ws.cell(row=hdr + 1 + r, column=j, value=val)
            cell.alignment = WRAP
            cell.border = BORDER
    return hdr + 1 + len(df) + 2  # blank line before next block


def build() -> Workbook:
    df = eda.load_data()
    wb = Workbook()

    # Overview -------------------------------------------------------------
    ws = wb.active
    ws.title = "Overview"
    _title(ws, "PepsiCo Demand — EDA (market-wise)", span=8)
    ws.cell(
        row=2,
        column=1,
        value="Synthetic dataset. Per-market sheets follow; cross-market comparisons at the end.",
    ).font = Font(italic=True, color="808080")
    _block(ws, 4, "Market summary", eda.market_summary(df), [12, 12, 14, 12, 10, 10, 10, 10])

    # One sheet per market -------------------------------------------------
    for market in df["market"].unique():
        ws = wb.create_sheet(market[:28])
        _title(ws, f"EDA — {market}", span=6)
        row = 3
        for subtitle, table in eda.per_market_tables(df, market).items():
            row = _block(ws, row, subtitle, table, [26, 14, 12, 12])

    # Cross-market comparison sheets --------------------------------------
    for name, table in eda.cross_market_tables(df).items():
        ws = wb.create_sheet(name[:28])
        _title(ws, f"Cross-market — {name}", span=max(len(table.columns), 3))
        _block(ws, 3, name, table, [18] + [13] * (len(table.columns) - 1))

    return wb


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    wb = build()
    wb.save(OUT_PATH)
    print(
        f"Wrote {OUT_PATH.relative_to(OUT_PATH.parents[1])} with {len(wb.sheetnames)} sheets: {wb.sheetnames}"
    )


if __name__ == "__main__":
    main()
