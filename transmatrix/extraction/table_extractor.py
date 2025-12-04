"""
Extractor de tablas de PDFs usando pdfplumber.
"""

import pdfplumber
from pathlib import Path
from typing import Optional

from transmatrix.models.document import Document, Table, TableCell, BBox


class TableExtractor:
    """Extrae tablas de archivos PDF."""

    def __init__(
        self,
        vertical_strategy: str = "lines",
        horizontal_strategy: str = "lines",
        snap_tolerance: int = 3,
        join_tolerance: int = 3,
    ):
        self.table_settings = {
            "vertical_strategy": vertical_strategy,
            "horizontal_strategy": horizontal_strategy,
            "snap_tolerance": snap_tolerance,
            "join_tolerance": join_tolerance,
        }

    def extract_tables_from_pdf(self, pdf_path: str | Path) -> list[list[Table]]:
        pdf_path = Path(pdf_path)
        all_tables = []

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_tables = self._extract_tables_from_page(page)
                all_tables.append(page_tables)

        return all_tables

    def _extract_tables_from_page(self, page: pdfplumber.page.Page) -> list[Table]:
        tables = []
        found_tables = page.find_tables(table_settings=self.table_settings)

        for table_obj in found_tables:
            table = self._convert_table(table_obj, page.height)
            if table and table.cells:
                tables.append(table)

        return tables

    def _convert_table(
        self,
        table_obj: pdfplumber.table.Table,
        page_height: float,
    ) -> Optional[Table]:
        try:
            data = table_obj.extract()

            if not data or len(data) == 0:
                return None

            rows = len(data)
            cols = max(len(row) for row in data) if data else 0

            if rows == 0 or cols == 0:
                return None

            bbox = BBox(
                x0=table_obj.bbox[0],
                y0=table_obj.bbox[1],
                x1=table_obj.bbox[2],
                y1=table_obj.bbox[3],
            )

            cells = []
            for row_idx, row in enumerate(data):
                for col_idx, cell_text in enumerate(row):
                    text = cell_text if cell_text else ""
                    cell_bbox = self._estimate_cell_bbox(
                        bbox, rows, cols, row_idx, col_idx
                    )
                    cell = TableCell(
                        bbox=cell_bbox,
                        text=text.strip() if isinstance(text, str) else str(text),
                        row=row_idx,
                        col=col_idx,
                    )
                    cells.append(cell)

            return Table(bbox=bbox, rows=rows, cols=cols, cells=cells)

        except Exception as e:
            print(f"Error extrayendo tabla: {e}")
            return None

    def _estimate_cell_bbox(
        self,
        table_bbox: BBox,
        total_rows: int,
        total_cols: int,
        row: int,
        col: int,
    ) -> BBox:
        cell_width = table_bbox.width / total_cols
        cell_height = table_bbox.height / total_rows

        return BBox(
            x0=table_bbox.x0 + col * cell_width,
            y0=table_bbox.y0 + row * cell_height,
            x1=table_bbox.x0 + (col + 1) * cell_width,
            y1=table_bbox.y0 + (row + 1) * cell_height,
        )

    def enrich_document(self, document: Document, pdf_path: str | Path) -> Document:
        all_tables = self.extract_tables_from_pdf(pdf_path)

        for page_idx, page_tables in enumerate(all_tables):
            if page_idx < len(document.pages):
                document.pages[page_idx].tables = page_tables

        return document


def print_table(table: Table, max_width: int = 20) -> str:
    matrix = table.to_matrix()

    if not matrix:
        return "(tabla vacía)"

    col_widths = []
    for col in range(table.cols):
        max_col_width = 0
        for row in range(table.rows):
            cell_text = matrix[row][col] if col < len(matrix[row]) else ""
            max_col_width = max(max_col_width, len(cell_text[:max_width]))
        col_widths.append(min(max_col_width, max_width))

    separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

    lines = [separator]
    for row in range(table.rows):
        row_parts = []
        for col in range(table.cols):
            cell_text = matrix[row][col] if col < len(matrix[row]) else ""
            cell_text = cell_text[:max_width]
            row_parts.append(f" {cell_text:<{col_widths[col]}} ")
        lines.append("|" + "|".join(row_parts) + "|")
        lines.append(separator)

    return "\n".join(lines)