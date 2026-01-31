import pandas as pd
from supabase import create_client
import os
from dotenv import load_dotenv
import json
import math

load_dotenv()

# Conexión a Supabase


def clean_nan_values(obj):
    """Limpia valores NaN/None recursivamente."""
    if isinstance(obj, dict):
        return {k: clean_nan_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_values(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif pd.isna(obj):
        return None
    return obj


def clean_json_field(value):
    """Convierte strings JSON a objetos Python y limpia NaN."""
    if pd.isna(value) or value == "" or value is None:
        return None
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return clean_nan_values(parsed)
        except:
            return value
    if isinstance(value, dict):
        return clean_nan_values(value)
    return value


supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


def load_experiences(csv_path: str):
    """Carga experiences_rows.csv a Supabase."""
    print("Cargando experiences...")

    df = pd.read_csv(csv_path)
    df["min_adult_age"] = df["min_adult_age"].fillna(0).astype(int)
    df["max_adult_age"] = df["max_adult_age"].fillna(0).astype(int)
    df["min_child_age"] = df["min_child_age"].fillna(0).astype(int)
    df["max_child_age"] = df["max_child_age"].fillna(0).astype(int)
    df["duration"] = df["duration"].fillna(0).astype(int)
    # Seleccionar y renombrar columnas necesarias
    columns_to_keep = [
        "id",
        "narrative_text",
        "service_type",
        "destination_name",
        "supplier_name",
        "city",
        "location_address",
        "duration",
        "lat",
        "lon",
        "min_adult_age",
        "max_adult_age",
        "min_child_age",
        "max_child_age",
    ]

    # Filtrar columnas que existen
    existing_cols = [c for c in columns_to_keep if c in df.columns]
    df = df[existing_cols]

    df = df.dropna(subset=["lat", "lon"], how="any")

    # Si quieres estar seguro de que los índices se reorganicen desde 0
    df = df.reset_index(drop=True)

    # Reemplazar NaN con None
    df = df.where(pd.notnull(df), None)

    # Convertir a lista de diccionarios
    records = df.to_dict("records")

    # Insertar en batches de 500
    batch_size = 20
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        try:
            supabase.table("experiences").insert(batch).execute()
            print(f"  Insertados {i + len(batch)}/{len(records)}")
        except Exception as e:
            print(df.iloc[i, i + len(batch)])
            print(f"  Error en batch {i}: {e}")
            return

    print(f"✅ Cargadas {len(records)} experiencias")


def load_experiences_enhanced(csv_path: str):
    """Carga experiences_enhanced_rows.csv a Supabase."""
    print("Cargando experiences_enhanced...")

    df = pd.read_csv(csv_path)
    df = df.drop("full_option_code", axis=1)

    # Renombrar experience_id si es necesario
    if "experience_id" in df.columns:
        pass  # Ya tiene el nombre correcto
    elif "id" in df.columns:
        df = df.rename(columns={"id": "experience_id"})

    # Columnas JSON que necesitan parsing
    json_columns = [
        "secondary_experience_types",
        "semantic_tags",
        "unique_selling_points",
        "experience_mood",
        "target_interests",
        "best_seasons",
        "special_occasions",
    ]

    for col in json_columns:
        if col in df.columns:
            df[col] = df[col].apply(clean_json_field)

    # Convertir booleanos
    bool_columns = [
        "family_friendly",
        "requires_guide",
        "weather_dependent",
        "indoor_activity",
        "includes_food",
        "includes_transport",
        "accessibility_friendly",
    ]

    for col in bool_columns:
        if col in df.columns:
            df[col] = df[col].map(
                {"TRUE": True, "FALSE": False, True: True, False: False}
            )

    # Reemplazar NaN con None
    df = df.where(pd.notnull(df), None)
    # Convertir a lista de diccionarios
    records = df.to_dict("records")

    # Insertar en batches
    batch_size = 500
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        try:
            supabase.table("experiences_enhanced").insert(batch).execute()
            print(f"  Insertados {i + len(batch)}/{len(records)}")
        except Exception as e:
            print(f"  Error en batch {i}: {e}")

    print(f"✅ Cargadas {len(records)} experiencias enhanced")


if __name__ == "__main__":
    # Ajusta las rutas a tus archivos CSV
    print("\n🎉 Cargando experiencias...")
    # load_experiences("./experiences_rows_clean_2.csv")
    load_experiences_enhanced("./experiences_enhanced_rows.csv")
    print("\n🎉 Datos cargados exitosamente!")
