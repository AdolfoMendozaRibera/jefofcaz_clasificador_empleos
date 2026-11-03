"""Modulo para la division estratificada del dataset en entrenamiento y prueba.

Garantiza la ausencia total de fuga de datos (anti data leakage):
1. Divide el dataset de 5 sectores procesados ANTES de cualquier vectorizacion o ajuste.
2. Utiliza muestreo estratificado (stratify) para conservar exactamente las mismas
   proporciones de clases en train y test.
3. Fija la semilla pseudoaleatoria (random_state) desde params.yaml para reproducibilidad.
4. Serializa fisicamente los archivos data/processed/train.csv y data/processed/test.csv.
"""

import argparse
import logging
from pathlib import Path
import sys
from typing import Any, Dict, Optional, Tuple

# Configuracion de logging estructurado
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("split_data")


def cargar_configuracion(ruta_yaml: Optional[Path] = None) -> Dict[str, Any]:
    """Carga los parametros del proyecto desde params.yaml.

    Args:
        ruta_yaml: Ruta opcional al archivo YAML. Si es None, busca en la raiz.

    Returns:
        Diccionario con la configuracion del proyecto.
    """
    ruta = ruta_yaml or (Path(__file__).resolve().parent.parent.parent / "params.yaml")
    if not ruta.exists():
        logger.warning(f"No se encontro {ruta}. Se utilizaran parametros por defecto.")
        return {}

    try:
        import yaml
    except ImportError:
        logger.warning("PyYAML no esta instalado. Se emplean valores por defecto.")
        return {}

    with open(ruta, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def dividir_dataset_estratificado(
    df: Any,
    test_size: float = 0.20,
    random_state: int = 42,
    estratificar_por: str = "sector",
) -> Tuple[Any, Any]:
    """Divide un DataFrame en conjuntos de train y test con estratificacion estricta.

    Args:
        df: DataFrame de Pandas a dividir.
        test_size: Proporcion de registros para el conjunto de prueba (entre 0.0 y 1.0).
        random_state: Semilla pseudoaleatoria para garantizar reproducibilidad.
        estratificar_por: Nombre de la columna categorica para estratificar.

    Returns:
        Tupla con (df_train, df_test).

    Raises:
        ValueError: Si el DataFrame esta vacio, test_size esta fuera de rango o la columna no existe.

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({'texto': ['a', 'b', 'c', 'd', 'e'], 'sector': [1, 1, 1, 2, 2]})
        >>> train, test = dividir_dataset_estratificado(df, test_size=0.4, random_state=42)
        >>> len(train), len(test)
        (3, 2)
    """
    try:
        import pandas as pd
        from sklearn.model_selection import train_test_split
    except ImportError as e:
        logger.error("Se requiere pandas y scikit-learn para ejecutar la division.")
        raise RuntimeError("Dependencias faltantes: pandas o scikit-learn.") from e

    # Validaciones en el borde (fail-fast)
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("El argumento 'df' debe ser un DataFrame de pandas valido.")

    if len(df) == 0:
        raise ValueError("El DataFrame proporcionado esta vacio; no es posible particionar.")

    if not (0.0 < test_size < 1.0):
        raise ValueError(
            f"El parametro 'test_size' debe ser un flotante entre 0.0 y 1.0 (recibido: {test_size})."
        )

    if estratificar_por not in df.columns:
        raise ValueError(
            f"La columna de estratificacion '{estratificar_por}' no existe en el DataFrame. "
            f"Columnas disponibles: {list(df.columns)}"
        )

    if df[estratificar_por].isnull().any():
        raise ValueError(
            f"La columna '{estratificar_por}' contiene valores nulos, lo que impide la estratificacion."
        )

    logger.info(
        f"Iniciando particion estratificada: {len(df)} filas, test_size={test_size}, "
        f"random_state={random_state}, estratificar_por='{estratificar_por}'"
    )

    df_train, df_test = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        stratify=df[estratificar_por],
    )

    # Validacion de integridad: no debe existir solapamiento de indices
    indices_comunes = set(df_train.index).intersection(set(df_test.index))
    if indices_comunes:
        raise RuntimeError(
            f"Fallo critico de aislamiento: se detectaron {len(indices_comunes)} filas compartidas."
        )

    logger.info(
        f"Particion completada exitosamente: Train={len(df_train)} filas, Test={len(df_test)} filas"
    )
    return df_train.copy(), df_test.copy()


