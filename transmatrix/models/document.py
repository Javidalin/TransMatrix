"""
Modelo de datos interno para representar documentos PDF.
"""

import json
from dataclasses import dataclass, field
from enum import IntFlag
from typing import Optional
from pathlib import Path


class SpanFlags(IntFlag):
    """Flags de formato de texto según PyMuPDF."""
    NORMAL = 0
    SUPERSCRIPT = 1
    ITALIC = 2
    SERIFED = 4
    MONOSPACED = 8
    BOLD = 16


@dataclass
class BBox:
    """Bounding box de un elemento."""
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2)

    @classmethod
    def from_tuple(cls, t: tuple) -> "BBox":
        return cls(x0=t[0], y0=t[1], x1=t[2], y1=t[3])

    def to_tuple(self) -> tuple:
        return (self.x0, self.y0, self.x1, self.y1)

    def to_dict(self) -> dict:
        return {"x0": self.x0, "y0": self.y0, "x1": self.x1, "y1": self.y1}

    @classmethod
    def from_dict(cls, d: dict) -> "BBox":
        return cls(x0=d["x0"], y0=d["y0"], x1=d["x1"], y1=d["y1"])


@dataclass
class TextSpan:
    """Segmento de texto con formato uniforme."""
    text: str
    bbox: BBox
    font: str
    size: float
    color: int
    flags: int
    translated_text: Optional[str] = None

    @property
    def is_bold(self) -> bool:
        return bool(self.flags & SpanFlags.BOLD)

    @property
    def is_italic(self) -> bool:
        return bool(self.flags & SpanFlags.ITALIC)

    @property
    def color_rgb(self) -> tuple[int, int, int]:
        r = (self.color >> 16) & 0xFF
        g = (self.color >> 8) & 0xFF
        b = self.color & 0xFF
        return (r, g, b)

    @property
    def color_hex(self) -> str:
        return f"#{self.color:06X}"

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "bbox": self.bbox.to_dict(),
            "font": self.font,
            "size": self.size,
            "color": self.color,
            "flags": self.flags,
            "translated_text": self.translated_text,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TextSpan":
        return cls(
            text=d["text"],
            bbox=BBox.from_dict(d["bbox"]),
            font=d["font"],
            size=d["size"],
            color=d["color"],
            flags=d["flags"],
            translated_text=d.get("translated_text"),
        )


