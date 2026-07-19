"""
nodes/executors/flow/utils.py — Flow Execution Utilities

This file provides helper functions for flow executors.
It includes logic for loading and parsing specific columns from CSV or Excel (.xlsx) files to be used by iterator nodes.
"""
from ..base import *
import csv

def _load_csv_column(path: str, column: str) -> list[str]:
    if path.lower().endswith((".xlsx", ".xls")):
        return _load_excel_column(path, column)
    items: list[str] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if column and column in row:
                items.append(row[column])
            elif not column:
                items.append(next(iter(row.values()), ""))
    return items


def _load_excel_column(path: str, column: str) -> list[str]:
    try:
        import openpyxl  # type: ignore
    except ImportError:
        raise ImportError(
            "openpyxl is required to read Excel files. Install it with: pip install openpyxl"
        )
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    items: list[str] = []
    headers: list[str] = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):  # type: ignore[union-attr]
        if i == 0:
            headers = [str(c) if c is not None else "" for c in row]
            continue
        if column and column in headers:
            val = row[headers.index(column)]
        elif not column and row:
            val = row[0]
        else:
            continue
        items.append(str(val) if val is not None else "")
    wb.close()
    return items