def ejecutar_particion(
    ruta_entrada: Optional[Path] = None,
    ruta_train: Optional[Path] = None,
    ruta_test: Optional[Path] = None,
    test_size: Optional[float] = None,
    random_state: Optional[int] = None,
) -> Tuple[Path, Path]:
    """Orquesta la lectura, particion estratificada y persistencia fisica de train y test.

    Args:
        ruta_entrada: Ruta al CSV procesado de 5 sectores.
        ruta_train: Ruta de destino para train.csv.
        ruta_test: Ruta de destino para test.csv.
        test_size: Fraccion para el conjunto de prueba.
        random_state: Semilla pseudoaleatoria.

    Returns:
        Tupla con las rutas (ruta_train_generada, ruta_test_generada).
    """
    try:
        import pandas as pd
    except ImportError as e:
        logger.error("pandas no esta instalado.")
        raise RuntimeError("Se requiere pandas para ejecutar la particion.") from e

    config = cargar_configuracion()
    cfg_data = config.get("data", {})
    semilla_global = config.get("seed", 42)

    in_path = ruta_entrada or Path(
        cfg_data.get("processed_path", "data/processed/ofertas_5_sectores.csv")
    )
    out_train = ruta_train or Path(cfg_data.get("train_path", "data/processed/train.csv"))
    out_test = ruta_test or Path(cfg_data.get("test_path", "data/processed/test.csv"))
    split_ratio = test_size if test_size is not None else float(cfg_data.get("test_size", 0.20))
    seed = random_state if random_state is not None else int(semilla_global)

    if not in_path.exists():
        msg = f"El archivo procesado no existe en {in_path}. Ejecuta primero prepare_dataset.py."
        logger.error(msg)
        raise FileNotFoundError(msg)

    logger.info(f"Cargando dataset procesado desde: {in_path}")
    df = pd.read_csv(in_path)

    df_train, df_test = dividir_dataset_estratificado(
        df=df,
        test_size=split_ratio,
        random_state=seed,
        estratificar_por="sector",
    )

    # Verificacion forense de proporciones de clases
    pct_original = df["sector"].value_counts(normalize=True) * 100
    pct_train = df_train["sector"].value_counts(normalize=True) * 100
    pct_test = df_test["sector"].value_counts(normalize=True) * 100

    logger.info("--- COMPARATIVA DE ESTRATIFICACION POR SECTOR ---")
    logger.info(f"{'Sector':<28} | {'Original %':>10} | {'Train %':>10} | {'Test %':>10}")
    logger.info("-" * 65)
    for sec in pct_original.index:
        logger.info(
            f"{sec:<28} | {pct_original[sec]:>9.2f}% | {pct_train[sec]:>9.2f}% | {pct_test[sec]:>9.2f}%"
        )

    # Persistencia fisica en disco
    out_train.parent.mkdir(parents=True, exist_ok=True)
    out_test.parent.mkdir(parents=True, exist_ok=True)

    df_train.to_csv(out_train, index=False, encoding="utf-8")
    df_test.to_csv(out_test, index=False, encoding="utf-8")

    tam_train_kb = out_train.stat().st_size / 1024
    tam_test_kb = out_test.stat().st_size / 1024

    logger.info(f"Archivo de entrenamiento guardado en: {out_train} ({len(df_train)} filas, {tam_train_kb:.1f} KB)")
    logger.info(f"Archivo de evaluacion guardado en: {out_test} ({len(df_test)} filas, {tam_test_kb:.1f} KB)")

    return out_train, out_test


def main() -> None:
    """Punto de entrada de linea de comandos."""
    parser = argparse.ArgumentParser(
        description="Divide el dataset de ofertas en conjuntos estratificados de train y test."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Ruta al CSV procesado de entrada.",
    )
    parser.add_argument(
        "--train-out",
        type=Path,
        default=None,
        help="Ruta de destino para el CSV de entrenamiento.",
    )
    parser.add_argument(
        "--test-out",
        type=Path,
        default=None,
        help="Ruta de destino para el CSV de evaluacion.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=None,
        help="Fraccion para el conjunto de prueba (por defecto 0.20 desde params.yaml).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Semilla pseudoaleatoria (por defecto 42 desde params.yaml).",
    )
    args = parser.parse_args()

    ejecutar_particion(
        ruta_entrada=args.input,
        ruta_train=args.train_out,
        ruta_test=args.test_out,
        test_size=args.test_size,
        random_state=args.seed,
    )


if __name__ == "__main__":
    main()
