"""Generador automatico del archivo PowerPoint (.pptx) para JobScope AI.

Crea 12 diapositivas ejecutivas en formato panoramico 16:9 alineadas al 100%
con la rubrica oficial, el EDA y la presentacion web.

Sin notas de orador nativas (diapositivas limpias y profesionales para el publico).
"""

from pathlib import Path
import sys

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    from pptx.enum.shapes import MSO_SHAPE
except ImportError:
    print("Error: La libreria 'python-pptx' no esta instalada.")
    print("Ejecuta: pip install python-pptx")
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
OUT_PPTX = BASE_DIR / "presentacion_jobscope.pptx"

# Paleta de colores ejecutiva Clean SaaS
C_BG = RGBColor(248, 250, 252)          # #F8FAFC
C_CARD_BG = RGBColor(255, 255, 255)     # Blanco
C_BORDER = RGBColor(226, 232, 240)      # #E2E8F0
C_PRIMARY = RGBColor(37, 99, 235)       # #2563EB (Azul primario)
C_TEXT = RGBColor(15, 23, 42)           # #0F172A (Texto principal oscuro)
C_MUTED = RGBColor(100, 116, 139)       # #64748B (Texto secundario)
C_SUCCESS = RGBColor(5, 150, 105)       # #059669 (Verde esmeralda)
C_DANGER = RGBColor(220, 38, 38)        # #DC2626 (Rojo alerta)
C_WARNING = RGBColor(217, 119, 6)       # #D97706 (Ambar / naranja)
C_DARK = RGBColor(11, 15, 25)           # #0B0F19 (Fondo oscuro codigo)


def aplicar_fondo(slide, prs):
    """Agrega un fondo suave uniforme de 16:9."""
    bg_shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height
    )
    bg_shape.fill.solid()
    bg_shape.fill.fore_color.rgb = C_BG
    bg_shape.line.fill.background()
    return bg_shape


def agregar_cabecera(slide, titulo_texto, badge_texto):
    """Crea la cabecera uniforme para cada diapositiva de contenido."""
    # Titulo principal
    t_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.35), Inches(8.8), Inches(0.75))
    tf = t_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = titulo_texto
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = C_TEXT

    # Badge de fase a la derecha
    b_box = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.8), Inches(0.38), Inches(2.7), Inches(0.42)
    )
    b_box.fill.solid()
    b_box.fill.fore_color.rgb = RGBColor(239, 246, 255)
    b_box.line.color.rgb = RGBColor(191, 219, 254)
    b_box.line.width = Pt(1)
    
    bf = b_box.text_frame
    bf.word_wrap = True
    bf.vertical_anchor = MSO_ANCHOR.MIDDLE
    bp = bf.paragraphs[0]
    bp.alignment = PP_ALIGN.CENTER
    bp.text = badge_texto.upper()
    bp.font.size = Pt(9.5)
    bp.font.bold = True
    bp.font.color.rgb = C_PRIMARY


def agregar_tarjeta(slide, left, top, width, height, bg_color=C_CARD_BG, border_color=C_BORDER, border_width=1):
    """Dibuja un rectangulo con estilo tarjeta limpia."""
    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height
    )
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = Pt(border_width)
    else:
        card.line.fill.background()
    return card


def agregar_imagen_segura(slide, nombre_archivo, left, top, width=None, height=None):
    """Inserta una imagen si existe en la carpeta assets."""
    img_path = ASSETS_DIR / nombre_archivo
    if img_path.exists():
        if width and height:
            return slide.shapes.add_picture(str(img_path), left, top, width=width, height=height)
        elif width:
            return slide.shapes.add_picture(str(img_path), left, top, width=width)
        elif height:
            return slide.shapes.add_picture(str(img_path), left, top, height=height)
        else:
            return slide.shapes.add_picture(str(img_path), left, top)
    else:
        print(f"Aviso: Imagen no encontrada: {img_path}")
        return None


