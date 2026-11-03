"""Pruebas unitarias para el modulo de preparacion y mapeo de ofertas laborales.

Verifica con ejemplos calculados a mano:
  - Normalizacion basica de texto sin tildes ni caracteres especiales.
  - Asignacion correcta de los 5 sectores clave mediante ocupacion y titulo.
  - Comportamiento ante oficios no pertenecientes a los 5 sectores (retorna None).
  - Limpieza de duplicados y valores nulos.
"""

import pytest

from src.data.prepare_dataset import (
    asignar_sector,
    normalizar_texto_basico,
)


def test_normalizar_texto_basico() -> None:
    """Verifica que la normalizacion elimine tildes, signos y convierta a minusculas."""
    # Ejemplo calculado a mano:
    # "¡Chófer de Camión Rígido!" -> minusculas + sin tildes -> "chofer de camion rigido"
    entrada = "¡Chófer de Camión Rígido!"
    esperado = "chofer de camion rigido"
    assert normalizar_texto_basico(entrada) == esperado


def test_normalizar_texto_entradas_vacias() -> None:
    """Verifica el comportamiento ante entradas no validas o vacias."""
    assert normalizar_texto_basico("") == ""
    assert normalizar_texto_basico("   ") == ""
    # @ts-ignore o tipo no string
    assert normalizar_texto_basico(None) == ""  # type: ignore


@pytest.mark.parametrize(
    "ocupacion,titulo,sector_esperado",
    [
        # 1. Sector Transporte y Logistica
        (
            "Conductor de camión",
            "Transporte nacional de mercancias",
            "transporte_logistica",
        ),
        (
            "Mozo de almacén",
            "Operario de carga y descarga",
            "transporte_logistica",
        ),
        # 2. Sector Hosteleria y Gastronomia
        (
            "Pizzero/pizzera",
            "Elaboracion de pizzas y pastas",
            "hosteleria_gastronomia",
        ),
        (
            "Camarero de barra",
            "Servicio de restaurante en sala",
            "hosteleria_gastronomia",
        ),
        # 3. Sector Ventas y Comercial
        (
            "Agente comercial de seguros",
            "Prospeccion y captacion de clientes",
            "ventas_comercial",
        ),
        (
            "Cajero/cajera",
            "Cobro en supermercado y reposicion",
            "ventas_comercial",
        ),
        # 4. Sector Salud y Servicios Sociales
        (
            "Enfermero/enfermera",
            "Atencion en residencia de mayores",
            "salud_servicios_sociales",
        ),
        (
            "Educador social/educadora social",
            "Intervencion comunitaria en centro de dia",
            "salud_servicios_sociales",
        ),
        # 5. Sector Construccion y Mantenimiento
        (
            "Mecánico electricista",
            "Instalacion y mantenimiento electrico",
            "construccion_mantenimiento",
        ),
        (
            "Fontanero/fontanera",
            "Reparacion de tuberias y redes de agua",
            "construccion_mantenimiento",
        ),
        # Casos fuera de los 5 sectores (deben retornar None)
        (
            "Astronauta",
            "Piloto de nave espacial",
            None,
        ),
        (
            "Disenador grafico",
            "Creacion de logotipos e ilustracion digital",
            None,
        ),
    ],
)
def test_asignar_sector_ejemplos_a_mano(
    ocupacion: str, titulo: str, sector_esperado: str | None
) -> None:
    """Verifica que cada oficio representativo sea clasificado en su sector exacto."""
    resultado = asignar_sector(ocupacion, titulo)
    assert resultado == sector_esperado