@dataclass
class TextLine:
    """Línea de texto compuesta por spans."""
    bbox: BBox
    spans: list[TextSpan] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "".join(span.text for span in self.spans)

    @property
    def translated_text(self) -> str:
        return "".join(span.translated_text or span.text for span in self.spans)

    def to_dict(self) -> dict:
        return {
            "bbox": self.bbox.to_dict(),
            "spans": [span.to_dict() for span in self.spans],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TextLine":
        return cls(
            bbox=BBox.from_dict(d["bbox"]),
            spans=[TextSpan.from_dict(s) for s in d["spans"]],
        )


@dataclass
class TextBlock:
    """Bloque de texto compuesto por líneas."""
    bbox: BBox
    lines: list[TextLine] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(line.text for line in self.lines)

    @property
    def translated_text(self) -> str:
        return "\n".join(line.translated_text for line in self.lines)

    def to_dict(self) -> dict:
        return {
            "bbox": self.bbox.to_dict(),
            "lines": [line.to_dict() for line in self.lines],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TextBlock":
        return cls(
            bbox=BBox.from_dict(d["bbox"]),
            lines=[TextLine.from_dict(l) for l in d["lines"]],
        )


@dataclass
class ImageBlock:
    """Bloque de imagen."""
    bbox: BBox
    width: int
    height: int
    image_data: Optional[bytes] = None
    ocr_text: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "bbox": self.bbox.to_dict(),
            "width": self.width,
            "height": self.height,
            "ocr_text": self.ocr_text,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ImageBlock":
        return cls(
            bbox=BBox.from_dict(d["bbox"]),
            width=d["width"],
            height=d["height"],
            ocr_text=d.get("ocr_text"),
        )


@dataclass
class TableCell:
    """Celda de una tabla."""
    bbox: BBox
    text: str
    row: int
    col: int
    rowspan: int = 1
    colspan: int = 1
    translated_text: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "bbox": self.bbox.to_dict(),
            "text": self.text,
            "row": self.row,
            "col": self.col,
            "rowspan": self.rowspan,
            "colspan": self.colspan,
            "translated_text": self.translated_text,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TableCell":
        return cls(
            bbox=BBox.from_dict(d["bbox"]),
            text=d["text"],
            row=d["row"],
            col=d["col"],
            rowspan=d.get("rowspan", 1),
            colspan=d.get("colspan", 1),
            translated_text=d.get("translated_text"),
        )


@dataclass
class Table:
    """Tabla extraída del documento."""
    bbox: BBox
    rows: int
    cols: int
    cells: list[TableCell] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "bbox": self.bbox.to_dict(),
            "rows": self.rows,
            "cols": self.cols,
            "cells": [cell.to_dict() for cell in self.cells],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Table":
        return cls(
            bbox=BBox.from_dict(d["bbox"]),
            rows=d["rows"],
            cols=d["cols"],
            cells=[TableCell.from_dict(c) for c in d["cells"]],
        )

    def get_cell(self, row: int, col: int) -> Optional[TableCell]:
        for cell in self.cells:
            if cell.row == row and cell.col == col:
                return cell
        return None

    def to_matrix(self) -> list[list[str]]:
        matrix = [["" for _ in range(self.cols)] for _ in range(self.rows)]
        for cell in self.cells:
            if cell.row < self.rows and cell.col < self.cols:
                matrix[cell.row][cell.col] = cell.text
        return matrix


@dataclass
class Page:
    """Página del documento."""
    page_number: int
    width: float
    height: float
    text_blocks: list[TextBlock] = field(default_factory=list)
    image_blocks: list[ImageBlock] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)

    @property
    def all_text(self) -> str:
        return "\n\n".join(block.text for block in self.text_blocks)

    def to_dict(self) -> dict:
        return {
            "page_number": self.page_number,
            "width": self.width,
            "height": self.height,
            "text_blocks": [block.to_dict() for block in self.text_blocks],
            "image_blocks": [block.to_dict() for block in self.image_blocks],
            "tables": [table.to_dict() for table in self.tables],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Page":
        return cls(
            page_number=d["page_number"],
            width=d["width"],
            height=d["height"],
            text_blocks=[TextBlock.from_dict(b) for b in d["text_blocks"]],
            image_blocks=[ImageBlock.from_dict(b) for b in d["image_blocks"]],
            tables=[Table.from_dict(t) for t in d.get("tables", [])],
        )


@dataclass
class Document:
    """Documento completo."""
    filename: str
    pages: list[Page] = field(default_factory=list)
    source_lang: Optional[str] = None
    target_lang: Optional[str] = None

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def total_text_blocks(self) -> int:
        return sum(len(page.text_blocks) for page in self.pages)

    @property
    def total_image_blocks(self) -> int:
        return sum(len(page.image_blocks) for page in self.pages)

    @property
    def total_tables(self) -> int:
        return sum(len(page.tables) for page in self.pages)

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "source_lang": self.source_lang,
            "target_lang": self.target_lang,
            "page_count": self.page_count,
            "total_text_blocks": self.total_text_blocks,
            "total_image_blocks": self.total_image_blocks,
            "total_tables": self.total_tables,
            "pages": [page.to_dict() for page in self.pages],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Document":
        return cls(
            filename=d["filename"],
            source_lang=d.get("source_lang"),
            target_lang=d.get("target_lang"),
            pages=[Page.from_dict(p) for p in d["pages"]],
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "Document":
        return cls.from_dict(json.loads(json_str))

    def save(self, path: str | Path):
        path = Path(path)
        path.write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "Document":
        path = Path(path)
        return cls.from_json(path.read_text(encoding="utf-8"))