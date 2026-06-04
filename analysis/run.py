"""Script unico: limpieza, agregados OLAP para dashboard y exportacion."""

from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.prepare import save_dataset, prepare

PROCESSED = PROJECT_ROOT / "data" / "processed"
FILTER_DIMS = [
    "anio_hecho",
    "departamento_hecho",
    "municipio_hecho",
    "sexo_victima",
    "zona_hecho",
    "pertenencia_etnica",
    "pertenencia_grupal",
    "ciclo_vital",
]


def _dedupe_dims(*dims: str) -> list[str]:
    return list(dict.fromkeys(dims))


def export_dashboard_aggregates(df: pd.DataFrame) -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)

    df.groupby(
        _dedupe_dims(
            "departamento_hecho",
            "municipio_hecho",
            "localidad_hecho",
            *FILTER_DIMS,
        ),
        observed=True,
    ).size().reset_index(name="casos").to_parquet(
        PROCESSED / "agg_territorial.parquet", index=False
    )

    df.groupby(
        _dedupe_dims(
            "sexo_victima",
            "grupo_edad_quinquenal",
            "ciclo_vital",
            *FILTER_DIMS,
        ),
        observed=True,
    ).size().reset_index(name="casos").to_parquet(
        PROCESSED / "agg_demografia.parquet", index=False
    )

    esc = (
        df.groupby(["escenario_hecho", *FILTER_DIMS], observed=True)
        .size()
        .reset_index(name="casos")
    )
    mec = (
        df.groupby(["mecanismo_causal", *FILTER_DIMS], observed=True)
        .size()
        .reset_index(name="casos")
    )
    sev = (
        df.groupby(["severidad_categoria", *FILTER_DIMS], observed=True)
        .size()
        .reset_index(name="casos")
    )
    agr = (
        df.groupby(["presunto_agresor", *FILTER_DIMS], observed=True)
        .size()
        .reset_index(name="casos")
    )
    esc["tipo"] = "escenario"
    esc = esc.rename(columns={"escenario_hecho": "categoria"})
    mec["tipo"] = "mecanismo"
    mec = mec.rename(columns={"mecanismo_causal": "categoria"})
    sev["tipo"] = "severidad"
    sev = sev.rename(columns={"severidad_categoria": "categoria"})
    agr["tipo"] = "agresor"
    agr = agr.rename(columns={"presunto_agresor": "categoria"})
    pd.concat([esc, mec, sev, agr], ignore_index=True).to_parquet(
        PROCESSED / "agg_patrones.parquet", index=False
    )

    df.groupby(
        ["dia_hecho", "rango_hora", *FILTER_DIMS], observed=True
    ).size().reset_index(name="casos").to_parquet(
        PROCESSED / "agg_dia_hora.parquet", index=False
    )

    df.groupby(FILTER_DIMS, observed=True).size().reset_index(name="casos").to_parquet(
        PROCESSED / "agg_filtros.parquet", index=False
    )

    print(f"   Agregados dashboard en {PROCESSED}")



def _train_random_forest(df: pd.DataFrame) -> None:
    """Entrena y evalúa un modelo de bosque aleatorio (Random Forest) para clasificar presunto_agresor."""
    # Filtrar registros "Sin informacion" y hacer copia limpia
    clean_df = df[df["presunto_agresor"] != "Sin informacion"].copy()

    # Mapear presunto_agresor a las 5 macro-categorías
    clean_df["agresor_tipo"] = clean_df["presunto_agresor"].replace({
        "Conocido sin ningun trato": "Conocido sin trato",
        "Conocido sin ningún trato": "Conocido sin trato",
        "Conocido": "Conocido sin trato",
        "Otros conocidos": "Conocido sin trato",
        "Agresor desconocido": "Desconocido/Delincuencia",
        "Delincuencia común": "Desconocido/Delincuencia",
        "Delincuencia común": "Desconocido/Delincuencia",
        "Bandas criminales": "Desconocido/Delincuencia",
        "Otro": "Desconocido/Delincuencia",
        "Policía": "Fuerza Pública",
        "Policía": "Fuerza Pública",
        "Amigo(a)": "Amistad/Entorno",
        "Compañero (a) de trabajo": "Amistad/Entorno",
        "Compañero (a) de estudio": "Amistad/Entorno",
        "Compañero (a) de celda": "Amistad/Entorno",
        "Compañero (a) de cohabitación": "Amistad/Entorno"
    })

    TARGETS = [
        "Conocido sin trato",
        "Desconocido/Delincuencia",
        "Vecino",
        "Fuerza Pública",
        "Amistad/Entorno"
    ]
    clean_df = clean_df[clean_df["agresor_tipo"].isin(TARGETS)].copy()

    FEATURES = [
        "sexo_victima",
        "ciclo_vital",
        "zona_hecho",
        "escenario_hecho",
        "mecanismo_causal",
        "fin_semana",
        "rango_hora"
    ]
    TARGET = "agresor_tipo"

    clean_df = clean_df.dropna(subset=FEATURES + [TARGET])

    X = clean_df[FEATURES]
    y = clean_df[TARGET]

    # División de datos (Train-Test Split 80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=16000, stratify=y
    )

    # Preprocesador
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), FEATURES)
        ]
    )

    # Pipeline
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=100, max_depth=12, class_weight='balanced', random_state=16000, n_jobs=-1))
    ])

    print("  Entrenando Bosque Aleatorio (Random Forest)...")
    pipeline.fit(X_train, y_train)

    # Evaluación
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)
    classes_list = list(pipeline.classes_)
    cm = confusion_matrix(y_test, y_pred, labels=classes_list)

    print(f"  Modelo entrenado. Exactitud en prueba (Test): {acc:.4f}")

    # Guardar modelo
    model_path = PROCESSED / "random_forest.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(pipeline, f)

    # Guardar métricas
    metrics = {
        "accuracy": acc,
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "classes": classes_list
    }
    metrics_path = PROCESSED / "model_metrics.json"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    # Guardar metadatos de características para poblar selectores en UI
    features_metadata = {}
    for col in FEATURES:
        # Convertir a str, boolean o lo que sea a formato string para JSON
        vals = sorted([str(val) for val in X[col].unique()])
        features_metadata[col] = vals

    features_path = PROCESSED / "model_features.json"
    features_path.write_text(json.dumps(features_metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  Archivos del modelo guardados en {PROCESSED}")


def main() -> None:
    print("1. Limpieza y preparacion")
    df = prepare()
    path_pq, path_csv = save_dataset(df)
    constantes = [c for c in df.columns if df[c].nunique() <= 1]
    print(f"   Registros: {len(df):,} | Columnas constantes: {constantes}")
    print(f"   Parquet (pipeline): {path_pq}")
    print(f"   CSV limpio (inspeccion): {path_csv}")

    print("2. Agregados OLAP para dashboard")
    export_dashboard_aggregates(df)

    print("3. Entrenando modelo predictivo (Bosque Aleatorio / Random Forest)")
    _train_random_forest(df)

    print("Listo. Ejecute: streamlit run app/streamlit_app.py")


if __name__ == "__main__":
    main()
