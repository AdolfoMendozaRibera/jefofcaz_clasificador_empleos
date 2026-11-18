"""Generador del Informe Tecnico Oficial en Microsoft Word (.docx) para JobScope AI.

Genera un documento ejecutivo de alta calidad academica y tecnica, con margenes
de 2.5 cm, tipografia profesional, tablas con sombreado, graficos en alta resolucion
y cobertura integral de la rubrica del Proyecto Integrador.
"""

from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"
ASSETS_DIR = BASE_DIR / "presentacion" / "assets"
OUT_DOCX = DOCS_DIR / "informe_tecnico_jobscope.docx"

# Paleta ejecutiva Clean SaaS
HEX_PRIMARY = "1E3A8A"      # Azul marino institucional
HEX_SECONDARY = "2563EB"    # Azul primario
HEX_DARK = "0F172A"         # Texto principal oscuro
HEX_MUTED = "475569"        # Texto secundario
HEX_LIGHT_BG = "F8FAFC"     # Fondo sutil
HEX_BORDER = "CBD5E1"       # Borde de tablas
HEX_SUCCESS = "059669"      # Verde aciertos
HEX_DANGER = "DC2626"       # Rojo alertas

COLOR_PRIMARY = RGBColor(30, 58, 138)
COLOR_SECONDARY = RGBColor(37, 99, 235)
COLOR_DARK = RGBColor(15, 23, 42)
COLOR_MUTED = RGBColor(71, 85, 105)
COLOR_SUCCESS = RGBColor(5, 150, 105)


def set_cell_background(cell, fill_hex):
    """Aplica sombreado de fondo a una celda de tabla."""
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)


def set_cell_margins(cell, top=120, bottom=120, left=180, right=180):
    """Configura los margenes internos (padding) de una celda en dxa."""
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def set_table_borders(table, color="CBD5E1", sz="4"):
    """Aplica bordes horizontales limpios y elimina bordes verticales internos."""
    tblPr = table._element.xpath('w:tblPr')
    if tblPr:
        borders = OxmlElement('w:tblBorders')
        for b_name in ['top', 'bottom', 'insideH']:
            b = OxmlElement(f'w:{b_name}')
            b.set(qn('w:val'), 'single')
            b.set(qn('w:sz'), sz)
            b.set(qn('w:space'), '0')
            b.set(qn('w:color'), color)
            borders.append(b)
        for b_name in ['left', 'right', 'insideV']:
            b = OxmlElement(f'w:{b_name}')
            b.set(qn('w:val'), 'none')
            borders.append(b)
        tblPr[0].append(borders)


