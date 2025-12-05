"""
Demo de traducción de documentos PDF.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from transmatrix.extraction.pdf_extractor import PDFExtractor
from transmatrix.extraction.table_extractor import TableExtractor
from transmatrix.translation.document_translator import translate_document_simple
from transmatrix.reconstruction.pdf_rebuilder import rebuild_pdf_simple


def main():
    if len(sys.argv) < 4:
        print("Uso: python translate_demo.py <pdf> <idioma_origen> <idioma_destino>")
        print("Ejemplo: python translate_demo.py documento.pdf es en")
        print("\nIdiomas: es, en, fr, de, it, pt, zh, ar, ru, ja, ko")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    source_lang = sys.argv[2]
    target_lang = sys.argv[3]

    if not pdf_path.exists():
        print(f"Error: No se encuentra el archivo {pdf_path}")
        sys.exit(1)

    print(f"PDF: {pdf_path}")
    print(f"Traducción: {source_lang} → {target_lang}")
    print("=" * 50)

    # Paso 1: Extraer documento
    print("\n[1/4] Extrayendo contenido...")
    extractor = PDFExtractor()
    document = extractor.extract(pdf_path)
    print(f"      → {document.total_text_blocks} bloques de texto")

    # Paso 2: Extraer tablas
    print("\n[2/4] Extrayendo tablas...")
    table_extractor = TableExtractor()
    document = table_extractor.enrich_document(document, pdf_path)
    print(f"      → {document.total_tables} tablas")

    # Paso 3: Traducir
    print("\n[3/4] Traduciendo...")
    print("      (Primera ejecución descarga el modelo ~1.2GB)")
    document = translate_document_simple(
        document,
        source_lang=source_lang,
        target_lang=target_lang,
        verbose=True,
    )

    # Paso 4: Reconstruir PDF
    print("\n[4/4] Generando PDF traducido...")
    output_pdf = Path(f"{pdf_path.stem}_{source_lang}_to_{target_lang}.pdf")
    rebuild_pdf_simple(pdf_path, document, output_pdf, verbose=True)
    print(f"      → {output_pdf}")

    # Guardar también el JSON
    output_json = Path(f"{pdf_path.stem}_{source_lang}_to_{target_lang}.json")
    document.save(output_json)
    print(f"      → {output_json}")

    # Resumen
    print("\n" + "=" * 50)
    print("✓ COMPLETADO")
    print("=" * 50)
    print(f"  PDF traducido: {output_pdf}")
    print(f"  Datos JSON:    {output_json}")

    # Mostrar muestra
    print("\n" + "-" * 50)
    print("MUESTRA DE TRADUCCIÓN:")
    print("-" * 50)

    if document.pages:
        page = document.pages[0]
        count = 0
        for block in page.text_blocks:
            if count >= 3:
                break
            for line in block.lines:
                original = line.text.strip()
                translated = line.translated_text.strip()
                if original and translated and original != translated:
                    print(f"\n  ES: {original[:60]}")
                    print(f"  EN: {translated[:60]}")
                    count += 1
                    if count >= 3:
                        break


if __name__ == "__main__":
    main()