def construir_presentacion():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    layout_vacio = prs.slide_layouts[6]

    # =========================================================================
    # SLIDE 1: PORTADA OFICIAL
    # =========================================================================
    s1 = prs.slides.add_slide(layout_vacio)
    aplicar_fondo(s1, prs)

    # Tarjeta central sutil
    agregar_tarjeta(s1, Inches(1.5), Inches(1.2), Inches(10.33), Inches(5.1), bg_color=C_CARD_BG, border_color=C_BORDER)

    tbox1 = s1.shapes.add_textbox(Inches(2.0), Inches(1.6), Inches(9.33), Inches(4.3))
    tf1 = tbox1.text_frame
    tf1.word_wrap = True

    # Tag de materia
    p_tag = tf1.paragraphs[0]
    p_tag.alignment = PP_ALIGN.CENTER
    p_tag.text = "PROYECTO INTEGRADOR — TÓPICOS Y PROGRAMACIÓN AVANZADA"
    p_tag.font.size = Pt(11)
    p_tag.font.bold = True
    p_tag.font.color.rgb = C_PRIMARY

    # Titulo principal
    p_title = tf1.add_paragraph()
    p_title.alignment = PP_ALIGN.CENTER
    p_title.text = "JobScope AI"
    p_title.font.size = Pt(46)
    p_title.font.bold = True
    p_title.font.color.rgb = C_TEXT
    p_title.space_before = Pt(10)

    # Subtitulo descriptivo
    p_sub = tf1.add_paragraph()
    p_sub.alignment = PP_ALIGN.CENTER
    p_sub.text = "Clasificación y Auditoría Inteligente de Ofertas Laborales en Español\nmediante NLP Riguroso y Machine Learning Supervisado"
    p_sub.font.size = Pt(17)
    p_sub.font.color.rgb = C_MUTED
    p_sub.space_before = Pt(12)

    # Linea divisoria de metadatos
    p_meta = tf1.add_paragraph()
    p_meta.alignment = PP_ALIGN.CENTER
    p_meta.text = "Autor: Adolfo Mendoza Ribera  ·  Stack: FastAPI · Scikit-Learn · React 18 · Docker Compose\nEvaluación Oficial: Noviembre 2026"
    p_meta.font.size = Pt(13)
    p_meta.font.bold = True
    p_meta.font.color.rgb = C_TEXT
    p_meta.space_before = Pt(28)

    # =========================================================================
    # SLIDE 2: EL PROBLEMA DE NEGOCIO Y NUESTRA SOLUCIÓN
    # =========================================================================
    s2 = prs.slides.add_slide(layout_vacio)
    aplicar_fondo(s2, prs)
    agregar_cabecera(s2, "El Problema de Negocio y Nuestra Solución", "Contexto y Propósito")

    # Tarjeta Izquierda: El Problema
    agregar_tarjeta(s2, Inches(0.8), Inches(1.3), Inches(5.6), Inches(5.6), border_color=C_DANGER, border_width=2)
    box2_l = s2.shapes.add_textbox(Inches(1.05), Inches(1.5), Inches(5.1), Inches(5.2))
    tf2_l = box2_l.text_frame
    tf2_l.word_wrap = True

    p = tf2_l.paragraphs[0]
    p.text = "⚠️  El Problema en Reclutamiento Actual"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = C_DANGER

    p = tf2_l.add_paragraph()
    p.text = "En plataformas masivas (LinkedIn, Computrabajo, Trabajópolis), miles de ofertas laborales se redactan en texto libre desestructurado:"
    p.font.size = Pt(12.5)
    p.font.color.rgb = C_TEXT
    p.space_before = Pt(8)

    p = tf2_l.add_paragraph()
    p.text = "• Categorización errónea: Reclutadores dudan ante perfiles híbridos o marcan categorías apresuradas."
    p.font.size = Pt(12)
    p.font.color.rgb = C_MUTED
    p.space_before = Pt(8)

    p = tf2_l.add_paragraph()
    p.text = "• Vacantes invisibles: Puestos mal indexados se pierden en la multitud sin llegar a los candidatos idóneos."
    p.font.size = Pt(12)
    p.font.color.rgb = C_MUTED
    p.space_before = Pt(6)

    p = tf2_l.add_paragraph()
    p.text = "• Alto costo operativo: La clasificación manual de 500 ofertas insume entre 4 y 6 horas de trabajo repetitivo."
    p.font.size = Pt(12)
    p.font.color.rgb = C_MUTED
    p.space_before = Pt(6)

    p = tf2_l.add_paragraph()
    p.text = "Impacto: Cuello de botella en RRHH y pérdida de talento calificado."
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = C_DANGER
    p.space_before = Pt(18)

    # Tarjeta Derecha: La Solución
    agregar_tarjeta(s2, Inches(6.9), Inches(1.3), Inches(5.6), Inches(5.6), border_color=C_SUCCESS, border_width=2)
    box2_r = s2.shapes.add_textbox(Inches(7.15), Inches(1.5), Inches(5.1), Inches(5.2))
    tf2_r = box2_r.text_frame
    tf2_r.word_wrap = True

    p = tf2_r.paragraphs[0]
    p.text = "💡  Nuestra Solución: JobScope AI"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = C_SUCCESS

    p = tf2_r.add_paragraph()
    p.text = "Un sistema integral de producción que ingesta texto crudo y predice el sector en milisegundos a través de 3 módulos clave:"
    p.font.size = Pt(12.5)
    p.font.color.rgb = C_TEXT
    p.space_before = Pt(8)

    soluciones = [
        ("1. Análisis Individual con Auditoría:", "Inferencia inmediata en 3 ms con desglose transparente paso a paso (cero caja negra)."),
        ("2. Procesamiento Masivo CSV:", "Carga de cientos de vacantes en lote y exportación enriquecida en menos de 1 segundo."),
        ("3. Panel de Métricas Científicas:", "Trazabilidad con matriz de confusión y explicabilidad global por coeficientes beta."),
    ]
    for tit, desc in soluciones:
        p = tf2_r.add_paragraph()
        p.text = f"{tit} {desc}"
        p.font.size = Pt(12)
        p.font.color.rgb = C_MUTED
        p.space_before = Pt(8)

    p = tf2_r.add_paragraph()
    p.text = "Beneficio clave: Ahorro del 95% de tiempo operativo y F1-Score de 91.55%."
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = C_SUCCESS
    p.space_before = Pt(16)

    # =========================================================================
    # SLIDE 3: DATASET EURES Y MAPEO A 5 SECTORES
    # =========================================================================
    s3 = prs.slides.add_slide(layout_vacio)
    aplicar_fondo(s3, prs)
    agregar_cabecera(s3, "Dataset EURES y Mapeo Jerárquico a 5 Sectores", "Fase 1: Datos y Curación")

    # Columna izquierda: Justificacion
    agregar_tarjeta(s3, Inches(0.8), Inches(1.3), Inches(5.6), Inches(5.6))
    box3_l = s3.shapes.add_textbox(Inches(1.05), Inches(1.5), Inches(5.1), Inches(5.2))
    tf3_l = box3_l.text_frame
    tf3_l.word_wrap = True

    p = tf3_l.paragraphs[0]
    p.text = "Origen y Principio de Inmutabilidad"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY

    p = tf3_l.add_paragraph()
    p.text = "Dataset oficial de la Red Europea EURES 2025 (MiguelGP-13/JobOffers_ESP). Las 7.261 filas crudas permanecen inmutables en data/raw/."
    p.font.size = Pt(12)
    p.font.color.rgb = C_TEXT
    p.space_before = Pt(6)

    p = tf3_l.add_paragraph()
    p.text = "Solución a la Dispersión de Clases:"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_WARNING
    p.space_before = Pt(16)

    p = tf3_l.add_paragraph()
    p.text = "El corpus original presentaba más de 300 oficios dispersos (pizzero, soldador, reponedor). Intentar clasificar 300 clases daría F1 < 20% y una matriz intratable de 300 × 300."
    p.font.size = Pt(12)
    p.font.color.rgb = C_TEXT
    p.space_before = Pt(6)

    p = tf3_l.add_paragraph()
    p.text = "Se implementó un mapeo jerárquico a 5 macro-sectores ESCO/EURES, consolidando 3.337 ofertas limpias, sin duplicados ni valores nulos."
    p.font.size = Pt(12)
    p.font.color.rgb = C_TEXT
    p.space_before = Pt(8)

    # Columna derecha: Los 5 Sectores
    agregar_tarjeta(s3, Inches(6.9), Inches(1.3), Inches(5.6), Inches(5.6))
    box3_r = s3.shapes.add_textbox(Inches(7.15), Inches(1.5), Inches(5.1), Inches(5.2))
    tf3_r = box3_r.text_frame
    tf3_r.word_wrap = True

    p = tf3_r.paragraphs[0]
    p.text = "Los 5 Sectores Económicos Oficiales:"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_TEXT

    sectores_datos = [
        ("🚛 Transporte y Logística", "914 ofertas (27.39%)", "Conductores, chóferes, reparto, almacén"),
        ("💼 Ventas y Comercial", "878 ofertas (26.31%)", "Comerciales, dependientes, asesores"),
        ("🩺 Salud y Servicios Sociales", "584 ofertas (17.50%)", "Enfermería, médicos, cuidado asistencial"),
        ("🍳 Hostelería y Gastronomía", "512 ofertas (15.34%)", "Cocineros, camareros, servicios de bar"),
        ("🏗️ Construcción y Mantenimiento", "449 ofertas (13.46%)", "Albañiles, electricistas, obras"),
    ]
    for tit, of, desc in sectores_datos:
        p = tf3_r.add_paragraph()
        p.text = f"{tit}  ·  {of}"
        p.font.size = Pt(12.5)
        p.font.bold = True
        p.font.color.rgb = C_PRIMARY
        p.space_before = Pt(10)

        p2 = tf3_r.add_paragraph()
        p2.text = f"   {desc}"
        p2.font.size = Pt(11)
        p2.font.color.rgb = C_MUTED
        p2.space_before = Pt(1)

    # =========================================================================
    # SLIDE 4: ANALISIS EXPLORATORIO (EDA) Y PARTICION ANTI-LEAKAGE
    # =========================================================================
    s4 = prs.slides.add_slide(layout_vacio)
    aplicar_fondo(s4, prs)
    agregar_cabecera(s4, "Análisis Exploratorio (EDA) y Partición Anti-Leakage", "Fase 1: EDA y Validación")

    # Tarjeta Izquierda: Explicaciones y Percentiles
    agregar_tarjeta(s4, Inches(0.8), Inches(1.3), Inches(5.6), Inches(5.6))
    box4_l = s4.shapes.add_textbox(Inches(1.05), Inches(1.5), Inches(5.1), Inches(5.2))
    tf4_l = box4_l.text_frame
    tf4_l.word_wrap = True

    p = tf4_l.paragraphs[0]
    p.text = "Partición Estratificada 80/20 (seed: 42)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY

    p = tf4_l.add_paragraph()
    p.text = "• Conjunto de Entrenamiento: 2.669 ofertas (train.csv)\n• Conjunto de Prueba Ciega: 668 ofertas (test.csv)"
    p.font.size = Pt(12)
    p.font.color.rgb = C_TEXT
    p.space_before = Pt(6)

    p = tf4_l.add_paragraph()
    p.text = "Blindaje Estricto Anti Data Leakage:"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_SUCCESS
    p.space_before = Pt(14)

    p = tf4_l.add_paragraph()
    p.text = "El vocabulario, frecuencias IDF y estimadores se calcularon ÚNICAMENTE sobre Train (fit_transform). El Test se mantuvo 100% aislado (solo transform)."
    p.font.size = Pt(12)
    p.font.color.rgb = C_MUTED
    p.space_before = Pt(4)

    p = tf4_l.add_paragraph()
    p.text = "Percentiles del EDA y Contratos FastAPI:"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_WARNING
    p.space_before = Pt(14)

    p = tf4_l.add_paragraph()
    p.text = "• Mediana P50: 315 caracteres (78 palabras por oferta).\n• Percentil P99: 1.827 caracteres.\n• Justificación: Estos datos fundamentaron el rango estricto de [15, 5000] caracteres en Pydantic v2 para rechazar entradas vacías y prevenir ataques DoS."
    p.font.size = Pt(11.5)
    p.font.color.rgb = C_TEXT
    p.space_before = Pt(4)

    # Columna Derecha: Imagen distribucion_sectores.png
    agregar_tarjeta(s4, Inches(6.9), Inches(1.3), Inches(5.6), Inches(5.6))
    agregar_imagen_segura(s4, "distribucion_sectores.png", Inches(7.1), Inches(1.5), width=Inches(5.2))

    # =========================================================================
    # SLIDE 5: NLP 1 - LIMPIEZA Y BLINDAJE DE LA "Ñ"
    # =========================================================================
    s5 = prs.slides.add_slide(layout_vacio)
    aplicar_fondo(s5, prs)
    agregar_cabecera(s5, 'Pipeline de NLP: Limpieza y Blindaje de la "Ñ"', "Fase 2.1: Normalización")

    # Columna Izquierda: Reglas y Peligro
    agregar_tarjeta(s5, Inches(0.8), Inches(1.3), Inches(5.6), Inches(5.6))
    box5_l = s5.shapes.add_textbox(Inches(1.05), Inches(1.5), Inches(5.1), Inches(5.2))
    tf5_l = box5_l.text_frame
    tf5_l.word_wrap = True

    p = tf5_l.paragraphs[0]
    p.text = "1. Supresión de Ruido Web y Tipográfico"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY

    p = tf5_l.add_paragraph()
    p.text = "Expresiones regulares compiladas eliminan URLs (https://...), correos electrónicos y menciones. Se reducen elongaciones ('urgenteeeee' → 'urgente') preservando dígrafos válidos ('rr', 'll')."
    p.font.size = Pt(11.5)
    p.font.color.rgb = C_TEXT
    p.space_before = Pt(4)

    p = tf5_l.add_paragraph()
    p.text = "2. El Grave Peligro de librerías tipo 'unidecode'"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_DANGER
    p.space_before = Pt(12)

    p = tf5_l.add_paragraph()
    p.text = "Al desacentuar texto en español, las librerías en inglés convierten 'ñ' en 'n':\n• 'año' → 'ano'\n• 'campaña' → 'campana'\nEsto destruye totalmente la semántica de las ofertas de trabajo."
    p.font.size = Pt(11.5)
    p.font.color.rgb = C_TEXT
    p.space_before = Pt(4)

    p = tf5_l.add_paragraph()
    p.text = "3. Nuestra Solución con unicodedata"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_SUCCESS
    p.space_before = Pt(12)

    p = tf5_l.add_paragraph()
    p.text = "Blindaje centinela: protegemos temporalmente 'ñ'/'Ñ', descomponemos acentos gráficos en NFD (eliminando tildes agudas y diéresis) y restauramos la 'ñ' intacta."
    p.font.size = Pt(11.5)
    p.font.color.rgb = C_TEXT
    p.space_before = Pt(4)

    # Columna Derecha: Tarjeta oscura didactica
    agregar_tarjeta(s5, Inches(6.9), Inches(1.3), Inches(5.6), Inches(5.6), bg_color=C_DARK, border_color=RGBColor(30, 41, 59))
    box5_r = s5.shapes.add_textbox(Inches(7.15), Inches(1.6), Inches(5.1), Inches(5.0))
    tf5_r = box5_r.text_frame
    tf5_r.word_wrap = True

    p = tf5_r.paragraphs[0]
    p.text = "TRANSFORMACIÓN PASO A PASO EN VIVO:"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = RGBColor(56, 189, 248)

    ejemplos = [
        ("// 1. Texto crudo original:", '"¡¡URGENTEEEEE!! Chofer para camión en España. Contacto: rrhh@job.es"', RGBColor(248, 113, 113)),
        ("// 2. Normalización de elongaciones y ruido:", '"urgente chofer para camión en españa"', RGBColor(251, 191, 36)),
        ("// 3. Desacentuar conservando la Ñ:", '"urgente chofer para camion en españa"\n(camion sin tilde, ¡España con ñ intacta!)', RGBColor(52, 211, 153)),
        ("// 4. Tokenización léxica (longitud >= 2):", "['urgente', 'chofer', 'para', 'camion', 'en', 'españa']", RGBColor(56, 189, 248)),
    ]
    for label, code, color in ejemplos:
        p = tf5_r.add_paragraph()
        p.text = label
        p.font.size = Pt(11)
        p.font.color.rgb = RGBColor(148, 163, 184)
        p.space_before = Pt(14)

        p2 = tf5_r.add_paragraph()
        p2.text = code
        p2.font.size = Pt(11.5)
        p2.font.bold = True
        p2.font.color.rgb = color
        p2.space_before = Pt(2)

    # =========================================================================
    # SLIDE 6: NLP 2 - NEGACIONES BLINDADAS Y MORFOLOGIA
    # =========================================================================
    s6 = prs.slides.add_slide(layout_vacio)
    aplicar_fondo(s6, prs)
    agregar_cabecera(s6, "Pipeline de NLP: Negaciones Blindadas y Morfología", "Fases 2.2 y 2.3: Estaciones NLP")

    # Columna Izquierda: Negaciones
    agregar_tarjeta(s6, Inches(0.8), Inches(1.3), Inches(5.6), Inches(5.6))
    box6_l = s6.shapes.add_textbox(Inches(1.05), Inches(1.5), Inches(5.1), Inches(5.2))
    tf6_l = box6_l.text_frame
    tf6_l.word_wrap = True

    p = tf6_l.paragraphs[0]
    p.text = "Stop Words con Negaciones Blindadas 🛡️"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_WARNING

    p = tf6_l.add_paragraph()
    p.text = "En clasificación de vacantes de empleo, eliminar partículas como 'no', 'sin' o 'nunca' invierte por completo los requisitos del puesto:"
    p.font.size = Pt(12)
    p.font.color.rgb = C_TEXT
    p.space_before = Pt(8)

    p = tf6_l.add_paragraph()
    p.text = "'Sin experiencia requerida' → Sin protección pasa a ['experiencia', 'requerida'] ❌"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = C_DANGER
    p.space_before = Pt(10)

    p = tf6_l.add_paragraph()
    p.text = "Definimos NEGACIONES_BLINDADAS (no, sin, nunca, jamás, nada) y añadimos jerga vacía de reclutamiento ('se busca', 'se necesita') configurable en params.yaml."
    p.font.size = Pt(12)
    p.font.color.rgb = C_MUTED
    p.space_before = Pt(10)

    p = tf6_l.add_paragraph()
    p.text = "Alineación diacrítica: las stop words se desacentúan con la misma función que el texto para evitar desalineaciones."
    p.font.size = Pt(11)
    p.font.color.rgb = C_PRIMARY
    p.space_before = Pt(14)

    # Columna Derecha: Morfologia Benchmark
    agregar_tarjeta(s6, Inches(6.9), Inches(1.3), Inches(5.6), Inches(5.6))
    box6_r = s6.shapes.add_textbox(Inches(7.15), Inches(1.5), Inches(5.1), Inches(5.2))
    tf6_r = box6_r.text_frame
    tf6_r.word_wrap = True

    p = tf6_r.paragraphs[0]
    p.text = "Morfología: Stemming vs Lematización"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY

    p = tf6_r.add_paragraph()
    p.text = "Evaluación empírica según exige la rúbrica oficial:"
    p.font.size = Pt(12)
    p.font.color.rgb = C_TEXT
    p.space_before = Pt(6)

    # Tabla comparativa
    table_shape = s6.shapes.add_table(4, 3, Inches(7.15), Inches(2.6), Inches(5.1), Inches(2.4))
    table = table_shape.table
    table.columns[0].width = Inches(1.7)
    table.columns[1].width = Inches(1.7)
    table.columns[2].width = Inches(1.7)

    headers = ["Criterio", "Lematización (spaCy)", "Stemming (Snowball)"]
    for col_idx, h_text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.text = h_text
        p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = C_TEXT

    filas = [
        ("Velocidad", "18.26 seg", "7.82 seg (2.3x veloz)"),
        ("F1-Macro", "88.36%", "90.41% (+2.05 pts) 🏆"),
        ("Jergas laborales", "Falla en oficios raros", "Robusto con sufijos"),
    ]
    for row_idx, (c0, c1, c2) in enumerate(filas, start=1):
        for col_idx, val in enumerate([c0, c1, c2]):
            cell = table.cell(row_idx, col_idx)
            cell.text = val
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(9.5)
            if col_idx == 2:
                p.font.bold = True
                p.font.color.rgb = C_SUCCESS

    # Nota final debajo de tabla
    box6_sub = s6.shapes.add_textbox(Inches(7.15), Inches(5.3), Inches(5.1), Inches(1.2))
    tf6_sub = box6_sub.text_frame
    tf6_sub.word_wrap = True
    p = tf6_sub.paragraphs[0]
    p.text = "Clase TextPreprocessor: implementa .explain() para auditoría anatómica en vivo en FastAPI y React."
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY

    # =========================================================================
    # SLIDE 7: TF-IDF Y PIPELINE UNIFICADO
    # =========================================================================
    s7 = prs.slides.add_slide(layout_vacio)
    aplicar_fondo(s7, prs)
    agregar_cabecera(s7, "Vectorización TF-IDF (1, 2) y Pipeline Unificado", "Fase 2.4: Representación Vectorial")

    # Diagrama superior
    agregar_tarjeta(s7, Inches(0.8), Inches(1.3), Inches(11.73), Inches(2.3))
    agregar_imagen_segura(s7, "pipeline_nlp_diagrama.png", Inches(1.0), Inches(1.4), width=Inches(11.33))

    # Columna Izquierda: N-gramas
    agregar_tarjeta(s7, Inches(0.8), Inches(3.8), Inches(5.6), Inches(3.1))
    box7_l = s7.shapes.add_textbox(Inches(1.05), Inches(3.95), Inches(5.1), Inches(2.8))
    tf7_l = box7_l.text_frame
    tf7_l.word_wrap = True

    p = tf7_l.paragraphs[0]
    p.text = "Captura de Contexto con N-Gramas (1, 2)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY

    p = tf7_l.add_paragraph()
    p.text = "Los unigramas destruyen el orden contextual. Con bigramas, colocaciones decisivas como 'sin_experienci', 'atencion_client' o 'auxili_enferm' obtienen un peso numérico independiente."
    p.font.size = Pt(11.5)
    p.font.color.rgb = C_TEXT
    p.space_before = Pt(6)

    p = tf7_l.add_paragraph()
    p.text = "Cálculo verificado a mano con smooth_idf=True y normalización L2 en tests/test_pipeline.py."
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = C_MUTED
    p.space_before = Pt(8)

    # Columna Derecha: Hiperparametros
    agregar_tarjeta(s7, Inches(6.9), Inches(3.8), Inches(5.6), Inches(3.1))
    box7_r = s7.shapes.add_textbox(Inches(7.15), Inches(3.95), Inches(5.1), Inches(2.8))
    tf7_r = box7_r.text_frame
    tf7_r.word_wrap = True

    p = tf7_r.paragraphs[0]
    p.text = "Hiperparámetros Clave en params.yaml"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_WARNING

    params_info = [
        ("max_features: 4000", "Previene sobreajuste y maldición de la dimensionalidad."),
        ("min_df: 2", "Descarta erratas tipográficas presentes solo 1 vez."),
        ("max_df: 0.85", "Filtra palabras omnipresentes sin poder discriminativo."),
        ("sublinear_tf: true", "Escala logarítmica 1 + ln(tf) para amortiguar repeticiones."),
    ]
    for param, desc in params_info:
        p = tf7_r.add_paragraph()
        p.text = f"• {param}: {desc}"
        p.font.size = Pt(11)
        p.font.color.rgb = C_TEXT
        p.space_before = Pt(4)

    # =========================================================================
    # SLIDE 8: MATRIZ DE 13 EXPERIMENTOS Y VALIDACION CRUZADA
    # =========================================================================
    s8 = prs.slides.add_slide(layout_vacio)
    aplicar_fondo(s8, prs)
    agregar_cabecera(s8, "Matriz de 13 Experimentos y Validación Cruzada", "Fase 3.1: Modelado y Comparación")

    # Columna Izquierda: Tabla y Explicacion
    agregar_tarjeta(s8, Inches(0.8), Inches(1.3), Inches(5.6), Inches(5.6))
    box8_l = s8.shapes.add_textbox(Inches(1.05), Inches(1.45), Inches(5.1), Inches(5.3))
    tf8_l = box8_l.text_frame
    tf8_l.word_wrap = True

    p = tf8_l.paragraphs[0]
    p.text = "Resultados en Validación Cruzada (k=5):"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_TEXT

    # Tabla de experimentos
    table_s8 = s8.shapes.add_table(5, 3, Inches(1.05), Inches(2.0), Inches(5.1), Inches(2.6))
    t8 = table_s8.table
    t8.columns[0].width = Inches(1.8)
    t8.columns[1].width = Inches(1.8)
    t8.columns[2].width = Inches(1.5)

    headers_exp = ["Modelo", "Configuración", "F1-Macro (k=5)"]
    for col_idx, h_text in enumerate(headers_exp):
        cell = t8.cell(0, col_idx)
        cell.text = h_text
        p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = C_TEXT

    filas_exp = [
        ("DummyClassifier", "most_frequent", "8.92% (Superado)"),
        ("Multinomial NB", "alpha=0.1, unigramas", "83.73% ± 2.69%"),
        ("Regresión Logística", "C=2.0 (sin balanceo)", "87.75% ± 3.14%"),
        ("Regresión Logística", "C=2.0 (balanced)", "90.41% ± 1.36% 🏆"),
    ]
    for row_idx, (c0, c1, c2) in enumerate(filas_exp, start=1):
        for col_idx, val in enumerate([c0, c1, c2]):
            cell = t8.cell(row_idx, col_idx)
            cell.text = val
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(9.5)
            if row_idx == 4:
                p.font.bold = True
                p.font.color.rgb = C_SUCCESS

    # Texto inferior de explicacion
    box8_sub = s8.shapes.add_textbox(Inches(1.05), Inches(4.85), Inches(5.1), Inches(1.8))
    tf8_sub = box8_sub.text_frame
    tf8_sub.word_wrap = True
    p = tf8_sub.paragraphs[0]
    p.text = "¿Por qué ganó Regresión Logística?"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY

    p = tf8_sub.add_paragraph()
    p.text = "Naive Bayes asume independencia irreal entre palabras. La Regresión Logística calcula combinaciones lineales de pesos beta y ajusta penalizaciones proporcionales con class_weight='balanced' (+1.86 F1), protegiendo clases minoritarias."
    p.font.size = Pt(10.5)
    p.font.color.rgb = C_TEXT
    p.space_before = Pt(3)

    # Columna Derecha: Imagen comparativa_modelos.png
    agregar_tarjeta(s8, Inches(6.9), Inches(1.3), Inches(5.6), Inches(5.6))
    agregar_imagen_segura(s8, "comparativa_modelos.png", Inches(7.1), Inches(1.6), width=Inches(5.2))

    # =========================================================================
    # SLIDE 9: EVALUACION CIEGA EN TEST Y ANALISIS DE ERRORES
    # =========================================================================
    s9 = prs.slides.add_slide(layout_vacio)
    aplicar_fondo(s9, prs)
    agregar_cabecera(s9, "Evaluación Ciega en Test y Análisis de Errores", "Fases 3.2 y 3.4: Evidencia Científica")

    # Columna Izquierda: Matriz de Confusion
    agregar_tarjeta(s9, Inches(0.8), Inches(1.3), Inches(5.6), Inches(5.6))
    agregar_imagen_segura(s9, "matriz_confusion_5x5.png", Inches(1.0), Inches(1.4), width=Inches(5.2))

    # Columna Derecha: Metricas y 58 Errores
    agregar_tarjeta(s9, Inches(6.9), Inches(1.3), Inches(5.6), Inches(5.6))
    box9_r = s9.shapes.add_textbox(Inches(7.15), Inches(1.5), Inches(5.1), Inches(5.2))
    tf9_r = box9_r.text_frame
    tf9_r.word_wrap = True

    p = tf9_r.paragraphs[0]
    p.text = "Rendimiento en Prueba Ciega (668 Ofertas)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_SUCCESS

    p = tf9_r.add_paragraph()
    p.text = "• F1-Score Macro Oficial: 91.55%\n• Exactitud Global (Accuracy): 91.32%\n• Total de Aciertos: 610 de 668 ofertas clasificadas con éxito."
    p.font.size = Pt(12)
    p.font.color.rgb = C_TEXT
    p.space_before = Pt(6)

    p = tf9_r.add_paragraph()
    p.text = "Diagnóstico Científico de los 58 Errores (8.68%):"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_DANGER
    p.space_before = Pt(14)

    errores_diag = [
        ("1. Vocabulario Cruzado:", "Ofertas de hostelería o comercio que exigen carnet de conducir B/C (el modelo predice Transporte)."),
        ("2. Roles Híbridos:", "'Comercial con conocimientos de informática' o 'Mantenimiento de clínicas sanitarias'."),
        ("3. Convocatorias en Catalán/Gallego:", "Presencia de términos como 'feina' o 'empresa' no normalizados."),
    ]
    for tit, desc in errores_diag:
        p = tf9_r.add_paragraph()
        p.text = f"{tit} {desc}"
        p.font.size = Pt(11)
        p.font.color.rgb = C_MUTED
        p.space_before = Pt(6)

    p = tf9_r.add_paragraph()
    p.text = "Conclusión: Ningún error se debe a desbalance o fuga de datos; el sistema generaliza de forma robusta."
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = C_SUCCESS
    p.space_before = Pt(14)

    # =========================================================================
    # SLIDE 10: ARQUITECTURA DE SOFTWARE, BACKEND Y DOCKER
    # =========================================================================
    s10 = prs.slides.add_slide(layout_vacio)
    aplicar_fondo(s10, prs)
    agregar_cabecera(s10, "Arquitectura de Software, Backend y Docker", "Fases 0, 4 y 5: Producción")

    # Diagrama superior
    agregar_tarjeta(s10, Inches(0.8), Inches(1.3), Inches(11.73), Inches(2.5))
    agregar_imagen_segura(s10, "arquitectura_diagrama.png", Inches(1.0), Inches(1.4), width=Inches(11.33))

    # Columna Izquierda: Backend FastAPI
    agregar_tarjeta(s10, Inches(0.8), Inches(4.0), Inches(5.6), Inches(2.9))
    box10_l = s10.shapes.add_textbox(Inches(1.05), Inches(4.15), Inches(5.1), Inches(2.6))
    tf10_l = box10_l.text_frame
    tf10_l.word_wrap = True

    p = tf10_l.paragraphs[0]
    p.text = "Backend FastAPI en 3 Capas Desacopladas"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY

    p = tf10_l.add_paragraph()
    p.text = "• schemas.py: Contratos Pydantic v2 y validación Fail-Fast HTTP 422.\n• service.py: Lifespan (carga única de model.joblib en RAM, respuesta en < 5ms).\n• main.py: Endpoints limpios (/predict, /predict/batch, /metrics, /health)."
    p.font.size = Pt(11)
    p.font.color.rgb = C_TEXT
    p.space_before = Pt(6)

    # Columna Derecha: Docker y Calidad
    agregar_tarjeta(s10, Inches(6.9), Inches(4.0), Inches(5.6), Inches(2.9))
    box10_r = s10.shapes.add_textbox(Inches(7.15), Inches(4.15), Inches(5.1), Inches(2.6))
    tf10_r = box10_r.text_frame
    tf10_r.word_wrap = True

    p = tf10_r.paragraphs[0]
    p.text = "Producción Docker y Calidad de Código"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_SUCCESS

    p = tf10_r.add_paragraph()
    p.text = "• Nginx Alpine: Reverse Proxy en puerto 8080 que redirige internamente a /api/* sin conflictos de CORS.\n• Docker Multi-Etapa: Imagen ligera de frontend (< 25 MB).\n• 81 Pruebas Pytest: Cobertura 100% en verde de regex, contratos y probabilidades Softmax."
    p.font.size = Pt(11)
    p.font.color.rgb = C_TEXT
    p.space_before = Pt(6)

    # =========================================================================
    # SLIDE 11: DEMOSTRACION EN VIVO
    # =========================================================================
    s11 = prs.slides.add_slide(layout_vacio)
    aplicar_fondo(s11, prs)
    agregar_cabecera(s11, "Demostración del Sistema en Vivo", "Ejecución en Tiempo Real")

    # Columna Izquierda: Captura de la UI
    agregar_tarjeta(s11, Inches(0.8), Inches(1.3), Inches(6.8), Inches(5.6))
    agregar_imagen_segura(s11, "interfaz_web.png", Inches(0.95), Inches(1.45), width=Inches(6.5))

    # Columna Derecha: 3 Pestanas
    agregar_tarjeta(s11, Inches(7.8), Inches(1.3), Inches(4.73), Inches(5.6))
    box11_r = s11.shapes.add_textbox(Inches(8.0), Inches(1.5), Inches(4.3), Inches(5.2))
    tf11_r = box11_r.text_frame
    tf11_r.word_wrap = True

    p = tf11_r.paragraphs[0]
    p.text = "Flujos Clave a Demostrar:"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY

    pestanas = [
        ("1. Análisis Individual:", "Inferencia Softmax inmediata, botones de prueba rápida y desglose anatómico de las 5 estaciones NLP."),
        ("2. Procesamiento Masivo CSV:", "Drag & Drop de lotes masivos, predicción vectorizada en un solo pase y exportación con Blob."),
        ("3. Dashboard de Métricas:", "Matriz de confusión interactiva 5×5, comparativa con Baseline y ranking de coeficientes beta."),
        ("4. Swagger /docs:", "Contratos OpenAPI vivos y prueba de error HTTP 422."),
    ]
    for tit, desc in pestanas:
        p = tf11_r.add_paragraph()
        p.text = tit
        p.font.size = Pt(12.5)
        p.font.bold = True
        p.font.color.rgb = C_TEXT
        p.space_before = Pt(10)

        p2 = tf11_r.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(11)
        p2.font.color.rgb = C_MUTED
        p2.space_before = Pt(2)

    # =========================================================================
    # SLIDE 12: CONCLUSIONES Y RÚBRICA
    # =========================================================================
    s12 = prs.slides.add_slide(layout_vacio)
    aplicar_fondo(s12, prs)
    agregar_cabecera(s12, "Conclusiones y Cumplimiento de la Rúbrica", "Cierre y Defensa")

    # Tarjeta Izquierda: Cumplimiento
    agregar_tarjeta(s12, Inches(0.8), Inches(1.3), Inches(6.0), Inches(5.6))
    box12_l = s12.shapes.add_textbox(Inches(1.05), Inches(1.5), Inches(5.5), Inches(5.2))
    tf12_l = box12_l.text_frame
    tf12_l.word_wrap = True

    p = tf12_l.paragraphs[0]
    p.text = "Logros del Proyecto Integrador"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY

    logros = [
        ("🎯 Rúbrica Oficial al 100%:", "Implementadas todas las fases: datos, pipeline NLP con blindaje para el español, validación cruzada k=5, backend en 3 capas, frontend React y despliegue en Nginx Docker."),
        ("📊 Rendimiento Productivo Comprobado:", "Modelo final de 321 KB con 91.55% de F1-Macro, inferencia sub-5ms y probabilidades Softmax calibradas."),
        ("⚙️ Modificación en Vivo Garantizada:", "Parámetros centralizados en params.yaml (C, regularización, n-gramas) listos para reentrenar en 1 solo comando."),
        ("🧪 Calidad Automatizada:", "81 pruebas unitarias y de integración pasando al 100% en verde."),
    ]
    for tit, desc in logros:
        p = tf12_l.add_paragraph()
        p.text = tit
        p.font.size = Pt(12.5)
        p.font.bold = True
        p.font.color.rgb = C_TEXT
        p.space_before = Pt(10)

        p2 = tf12_l.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(11)
        p2.font.color.rgb = C_MUTED
        p2.space_before = Pt(2)

    # Tarjeta Derecha: Cierre y Preguntas
    agregar_tarjeta(s12, Inches(7.2), Inches(1.3), Inches(5.33), Inches(5.6))
    box12_r = s12.shapes.add_textbox(Inches(7.5), Inches(2.2), Inches(4.7), Inches(4.0))
    tf12_r = box12_r.text_frame
    tf12_r.word_wrap = True

    p = tf12_r.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "💼"
    p.font.size = Pt(44)

    p = tf12_r.add_paragraph()
    p.alignment = PP_ALIGN.CENTER
    p.text = "¡Muchas Gracias!"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = C_TEXT
    p.space_before = Pt(10)

    p = tf12_r.add_paragraph()
    p.alignment = PP_ALIGN.CENTER
    p.text = "Disponible para preguntas del jurado y la demostración de modificación en vivo."
    p.font.size = Pt(13)
    p.font.color.rgb = C_MUTED
    p.space_before = Pt(10)

    p = tf12_r.add_paragraph()
    p.alignment = PP_ALIGN.CENTER
    p.text = "Etiqueta Git: entrega-final ✅"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = C_SUCCESS
    p.space_before = Pt(22)

    # Guardar presentacion
    prs.save(str(OUT_PPTX))
    print(f"Presentacion PowerPoint generada exitosamente en:\n{OUT_PPTX}")


if __name__ == "__main__":
    construir_presentacion()
