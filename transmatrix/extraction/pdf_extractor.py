"""
Extractor de contenido de PDFs usando PyMuPDF.
"""

import fitz
from pathlib import Path
from typing import Optional

from transmatrix.models.document import (
    Document,
    Page,
    TextBlock,
    TextLine,
    TextSpan,
    ImageBlock,
    BBox,
)


class PDFExtractor:
    """Extrae contenido estructurado de archivos PDF."""

    def __init__(self, preserve_whitespace: bool = True):
        self.preserve_whitespace = preserve_whitespace

    def extract(self, pdf_path: str | Path) -> Document:
        pdf_path = Path(pdf_path)
        doc = fitz.open(pdf_path)

        pages = []
        for page_num, fitz_page in enumerate(doc):
            page = self._extract_page(fitz_page, page_num + 1)
            pages.append(page)

        doc.close()
        return Document(filename=pdf_path.name, pages=pages)

    def _extract_page(self, fitz_page: fitz.Page, page_number: int) -> Page:
        page = Page(
            page_number=page_number,
            width=fitz_page.rect.width,
            height=fitz_page.rect.height,
        )

        flags = fitz.TEXT_PRESERVE_WHITESPACE if self.preserve_whitespace else 0
        blocks = fitz_page.get_text("dict", flags=flags)["blocks"]

        for block in blocks:
            if block["type"] == 0:
                text_block = self._extract_text_block(block)
                if text_block:
                    page.text_blocks.append(text_block)
            elif block["type"] == 1:
                image_block = self._extract_image_block(block)
                page.image_blocks.append(image_block)

        return page

    def _extract_text_block(self, block: dict) -> Optional[TextBlock]:
        lines = []
        for line_data in block.get("lines", []):
            line = self._extract_text_line(line_data)
            if line and line.spans:
                lines.append(line)

        if not lines:
            return None

        return TextBlock(bbox=BBox.from_tuple(block["bbox"]), lines=lines)

    def _extract_text_line(self, line_data: dict) -> Optional[TextLine]:
        spans = []
        for span_data in line_data.get("spans", []):
            span = self._extract_text_span(span_data)
            if span and span.text.strip():
                spans.append(span)

        if not spans:
            return None

        return TextLine(bbox=BBox.from_tuple(line_data["bbox"]), spans=spans)

    def _extract_text_span(self, span_data: dict) -> Optional[TextSpan]:
        text = span_data.get("text", "")
        if not text:
            return None

        return TextSpan(
            text=text,
            bbox=BBox.from_tuple(span_data["bbox"]),
            font=span_data.get("font", ""),
            size=round(span_data.get("size", 0), 2),
            color=span_data.get("color", 0),
            flags=span_data.get("flags", 0),
        )

    def _extract_image_block(self, block: dict) -> ImageBlock:
        return ImageBlock(
            bbox=BBox.from_tuple(block["bbox"]),
            width=block.get("width", 0),
            height=block.get("height", 0),
        )


class PDFVisualizer:
    """Genera visualizaciones de debug para PDFs."""

    COLOR_TEXT = (1, 0, 0)
    COLOR_IMAGE = (0, 0, 1)
    COLOR_LINE = (0, 0.7, 0)

    def __init__(self, line_width: float = 0.5):
        self.line_width = line_width

    def visualize_document(
        self,
        pdf_path: str | Path,
        output_path: str | Path,
        show_lines: bool = False,
    ):
        doc = fitz.open(pdf_path)

        for page in doc:
            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                rect = fitz.Rect(block["bbox"])

                if block["type"] == 0:
                    page.draw_rect(rect, color=self.COLOR_TEXT, width=self.line_width)

                    if show_lines:
                        for line in block.get("lines", []):
                            line_rect = fitz.Rect(line["bbox"])
                            page.draw_rect(
                                line_rect,
                                color=self.COLOR_LINE,
                                width=self.line_width * 0.5,
                            )
                else:
                    page.draw_rect(rect, color=self.COLOR_IMAGE, width=self.line_width)

        doc.save(output_path)
        doc.close()