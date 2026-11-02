"""Modulo para la descarga automatizada y reproducible del dataset de ofertas laborales.

Descarga el archivo oficial de Hugging Face (MiguelGP-13/JobOffers_ESP) y lo guarda
de forma inmutable en data/raw/ofertas_laborales.csv para su posterior analisis y entrenamiento.
"""

import argparse
import logging
from pathlib import Path
import sys
import urllib.request
from typing import Any, Dict

# Configuracion de logging estructurado
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("download_dataset")


def cargar_configuracion(ruta_params: Path = Path("params.yaml")) -> Dict[str, Any]:
    """Carga los parametros centrales desde el archivo params.yaml.

    Args:
        ruta_params: Ruta al archivo YAML de configuracion.

    Returns:
        Diccionario con las claves y valores de configuracion.

    Example:
        >>> config = cargar_configuracion(Path("params.yaml"))
        >>> "data" in config
        True
    """
    if not ruta_params.exists():
        logger.warning(
            f"No se encontro {ruta_params}. Usando configuracion por defecto."
        )
        return {
            "data": {
                "raw_path": "data/raw/ofertas_laborales.csv",
                "raw_parquet_path": "data/raw/ofertas_laborales.parquet",
                "dataset_url": (
                    "https://huggingface.co/datasets/MiguelGP-13/JobOffers_ESP/"
                    "resolve/main/empleos-espanoles-eures-2025.parquet"
                ),
            }
        }

    try:
        import yaml

        with open(ruta_params, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        logger.warning(
            "PyYAML no esta instalado aun. Cargando valores por defecto de Hugging Face."
        )
        return {
            "data": {
                "raw_path": "data/raw/ofertas_laborales.csv",
                "raw_parquet_path": "data/raw/ofertas_laborales.parquet",
                "dataset_url": (
                    "https://huggingface.co/datasets/MiguelGP-13/JobOffers_ESP/"
                    "resolve/main/empleos-espanoles-eures-2025.parquet"
                ),
            }
        }


def descargar_archivo(url: str, destino: Path, forzar: bool = False) -> Path:
    """Descarga un archivo remoto a un destino local si no existe o si forzar=True.

    Args:
        url: URL de descarga directa del dataset.
        destino: Ruta local donde se almacenara el archivo descargado.
        forzar: Si es True, descarga nuevamente aunque el archivo ya exista.

    Returns:
        Ruta Path del archivo descargado.
    """
    destino.parent.mkdir(parents=True, exist_ok=True)

    if destino.exists() and not forzar:
        logger.info(f"El archivo ya existe en {destino}. Omitiendo descarga.")
        return destino

    logger.info(f"Descargando dataset desde {url}...")
    try:
        urllib.request.urlretrieve(url, destino)
        tamano_mb = destino.stat().st_size / (1024 * 1024)
        logger.info(f"Descarga completada: {destino} ({tamano_mb:.2f} MB)")
        return destino
    except Exception as e:
        logger.error(f"Error al descargar desde {url}: {e}")
        raise RuntimeError(f"Fallo la descarga del dataset: {e}") from e


def convertir_parquet_a_csv(origen_parquet: Path, destino_csv: Path) -> Path:
    """Convierte el archivo crudo Parquet a formato CSV para uso estandar en el pipeline.

    Args:
        origen_parquet: Ruta del archivo Parquet descargado.
        destino_csv: Ruta del archivo CSV de salida.

    Returns:
        Ruta Path del archivo CSV generado.
    """
    try:
        import pandas as pd

        logger.info(f"Leyendo archivo Parquet desde {origen_parquet}...")
        df = pd.read_parquet(origen_parquet)
        logger.info(f"Dataset cargado en memoria. Filas: {len(df)}, Columnas: {list(df.columns)}")

        df.to_csv(destino_csv, index=False, encoding="utf-8")
        logger.info(f"Dataset CSV crudo inmutable guardado en {destino_csv}")
        return destino_csv
    except ImportError:
        logger.warning(
            "pandas o pyarrow no estan instalados en este entorno. "
            f"El archivo Parquet original permanece disponible en {origen_parquet}. "
            "Se convertira a CSV automaticamente al ejecutar en el contenedor o venv."
        )
        return origen_parquet


def ejecutar_descarga(forzar: bool = False) -> None:
    """Orquesta el flujo completo de descarga y preparacion de datos crudos.

    Args:
        forzar: Si es True, fuerza la re-descarga del archivo aunque ya exista.
    """
    config = cargar_configuracion()
    cfg_data = config.get("data", {})

    url = cfg_data.get(
        "dataset_url",
        "https://huggingface.co/datasets/MiguelGP-13/JobOffers_ESP/resolve/main/empleos-espanoles-eures-2025.parquet",
    )
    destino_parquet = Path(cfg_data.get("raw_parquet_path", "data/raw/ofertas_laborales.parquet"))
    destino_csv = Path(cfg_data.get("raw_path", "data/raw/ofertas_laborales.csv"))

    # Paso 1: Descargar Parquet original
    archivo_parquet = descargar_archivo(url, destino_parquet, forzar=forzar)

    # Paso 2: Convertir a CSV si el CSV no existe o si forzar=True
    if not destino_csv.exists() or forzar:
        convertir_parquet_a_csv(archivo_parquet, destino_csv)
    else:
        logger.info(f"El archivo CSV crudo ya existe en {destino_csv}. Omitiendo conversion.")


def main() -> None:
    """Punto de entrada de linea de comandos."""
    parser = argparse.ArgumentParser(
        description="Descarga el dataset oficial de ofertas laborales de Hugging Face."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Fuerza la descarga y conversion aunque los archivos ya existan.",
    )
    args = parser.parse_args()
    ejecutar_descarga(forzar=args.force)


if __name__ == "__main__":
    main()
