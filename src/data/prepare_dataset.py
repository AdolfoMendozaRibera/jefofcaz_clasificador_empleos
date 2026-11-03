"""Modulo para el filtrado, limpieza y mapeo de ofertas laborales a 5 sectores clave.

Lee el archivo crudo inmutable (data/raw/ofertas_laborales.csv), aplica tecnicas de
deteccion de nulos, eliminacion de duplicados (anti data leakage), valida longitud de
texto y clasifica cada oferta en uno de los 5 sectores profesionales clave del proyecto:
  1. transporte_logistica
  2. hosteleria_gastronomia
  3. ventas_comercial
  4. salud_servicios_sociales
  5. construccion_mantenimiento

El resultado se serializa en data/processed/ofertas_5_sectores.csv sin modificar el origen.
"""

import argparse
import logging
from pathlib import Path
import re
import sys
from typing import Any, Dict, Optional
import unicodedata

# Configuracion de logging estructurado
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("prepare_dataset")

# Mapeo oficial de palabras clave por sector profesional
MAPA_SECTORES: Dict[str, list[str]] = {
    "transporte_logistica": [
        "conductor",
        "conductora",
        "chofer",
        "chofere",
        "camion",
        "camionero",
        "camionera",
        "furgoneta",
        "transporte",
        "reparto",
        "repartidor",
        "repartidora",
        "almacen",
        "almacenista",
        "carretillero",
        "carretillera",
        "mozo",
        "moza",
        "logistica",
        "mensajero",
        "mensajera",
        "gruista",
        "flota",
        "mercancias",
        "trailer",
        "autobus",
    ],
    "hosteleria_gastronomia": [
        "camarero",
        "camarera",
        "cocinero",
        "cocinera",
        "cocina",
        "chef",
        "pizzero",
        "pizzera",
        "barista",
        "barman",
        "bartender",
        "hosteleria",
        "restaurante",
        "comedor",
        "planchista",
        "pastelero",
        "pastelera",
        "repostero",
        "repostera",
        "buffet",
        "cafeteria",
        "mesonero",
        "mesonera",
        "ayudante de cocina",
        "fregaplatos",
    ],
    "ventas_comercial": [
        "comercial",
        "ventas",
        "vendedor",
        "vendedora",
        "dependiente",
        "dependienta",
        "seguros",
        "asesor comercial",
        "asesora comercial",
        "agente comercial",
        "teleoperador",
        "teleoperadora",
        "cajero",
        "cajera",
        "caja",
        "supermercado",
        "atencion al cliente",
        "televenta",
        "prospeccion",
        "cartera de clientes",
        "ejecutivo comercial",
        "ejecutiva comercial",
    ],
    "salud_servicios_sociales": [
        "enfermero",
        "enfermera",
        "enfermeria",
        "medico",
        "medica",
        "sanitario",
        "sanitaria",
        "salud",
        "auxiliar de enfermeria",
        "trabajador social",
        "trabajadora social",
        "educador social",
        "educadora social",
        "cuidador",
        "cuidadora",
        "gerocultor",
        "gerocultora",
        "fisioterapeuta",
        "terapeuta",
        "odontologo",
        "odontologa",
        "farmaceutico",
        "farmaceutica",
        "psicologo",
        "psicologa",
        "residencia de ancianos",
        "residencia de mayores",
        "centro de dia",
        "geriatria",
    ],
    "construccion_mantenimiento": [
        "electricista",
        "mecanico",
        "mecanica",
        "fontanero",
        "fontanera",
        "albanil",
        "carpintero",
        "carpintera",
        "pintor",
        "pintora",
        "soldador",
        "soldadora",
        "cerrajero",
        "cerrajera",
        "construccion",
        "mantenimiento",
        "frigorista",
        "instalador",
        "instaladora",
        "obra",
        "encofrador",
        "encofradora",
        "peon de construccion",
        "peon de obra",
        "climatizacion",
        "fontaneria",
        "electricidad",
    ],
}


