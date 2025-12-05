"""
Reconstructor de PDFs con texto traducido.
"""

import fitz
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.console import Console

from transmatrix.models.document import Document, Page, TextBlock, TextSpan, BBox

console = Console()


@dataclass
class RebuilderConfig:
    """Configuración para el reconstructor."""
    cover_margin: float = 2.0
    cover_color: tuple = (1, 1, 1)
    min_font_scale: float = 0.6
    fallback_font: str = "helv"
    preserve_fonts: bool = True


class PDFRebuilder:
    """Reconstruye PDFs con texto traducido."""

    FONT_MAP = {
        "arial": "helv",
        "arialmt": "helv",
        "arial-boldmt": "hebo",
        "arial-italicmt": "heit",
        "arial-bolditalicmt": "hebi",
        "arialroundedmtbold": "hebo",
        "helvetica": "helv",
        "helvetica-bold": "hebo",
        "times": "tiro",
        "timesnewroman": "tiro",
        "times-roman": "tiro",
        "times-bold": "tibo",
        "courier": "cour",
        "couriernew": "cour",
        "impact": "hebo",
    }

    def __init__(self, config: Optional[RebuilderConfig] = None):
        self.config = config or RebuilderConfig()

    def rebuild(
        self,
        original_pdf: str | Path,
        document: Document,
        output_path: str | Path,
        verbose: bool = True,
    ) -> Path:
        original_pdf = Path(original_pdf)
        output_path = Path(output_path)

        pdf = fitz.open(original_pdf)
        total_pages = len(document.pages)

        for page_num, page_data in enumerate(document.pages):
            if page_num >= len(pdf):
                break

            console.print(f"\n[bold green]Reconstruyendo página {page_num + 1}/{total_pages}[/bold green]")
            
            fitz_page = pdf[page_num]
            self._rebuild_page_with_progress(fitz_page, page_data)

        console.print("\n[bold green]✓ Reconstrucción completada[/bold green]")

        pdf.save(output_path)
        pdf.close()

        return output_path

    def _rebuild_page_with_progress(self, fitz_page: fitz.Page, page_data: Page):
        # Contar elementos a procesar
        spans_to_process = []
        for block in page_data.text_blocks:
            for line in block.lines:
                for span in line.spans:
                    if span.translated_text and span.translated_text != span.text:
                        spans_to_process.append(span)

        cells_to_process = []
        for table in page_data.tables:
            for cell in table.cells:
                if cell.translated_text and cell.translated_text != cell.text:
                    cells_to_process.append(cell)

        total = len(spans_to_process) + len(cells_to_process)
        
        if total == 0:
            console.print("  [dim]Sin cambios en esta página[/dim]")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]Elementos"),
            BarColumn(bar_width=50),
            TaskProgressColumn(),
            TextColumn("[yellow]{task.completed}/{task.total}"),
        ) as progress:
            
            task = progress.add_task("Escribiendo...", total=total)

            # Procesar spans
            for span in spans_to_process:
                self._replace_span(fitz_page, span)
                progress.advance(task)

            # Procesar celdas
            for cell in cells_to_process:
                self._replace_cell(fitz_page, cell)
                progress.advance(task)

    def _rebuild_page(self, fitz_page: fitz.Page, page_data: Page):
        """Versión sin progreso."""
        for block in page_data.text_blocks:
            self._rebuild_text_block(fitz_page, block)

        for table in page_data.tables:
            self._rebuild_table(fitz_page, table)

    def _rebuild_text_block(self, fitz_page: fitz.Page, block: TextBlock):
        for line in block.lines:
            for span in line.spans:
                if span.translated_text and span.translated_text != span.text:
                    self._replace_span(fitz_page, span)

    def _replace_span(self, fitz_page: fitz.Page, span: TextSpan):
        rect = fitz.Rect(
            span.bbox.x0 - self.config.cover_margin,
            span.bbox.y0 - self.config.cover_margin,
            span.bbox.x1 + self.config.cover_margin,
            span.bbox.y1 + self.config.cover_margin,
        )

        shape = fitz_page.new_shape()
        shape.draw_rect(rect)
        shape.finish(color=None, fill=self.config.cover_color)
        shape.commit()

        font_name = self._get_font(span.font, span.is_bold, span.is_italic)
        font_size = self._calculate_font_size(
            span.translated_text,
            span.bbox,
            span.size,
            font_name,
            fitz_page,
        )

        color = self._int_to_rgb(span.color)
        text_point = fitz.Point(span.bbox.x0, span.bbox.y1 - 1)

        try:
            fitz_page.insert_text(
                text_point,
                span.translated_text,
                fontname=font_name,
                fontsize=font_size,
                color=color,
            )
        except Exception:
            try:
                fitz_page.insert_text(
                    text_point,
                    span.translated_text,
                    fontname=self.config.fallback_font,
                    fontsize=font_size,
                    color=color,
                )
            except Exception as e2:
                pass  # Silenciar errores en modo progreso

    def _rebuild_table(self, fitz_page: fitz.Page, table):
        for cell in table.cells:
            if cell.translated_text and cell.translated_text != cell.text:
                self._replace_cell(fitz_page, cell)

    def _replace_cell(self, fitz_page: fitz.Page, cell):
        rect = fitz.Rect(
            cell.bbox.x0 + 1,
            cell.bbox.y0 + 1,
            cell.bbox.x1 - 1,
            cell.bbox.y1 - 1,
        )

        shape = fitz_page.new_shape()
        shape.draw_rect(rect)
        shape.finish(color=None, fill=self.config.cover_color)
        shape.commit()

        font_size = self._fit_text_in_rect(
            cell.translated_text,
            cell.bbox,
            max_size=10,
        )

        text_point = fitz.Point(
            cell.bbox.x0 + 2,
            cell.bbox.y0 + (cell.bbox.height / 2) + (font_size / 3),
        )

        try:
            fitz_page.insert_text(
                text_point,
                cell.translated_text,
                fontname=self.config.fallback_font,
                fontsize=font_size,
                color=(0, 0, 0),
            )
        except Exception:
            pass

    def _get_font(self, original_font: str, is_bold: bool, is_italic: bool) -> str:
        font_lower = original_font.lower().replace(" ", "").replace("-", "")

        if font_lower in self.FONT_MAP:
            return self.FONT_MAP[font_lower]

        if is_bold and is_italic:
            return "hebi"
        elif is_bold:
            return "hebo"
        elif is_italic:
            return "heit"
        else:
            return "helv"

    def _calculate_font_size(
        self,
        text: str,
        bbox: BBox,
        original_size: float,
        font_name: str,
        fitz_page: fitz.Page,
    ) -> float:
        size = original_size
        available_width = bbox.width
        estimated_width = len(text) * size * 0.5

        if estimated_width > available_width and available_width > 0:
            scale = available_width / estimated_width
            size = max(size * scale, size * self.config.min_font_scale)

        return round(size, 1)

    def _fit_text_in_rect(
        self,
        text: str,
        bbox: BBox,
        max_size: float = 12,
        min_size: float = 4,
    ) -> float:
        available_width = bbox.width - 4

        for size in [max_size, 10, 8, 6, min_size]:
            estimated_width = len(text) * size * 0.5
            if estimated_width <= available_width:
                return size

        return min_size

    def _int_to_rgb(self, color_int: int) -> tuple:
        r = ((color_int >> 16) & 0xFF) / 255
        g = ((color_int >> 8) & 0xFF) / 255
        b = (color_int & 0xFF) / 255
        return (r, g, b)


def rebuild_pdf_simple(
    original_pdf: str | Path,
    document: Document,
    output_path: Optional[str | Path] = None,
    verbose: bool = True,
) -> Path:
    original_pdf = Path(original_pdf)

    if output_path is None:
        output_path = original_pdf.parent / f"{original_pdf.stem}_translated.pdf"

    rebuilder = PDFRebuilder()
    return rebuilder.rebuild(original_pdf, document, output_path, verbose=verbose)