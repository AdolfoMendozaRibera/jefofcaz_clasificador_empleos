"""Pruebas de integración automatizadas para la API REST con FastAPI (tests/test_api.py).

Utiliza `TestClient` de FastAPI/HTTPX para verificar los contratos HTTP, códigos de estado,
validaciones Fail-Fast (HTTP 422), inferencia Softmax y procesamiento masivo de CSV.
"""

from __future__ import annotations

import io
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health_check_endpoint():
    """Verifica que /api/health responda HTTP 200 con el modelo cargado."""
    with TestClient(app) as test_client:
        response = test_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["estado"] == "ok"
        assert data["modelo_cargado"] is True
        assert len(data["sectores_soportados"]) == 5


def test_predict_oferta_valida_transporte():
    """Verifica que una oferta de transporte sea clasificada correctamente con probabilidades."""
    with TestClient(app) as test_client:
        payload = {
            "texto": "Conductor repartidor de paquetería ruta fija con furgoneta carnet de conducir B."
        }
        response = test_client.post("/api/predict", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["sector_predicho"] == "transporte_logistica"
        assert data["probabilidad"] > 0.60

        # Propiedad matemática de Softmax: suma 1.0
        probabilidades = data["probabilidades"]
        assert len(probabilidades) == 5
        assert sum(probabilidades.values()) == pytest.approx(1.0, abs=1e-3)

        # Auditoría de NLP para el Frontend presente
        audit = data["preprocesamiento"]
        assert "conductor" in audit["tokens"]
        assert len(audit["raices"]) > 0


def test_predict_oferta_valida_salud():
    """Verifica clasificación de oferta del sector salud y servicios sociales."""
    with TestClient(app) as test_client:
        payload = {
            "texto": "Enfermero para residencia de ancianos y centro sociosanitario turno de noche."
        }
        response = test_client.post("/api/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["sector_predicho"] == "salud_servicios_sociales"


def test_predict_texto_vacio_retorna_422():
    """Verifica que un texto vacío sea rechazado en el borde con HTTP 422."""
    with TestClient(app) as test_client:
        response = test_client.post("/api/predict", json={"texto": "   "})
        assert response.status_code == 422
        data = response.json()
        assert data["status"] == "error"
        assert "vacío o solo contiene espacios" in data["mensaje"]


def test_predict_texto_muy_corto_retorna_422():
    """Verifica que un texto con menos caracteres de los permitidos retorne HTTP 422."""
    with TestClient(app) as test_client:
        response = test_client.post("/api/predict", json={"texto": "Camarero"})
        assert response.status_code == 422
        data = response.json()
        assert "el mínimo requerido es de" in data["mensaje"]


def test_predict_texto_sin_letras_retorna_422():
    """Verifica que texto sin caracteres lingüísticos retorne HTTP 422."""
    with TestClient(app) as test_client:
        response = test_client.post("/api/predict", json={"texto": "12345678901234567890"})
        assert response.status_code == 422
        data = response.json()
        assert "no contiene letras o palabras válidas" in data["mensaje"]


def test_predict_batch_csv_exitoso():
    """Verifica la carga masiva mediante multipart/form-data con un CSV."""
    with TestClient(app) as test_client:
        csv_contenido = (
            "descripcion\n"
            "Conductor camión tráiler ruta internacional transporte mercancías pesadas carnet CE\n"
            "Cocinero para restaurante italiano preparación de pastas salsas y pizzas artesanas\n"
            "Asesor comercial inmobiliario captación de inmuebles y atención a compradores visitas\n"
        )
        archivos = {
            "archivo": ("ofertas.csv", io.BytesIO(csv_contenido.encode("utf-8")), "text/csv")
        }
        response = test_client.post("/api/predict/batch", files=archivos)
        assert response.status_code == 200
        data = response.json()

        assert data["total_procesados"] == 3
        assert len(data["resultados"]) == 3
        assert data["resultados"][0]["sector_predicho"] == "transporte_logistica"
        assert data["resultados"][1]["sector_predicho"] == "hosteleria_gastronomia"
        assert data["resultados"][2]["sector_predicho"] == "ventas_comercial"


def test_predict_batch_archivo_no_csv_retorna_400():
    """Verifica que subir un archivo que no sea .csv retorne HTTP 400."""
    with TestClient(app) as test_client:
        archivos = {
            "archivo": ("documento.txt", io.BytesIO(b"texto de prueba"), "text/plain")
        }
        response = test_client.post("/api/predict/batch", files=archivos)
        assert response.status_code == 400
        assert "debe tener formato .csv" in response.json()["detail"]


def test_get_metrics_retorna_json_oficial():
    """Verifica que /api/metrics entregue el JSON con la matriz 5x5 y F1-score."""
    with TestClient(app) as test_client:
        response = test_client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "f1_macro" in data
        assert data["f1_macro"] >= 0.85
        assert "matriz_confusion" in data
        assert len(data["matriz_confusion"]) == 5
        assert "terminos_mas_influyentes" in data


def test_root_endpoint_info():
    """Verifica que la raíz / retorne información y link a /docs."""
    with TestClient(app) as test_client:
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["documentacion"] == "/docs"

