"""
Demo de extracción de PDF con el modelo de datos.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from transmatrix.extraction.pdf_extractor import PDFExtractor, PDFVisualizer
from transmatrix.extraction.table_extractor import TableExtractor, print_table


def main():
    if len(sys.argv) < 2:
        print("Uso: python extract_demo.py <ruta_al_pdf>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])

    if not pdf_path.exists():
        print(f"Error: No se encuentra el archivo {pdf_path}")
        sys.exit(1)

    print(f"Procesando: {pdf_path}")
    print("-" * 50)

    # Extraer documento
    print("1. Extrayendo texto...")
    extractor = PDFExtractor()
    document = extractor.extract(pdf_path)
    print(f"   → {document.total_text_blocks} bloques de texto")

    # Extraer tablas
    print("2. Extrayendo tablas...")
    table_extractor = TableExtractor()
    document = table_extractor.enrich_document(document, pdf_path)
    print(f"   → {document.total_tables} tablas")

    # Guardar JSON
    print("3. Guardando JSON...")
    output_json = Path(pdf_path.stem + "_extracted.json")
    document.save(output_json)
    print(f"   → {output_json}")

    # Generar visualización
    print("4. Generando visualización...")
    output_viz = pdf_path.stem + "_visualized.pdf"
    visualizer = PDFVisualizer()
    visualizer.visualize_document(pdf_path, output_viz, show_lines=True)
    print(f"   → {output_viz}")

    # Resumen
    print("-" * 50)
    print(f"Páginas: {document.page_count}")
    print(f"Bloques de texto: {document.total_text_blocks}")
    print(f"Tablas: {document.total_tables}")

    # Mostrar tablas
    if document.total_tables > 0:
        print("-" * 50)
        print("Primeras 3 tablas encontradas:")
        count = 0
        for page in document.pages:
            for idx, table in enumerate(page.tables):
                if count >= 3:
                    break
                print(f"\n[Página {page.page_number}, Tabla {idx + 1}] ({table.rows}x{table.cols}):")
                print(print_table(table))
                count += 1
            if count >= 3:
                break

    print("-" * 50)
    print("✓ Completado")


if __name__ == "__main__":
    main()