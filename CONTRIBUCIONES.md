# Registro de Contribuciones del Equipo

Este documento registra los aportes individuales de cada integrante del equipo, los cuales deben coincidir estrictamente con el historial de commits en Git.

| Integrante | Rol | Aporte Principal | Commits Clave | Aporte en NLP o ML |
|---|---|---|---|---|
| Adolfo Mendoza Ribera | Arquitectura / Repo | Inicialización del repositorio, estructura base y configuración de Docker | `chore(repo): inicializar repositorio y estructura base` | Definición de parámetros y dataset |
| [Completar Integrante 2] | Datos y NLP | Descarga de dataset, EDA y pipeline de preprocesamiento | [Commits] | Tratamiento de negaciones y lematización |
| [Completar Integrante 3] | Modelado | Entrenamiento, validación cruzada y análisis de errores | [Commits] | Comparación Naive Bayes vs Regresión Logística |
| [Completar Integrante 4] | Fullstack / API | Backend FastAPI, Docker y Frontend React | [Commits] | Auditoría paso a paso de NLP en API |

## Reglas Obligatorias de la Rúbrica
- **Cada integrante debe tener al menos un commit significativo en NLP o Machine Learning.**
- El trabajo en pareja se registra con `Co-authored-by: Nombre <correo>` en el commit.
- Las contribuciones se auditan antes de la defensa con:
  ```bash
  git shortlog -sn --no-merges
  git log --author="Nombre" --oneline
  ```
