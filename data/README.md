# Datos: Ofertas Laborales en Español (EURES 2025)

## Origen, Licencia y Fecha

| Campo | Valor |
|---|---|
| **Repositorio** | [`MiguelGP-13/JobOffers_ESP`](https://huggingface.co/datasets/MiguelGP-13/JobOffers_ESP) (Hugging Face) |
| **Origen** | Ofertas públicas de empleo de la red europea EURES y servicios de empleo de España. |
| **Licencia** | Creative Commons Attribution 4.0 International (CC-BY 4.0). |
| **Fecha de obtención** | Noviembre 2026 (Datos publicados en 2025). |
| **Tamaño crudo** | 7.261 registros de ofertas laborales. |
| **Idioma** | Español (`es`), texto natural humano con requisitos, perfiles y tareas. |

---

## Diccionario de Columnas (Datos Crudos)

| Columna | Tipo | Descripción |
|---|---|---|
| `titulo` | texto | Puesto de trabajo solicitado. |
| `descripcion` | texto | **Texto principal para NLP.** Requisitos, tareas, horario y funciones. |
| `ocupacion` | texto | Nombre específico del oficio (ej. *Pizzero*, *Conductor*). |
| `provincia` | texto | Localización geográfica de la vacante. |
| `tipo_contrato` | texto | Modalidad contractual (*Determinado*, *Indefinido*). |
| `timestamp` | texto | Fecha de publicación de la oferta. |

---

## Agrupación de Clases (5 Sectores Principales)

Para evitar la dispersión excesiva de ~300 ocupaciones hiperespecíficas, los oficios más frecuentes se agrupan en **5 grandes sectores de negocio**:

1. **Transporte y Logística:** Conductores de camión, repartidores, mozos de almacén.
2. **Hostelería y Gastronomía:** Cocineros, camareros, pizzeros, ayudantes de cocina.
3. **Ventas y Comercial:** Asesores comerciales, agentes de seguros, teleoperadores.
4. **Salud y Servicios Sociales:** Auxiliares de enfermería, educadores sociales, cuidadores.
5. **Construcción y Mantenimiento:** Albañiles, electricistas, fontaneros, peones de obra.
