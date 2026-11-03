"""Punto de entrada unificado para la orquestacion del pipeline de ML y NLP.

Permite entrenar, evaluar y serializar el modelo oficial, o reutilizar
los artefactos existentes si se pasa el flag `--skip-if-trained`.
"""

import argparse
import logging
from pathlib import Path
import sys

from src.models.train import entrenar_evaluar_y_serializar

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("pipeline")


def ejecutar_pipeline(skip_if_trained: bool = False, force: bool = False) -> None:
    """Ejecuta el pipeline completo de entrenamiento o verifica artefactos existentes.

    Args:
        skip_if_trained: Si es True y los artefactos ya existen, no reentrena.
        force: Si es True, fuerza el reentrenamiento aunque existan los artefactos.
    """
    raiz = Path(__file__).resolve().parent.parent
    modelo_path = raiz / "artifacts" / "model.joblib"
    metricas_path = raiz / "artifacts" / "metrics.json"

    ya_entrenado = modelo_path.exists() and metricas_path.exists()

    if ya_entrenado and skip_if_trained and not force:
        logger.info(
            "Artefactos de produccion encontrados (model.joblib y metrics.json). "
            "Flag --skip-if-trained activo: omitiendo reentrenamiento."
        )
        sys.exit(0)

    logger.info("Iniciando pipeline oficial de entrenamiento y evaluacion ciega...")
    res = entrenar_evaluar_y_serializar()
    logger.info(
        f"Pipeline completado exitosamente. F1-Macro en Test: {res['f1_macro']:.4f}"
    )


def main() -> None:
    """Parsea argumentos de terminal y ejecuta el pipeline."""
    parser = argparse.ArgumentParser(
        description="Orquestador del Pipeline de ML y NLP para Clasificacion de Empleos."
    )
    parser.add_argument(
        "--skip-if-trained",
        action="store_true",
        help="Omitir el entrenamiento si model.joblib y metrics.json ya existen.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forzar el reentrenamiento completo aunque ya existan artefactos.",
    )

    args = parser.parse_args()
    ejecutar_pipeline(skip_if_trained=args.skip_if_trained, force=args.force)


if __name__ == "__main__":
    main()

