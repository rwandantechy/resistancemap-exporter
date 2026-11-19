from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

from config import OUTPUT_DIR

NAVY = "1B365D"
LIGHT_BLUE = "D9EAF7"
WHITE = "FFFFFF"
GRID = "D9E2F3"


def autofit(ws, min_width: int = 12, max_width: int = 45) -> None:
    for column_cells in ws.columns:
        column_letter = get_column_letter(column_cells[0].column)
        width = min_width
        for cell in column_cells:
            if cell.value is not None:
                width = max(width, min(max_width, len(str(cell.value).replace("\n", " ")) + 2))
        ws.column_dimensions[column_letter].width = width


def add_dataframe_sheet(wb, title: str, df: pd.DataFrame, freeze_row: int = 1) -> None:
    ws = wb.create_sheet(title)
    ws.append(list(df.columns))
    for row in df.itertuples(index=False, name=None):
        ws.append([None if pd.isna(value) else value for value in row])

    ws.freeze_panes = f"A{freeze_row + 1}"
    ws.auto_filter.ref = ws.dimensions
    header_fill = PatternFill("solid", fgColor=NAVY)
    thin = Side(style="thin", color=GRID)
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = Font(bold=True, color=WHITE)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = Border(bottom=thin)

    for row_index in range(2, ws.max_row + 1):
        if row_index % 2 == 0:
            fill = PatternFill("solid", fgColor="F5F8FC")
            for cell in ws[row_index]:
                cell.fill = fill
        for cell in ws[row_index]:
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    for column_name in ("Resistance Percentage",):
        if column_name in df.columns:
            col = df.columns.get_loc(column_name) + 1
            for cell in ws.iter_cols(min_col=col, max_col=col, min_row=2):
                for item in cell:
                    item.number_format = "0.0"

    for column_name in ("Consumption Rate",):
        if column_name in df.columns:
            col = df.columns.get_loc(column_name) + 1
            for row in ws.iter_rows(min_row=2, min_col=col, max_col=col):
                row[0].number_format = "0.000"

    for column_name in ("Year", "Latest Resistance Year", "Latest Use Year", "Isolates Tested"):
        if column_name in df.columns:
            col = df.columns.get_loc(column_name) + 1
            for row in ws.iter_rows(min_row=2, min_col=col, max_col=col):
                row[0].number_format = "0"

    autofit(ws)


def build_overview_sheet(wb, df_overview: pd.DataFrame, extracted_at: datetime) -> None:
    ws = wb.create_sheet("Overview & Availability")
    ws.append(["ResistanceMap Country Availability"])
    ws.append(["Yes = the directory indicates data are available. No = no data are indicated. Not Reported = no numeric value was available in the source payload."])
    ws.append([f"Extracted: {extracted_at.isoformat(timespec='seconds')}"])
    ws.append([])
    ws.append(list(df_overview.columns))

    header_fill = PatternFill("solid", fgColor=NAVY)
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = Font(bold=True, color=WHITE)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max(7, len(df_overview.columns)))
    ws["A2"].alignment = Alignment(wrap_text=True)
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=max(7, len(df_overview.columns)))
    ws["A3"].alignment = Alignment(wrap_text=True)

    for cell in ws[5]:
        cell.fill = header_fill
        cell.font = Font(bold=True, color=WHITE)
        cell.alignment = Alignment(wrap_text=True)
    for row in df_overview.itertuples(index=False, name=None):
        ws.append([None if pd.isna(value) else value for value in row])

    ws.freeze_panes = "A6"
    ws.auto_filter.ref = ws.dimensions
    for row_index in range(6, ws.max_row + 1):
        if row_index % 2 == 0:
            for cell in ws[row_index]:
                cell.fill = PatternFill("solid", fgColor="F5F8FC")
    autofit(ws)


def build_notes_sheet(wb, extracted_at: datetime) -> None:
    ws = wb.create_sheet("Data Dictionary & Notes")
    ws.append(["ResistanceMap Data Dictionary & Notes"])
    ws.append(["Source", "One Health Trust - ResistanceMap"])
    ws.append(["Base URL", "https://resistancemap.onehealthtrust.org"])
    ws.append(["Extraction timestamp", extracted_at.isoformat(timespec="seconds")])
    ws.append(["Timezone", "UTC"])
    ws.append(["Resistance scale", "Percentages are stored on the site-reported 0-100 scale"])
    ws.append(["Missing values", "No source value: blank/NaN; not imputed or converted to zero"])
    ws.append(["Antibiotic-use unit", "Taken from the source request or payload; blank when not verified"])
    ws.append([])
    ws.append(["Tab", "Column", "Description", "Unit / Format"])

    dictionary = [
        ("Overview & Availability", "Region", "ResistanceMap world region", "Text"),
        ("Overview & Availability", "Country", "Country or reporting area name", "Text"),
        ("Overview & Availability", "Resistance Data Available", "Directory availability indicator", "Yes / No"),
        ("Overview & Availability", "Use Data Available", "Directory availability indicator", "Yes / No"),
        ("Overview & Availability", "Latest Resistance Year", "Latest resistance year found in cached payload", "Integer year"),
        ("Overview & Availability", "Latest Use Year", "Latest use year found in cached payload", "Integer year"),
        ("Antibiotic Resistance", "Resistance Percentage", "Resistance rate reported by ResistanceMap", "Percent, 0-100"),
        ("Antibiotic Resistance", "Isolates Tested", "Number of isolates tested", "Count"),
        ("Antibiotic Resistance", "Pathogen", "Target pathogen / organism", "Text"),
        ("Antibiotic Resistance", "Antibiotic", "Antibiotic or antibiotic class", "Text"),
        ("Antibiotic Use", "Consumption Rate", "Reported antibiotic consumption value", "Numeric"),
        ("Antibiotic Use", "Unit", "Measurement unit from the source request or payload", "Source-provided; blank if unverified"),
        ("Antibiotic Use", "Antibiotic Class / Category", "Antibiotic category", "Text"),
        ("Antibiotic Use", "Data Source", "Sector or source attribution from payload", "Text"),
    ]
    for row in dictionary:
        ws.append(row)

    ws.freeze_panes = "A10"
    for cell in ws[10]:
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.font = Font(bold=True, color=WHITE)
    autofit(ws)


def export_workbook(df_overview: pd.DataFrame, df_resistance: pd.DataFrame, df_use: pd.DataFrame, extracted_at: datetime) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    date_label = extracted_at.date().isoformat()
    output_path = OUTPUT_DIR / f"ResistanceMap_Country_Data_{date_label}.xlsx"

    wb = Workbook()
    wb.remove(wb.active)
    build_overview_sheet(wb, df_overview, extracted_at)
    add_dataframe_sheet(wb, "Antibiotic Resistance", df_resistance)
    add_dataframe_sheet(wb, "Antibiotic Use", df_use)
    build_notes_sheet(wb, extracted_at)
    wb.save(output_path)
    return output_path