def cargar_configuracion(ruta_params: Path = Path("params.yaml")) -> Dict[str, Any]:
    """Carga los parametros centrales desde el archivo params.yaml.

    Args:
        ruta_params: Ruta al archivo YAML de configuracion.

    Returns:
        Diccionario con la configuracion cargada.

    Example:
        >>> config = cargar_configuracion(Path("params.yaml"))
        >>> "data" in config
        True
    """
    if not ruta_params.exists():
        logger.warning(f"No se encontro {ruta_params}. Usando configuracion por defecto.")
        return {
            "data": {
                "raw_path": "data/raw/ofertas_laborales.csv",
                "processed_path": "data/processed/ofertas_5_sectores.csv",
                "min_chars": 15,
                "max_chars": 5000,
            }
        }

    try:
        import yaml

        with open(ruta_params, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        logger.warning("PyYAML no disponible. Usando configuracion por defecto.")
        return {
            "data": {
                "raw_path": "data/raw/ofertas_laborales.csv",
                "processed_path": "data/processed/ofertas_5_sectores.csv",
                "min_chars": 15,
                "max_chars": 5000,
            }
        }


def normalizar_texto_basico(texto: str) -> str:
    """Normaliza una cadena eliminando acentos, caracteres especiales y convirtiendo a minusculas.

    Args:
        texto: Cadena original a normalizar.

    Returns:
        Cadena normalizada en minusculas sin tildes.

    Example:
        >>> normalizar_texto_basico("¡Camión Eléctrico!")
        'camion electrico'
    """
    if not isinstance(texto, str):
        return ""

    # Descomponer caracteres con acentos (NFD) y filtrar diacriticos
    texto_descompuesto = unicodedata.normalize("NFD", texto)
    texto_sin_tildes = "".join(
        c for c in texto_descompuesto if unicodedata.category(c) != "Mn"
    )

    # Minusculas y reemplazo de caracteres no alfanumericos por espacios
    texto_limpio = re.sub(r"[^\w\s]", " ", texto_sin_tildes.lower())
    # Colapsar espacios multiples
    return re.sub(r"\s+", " ", texto_limpio).strip()


def asignar_sector(ocupacion: str, titulo: str) -> Optional[str]:
    """Determina a cual de los 5 sectores clave pertenece una oferta laboral.

    Aplica una estrategia jerarquica:
      1. Evalua primero la columna 'ocupacion' (estandard EURES/ESCO de alta fidelidad).
      2. Si no coincide, evalua la columna 'titulo'.
      3. Si no coincide con ningun sector definido, retorna None.

    Args:
        ocupacion: Texto del oficio o categoria segun EURES.
        titulo: Titulo de la vacante publicado por el empleador.

    Returns:
        Identificador del sector ('transporte_logistica', 'hosteleria_gastronomia', etc.)
        o None si la oferta no pertenece a ninguno de los 5 sectores.

    Example:
        >>> asignar_sector("Conductor de camión", "Transportista nacional")
        'transporte_logistica'
        >>> asignar_sector("Astronauta", "Mision espacial")
        None
    """
    ocupacion_norm = normalizar_texto_basico(ocupacion)
    titulo_norm = normalizar_texto_basico(titulo)

    # Paso 1: Prioridad alta a la ocupacion estandarizada
    for sector, palabras_clave in MAPA_SECTORES.items():
        for palabra in palabras_clave:
            patron = rf"\b{re.escape(palabra)}\b"
            if re.search(patron, ocupacion_norm):
                return sector

    # Paso 2: Evaluar el titulo si la ocupacion no produjo match
    for sector, palabras_clave in MAPA_SECTORES.items():
        for palabra in palabras_clave:
            patron = rf"\b{re.escape(palabra)}\b"
            if re.search(patron, titulo_norm):
                return sector

    return None


def preparar_dataset(
    ruta_raw: Optional[Path] = None,
    ruta_processed: Optional[Path] = None,
    min_chars: int = 15,
    max_chars: int = 5000,
) -> Path:
    """Ejecuta el pipeline completo de limpieza, descarte de duplicados y mapeo a 5 sectores.

    Args:
        ruta_raw: Ruta al CSV crudo (data/raw/ofertas_laborales.csv).
        ruta_processed: Ruta al CSV limpio resultante (data/processed/ofertas_5_sectores.csv).
        min_chars: Longitud minima requerida para el texto descriptivo.
        max_chars: Longitud maxima admisible para el texto descriptivo.

    Returns:
        Ruta Path del archivo CSV procesado generado.
    """
    try:
        import pandas as pd
    except ImportError as e:
        logger.error("pandas no esta instalado en el entorno.")
        raise RuntimeError("Se requiere pandas para ejecutar la preparacion de datos.") from e

    config = cargar_configuracion()
    cfg_data = config.get("data", {})

    ruta_entrada = ruta_raw or Path(cfg_data.get("raw_path", "data/raw/ofertas_laborales.csv"))
    ruta_salida = ruta_processed or Path(
        cfg_data.get("processed_path", "data/processed/ofertas_5_sectores.csv")
    )
    limite_min = cfg_data.get("min_chars", min_chars)
    limite_max = cfg_data.get("max_chars", max_chars)

    if not ruta_entrada.exists():
        msg = f"El archivo crudo no existe en {ruta_entrada}. Ejecuta primero download_dataset.py"
        logger.error(msg)
        raise FileNotFoundError(msg)

    logger.info(f"Cargando dataset crudo desde: {ruta_entrada}")
    df_raw = pd.read_csv(ruta_entrada)
    filas_iniciales = len(df_raw)
    logger.info(f"Total de registros crudos leidos: {filas_iniciales}")

    # 1. Tratamiento de nulos: la descripcion es el texto indispensable
    df_limpio = df_raw.dropna(subset=["descripcion"]).copy()
    descarte_nulos = filas_iniciales - len(df_limpio)
    logger.info(f"Ofertas con descripcion nula descartadas: {descarte_nulos}")

    # 2. Construccion del campo de texto unificado (titulo + descripcion)
    df_limpio["titulo_limpio"] = df_limpio["titulo"].fillna("").astype(str).str.strip()
    df_limpio["descripcion_limpia"] = df_limpio["descripcion"].astype(str).str.strip()
    df_limpio["texto"] = (
        df_limpio["titulo_limpio"] + ". " + df_limpio["descripcion_limpia"]
    ).str.strip(". ")

    # 3. Deteccion y eliminacion de duplicados (ANTI DATA LEAKAGE)
    filas_antes_dup = len(df_limpio)
    df_limpio = df_limpio.drop_duplicates(subset=["texto"]).copy()
    descarte_duplicados = filas_antes_dup - len(df_limpio)
    logger.info(f"Ofertas duplicadas exactas eliminadas (pre-split): {descarte_duplicados}")

    # 4. Validacion de longitud en caracteres
    df_limpio["longitud_chars"] = df_limpio["texto"].str.len()
    mascara_longitud = (df_limpio["longitud_chars"] >= limite_min) & (
        df_limpio["longitud_chars"] <= limite_max
    )
    descarte_longitud = (~mascara_longitud).sum()
    df_limpio = df_limpio[mascara_longitud].copy()
    logger.info(
        f"Ofertas fuera del rango permitido [{limite_min}, {limite_max}] caracteres descartadas: {descarte_longitud}"
    )

    # 5. Mapeo jerarquico a los 5 sectores clave
    logger.info("Mapeando ofertas a los 5 sectores clave...")
    df_limpio["sector"] = df_limpio.apply(
        lambda r: asignar_sector(str(r.get("ocupacion", "")), str(r.get("titulo", ""))),
        axis=1,
    )

    # Filtrar solo registros que pertenezcan a los 5 sectores definidos
    df_filtrado = df_limpio[df_limpio["sector"].notnull()].copy()
    descarte_otros_sectores = len(df_limpio) - len(df_filtrado)
    logger.info(
        f"Ofertas pertenecientes a otros oficios no incluidos en los 5 sectores: {descarte_otros_sectores}"
    )

    # Resumen de distribucion de clases
    conteo_clases = df_filtrado["sector"].value_counts()
    porcentajes = df_filtrado["sector"].value_counts(normalize=True) * 100
    logger.info("--- DISTRIBUCION FINAL DE CLASES (5 SECTORES) ---")
    for sec, cant in conteo_clases.items():
        pct = porcentajes[sec]
        logger.info(f"  * {sec:<28}: {cant:>5} ofertas ({pct:>5.1f}%)")

    # 6. Seleccion y preservacion de columnas
    columnas_finales = [
        "id",
        "timestamp",
        "titulo",
        "ocupacion",
        "descripcion",
        "provincia",
        "tipo_contrato",
        "texto",
        "sector",
    ]
    # Conservar unicamente columnas presentes
    cols_a_guardar = [c for c in columnas_finales if c in df_filtrado.columns]
    df_final = df_filtrado[cols_a_guardar].copy()

    # 7. Serializacion inmutable en data/processed/
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(ruta_salida, index=False, encoding="utf-8")
    tamano_mb = ruta_salida.stat().st_size / (1024 * 1024)
    logger.info(
        f"Dataset final de 5 sectores guardado exitosamente en {ruta_salida} "
        f"({len(df_final)} filas, {tamano_mb:.2f} MB)"
    )

    return ruta_salida


def main() -> None:
    """Punto de entrada de linea de comandos."""
    parser = argparse.ArgumentParser(
        description="Limpia y mapea el dataset crudo de ofertas a 5 sectores clave."
    )
    parser.add_argument(
        "--raw-path",
        type=Path,
        default=None,
        help="Ruta alternativa al archivo CSV crudo.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="Ruta alternativa de salida para el CSV procesado.",
    )
    args = parser.parse_args()

    preparar_dataset(ruta_raw=args.raw_path, ruta_processed=args.output_path)


if __name__ == "__main__":
    main()
