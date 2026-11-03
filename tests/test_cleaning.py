"""Pruebas unitarias para el modulo de limpieza base (src/nlp/cleaning.py).

Verifica con ejemplos calculados a mano:
  1. Desacentuacion selectiva: remocion de tildes y dieresis preservando la letra 'ñ' y 'Ñ'.
  2. Reduccion de elongaciones excesivas sin alterar digrafos legitimos ('rr', 'll', 'cc').
  3. Eliminacion de URLs, emails, menciones y puntuacion en texto crudo de ofertas.
  4. Tokenizacion con filtrado estricto de longitud minima de caracteres.
  5. Casos borde: None, cadenas vacias y solo espacios.
"""

import pytest

from src.nlp.cleaning import (
    desacentuar_conservando_ene,
    limpiar_texto_base,
    normalizar_elongaciones,
    tokenizar_palabras,
)


def test_desacentuar_conservando_ene_ejemplos_a_mano() -> None:
    """Verifica que las tildes se remuevan pero la 'ñ' y 'Ñ' permanezcan intactas."""
    # Ejemplo calculado a mano 1: Palabras clasicas con acentos y dieresis
    entrada = "El camión transporta leña y cigüeñas en otoño"
    esperado = "El camion transporta leña y cigueñas en otoño"
    assert desacentuar_conservando_ene(entrada) == esperado

    # Ejemplo 2: Mayusculas y preservacion de la Ñ
    entrada_mayus = "AÑO NUEVO EN ESPAÑA CON ATENCIÓN"
    esperado_mayus = "AÑO NUEVO EN ESPAÑA CON ATENCION"
    assert desacentuar_conservando_ene(entrada_mayus) == esperado_mayus


def test_normalizar_elongaciones_ejemplos_a_mano() -> None:
    """Verifica la reduccion de secuencias de 3 o mas letras sin romper palabras normales."""
    # Elongaciones excesivas (3 o mas repeticiones)
    assert normalizar_elongaciones("buenoooooo") == "bueno"
    assert normalizar_elongaciones("siiiii yaaaaa") == "si ya"

    # Palabras legitimas en español con letras dobles (deben conservarse intactas)
    assert normalizar_elongaciones("carro") == "carro"
    assert normalizar_elongaciones("llave") == "llave"
    assert normalizar_elongaciones("accion") == "accion"


def test_limpiar_texto_base_oferta_real() -> None:
    """Verifica la limpieza completa de una oferta laboral con ruido tipografico."""
    # Ejemplo calculado a mano de oferta real con URLs, emails, menciones y signos
    oferta_cruda = (
        "¡¡¡OFERTA URGENTEEEEE!!! Chofer para camión. "
        "Postular en https://eures.europa.eu o escribir a rrhh@empresa.es vía @empleos_es. "
        "2 años de experiencia mínima."
    )
    esperado = "oferta urgente chofer para camion postular en o escribir a via 2 años de experiencia minima"
    resultado = limpiar_texto_base(oferta_cruda)
    assert resultado == esperado


def test_tokenizar_palabras_filtrado_longitud() -> None:
    """Verifica que los tokens de longitud menor a 2 sean descartados."""
    texto_limpio = "chofer de camion y repartidor a domicilio"
    tokens = tokenizar_palabras(texto_limpio, min_length=2)
    # Se deben eliminar 'y' y 'a' (longitud 1)
    assert tokens == ["chofer", "de", "camion", "repartidor", "domicilio"]
    assert "y" not in tokens
    assert "a" not in tokens

    # Prueba con min_length=3
    tokens_len3 = tokenizar_palabras(texto_limpio, min_length=3)
    assert "de" not in tokens_len3
    assert tokens_len3 == ["chofer", "camion", "repartidor", "domicilio"]


def test_casos_borde_entradas_vacias() -> None:
    """Verifica el comportamiento seguro ante entradas None, vacias o no string."""
    assert normalizar_elongaciones("") == ""
    assert normalizar_elongaciones(None) == ""  # type: ignore

    assert desacentuar_conservando_ene("") == ""
    assert desacentuar_conservando_ene(None) == ""  # type: ignore

    assert limpiar_texto_base("") == ""
    assert limpiar_texto_base("    ") == ""
    assert limpiar_texto_base(None) == ""

    assert tokenizar_palabras("") == []
    assert tokenizar_palabras("    ") == []
    assert tokenizar_palabras(None) == []
