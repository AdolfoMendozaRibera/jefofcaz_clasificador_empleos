"""Generador de graficos y diagramas de alta resolucion para las diapositivas del proyecto."""

import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Configuracion global de estilo estetico limpio
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#CBD5E1"
plt.rcParams["axes.linewidth"] = 1.0

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "presentacion" / "assets"
OUT_DIR.mkdir(parents=True, exist_ok=True)

NOMBRES_SECTORES = [
    "Construcción y Mantenimiento",
    "Hostelería y Gastronomía",
    "Salud y Servicios Sociales",
    "Transporte y Logística",
    "Ventas y Comercial",
]

NOMBRES_CORTOS = [
    "Construcción",
    "Hostelería",
    "Salud",
    "Transporte",
    "Ventas",
]

COLORES_SECTORES = [
    "#D97706",  # Construccion
    "#EA580C",  # Hosteleria
    "#E11D48",  # Salud
    "#0284C7",  # Transporte
    "#059669",  # Ventas
]


def generar_grafico_distribucion():
    """Genera grafico de barras de las 3.337 ofertas procesadas."""
    df_path = BASE_DIR / "data" / "processed" / "ofertas_5_sectores.csv"
    if not df_path.exists():
        print("No se encontro ofertas_5_sectores.csv")
        return

    df = pd.read_csv(df_path)
    conteo = df["sector"].value_counts()
    
    # Ordenar segun NOMBRES_SECTORES
    sectores_keys = [
        "construccion_mantenimiento",
        "hosteleria_gastronomia",
        "salud_servicios_sociales",
        "transporte_logistica",
        "ventas_comercial",
    ]
    valores = [conteo.get(k, 0) for k in sectores_keys]
    total = sum(valores)

    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=300)
    bars = ax.bar(NOMBRES_CORTOS, valores, color=COLORES_SECTORES, width=0.55, edgecolor="#0F172A", linewidth=1.2)

    for bar, val in zip(bars, valores):
        pct = (val / total) * 100
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 25,
            f"{val:,}\n({pct:.1f}%)",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color="#0F172A",
        )

    ax.set_title("Distribución Oficial de Ofertas por Sector (Total: 3.337)", fontsize=13, fontweight="bold", pad=20, color="#0F172A")
    ax.set_ylabel("Cantidad de Ofertas", fontsize=11, fontweight="bold", color="#334155")
    ax.set_ylim(0, max(valores) * 1.25)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    out_file = OUT_DIR / "distribucion_sectores.png"
    plt.savefig(out_file, bbox_inches="tight")
    plt.close()
    print(f"Grafico guardado en: {out_file}")


def generar_matriz_confusion():
    """Genera el mapa de calor de la Matriz de Confusion 5x5."""
    metrics_path = BASE_DIR / "artifacts" / "metrics.json"
    if not metrics_path.exists():
        print("No se encontro metrics.json")
        return

    with open(metrics_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cm = np.array(data["matriz_confusion"])
    
    fig, ax = plt.subplots(figsize=(7.5, 6), dpi=300)
    cmap = sns.light_palette("#059669", as_cmap=True)
    
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap=cmap,
        cbar=False,
        xticklabels=NOMBRES_CORTOS,
        yticklabels=NOMBRES_CORTOS,
        linewidths=1.5,
        linecolor="#E2E8F0",
        square=True,
        annot_kws={"size": 12, "weight": "bold", "color": "#064E3B"},
        ax=ax,
    )

    ax.set_title("Matriz de Confusión Oficial (5 × 5)\nEvaluada en 668 Ofertas de Prueba (F1: 91.55%)", fontsize=13, fontweight="bold", pad=15, color="#0F172A")
    ax.set_xlabel("Predicción del Modelo", fontsize=11, fontweight="bold", color="#0F172A", labelpad=10)
    ax.set_ylabel("Sector Real (Verdadero)", fontsize=11, fontweight="bold", color="#0F172A", labelpad=10)
    plt.xticks(rotation=20, ha="right", fontsize=10, fontweight="bold", color="#334155")
    plt.yticks(rotation=0, fontsize=10, fontweight="bold", color="#334155")

    plt.tight_layout()
    out_file = OUT_DIR / "matriz_confusion_5x5.png"
    plt.savefig(out_file, bbox_inches="tight")
    plt.close()
    print(f"Matriz de confusion guardada en: {out_file}")


import matplotlib.patches as mpatches

def generar_comparativa_modelos():
    """Genera grafico de barras comparativo de modelos con F1-Score."""
    modelos = [
        "Línea Base\n(DummyClassifier)",
        "Multinomial\nNaive Bayes",
        "Regresión Logística\n(Modelo Oficial Ganador)",
    ]
    f1_scores = [8.92, 89.15, 91.55]
    colores = ["#94A3B8", "#38BDF8", "#059669"]

    fig, ax = plt.subplots(figsize=(7.5, 4.6), dpi=300)
    bars = ax.bar(modelos, f1_scores, color=colores, width=0.5, edgecolor="#0F172A", linewidth=1.2)

    for bar, val in zip(bars, f1_scores):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 2,
            f"{val:.2f}%",
            ha="center",
            va="bottom",
            fontsize=12,
            fontweight="bold",
            color="#0F172A",
        )

    ax.set_title("Evolución Experimental: F1-Score Macro", fontsize=13, fontweight="bold", pad=20, color="#0F172A")
    ax.set_ylabel("F1-Score Macro (%)", fontsize=11, fontweight="bold", color="#334155")
    ax.set_ylim(0, 110)
    ax.axhline(90, color="#10B981", linestyle=":", alpha=0.7, label="Umbral Excelente (≥ 90%)")
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.legend(loc="upper left", frameon=True, facecolor="#F8FAFC", edgecolor="#CBD5E1")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    out_file = OUT_DIR / "comparativa_modelos.png"
    plt.savefig(out_file, bbox_inches="tight")
    plt.close()
    print(f"Comparativa guardada en: {out_file}")


