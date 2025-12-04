# TransMatrix

**El motor de traducción de PDFs open-source que realmente preserva tus layouts.**

TransMatrix es una herramienta de traducción de documentos diseñada para PDFs complejos: manuales técnicos, catálogos de producto, fichas técnicas y folletos con tablas, columnas e imágenes. A diferencia de los traductores genéricos, TransMatrix entiende la estructura del documento y reconstruye los documentos traducidos con fidelidad visual.

---

## 🎯 ¿Por qué TransMatrix?

La mayoría de herramientas de traducción tratan los PDFs como texto plano. Rompen layouts, destruyen tablas y producen documentos que necesitan horas de corrección manual.

TransMatrix toma un enfoque diferente:

- **Extracción basada en estructura** — Entiende bloques, columnas, tablas y orden de lectura
- **Integración inteligente de OCR** — Maneja documentos escaneados y texto en imágenes
- **Traducción consciente del contexto** — Traduce con contexto del documento, no fragmentos aislados
- **Reconstrucción que preserva el layout** — Genera PDFs que se ven como el original, solo que en otro idioma

---

## 🏗️ Arquitectura
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  EXTRACCIÓN │ ──▶ │     OCR     │ ──▶ │ TRADUCCIÓN  │ ──▶ │RECONSTRUCCIÓN│
│             │     │ (si needed) │     │             │     │              │
│ PyMuPDF     │     │ PaddleOCR   │     │ NLLB/M2M100 │     │ ReportLab   │
│ pdfplumber  │     │ Tesseract   │     │ + Glosarios │     │ HTML→PDF    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Modelo Interno  │
                    │  (JSON unificado)│
                    └─────────────────┘
```

---

## 🚀 Características

### Actual / En desarrollo
- [x] Extracción de texto con bounding boxes y metadatos de fuentes
- [x] Detección y extracción estructurada de tablas
- [x] Reconocimiento de layouts multi-columna
- [x] Serialización JSON bidireccional
- [ ] Pipeline de OCR para documentos escaneados
- [ ] Traducción automática neuronal (NLLB-200, M2M100)
- [ ] Soporte para glosarios personalizados
- [ ] Reconstrucción de PDF preservando layout
- [ ] Métricas de calidad e informes

### Planificado
- [ ] API REST para integración
- [ ] Interfaz web
- [ ] Procesamiento por lotes
- [ ] Modelos fine-tuned para dominios técnicos

---

## 📋 Requisitos

- Python 3.10 - 3.12 (recomendado 3.12)
- PyTorch 2.0+
- ~8GB RAM mínimo (16GB+ recomendado para documentos grandes)
- GPU opcional pero recomendada para velocidad de traducción

---

## 🛠️ Instalación
```bash
# Clonar el repositorio
git clone https://github.com/TU_USUARIO/TransMatrix.git
cd TransMatrix

# Crear entorno virtual
python -m venv .venv
source .venv/Scripts/activate  # Windows
# source .venv/bin/activate    # Linux/Mac

# Instalar dependencias
pip install -e ".[dev]"
pip install pdfplumber transformers sentencepiece torch
```

---

## 📖 Uso rápido

### Extraer contenido de un PDF
```bash
python scripts/extract_demo.py documento.pdf
```

Genera:
- `documento_extracted.json` — Estructura completa del documento
- `documento_visualized.pdf` — PDF con bounding boxes visualizados

### Traducir un documento
```bash
python scripts/translate_demo.py documento.pdf es en
```

Idiomas soportados: `es`, `en`, `fr`, `de`, `it`, `pt`, `zh`, `ar`, `ru`, `ja`, `ko`

---

## 🎯 Tipos de documento objetivo

TransMatrix está optimizado para:

| Tipo de documento | Nivel de soporte |
|-------------------|------------------|
| Catálogos de producto | 🟢 Foco principal |
| Fichas técnicas | 🟢 Foco principal |
| Manuales de usuario | 🟢 Foco principal |
| Folletos con tablas | 🟢 Foco principal |
| Papers científicos | 🟡 Soportado |
| PDFs de texto simple | 🟡 Soportado (overkill) |
| Formularios rellenables | 🔴 No soportado aún |
| Revistas muy diseñadas | 🔴 Soporte limitado |

---

## 📁 Estructura del proyecto
```
TransMatrix/
├── transmatrix/
│   ├── extraction/      # Extractores de PDF y tablas
│   ├── translation/     # Motor de traducción
│   ├── reconstruction/  # Generación de PDF (pendiente)
│   ├── ocr/            # Integración OCR (pendiente)
│   ├── models/         # Modelos de datos
│   └── utils/          # Utilidades
├── scripts/            # Scripts de demostración
├── tests/              # Tests y fixtures
└── docs/               # Documentación
```

---

## 🤝 Contribuir

TransMatrix está en desarrollo activo. ¡Las contribuciones son bienvenidas!

1. Fork del repositorio
2. Crear rama de feature (`git checkout -b feature/nueva-feature`)
3. Commit de cambios (`git commit -m 'Añadir nueva feature'`)
4. Push a la rama (`git push origin feature/nueva-feature`)
5. Abrir Pull Request

---

## 📜 Licencia

Este proyecto está bajo la licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

---

## 🙏 Agradecimientos

Construido con:
- [PyMuPDF](https://pymupdf.readthedocs.io/) — Manipulación de PDFs
- [pdfplumber](https://github.com/jsvine/pdfplumber) — Extracción de tablas
- [Hugging Face Transformers](https://huggingface.co/transformers/) — Traducción automática neuronal
- [NLLB-200](https://github.com/facebookresearch/fairseq/tree/nllb) — Modelo multilingüe de Meta

---

<p align="center">
  <b>TransMatrix</b> — Porque tus documentos traducidos merecen verse profesionales.
</p>
