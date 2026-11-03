"""Modulo de funciones puras para la limpieza base y normalizacion diacritica de texto.

Implementa la primera y segunda estacion de preprocesamiento de NLP:
1. Normalizacion de caracteres: minusculas, reduccion de elongaciones, eliminacion de URLs,
   correos electronicos, menciones y puntuacion.
2. Desacentuacion selectiva: remocion de tildes conservando estrictamente la letra 'ñ'.
3. Tokenizacion por espacios con filtrado de longitud minima (len(t) > 1).
"""

import re
from typing import List, Optional
import unicodedata

# Expresiones regulares precompiladas para maximo rendimiento
RE_URL = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
RE_EMAIL = re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", re.IGNORECASE)
RE_MENCION = re.compile(r"@\w+", re.IGNORECASE)
RE_ELONGACION = re.compile(r"(\w)\1{2,}", re.IGNORECASE)
RE_SIGNOS = re.compile(r"[^\w\sñÑáéíóúÁÉÍÓÚüÜ]", re.UNICODE)
RE_ESPACIOS = re.compile(r"\s+")


def normalizar_elongaciones(texto: str) -> str:
    """Reduce secuencias de 3 o mas caracteres repetidos consecutivos a uno solo.

    En español ninguna letra se repite 3 veces de forma legitima. Convierte
    expresiones informales o enfaticas en su forma lexica estandar.

    Args:
        texto: Cadena de texto a procesar.

    Returns:
        Cadena con elongaciones reducidas.

    Example:
        >>> normalizar_elongaciones("buenoooooo")
        'bueno'
        >>> normalizar_elongaciones("urgenteeeee yaaaaa")
        'urgente ya'
    """
    if not texto or not isinstance(texto, str):
        return ""
    return RE_ELONGACION.sub(r"\1", texto)


def desacentuar_conservando_ene(texto: str) -> str:
    """Elimina tildes y dieresis del texto en español conservando intacta la 'ñ' y 'Ñ'.

    A diferencia de librerias anglosajonas (como unidecode) que destruyen la 'ñ'
    convirtiendola en 'n' ('año' -> 'ano'), esta funcion descompone los caracteres
    diacriticos (NFD) y remueve exclusivamente los acentos ('Mn') tras blindar la 'ñ'.

    Args:
        texto: Cadena de texto con posibles tildes.

    Returns:
        Cadena sin tildes pero con la letra 'ñ'/'Ñ' preservada.

    Example:
        >>> desacentuar_conservando_ene("camión con año y cigüeña")
        'camion con año y cigueña'
    """
    if not texto or not isinstance(texto, str):
        return ""

    # Proteccion de la letra eñe con marcadores centinela unicos
    centinela_min = "\u0000"
    centinela_may = "\u0001"
    texto_blindado = texto.replace("ñ", centinela_min).replace("Ñ", centinela_may)

    # Descomposicion canonica NFD y filtrado de marcas no espaciadas (tildes)
    texto_descompuesto = unicodedata.normalize("NFD", texto_blindado)
    texto_sin_tildes = "".join(
        c for c in texto_descompuesto if unicodedata.category(c) != "Mn"
    )

    # Restauracion de las eñes protegidas
    return texto_sin_tildes.replace(centinela_min, "ñ").replace(centinela_may, "Ñ")


def limpiar_texto_base(
    texto: Optional[str],
    remover_tildes: bool = True,
) -> str:
    """Ejecuta la limpieza estructural base sobre un texto crudo.

    Secuencia de operaciones:
    1. Conversion a minusculas.
    2. Eliminacion de URLs, emails y menciones (@usuario).
    3. Reduccion de caracteres elongados (ej. 'urgente yaaaa' -> 'urgente ya').
    4. Sustitucion de puntuacion y caracteres especiales por espacios.
    5. Opcional: remocion de tildes conservando la 'ñ'.
    6. Colapso de espacios en blanco multiples.

    Args:
        texto: Cadena cruda de entrada (puede ser None o vacia).
        remover_tildes: Si es True, desacentua conservando la 'ñ'.

    Returns:
        Cadena normalizada y limpia.

    Example:
        >>> limpiar_texto_base("¡URGENTE! Chofer en https://empleos.es para camión")
        'urgente chofer para camion'
    """
    if texto is None or not isinstance(texto, str):
        return ""

    cadena = texto.strip().lower()
    if not cadena:
        return ""

    # 1. Eliminar URLs, emails y menciones
    cadena = RE_URL.sub(" ", cadena)
    cadena = RE_EMAIL.sub(" ", cadena)
    cadena = RE_MENCION.sub(" ", cadena)

    # 2. Reducir elongaciones de letras repetidas
    cadena = normalizar_elongaciones(cadena)

    # 3. Eliminar caracteres no alfabeticos / puntuacion
    cadena = RE_SIGNOS.sub(" ", cadena)

    # 4. Desacentuar conservando la eñe si se solicita
    if remover_tildes:
        cadena = desacentuar_conservando_ene(cadena)

    # 5. Colapsar espacios consecutivos
    cadena = RE_ESPACIOS.sub(" ", cadena).strip()
    return cadena


def tokenizar_palabras(texto: Optional[str], min_length: int = 2) -> List[str]:
    """Segmenta un texto limpio en una lista de tokens filtrando palabras demasiado cortas.

    Args:
        texto: Cadena de texto ya normalizada.
        min_length: Longitud minima para admitir un token (por defecto 2 para descartar
                   letras sueltas como 'a', 'y', 'o', 'e').

    Returns:
        Lista de tokens que cumplen con la longitud minima.

    Example:
        >>> tokenizar_palabras("chofer de camion y repartidor a domicilio")
        ['chofer', 'de', 'camion', 'repartidor', 'domicilio']
    """
    if not texto or not isinstance(texto, str):
        return []

    tokens_brutos = texto.split()
    return [t for t in tokens_brutos if len(t) >= min_length]