def generar_diagrama_pipeline():
    """Genera un diagrama visual vectorial del pipeline NLP en 5 estaciones."""
    fig, ax = plt.subplots(figsize=(10.5, 3.0), dpi=300)
    ax.set_xlim(0, 10.5)
    ax.set_ylim(0, 2.5)
    ax.axis("off")

    pasos = [
        ("1. Normalización", "Regex URLs/emails\nBlindaje de la Ñ", "#0284C7"),
        ("2. Tokenización", "Separación léxica\nlen >= 2", "#3B82F6"),
        ("3. Stop Words", "Español NLTK +\nNegaciones 'no','sin'", "#D97706"),
        ("4. Morfología", "Snowball Stemming\n(40x más veloz)", "#EA580c"),
        ("5. TF-IDF", "N-gramas (1, 2)\nsublinear_tf=True", "#059669"),
    ]

    for i, (titulo, desc, col) in enumerate(pasos):
        x = i * 2.05 + 0.2
        box = mpatches.FancyBboxPatch((x, 0.4), 1.7, 1.6, boxstyle="round,pad=0.08,rounding_size=0.15", facecolor="#F8FAFC", edgecolor=col, linewidth=2.0)
        ax.add_patch(box)
        ax.text(x + 0.85, 1.6, titulo, ha="center", va="center", fontsize=9.5, fontweight="bold", color=col)
        ax.text(x + 0.85, 0.95, desc, ha="center", va="center", fontsize=8.5, color="#334155")

        if i < len(pasos) - 1:
            ax.annotate("", xy=(x + 2.02, 1.2), xytext=(x + 1.72, 1.2),
                        arrowprops=dict(arrowstyle="->", color="#64748B", lw=2.5, mutation_scale=15))

    plt.tight_layout()
    out_file = OUT_DIR / "pipeline_nlp_diagrama.png"
    plt.savefig(out_file, bbox_inches="tight")
    plt.close()
    print(f"Diagrama de pipeline guardado en: {out_file}")


def generar_diagrama_arquitectura():
    """Genera un diagrama visual vectorial de la arquitectura Docker y 4 capas."""
    fig, ax = plt.subplots(figsize=(10.5, 3.4), dpi=300)
    ax.set_xlim(0, 10.5)
    ax.set_ylim(0, 3.0)
    ax.axis("off")

    capas = [
        ("1. Navegador Web", "React 18 + Vite\nDiseño Clean SaaS\nTabs, Dropzone CSV", "#0284C7"),
        ("2. Nginx Alpine", "Reverse Proxy :8080\nRutas SPA (/index.html)\nProxy /api/* hacia FastAPI", "#3B82F6"),
        ("3. Backend FastAPI", "3 Capas: schemas, service, main\nValidación Fail-Fast HTTP 422\nLifespan (Carga única RAM)", "#7C3AED"),
        ("4. Pipeline ML/NLP", "model.joblib (321 KB)\nTF-IDF + LogisticRegression\nInferencia < 5ms (Softmax)", "#059669"),
    ]

    for i, (titulo, desc, col) in enumerate(capas):
        x = i * 2.55 + 0.2
        box = mpatches.FancyBboxPatch((x, 0.4), 2.1, 2.2, boxstyle="round,pad=0.1,rounding_size=0.15", facecolor="#F8FAFC", edgecolor=col, linewidth=2.0)
        ax.add_patch(box)
        ax.text(x + 1.05, 2.15, titulo, ha="center", va="center", fontsize=10, fontweight="bold", color=col)
        ax.text(x + 1.05, 1.2, desc, ha="center", va="center", fontsize=8.5, color="#334155")

        if i < len(capas) - 1:
            ax.annotate("", xy=(x + 2.5, 1.5), xytext=(x + 2.15, 1.5),
                        arrowprops=dict(arrowstyle="->", color="#64748B", lw=2.5, mutation_scale=15))

    plt.tight_layout()
    out_file = OUT_DIR / "arquitectura_diagrama.png"
    plt.savefig(out_file, bbox_inches="tight")
    plt.close()
    print(f"Diagrama de arquitectura guardado en: {out_file}")


if __name__ == "__main__":
    print("Iniciando generacion de activos visuales para la presentacion...")
    generar_grafico_distribucion()
    generar_matriz_confusion()
    generar_comparativa_modelos()
    generar_diagrama_pipeline()
    generar_diagrama_arquitectura()
    print("Todos los graficos fueron generados con exito.")
