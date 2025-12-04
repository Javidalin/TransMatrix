"""
Traduce documentos completos manteniendo la estructura.
"""

from transmatrix.models.document import Document, Page
from transmatrix.translation.translator import Translator, TranslationConfig


class DocumentTranslator:
    """Traduce documentos completos preservando estructura."""

    def __init__(self, translator: Translator):
        self.translator = translator

    def translate_document(
        self,
        document: Document,
        translate_tables: bool = True,
        verbose: bool = True,
    ) -> Document:
        total_pages = len(document.pages)

        for i, page in enumerate(document.pages):
            if verbose:
                print(f"Traduciendo página {i + 1}/{total_pages}...")

            self._translate_page(page)

            if translate_tables:
                self._translate_tables(page)

        return document

    def _translate_page(self, page: Page):
        all_spans = []
        for block in page.text_blocks:
            for line in block.lines:
                for span in line.spans:
                    all_spans.append(span)

        if not all_spans:
            return

        texts = [span.text for span in all_spans]
        translated = self.translator.translate_batch(texts)

        for span, trans in zip(all_spans, translated):
            span.translated_text = trans

    def _translate_tables(self, page: Page):
        all_cells = []
        for table in page.tables:
            for cell in table.cells:
                if cell.text and cell.text.strip():
                    all_cells.append(cell)

        if not all_cells:
            return

        texts = [cell.text for cell in all_cells]
        translated = self.translator.translate_batch(texts)

        for cell, trans in zip(all_cells, translated):
            cell.translated_text = trans


def translate_document_simple(
    document: Document,
    source_lang: str,
    target_lang: str,
    model_name: str = "facebook/nllb-200-distilled-600M",
    verbose: bool = True,
) -> Document:
    from transmatrix.translation.translator import NLLBTranslator

    config = TranslationConfig(
        source_lang=source_lang,
        target_lang=target_lang,
    )

    translator = NLLBTranslator(config, model_name=model_name)
    doc_translator = DocumentTranslator(translator)

    document.source_lang = source_lang
    document.target_lang = target_lang

    return doc_translator.translate_document(document, verbose=verbose)