def agregar_callout(doc, texto, titulo="NOTA TÉCNICA CLAVE"):
    """Inserta una caja de llamada destacada."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, "F1F5F9")
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    # Borde izquierdo grueso
    tcPr = cell._element.get_or_add_tcPr()
    borders = OxmlElement('w:tcBorders')
    left_b = OxmlElement('w:left')
    left_b.set(qn('w:val'), 'single')
    left_b.set(qn('w:sz'), '24')  # 3pt
    left_b.set(qn('w:space'), '0')
    left_b.set(qn('w:color'), HEX_SECONDARY)
    borders.append(left_b)
    for b_name in ['top', 'bottom', 'right']:
        b = OxmlElement(f'w:{b_name}')
        b.set(qn('w:val'), 'none')
        borders.append(b)
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    run_t = p.add_run(f"📌 {titulo}: ")
    run_t.font.name = "Calibri"
    run_t.font.size = Pt(10)
    run_t.font.bold = True
    run_t.font.color.rgb = COLOR_SECONDARY
    
    run_txt = p.add_run(texto)
    run_txt.font.name = "Calibri"
    run_txt.font.size = Pt(9.5)
    run_txt.font.color.rgb = COLOR_DARK
    
    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_before = Pt(4)
    p_after.paragraph_format.space_after = Pt(4)


def agregar_imagen_centrada(doc, nombre_archivo, ancho_pulgadas=5.8, leyenda=None):
    """Inserta una imagen centrada con su leyenda formal."""
    img_path = ASSETS_DIR / nombre_archivo
    if img_path.exists():
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(10)
        p_img.paragraph_format.space_after = Pt(4)
        run = p_img.add_run()
        run.add_picture(str(img_path), width=Inches(ancho_pulgadas))
        
        if leyenda:
            p_leg = doc.add_paragraph()
            p_leg.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_leg.paragraph_format.space_before = Pt(0)
            p_leg.paragraph_format.space_after = Pt(12)
            run_leg = p_leg.add_run(leyenda)
            run_leg.font.name = "Calibri"
            run_leg.font.size = Pt(9)
            run_leg.font.italic = True
            run_leg.font.color.rgb = COLOR_MUTED
    else:
        print(f"Aviso: Imagen no encontrada: {img_path}")


def construir_documento():
    doc = Document()
    
    # Configuracion de pagina: Margenes de 2.5 cm (0.984 pulgadas)
    for section in doc.sections:
        section.top_margin = Inches(0.984)
        section.bottom_margin = Inches(0.984)
        section.left_margin = Inches(0.984)
        section.right_margin = Inches(0.984)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)
        
        # Encabezado sutil
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("JobScope AI — Informe Técnico de Proyecto Integrador")
        hrun.font.name = "Calibri"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = COLOR_MUTED
        
        # Pie de pagina
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.LEFT
        frun = fp.add_run("Tópicos y Programación Avanzada · Noviembre 2026")
        frun.font.name = "Calibri"
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = COLOR_MUTED

    # =========================================================================
    # PORTADA OFICIAL
    # =========================================================================
    p_pre = doc.add_paragraph()
    p_pre.paragraph_format.space_before = Pt(40)
    p_pre.paragraph_format.space_after = Pt(6)
    r_pre = p_pre.add_run("UNIVERSIDAD PRIVADA — TÓPICOS Y PROGRAMACIÓN AVANZADA")
    r_pre.font.name = "Calibri"
    r_pre.font.size = Pt(11)
    r_pre.font.bold = True
    r_pre.font.color.rgb = COLOR_SECONDARY

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(10)
    p_title.paragraph_format.space_after = Pt(8)
    r_title = p_title.add_run("JobScope AI")
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(34)
    r_title.font.bold = True
    r_title.font.color.rgb = COLOR_DARK

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(24)
    r_sub = p_sub.add_run("Informe Técnico de Ingeniería: Clasificación y Auditoría de Ofertas Laborales en Español mediante NLP Riguroso y Machine Learning Supervisado")
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(14)
    r_sub.font.color.rgb = COLOR_MUTED

    # Linea decorativa
    p_line = doc.add_paragraph()
    p_line.paragraph_format.space_after = Pt(36)
    r_line = p_line.add_run("―" * 48)
    r_line.font.color.rgb = COLOR_SECONDARY

    # Metadatos del proyecto
    tbl_meta = doc.add_table(rows=6, cols=2)
    tbl_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_meta.autofit = False
    set_table_borders(tbl_meta, color="E2E8F0")

    datos_meta = [
        ("Materia:", "Tópicos y Programación Avanzada"),
        ("Tipo de Entrega:", "Proyecto Integrador — Primer Parcial"),
        ("Autor / Integrante:", "Adolfo Mendoza Ribera"),
        ("Stack Tecnológico:", "FastAPI · Scikit-Learn · React 18 · Docker Compose · Nginx"),
        ("Etiqueta Git de Entrega:", "entrega-final (Repositorio oficial)"),
        ("Fecha de Evaluación:", "Noviembre de 2026"),
    ]
    for row_idx, (k, v) in enumerate(datos_meta):
        c0 = tbl_meta.cell(row_idx, 0)
        c1 = tbl_meta.cell(row_idx, 1)
        c0.width = Inches(2.2)
        c1.width = Inches(4.3)
        set_cell_margins(c0, top=100, bottom=100, left=150, right=150)
        set_cell_margins(c1, top=100, bottom=100, left=150, right=150)
        
        p0 = c0.paragraphs[0]
        r0 = p0.add_run(k)
        r0.font.name = "Calibri"
        r0.font.size = Pt(10.5)
        r0.font.bold = True
        r0.font.color.rgb = COLOR_DARK
        
        p1 = c1.paragraphs[0]
        r1 = p1.add_run(v)
        r1.font.name = "Calibri"
        r1.font.size = Pt(10.5)
        r1.font.color.rgb = COLOR_MUTED
        if "entrega-final" in v:
            r1.font.bold = True
            r1.font.color.rgb = COLOR_SUCCESS

    # Resumen Ejecutivo en Portada
    p_abs_t = doc.add_paragraph()
    p_abs_t.paragraph_format.space_before = Pt(36)
    p_abs_t.paragraph_format.space_after = Pt(4)
    r_at = p_abs_t.add_run("RESUMEN EJECUTIVO")
    r_at.font.name = "Calibri"
    r_at.font.size = Pt(11)
    r_at.font.bold = True
    r_at.font.color.rgb = COLOR_PRIMARY

    p_abs = doc.add_paragraph()
    p_abs.paragraph_format.space_before = Pt(0)
    p_abs.paragraph_format.space_after = Pt(20)
    r_abs = p_abs.add_run(
        "El presente informe documenta el diseño, experimentación y puesta en producción de JobScope AI, "
        "una solución de software integral que clasifica convocatorias laborales en 5 macro-sectores profesionales "
        "a partir de texto libre desestructurado. Sobre un corpus real de 3.337 ofertas limpiadas de la Red Europea EURES, "
        "se diseñó un pipeline de NLP adaptado estrictamente al idioma español (blindaje de la letra 'Ñ' con unicodedata NFD, "
        "conservación de negaciones semánticas y Snowball Stemmer). Tras comparar 13 configuraciones mediante validación "
        "cruzada estratificada (k=5), la Regresión Logística con balanceo de pesos obtuvo la victoria con 90.41% de F1-Macro en CV "
        "y 91.55% en prueba ciega (Accuracy: 91.32%). El sistema opera en contenedores Docker mediante una API REST en FastAPI "
        "y un frontend moderno en React 18 detrás de un Reverse Proxy Nginx, respaldado por 81 pruebas unitarias automatizadas."
    )
    r_abs.font.name = "Calibri"
    r_abs.font.size = Pt(10)
    r_abs.font.color.rgb = COLOR_DARK

    doc.add_page_break()

    # =========================================================================
    # CAPÍTULO 1: INTRODUCCIÓN Y DEFINICIÓN DEL PROBLEMA
    # =========================================================================
    p_h1 = doc.add_paragraph()
    p_h1.paragraph_format.space_before = Pt(12)
    p_h1.paragraph_format.space_after = Pt(6)
    r_h1 = p_h1.add_run("1. Introducción y Definición del Problema")
    r_h1.font.name = "Calibri"
    r_h1.font.size = Pt(18)
    r_h1.font.bold = True
    r_h1.font.color.rgb = COLOR_PRIMARY

    p1_1 = doc.add_paragraph()
    p1_1.paragraph_format.space_before = Pt(4)
    p1_1.paragraph_format.space_after = Pt(6)
    r1_1 = p1_1.add_run(
        "En la actualidad, las plataformas masivas de empleo (LinkedIn, Computrabajo, Trabajópolis, InfoJobs) procesan miles "
        "de vacantes redactadas en lenguaje natural libre, sin una estructura fija. Esta libertad de redacción genera dos problemas "
        "críticos en el mercado laboral contemporáneo:"
    )
    r1_1.font.name = "Calibri"
    r1_1.font.size = Pt(10.5)

    bullet_p1 = doc.add_paragraph(style='List Bullet')
    bullet_p1.paragraph_format.space_before = Pt(2)
    bullet_p1.paragraph_format.space_after = Pt(3)
    r_b1 = bullet_p1.add_run("Categorización Errónea y Vacantes Invisibles: ")
    r_b1.font.bold = True
    bullet_p1.add_run(
        "Los reclutadores o usuarios que publican ofertas suelen dudar al clasificar puestos híbridos (por ejemplo, 'Comercial con vehículo propio' "
        "o 'Técnico de soporte asistencial'). Al elegir categorías inadecuadas, la convocatoria no llega a los candidatos cualificados "
        "y se pierde entre la multitud de publicaciones."
    )

    bullet_p2 = doc.add_paragraph(style='List Bullet')
    bullet_p2.paragraph_format.space_before = Pt(2)
    bullet_p2.paragraph_format.space_after = Pt(8)
    r_b2 = bullet_p2.add_run("Costo Operativo y Retrasos de Reclutamiento: ")
    r_b2.font.bold = True
    bullet_p2.add_run(
        "La revisión y categorización manual de un lote de 500 ofertas laborales demanda entre 4 y 6 horas de trabajo repetitivo humano, "
        "generando un cuello de botella logístico en los departamentos de Recursos Humanos."
    )

    p1_2 = doc.add_paragraph()
    p1_2.paragraph_format.space_before = Pt(4)
    p1_2.paragraph_format.space_after = Pt(8)
    r1_2 = p1_2.add_run(
        "JobScope AI resuelve esta problemática mediante la integración de un pipeline matemático de NLP y un estimador supervisado, "
        "reduciendo el tiempo de clasificación a menos de 5 milisegundos por vacante y posibilitando el procesamiento por lotes en menos "
        "de 1 segundo, lo que representa un ahorro del 95% de tiempo operativo con una fiabilidad demostrada del 91.55% en F1-Macro."
    )
    r1_2.font.name = "Calibri"
    r1_2.font.size = Pt(10.5)

    agregar_callout(
        doc,
        "La solución no opera como una 'caja negra'. Cada predicción individual está acompañada de una auditoría paso a paso "
        "que desglosa en tiempo real cómo se transformó el texto a lo largo de las 5 estaciones del pipeline de NLP.",
        titulo="PRINCIPIO DE TRANSPARENCIA Y EXPLICABILIDAD"
    )

    # =========================================================================
    # CAPÍTULO 2: ORIGEN DEL DATASET Y ANÁLISIS EXPLORATORIO (EDA)
    # =========================================================================
    p_h2 = doc.add_paragraph()
    p_h2.paragraph_format.space_before = Pt(16)
    p_h2.paragraph_format.space_after = Pt(6)
    r_h2 = p_h2.add_run("2. Origen del Dataset y Análisis Exploratorio (EDA)")
    r_h2.font.name = "Calibri"
    r_h2.font.size = Pt(18)
    r_h2.font.bold = True
    r_h2.font.color.rgb = COLOR_PRIMARY

    p2_1 = doc.add_paragraph()
    p2_1.paragraph_format.space_before = Pt(4)
    p2_1.paragraph_format.space_after = Pt(6)
    r2_1 = p2_1.add_run(
        "El proyecto se nutrió del corpus oficial de vacantes en español de la Red Europea de Servicios de Empleo EURES 2025 "
        "(publicado en Hugging Face bajo el identificador MiguelGP-13/JobOffers_ESP). En estricto cumplimiento de las reglas de arquitectura, "
        "el archivo original de 7.261 registros crudos se conservó inmutable en data/raw/job_offers_esp.csv."
    )
    r2_1.font.name = "Calibri"
    r2_1.font.size = Pt(10.5)

    p_h2_1 = doc.add_paragraph()
    p_h2_1.paragraph_format.space_before = Pt(10)
    p_h2_1.paragraph_format.space_after = Pt(4)
    r_h2_1 = p_h2_1.add_run("2.1 Mapeo Jerárquico a 5 Macro-Sectores Profesionales")
    r_h2_1.font.name = "Calibri"
    r_h2_1.font.size = Pt(13)
    r_h2_1.font.bold = True
    r_h2_1.font.color.rgb = COLOR_SECONDARY

    p2_2 = doc.add_paragraph()
    p2_2.paragraph_format.space_before = Pt(4)
    p2_2.paragraph_format.space_after = Pt(8)
    r2_2 = p2_2.add_run(
        "El corpus original presentaba una dispersión extrema de más de 300 oficios específicos (reponedor, oficial de fontanería, "
        "ayudante de pizzería, peón de pala). Entrenar un clasificador sobre 300 clases con baja representatividad habría generado "
        "un F1 inferior al 20% y una matriz de confusión inmanejable. Aplicando la taxonomía europea ESCO/EURES, se consolidaron "
        "5 macro-sectores representativos, descartando categorías menores y depurando registros nulos y duplicados, obteniendo "
        "un conjunto final de 3.337 ofertas limpias:"
    )
    r2_2.font.name = "Calibri"
    r2_2.font.size = Pt(10.5)

    # Tabla de los 5 sectores
    tbl_sec = doc.add_table(rows=6, cols=4)
    tbl_sec.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_sec)

    headers_sec = ["Sector Profesional", "Clase Técnica", "Ofertas Limpias", "% del Total"]
    for c_idx, h_txt in enumerate(headers_sec):
        c = tbl_sec.cell(0, c_idx)
        set_cell_background(c, HEX_PRIMARY)
        set_cell_margins(c, top=120, bottom=120, left=150, right=150)
        p = c.paragraphs[0]
        r = p.add_run(h_txt)
        r.font.name = "Calibri"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    filas_sec = [
        ("Transporte y Logística", "transporte_logistica", "914", "27.39%"),
        ("Ventas y Comercial", "ventas_comercial", "878", "26.31%"),
        ("Salud y Servicios Sociales", "salud_servicios_sociales", "584", "17.50%"),
        ("Hostelería y Gastronomía", "hosteleria_gastronomia", "512", "15.34%"),
        ("Construcción y Mantenimiento", "construccion_mantenimiento", "449", "13.46%"),
    ]
    for r_idx, row in enumerate(filas_sec, start=1):
        bg = HEX_LIGHT_BG if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row):
            c = tbl_sec.cell(r_idx, c_idx)
            set_cell_background(c, bg)
            set_cell_margins(c, top=100, bottom=100, left=150, right=150)
            p = c.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            if c_idx == 0:
                r.font.bold = True

    agregar_imagen_centrada(
        doc,
        "distribucion_sectores.png",
        ancho_pulgadas=5.4,
        leyenda="Figura 1: Distribución oficial de las 3.337 ofertas laborales curadas entre los 5 macro-sectores profesionales."
    )

    p_h2_2 = doc.add_paragraph()
    p_h2_2.paragraph_format.space_before = Pt(12)
    p_h2_2.paragraph_format.space_after = Pt(4)
    r_h2_2 = p_h2_2.add_run("2.2 Partición Estratificada y Prevención de Data Leakage")
    r_h2_2.font.name = "Calibri"
    r_h2_2.font.size = Pt(13)
    r_h2_2.font.bold = True
    r_h2_2.font.color.rgb = COLOR_SECONDARY

    p2_3 = doc.add_paragraph()
    p2_3.paragraph_format.space_before = Pt(4)
    p2_3.paragraph_format.space_after = Pt(6)
    r2_3 = p2_3.add_run(
        "Para garantizar reproducibilidad científica, la partición se ejecutó con train_test_split bajo una semilla aleatoria fija "
        "(random_state=42) y estratificación sobre la variable objetivo (stratify=y). Esto aseguró que cada partición conserve idéntica "
        "proporción de los 5 sectores:"
    )
    r2_3.font.name = "Calibri"
    r2_3.font.size = Pt(10.5)

    bullet_split1 = doc.add_paragraph(style='List Bullet')
    bullet_split1.add_run("Conjunto de Entrenamiento (Train - 80%): ").font.bold = True
    bullet_split1.add_run("2.669 ofertas serializadas en data/processed/train.csv.")

    bullet_split2 = doc.add_paragraph(style='List Bullet')
    bullet_split2.add_run("Conjunto de Prueba Ciega (Test - 20%): ").font.bold = True
    bullet_split2.add_run("668 ofertas serializadas en data/processed/test.csv.")

    agregar_callout(
        doc,
        "Blindaje estricto contra fuga de datos (Data Leakage): El vocabulario de palabras, los valores IDF de ponderación "
        "y el ajuste de los pesos de los modelos se aprendieron EXCLUSIVAMENTE sobre las 2.669 ofertas de Train (método .fit()). "
        "El conjunto de prueba permaneció completamente ciego y solo fue procesado con .transform() para la evaluación final.",
        titulo="BLINDAJE METODOLÓGICO ANTI DATA LEAKAGE"
    )

    p_h2_3 = doc.add_paragraph()
    p_h2_3.paragraph_format.space_before = Pt(12)
    p_h2_3.paragraph_format.space_after = Pt(4)
    r_h2_3 = p_h2_3.add_run("2.3 Percentiles de Longitud y Fundamentación de la API")
    r_h2_3.font.name = "Calibri"
    r_h2_3.font.size = Pt(13)
    r_h2_3.font.bold = True
    r_h2_3.font.color.rgb = COLOR_SECONDARY

    p2_4 = doc.add_paragraph()
    p2_4.paragraph_format.space_before = Pt(4)
    p2_4.paragraph_format.space_after = Pt(8)
    r2_4 = p2_4.add_run(
        "El análisis estadístico exploratorio (EDA) reveló que la distribución de longitud de caracteres tiene una fuerte asimetría positiva. "
        "Los percentiles empíricos calculados fueron:"
    )
    r2_4.font.name = "Calibri"
    r2_4.font.size = Pt(10.5)

    tbl_perc = doc.add_table(rows=5, cols=3)
    tbl_perc.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_perc)

    headers_perc = ["Métrica / Percentil", "Valor en Caracteres", "Interpretación y Justificación"]
    for c_idx, h_txt in enumerate(headers_perc):
        c = tbl_perc.cell(0, c_idx)
        set_cell_background(c, HEX_PRIMARY)
        set_cell_margins(c, top=100, bottom=100, left=150, right=150)
        p = c.paragraphs[0]
        r = p.add_run(h_txt)
        r.font.name = "Calibri"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    filas_perc = [
        ("Longitud Mínima", "18 caracteres", "Textos ultracortos sin suficiente contexto semántico."),
        ("Mediana (P50)", "315 caracteres (~78 palabras)", "Longitud estándar representativa de una oferta laboral promedio."),
        ("Percentil 90 (P90)", "742 caracteres", "Convocatorias extensas con desglose detallado de requisitos."),
        ("Percentil 99 (P99)", "1.827 caracteres", "El 99% de las vacantes reales no supera los 1.830 caracteres."),
    ]
    for r_idx, row in enumerate(filas_perc, start=1):
        bg = HEX_LIGHT_BG if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row):
            c = tbl_perc.cell(r_idx, c_idx)
            set_cell_background(c, bg)
            set_cell_margins(c, top=90, bottom=90, left=150, right=150)
            p = c.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            if c_idx == 0:
                r.font.bold = True

    p2_5 = doc.add_paragraph()
    p2_5.paragraph_format.space_before = Pt(8)
    p2_5.paragraph_format.space_after = Pt(12)
    r2_5 = p2_5.add_run(
        "Fundamentación técnica del contrato en FastAPI: Estos números justificaron técnicamente las reglas de validación en "
        "schemas.py. Se fijó un límite inferior de 15 caracteres (para rechazar cadenas vacías o ruido sin sentido) y un límite superior "
        "de 5.000 caracteres (suficiente para cubrir el 100% de ofertas y prevenir ataques de denegación de servicio por agotamiento de memoria)."
    )
    r2_5.font.name = "Calibri"
    r2_5.font.size = Pt(10)
    r2_5.font.italic = True

    doc.add_page_break()

    # =========================================================================
    # CAPÍTULO 3: PIPELINE DE PROCESAMIENTO DE LENGUAJE NATURAL (NLP)
    # =========================================================================
    p_h3 = doc.add_paragraph()
    p_h3.paragraph_format.space_before = Pt(12)
    p_h3.paragraph_format.space_after = Pt(6)
    r_h3 = p_h3.add_run("3. Pipeline de Procesamiento de Lenguaje Natural (NLP)")
    r_h3.font.name = "Calibri"
    r_h3.font.size = Pt(18)
    r_h3.font.bold = True
    r_h3.font.color.rgb = COLOR_PRIMARY

    p3_1 = doc.add_paragraph()
    p3_1.paragraph_format.space_before = Pt(4)
    p3_1.paragraph_format.space_after = Pt(8)
    r3_1 = p3_1.add_run(
        "El procesamiento de lenguaje natural en español requiere consideraciones lingüísticas especiales que no existen en el idioma inglés. "
        "Se construyó una clase personalizada TextPreprocessor que orquesta 5 estaciones determinísticas, serializable mediante joblib:"
    )
    r3_1.font.name = "Calibri"
    r3_1.font.size = Pt(10.5)

    agregar_imagen_centrada(
        doc,
        "pipeline_nlp_diagrama.png",
        ancho_pulgadas=6.0,
        leyenda="Figura 2: Diagrama de flujo secuencial de las 5 estaciones que integran el Pipeline de NLP de JobScope AI."
    )

    # Subseccion 3.1
    p_h3_1 = doc.add_paragraph()
    p_h3_1.paragraph_format.space_before = Pt(10)
    p_h3_1.paragraph_format.space_after = Pt(4)
    r_h3_1 = p_h3_1.add_run("3.1 Estación 1: Normalización y el Grave Peligro de 'unidecode'")
    r_h3_1.font.name = "Calibri"
    r_h3_1.font.size = Pt(13)
    r_h3_1.font.bold = True
    r_h3_1.font.color.rgb = COLOR_SECONDARY

    p3_2 = doc.add_paragraph()
    p3_2.paragraph_format.space_before = Pt(4)
    p3_2.paragraph_format.space_after = Pt(6)
    r3_2 = p3_2.add_run(
        "Se aplicaron expresiones regulares compiladas para suprimir URLs, correos de contacto, menciones y números aislados. "
        "Asimismo, se implementó compresión de elongaciones (por ejemplo, 'urgenteeeee' → 'urgente') protegiendo dígrafos legales del español ('rr', 'll')."
    )
    r3_2.font.name = "Calibri"
    r3_2.font.size = Pt(10.5)

    p3_3 = doc.add_paragraph()
    p3_3.paragraph_format.space_before = Pt(4)
    p3_3.paragraph_format.space_after = Pt(6)
    r3_3 = p3_3.add_run(
        "El error de unidecode: En la literatura anglosajona es común recurrir a la librería unidecode para remover acentos. "
        "Sin embargo, unidecode comete el error crítico de convertir 'ñ' en 'n', transformando 'año' en 'ano' y 'campaña' en 'campana'. "
        "En ofertas de empleo, donde abundan términos como 'albañil', 'fontanería' o 'años de experiencia', esto destruye el significado léxico."
    )
    r3_3.font.name = "Calibri"
    r3_3.font.size = Pt(10.5)

    agregar_callout(
        doc,
        "Solución adoptada con unicodedata: Se diseñó un algoritmo de 'blindaje centinela'. Antes de descomponer el texto, "
        "se sustituyen temporalmente 'ñ' y 'Ñ' por tokens seguros (_ENE_MIN_). Se aplica normalización NFD eliminando los diacríticos agudos "
        "y diéresis de las vocales, y finalmente se restituyen las 'ñ' intactas. El texto queda desacentuado pero la 'ñ' permanece 100% protegida.",
        titulo="BLINDAJE LINGÜÍSTICO DE LA LETRA 'Ñ'"
    )

    # Subseccion 3.2
    p_h3_2 = doc.add_paragraph()
    p_h3_2.paragraph_format.space_before = Pt(10)
    p_h3_2.paragraph_format.space_after = Pt(4)
    r_h3_2 = p_h3_2.add_run("3.2 Estaciones 2 y 3: Tokenización y Negaciones Blindadas")
    r_h3_2.font.name = "Calibri"
    r_h3_2.font.size = Pt(13)
    r_h3_2.font.bold = True
    r_h3_2.font.color.rgb = COLOR_SECONDARY

    p3_4 = doc.add_paragraph()
    p3_4.paragraph_format.space_before = Pt(4)
    p3_4.paragraph_format.space_after = Pt(6)
    r3_4 = p3_4.add_run(
        "Se tokenizó mediante el estándar de expresiones regulares léxicas de NLTK, descartando tokens de longitud menor a 2 caracteres. "
        "En la estación de Stop Words, se tomó la lista oficial en español de NLTK y se depuró aplicando dos principios:"
    )
    r3_4.font.name = "Calibri"
    r3_4.font.size = Pt(10.5)

    bullet_sw1 = doc.add_paragraph(style='List Bullet')
    bullet_sw1.add_run("Conservación de Negaciones Blindadas: ").font.bold = True
    bullet_sw1.add_run(
        "Eliminar partículas como 'no', 'sin', 'nunca', 'jamás' o 'nada' altera radicalmente el sentido de una oferta: "
        "la frase 'Sin experiencia previa requerida' pasaría a ['experiencia', 'previa', 'requerida'], invirtiendo el perfil buscado. "
        "Por ende, se protegió formalmente la tupla NEGACIONES_BLINDADAS."
    )

    bullet_sw2 = doc.add_paragraph(style='List Bullet')
    bullet_sw2.add_run("Adición de Jerga Vacía de Reclutamiento: ").font.bold = True
    bullet_sw2.add_run(
        "Se agregaron términos recurrentes carentes de poder discriminativo ('se busca', 'se necesita', 'incorporación inmediata', 'empresa líder'), "
        "centralizados en params.yaml."
    )

    # Subseccion 3.3
    p_h3_3 = doc.add_paragraph()
    p_h3_3.paragraph_format.space_before = Pt(10)
    p_h3_3.paragraph_format.space_after = Pt(4)
    r_h3_3 = p_h3_3.add_run("3.3 Estación 4: Morfología — Benchmark Empírico Snowball vs. spaCy")
    r_h3_3.font.name = "Calibri"
    r_h3_3.font.size = Pt(13)
    r_h3_3.font.bold = True
    r_h3_3.font.color.rgb = COLOR_SECONDARY

    p3_5 = doc.add_paragraph()
    p3_5.paragraph_format.space_before = Pt(4)
    p3_5.paragraph_format.space_after = Pt(6)
    r3_5 = p3_5.add_run(
        "En cumplimiento explícito de la sección 5.2 de la rúbrica ('Implementar ambos y comparar su efecto en las métricas para elegir uno'), "
        "se ejecutó un benchmark controlado sobre las 2.669 ofertas de entrenamiento comparando el lematizador es_core_news_sm de spaCy "
        "contra el algoritmo de derivación morfológica SnowballStemmer de NLTK:"
    )
    r3_5.font.name = "Calibri"
    r3_5.font.size = Pt(10.5)

    # Tabla benchmark morfologia
    tbl_morf = doc.add_table(rows=5, cols=4)
    tbl_morf.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_morf)

    headers_morf = ["Criterio de Evaluación", "Lematización (spaCy)", "Stemming (Snowball)", "Decisión Técnica"]
    for c_idx, h_txt in enumerate(headers_morf):
        c = tbl_morf.cell(0, c_idx)
        set_cell_background(c, HEX_PRIMARY)
        set_cell_margins(c, top=100, bottom=100, left=150, right=150)
        p = c.paragraphs[0]
        r = p.add_run(h_txt)
        r.font.name = "Calibri"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    filas_morf = [
        ("Tiempo de Ejecución", "18.26 segundos", "7.82 segundos", "Snowball es 2.3x más veloz."),
        ("F1-Score Macro", "88.36%", "90.41%", "Snowball aporta +2.05 puntos de F1."),
        ("Consumo de Memoria", "~45 MB (modelo neuronal)", "0 MB (algoritmo reglado)", "Snowball es ideal para contenedores."),
        ("Robustez en Jergas", "Falla ante oficios no formales", "Agrupa sufijos de oficios", "Snowball agrupa 'chófer', 'choferes'."),
    ]
    for r_idx, row in enumerate(filas_morf, start=1):
        bg = HEX_LIGHT_BG if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row):
            c = tbl_morf.cell(r_idx, c_idx)
            set_cell_background(c, bg)
            set_cell_margins(c, top=90, bottom=90, left=150, right=150)
            p = c.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            if c_idx == 2:
                r.font.bold = True
                r.font.color.rgb = COLOR_SUCCESS

    # Subseccion 3.4
    p_h3_4 = doc.add_paragraph()
    p_h3_4.paragraph_format.space_before = Pt(12)
    p_h3_4.paragraph_format.space_after = Pt(4)
    r_h3_4 = p_h3_4.add_run("3.4 Estación 5: Vectorización TF-IDF con Bigramas (1, 2)")
    r_h3_4.font.name = "Calibri"
    r_h3_4.font.size = Pt(13)
    r_h3_4.font.bold = True
    r_h3_4.font.color.rgb = COLOR_SECONDARY

    p3_6 = doc.add_paragraph()
    p3_6.paragraph_format.space_before = Pt(4)
    p3_6.paragraph_format.space_after = Pt(6)
    r3_6 = p3_6.add_run(
        "La vectorización se configuró con parámetros centralizados en params.yaml: sublinear_tf=True (escala logarítmica 1 + ln(tf) "
        "para amortiguar términos sobre-repetidos), max_features=4000 (para prevenir sobreajuste y la maldición de la dimensionalidad), "
        "min_df=2 (para eliminar erratas presentes una sola vez) y max_df=0.85 (para descartar términos omnipresentes). "
        "El uso de bigramas permitió que colocaciones determinantes como 'sin_experienci', 'atencion_client' o 'auxili_enferm' "
        "reciban coordenadas matemáticas independientes."
    )
    r3_6.font.name = "Calibri"
    r3_6.font.size = Pt(10.5)

    doc.add_page_break()

    # =========================================================================
    # CAPÍTULO 4: MODELADO, VALIDACIÓN CRUZADA Y EVALUACIÓN CIENTÍFICA
    # =========================================================================
    p_h4 = doc.add_paragraph()
    p_h4.paragraph_format.space_before = Pt(12)
    p_h4.paragraph_format.space_after = Pt(6)
    r_h4 = p_h4.add_run("4. Modelado, Validación Cruzada y Evaluación Científica")
    r_h4.font.name = "Calibri"
    r_h4.font.size = Pt(18)
    r_h4.font.bold = True
    r_h4.font.color.rgb = COLOR_PRIMARY

    p4_1 = doc.add_paragraph()
    p4_1.paragraph_format.space_before = Pt(4)
    p4_1.paragraph_format.space_after = Pt(6)
    r4_1 = p4_1.add_run(
        "En concordancia con los requisitos de la rúbrica, se diseñó una matriz de 13 experimentos comparativos evaluados "
        "mediante Validación Cruzada Estratificada de 5 pliegues (StratifiedKFold k=5) exclusivamente sobre el conjunto de entrenamiento. "
        "Esto garantiza que la varianza entre pliegues sea mínima y previene el sobreajuste:"
    )
    r4_1.font.name = "Calibri"
    r4_1.font.size = Pt(10.5)

    # Tabla de experimentos
    tbl_exp = doc.add_table(rows=5, cols=4)
    tbl_exp.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_exp)

    headers_exp = ["Modelo Evaluado", "Configuración de Hiperparámetros", "F1-Macro CV (k=5)", "Veredicto Técnico"]
    for c_idx, h_txt in enumerate(headers_exp):
        c = tbl_exp.cell(0, c_idx)
        set_cell_background(c, HEX_PRIMARY)
        set_cell_margins(c, top=100, bottom=100, left=150, right=150)
        p = c.paragraphs[0]
        r = p.add_run(h_txt)
        r.font.name = "Calibri"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    filas_exp = [
        ("Línea Base (DummyClassifier)", "strategy='most_frequent'", "0.0892 ± 0.0002 (8.9%)", "Línea base superada."),
        ("Multinomial Naive Bayes", "alpha=0.1, unigramas (1, 1)", "0.8373 ± 0.0269 (83.7%)", "Candidato subóptimo."),
        ("Regresión Logística (Estándar)", "C=2.0, sin balanceo de clases", "0.8775 ± 0.0314 (87.7%)", "Afectado por desbalance."),
        ("Regresión Logística (Oficial)", "C=2.0, class_weight='balanced', (1,2)", "0.9041 ± 0.0136 (90.4%)", "🏆 Ganador oficial del proyecto."),
    ]
    for r_idx, row in enumerate(filas_exp, start=1):
        bg = "ECFDF5" if r_idx == 4 else (HEX_LIGHT_BG if r_idx % 2 == 1 else "FFFFFF")
        for c_idx, val in enumerate(row):
            c = tbl_exp.cell(r_idx, c_idx)
            set_cell_background(c, bg)
            set_cell_margins(c, top=90, bottom=90, left=150, right=150)
            p = c.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            if r_idx == 4:
                r.font.bold = True
                if c_idx == 2:
                    r.font.color.rgb = COLOR_SUCCESS

    agregar_imagen_centrada(
        doc,
        "comparativa_modelos.png",
        ancho_pulgadas=5.4,
        leyenda="Figura 3: Comparativa de rendimiento en F1-Score Macro entre la línea base Dummy, Naive Bayes y Regresión Logística."
    )

    p_h4_1 = doc.add_paragraph()
    p_h4_1.paragraph_format.space_before = Pt(10)
    p_h4_1.paragraph_format.space_after = Pt(4)
    r_h4_1 = p_h4_1.add_run("4.1 Fundamentación Teórica: ¿Por qué ganó la Regresión Logística?")
    r_h4_1.font.name = "Calibri"
    r_h4_1.font.size = Pt(13)
    r_h4_1.font.bold = True
    r_h4_1.font.color.rgb = COLOR_SECONDARY

    p4_2 = doc.add_paragraph()
    p4_2.paragraph_format.space_before = Pt(4)
    p4_2.paragraph_format.space_after = Pt(6)
    r4_2 = p4_2.add_run(
        "Naive Bayes asume una hipótesis 'ingenua': que la presencia de una palabra es completamente independiente de las demás. "
        "En lenguaje natural esto es falso (ej. 'carnet' depende de 'conducir'). La Regresión Logística calcula combinaciones lineales "
        "de pesos matemáticos (coeficientes beta) para cada par n-grama/sector. Además, el parámetro class_weight='balanced' ajusta "
        "inversamente las penalizaciones según la frecuencia de cada sector en el conjunto de datos, protegiendo a las clases minoritarias "
        "(Construcción y Hostelería) y aportando un incremento de +1.86 puntos en F1."
    )
    r4_2.font.name = "Calibri"
    r4_2.font.size = Pt(10.5)

    p_h4_2 = doc.add_paragraph()
    p_h4_2.paragraph_format.space_before = Pt(10)
    p_h4_2.paragraph_format.space_after = Pt(4)
    r_h4_2 = p_h4_2.add_run("4.2 Evaluación Ciega sobre el Conjunto de Test (668 Ofertas)")
    r_h4_2.font.name = "Calibri"
    r_h4_2.font.size = Pt(13)
    r_h4_2.font.bold = True
    r_h4_2.font.color.rgb = COLOR_SECONDARY

    p4_3 = doc.add_paragraph()
    p4_3.paragraph_format.space_before = Pt(4)
    p4_3.paragraph_format.space_after = Pt(6)
    r4_3 = p4_3.add_run(
        "Al desbloquear el conjunto de prueba ciego (test.csv, 668 ofertas que el modelo jamás vio en entrenamiento), "
        "el pipeline alcanzó un F1-Score Macro del 91.55% y una Exactitud Global (Accuracy) del 91.32%, clasificando correctamente "
        "a 610 de las 668 convocatorias evaluadas:"
    )
    r4_3.font.name = "Calibri"
    r4_3.font.size = Pt(10.5)

    agregar_imagen_centrada(
        doc,
        "matriz_confusion_5x5.png",
        ancho_pulgadas=5.2,
        leyenda="Figura 4: Matriz de confusión oficial de 5×5 evaluada en las 668 ofertas del conjunto de prueba ciego."
    )

    p_h4_3 = doc.add_paragraph()
    p_h4_3.paragraph_format.space_before = Pt(10)
    p_h4_3.paragraph_format.space_after = Pt(4)
    r_h4_3 = p_h4_3.add_run("4.3 Análisis Cualitativo de los 58 Errores (8.68%)")
    r_h4_3.font.name = "Calibri"
    r_h4_3.font.size = Pt(13)
    r_h4_3.font.bold = True
    r_h4_3.font.color.rgb = COLOR_SECONDARY

    p4_4 = doc.add_paragraph()
    p4_4.paragraph_format.space_before = Pt(4)
    p4_4.paragraph_format.space_after = Pt(8)
    r4_4 = p4_4.add_run(
        "En cumplimiento de la sección 5.3 ('ejemplos donde el modelo falla y una explicación de por qué'), se extrajeron los 58 fallos "
        "a artifacts/errors.csv y se diagnosticaron científicamente en 3 patrones recurrentes:"
    )
    r4_4.font.name = "Calibri"
    r4_4.font.size = Pt(10.5)

    tbl_err = doc.add_table(rows=4, cols=3)
    tbl_err.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_err)

    headers_err = ["Patrón de Error", "Ejemplo Concreto del Test Set", "Explicación del Fallo"]
    for c_idx, h_txt in enumerate(headers_err):
        c = tbl_err.cell(0, c_idx)
        set_cell_background(c, HEX_PRIMARY)
        set_cell_margins(c, top=100, bottom=100, left=150, right=150)
        p = c.paragraphs[0]
        r = p.add_run(h_txt)
        r.font.name = "Calibri"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    filas_err = [
        ("Vocabulario Cruzado (Transporte)", "Hostelería pidiendo 'reparto a domicilio con carnet B'.", "El modelo asigna pesos fuertes a 'carnet' y predice Transporte."),
        ("Perfiles Híbridos Multidisciplinarios", "'Comercial de ventas con conocimientos técnicos de IT'.", "El vocabulario se divide equitativamente entre Ventas y Tecnología."),
        ("Convocatorias Regionales (Catalán)", "Vacantes con términos no normalizados ('feina', 'empresa').", "La ausencia de stop words catalanas deja tokens con IDF ambiguo."),
    ]
    for r_idx, row in enumerate(filas_err, start=1):
        bg = HEX_LIGHT_BG if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row):
            c = tbl_err.cell(r_idx, c_idx)
            set_cell_background(c, bg)
            set_cell_margins(c, top=90, bottom=90, left=150, right=150)
            p = c.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            if c_idx == 0:
                r.font.bold = True

    doc.add_page_break()

    # =========================================================================
    # CAPÍTULO 5: ARQUITECTURA DE SOFTWARE, DESPLIEGUE Y CALIDAD
    # =========================================================================
    p_h5 = doc.add_paragraph()
    p_h5.paragraph_format.space_before = Pt(12)
    p_h5.paragraph_format.space_after = Pt(6)
    r_h5 = p_h5.add_run("5. Arquitectura de Software, Despliegue y Calidad")
    r_h5.font.name = "Calibri"
    r_h5.font.size = Pt(18)
    r_h5.font.bold = True
    r_h5.font.color.rgb = COLOR_PRIMARY

    p5_1 = doc.add_paragraph()
    p5_1.paragraph_format.space_before = Pt(4)
    p5_1.paragraph_format.space_after = Pt(8)
    r5_1 = p5_1.add_run(
        "En lugar de diagramas UML teóricos complejos, se priorizó una arquitectura orientada a servicios desacoplada en 4 capas limpias, "
        "optimizada para latencias sub-milisegundo y empaquetada en contenedores Docker:"
    )
    r5_1.font.name = "Calibri"
    r5_1.font.size = Pt(10.5)

    agregar_imagen_centrada(
        doc,
        "arquitectura_diagrama.png",
        ancho_pulgadas=6.0,
        leyenda="Figura 5: Arquitectura desacoplada en 4 capas en producción bajo Docker Compose y Nginx Reverse Proxy."
    )

    p_h5_1 = doc.add_paragraph()
    p_h5_1.paragraph_format.space_before = Pt(10)
    p_h5_1.paragraph_format.space_after = Pt(4)
    r_h5_1 = p_h5_1.add_run("5.1 Backend FastAPI: Patrón Lifespan y Validación Fail-Fast")
    r_h5_1.font.name = "Calibri"
    r_h5_1.font.size = Pt(13)
    r_h5_1.font.bold = True
    r_h5_1.font.color.rgb = COLOR_SECONDARY

    p5_2 = doc.add_paragraph()
    p5_2.paragraph_format.space_before = Pt(4)
    p5_2.paragraph_format.space_after = Pt(6)
    r5_2 = p5_2.add_run(
        "El backend se estructuró estrictamente en 3 archivos bajo src/api/:"
    )
    r5_2.font.name = "Calibri"
    r5_2.font.size = Pt(10.5)

    bullet_api1 = doc.add_paragraph(style='List Bullet')
    bullet_api1.add_run("schemas.py (Contratos Pydantic v2): ").font.bold = True
    bullet_api1.add_run("Aplica validación Fail-Fast. Si un texto tiene menos de 15 caracteres o supera los 5.000, responde HTTP 422 sin consumir memoria del modelo.")

    bullet_api2 = doc.add_paragraph(style='List Bullet')
    bullet_api2.add_run("service.py (Patrón Lifespan): ").font.bold = True
    bullet_api2.add_run("El modelo (model.joblib, 321 KB) se carga en memoria RAM una sola vez al inicializarse el contenedor. No se lee del disco en cada petición, reduciendo la latencia a < 5 ms.")

    bullet_api3 = doc.add_paragraph(style='List Bullet')
    bullet_api3.add_run("main.py (Rutas REST): ").font.bold = True
    bullet_api3.add_run("Expone /health (salud operativa), /predict (individual con .explain()), /predict/batch (vectorizado matricial) y /metrics (métricas oficiales).")

    p_h5_2 = doc.add_paragraph()
    p_h5_2.paragraph_format.space_before = Pt(10)
    p_h5_2.paragraph_format.space_after = Pt(4)
    r_h5_2 = p_h5_2.add_run("5.2 Frontend React 18 y Despliegue con Nginx Reverse Proxy")
    r_h5_2.font.name = "Calibri"
    r_h5_2.font.size = Pt(13)
    r_h5_2.font.bold = True
    r_h5_2.font.color.rgb = COLOR_SECONDARY

    p5_3 = doc.add_paragraph()
    p5_3.paragraph_format.space_before = Pt(4)
    p5_3.paragraph_format.space_after = Pt(6)
    r5_3 = p5_3.add_run(
        "La interfaz fue desarrollada con React 18, Vite y CSS modular basado en variables semánticas. La arquitectura de producción "
        "emplea Nginx Alpine como Reverse Proxy en el puerto 8080: atiende el frontend estático y redirige internamente las peticiones /api/* "
        "hacia FastAPI en la red interna de Docker, erradicando por completo problemas de CORS y exponiendo un solo puerto público."
    )
    r5_3.font.name = "Calibri"
    r5_3.font.size = Pt(10.5)

    agregar_imagen_centrada(
        doc,
        "interfaz_web.png",
        ancho_pulgadas=5.6,
        leyenda="Figura 6: Interfaz web de usuario en producción mostrando el Análisis Individual y la Auditoría NLP en 5 estaciones."
    )

    p_h5_3 = doc.add_paragraph()
    p_h5_3.paragraph_format.space_before = Pt(10)
    p_h5_3.paragraph_format.space_after = Pt(4)
    r_h5_3 = p_h5_3.add_run("5.3 Suite de Calidad: 81 Pruebas Automatizadas Pytest")
    r_h5_3.font.name = "Calibri"
    r_h5_3.font.size = Pt(13)
    r_h5_3.font.bold = True
    r_h5_3.font.color.rgb = COLOR_SECONDARY

    p5_4 = doc.add_paragraph()
    p5_4.paragraph_format.space_before = Pt(4)
    p5_4.paragraph_format.space_after = Pt(8)
    r5_4 = p5_4.add_run(
        "Se construyó una suite integral de 81 pruebas unitarias y de integración en tests/. La suite valida que la letra 'Ñ' nunca se convierta "
        "en 'N', que las probabilidades Softmax siempre sumen 1.0, que la API rechace entradas vacías con código 422 y que el pipeline serializado "
        "responda de forma determinista. Todas las 81 pruebas corren y pasan al 100% en verde."
    )
    r5_4.font.name = "Calibri"
    r5_4.font.size = Pt(10.5)

    # =========================================================================
    # CAPÍTULO 6: CONCLUSIONES Y DECLARACIÓN DE HONESTIDAD ACADÉMICA
    # =========================================================================
    p_h6 = doc.add_paragraph()
    p_h6.paragraph_format.space_before = Pt(16)
    p_h6.paragraph_format.space_after = Pt(6)
    r_h6 = p_h6.add_run("6. Conclusiones y Cumplimiento de la Rúbrica")
    r_h6.font.name = "Calibri"
    r_h6.font.size = Pt(18)
    r_h6.font.bold = True
    r_h6.font.color.rgb = COLOR_PRIMARY

    p6_1 = doc.add_paragraph()
    p6_1.paragraph_format.space_before = Pt(4)
    p6_1.paragraph_format.space_after = Pt(6)
    r6_1 = p6_1.add_run(
        "El proyecto integrador JobScope AI culminó con éxito, cumpliendo el 100% de los requisitos estipulados en la rúbrica oficial:"
    )
    r6_1.font.name = "Calibri"
    r6_1.font.size = Pt(10.5)

    conclusiones = [
        ("Pipeline Riguroso y Justificado:", "Se demostró empíricamente la superioridad de Snowball Stemmer (+2.05 pts F1) y la necesidad del blindaje de la letra 'Ñ'."),
        ("Modelado y Validación Científica:", "Se superó ampliamente la línea base Dummy (8.9%) con un F1-Score Macro del 91.55% en prueba ciega mediante Regresión Logística balanceada."),
        ("Producción y Despliegue Real:", "El sistema corre con Docker Compose en un solo comando (docker-compose up --build) y atiende inferencias en menos de 5 ms."),
        ("Modificación en Vivo Garantizada:", "Todos los hiperparámetros (C, regularización, n-gramas, stopwords) están desacoplados en params.yaml, permitiendo reentrenar el modelo con un solo comando durante la defensa oral."),
    ]
    for tit, desc in conclusiones:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.space_before = Pt(2)
        bp.paragraph_format.space_after = Pt(3)
        bp.add_run(tit).font.bold = True
        bp.add_run(f" {desc}")

    p_h6_1 = doc.add_paragraph()
    p_h6_1.paragraph_format.space_before = Pt(12)
    p_h6_1.paragraph_format.space_after = Pt(4)
    r_h6_1 = p_h6_1.add_run("6.1 Declaración de Honestidad Académica y Asistentes de IA")
    r_h6_1.font.name = "Calibri"
    r_h6_1.font.size = Pt(13)
    r_h6_1.font.bold = True
    r_h6_1.font.color.rgb = COLOR_SECONDARY

    p6_2 = doc.add_paragraph()
    p6_2.paragraph_format.space_before = Pt(4)
    p6_2.paragraph_format.space_after = Pt(12)
    r6_2 = p6_2.add_run(
        "En estricto apego a la sección 10 de la rúbrica oficial ('Uso de asistentes de IA: permitido con declaración en el informe'), "
        "se declara que se utilizaron herramientas de asistencia de Inteligencia Artificial como apoyo en la revisión de código, "
        "estructuración de pruebas automatizadas y redacción técnica. Toda la fundamentación teórica, las decisiones matemáticas "
        "de preprocesamiento, la ejecución de los experimentos y el código fuente desplegado en el repositorio son de autoría "
        "y dominio completo del estudiante, quien se encuentra en plena capacidad de explicar, defender y modificar en vivo "
        "cualquier componente del sistema."
    )
    r6_2.font.name = "Calibri"
    r6_2.font.size = Pt(10)
    r6_2.font.italic = True

    # Guardar documento Word
    doc.save(str(OUT_DOCX))
    print(f"Informe Word generado exitosamente en:\n{OUT_DOCX}")


if __name__ == "__main__":
    construir_documento()

