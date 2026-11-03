"""Pruebas unitarias para el modulo de division estratificada (src/data/split_data.py).

Verifica de forma estricta:
  1. Ejemplo minimo calculado a mano con proporciones exactas.
  2. Aislamiento total: conjuntos disjuntos sin interseccion de registros.
  3. Estratificacion multiclase balanceada para los 5 sectores.
  4. Reproducibilidad mediante semilla (random_state).
  5. Casos borde y excepciones especificas ante entradas invalidas.
"""

import pandas as pd
import pytest

from src.data.split_data import dividir_dataset_estratificado


def test_split_ejemplo_calculado_a_mano() -> None:
    """Verifica la division con un ejemplo minimo calculado a mano.

    Ejemplo calculado a mano:
      - Total registros: 10
      - Clases desbalanceadas:
          * 'ventas_comercial': 6 registros (60%)
          * 'hosteleria_gastronomia': 4 registros (40%)
      - test_size = 0.20 (20% test / 80% train)

    Resultado matematico esperado:
      - len(test) = 10 * 0.20 = 2 registros
      - len(train) = 10 * 0.80 = 8 registros
      - En test:
          * ventas_comercial: round(2 * 0.60) = 1
          * hosteleria_gastronomia: round(2 * 0.40) = 1
      - En train:
          * ventas_comercial: 6 - 1 = 5 registros
          * hosteleria_gastronomia: 4 - 1 = 3 registros
    """
    datos = {
        "id": list(range(1, 11)),
        "texto": [f"oferta_{i}" for i in range(1, 11)],
        "sector": [
            "ventas_comercial",
            "ventas_comercial",
            "ventas_comercial",
            "ventas_comercial",
            "ventas_comercial",
            "ventas_comercial",
            "hosteleria_gastronomia",
            "hosteleria_gastronomia",
            "hosteleria_gastronomia",
            "hosteleria_gastronomia",
        ],
    }
    df = pd.DataFrame(datos)

    df_train, df_test = dividir_dataset_estratificado(
        df=df,
        test_size=0.20,
        random_state=42,
        estratificar_por="sector",
    )

    # 1. Verificacion de dimensiones
    assert len(df_train) == 8
    assert len(df_test) == 2

    # 2. Verificacion de conteos calculados a mano
    conteos_train = df_train["sector"].value_counts().to_dict()
    conteos_test = df_test["sector"].value_counts().to_dict()

    assert conteos_train["ventas_comercial"] == 5
    assert conteos_train["hosteleria_gastronomia"] == 3

    assert conteos_test["ventas_comercial"] == 1
    assert conteos_test["hosteleria_gastronomia"] == 1


def test_split_aislamiento_conjuntos_disjuntos() -> None:
    """Verifica que no exista ninguna fila ni ID compartido entre train y test."""
    datos = {
        "id": [f"job_{i}" for i in range(50)],
        "texto": [f"descripcion del puesto {i}" for i in range(50)],
        "sector": ["sector_a" if i % 2 == 0 else "sector_b" for i in range(50)],
    }
    df = pd.DataFrame(datos)

    df_train, df_test = dividir_dataset_estratificado(
        df=df,
        test_size=0.30,
        random_state=42,
        estratificar_por="sector",
    )

    # La interseccion de IDs debe ser un conjunto vacio
    ids_train = set(df_train["id"])
    ids_test = set(df_test["id"])
    assert ids_train.isdisjoint(ids_test)

    # La suma de tamaños debe ser exactamente igual al total original
    assert len(df_train) + len(df_test) == len(df)


def test_split_reproducibilidad_con_semilla() -> None:
    """Verifica que la misma semilla genere exactamente las mismas particiones."""
    datos = {
        "id": list(range(30)),
        "texto": [f"texto {i}" for i in range(30)],
        "sector": ["clase_1"] * 15 + ["clase_2"] * 15,
    }
    df = pd.DataFrame(datos)

    train_1, test_1 = dividir_dataset_estratificado(df, test_size=0.20, random_state=42)
    train_2, test_2 = dividir_dataset_estratificado(df, test_size=0.20, random_state=42)

    # Los indices seleccionados deben ser identicos
    assert list(train_1.index) == list(train_2.index)
    assert list(test_1.index) == list(test_2.index)

    # Con distinta semilla, el orden / seleccion debe cambiar
    train_3, _ = dividir_dataset_estratificado(df, test_size=0.20, random_state=999)
    assert list(train_1.index) != list(train_3.index)


def test_split_estratificacion_cinco_sectores() -> None:
    """Verifica la distribucion uniforme de los 5 sectores con 25% test size.

    20 ofertas en total: 4 por cada uno de los 5 sectores.
    Con test_size=0.25 (25%):
      - 5 ofertas en test -> exactamente 1 por sector.
      - 15 ofertas en train -> exactamente 3 por sector.
    """
    sectores = [
        "transporte_logistica",
        "hosteleria_gastronomia",
        "ventas_comercial",
        "salud_servicios_sociales",
        "construccion_mantenimiento",
    ]
    filas = []
    for sec in sectores:
        for i in range(4):
            filas.append({"texto": f"oferta {sec} {i}", "sector": sec})
    df = pd.DataFrame(filas)

    df_train, df_test = dividir_dataset_estratificado(
        df=df,
        test_size=0.25,
        random_state=42,
        estratificar_por="sector",
    )

    assert len(df_train) == 15
    assert len(df_test) == 5

    # Cada uno de los 5 sectores debe tener exactamente 3 en train y 1 en test
    for sec in sectores:
        assert (df_train["sector"] == sec).sum() == 3
        assert (df_test["sector"] == sec).sum() == 1


def test_split_excepciones_validaciones_borde() -> None:
    """Verifica que se disparen excepciones claras ante parametros o datos invalidos."""
    # 1. DataFrame vacio
    with pytest.raises(ValueError, match="esta vacio"):
        dividir_dataset_estratificado(pd.DataFrame(), test_size=0.20)

    # 2. Argumento None
    with pytest.raises(ValueError, match="DataFrame de pandas valido"):
        dividir_dataset_estratificado(None)  # type: ignore

    # 3. test_size invalido
    df_valido = pd.DataFrame({"texto": ["a", "b"], "sector": ["s1", "s2"]})
    with pytest.raises(ValueError, match="entre 0.0 y 1.0"):
        dividir_dataset_estratificado(df_valido, test_size=1.5)

    with pytest.raises(ValueError, match="entre 0.0 y 1.0"):
        dividir_dataset_estratificado(df_valido, test_size=0.0)

    # 4. Columna inexistente
    with pytest.raises(ValueError, match="no existe"):
        dividir_dataset_estratificado(df_valido, estratificar_por="columna_inexistente")

    # 5. Columna con nulos
    df_con_nulos = pd.DataFrame({"texto": ["a", "b"], "sector": ["s1", None]})
    with pytest.raises(ValueError, match="contiene valores nulos"):
        dividir_dataset_estratificado(df_con_nulos, estratificar_por="sector")
