import os
import time
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client

load_dotenv()

# Clientes
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


def build_embedding_text(experience: dict, enhanced: dict) -> str:
    """
    Construye el texto enriquecido para generar el embedding.
    Combina: semantic_tags + one_line_summary + location + tipo
    """
    parts = []

    # Semantic tags (lo más importante para búsqueda)
    if enhanced.get("semantic_tags"):
        tags = enhanced["semantic_tags"]
        if isinstance(tags, list):
            parts.append(" ".join(tags))

    if enhanced.get("unique_selling_points"):
        tags = enhanced["unique_selling_points"]
        if isinstance(tags, list):
            parts.append(" ".join(tags))

    if enhanced.get("bussines_description"):
        parts.append(enhanced["bussines_description"])

    # Tipo de experiencia y ambiente
    if enhanced.get("primary_experience_type"):
        parts.append(enhanced["primary_experience_type"])

    if enhanced.get("environment_type"):
        parts.append(enhanced["environment_type"])

    # Mood
    if enhanced.get("experience_mood"):
        mood = enhanced["experience_mood"]
        if isinstance(mood, list):
            parts.append(" ".join(mood))

    # Ubicación
    if experience.get("destination_name"):
        parts.append(experience["destination_name"])

    if experience.get("city"):
        parts.append(experience["city"])

    # Resumen
    if enhanced.get("one_line_summary"):
        parts.append(enhanced["one_line_summary"])

    # Intensidad física
    if enhanced.get("physical_intensity"):
        parts.append(f"physical intensity {enhanced['physical_intensity']}")

    # Características especiales
    if enhanced.get("family_friendly"):
        parts.append("family friendly")

    if enhanced.get("includes_food"):
        parts.append("includes food")

    if enhanced.get("includes_transport"):
        parts.append("includes transport")

    text = " ".join(filter(None, parts))
    return text[:8000]  # Límite de tokens aprox


def generate_embedding(text: str) -> list[float]:
    """Genera embedding usando OpenAI."""
    response = openai_client.embeddings.create(
        model="text-embedding-3-small", input=text
    )
    return response.data[0].embedding


def main():
    print("🚀 Generando embeddings...")

    # Obtener experiencias sin embedding
    print("  Obteniendo experiencias sin embedding...")

    # Traer experiencias que no tienen embedding
    result = (
        supabase.table("experiences")
        .select("id, destination_name, city")
        .is_("vector_embedding", "null")
        .execute()
    )

    experiences = result.data
    print(f"  Experiencias sin embedding: {len(experiences)}")

    if not experiences:
        print("✅ Todas las experiencias ya tienen embedding!")
        return

    # Procesar en batches
    batch_size = 50  # Para no saturar la API
    total = len(experiences)
    processed = 0
    errors = 0

    for i in range(0, total, batch_size):
        batch = experiences[i : i + batch_size]

        for exp in batch:
            try:
                # Obtener datos enhanced
                enhanced_result = (
                    supabase.table("experiences_enhanced")
                    .select("*")
                    .eq("experience_id", exp["id"])
                    .execute()
                )

                enhanced = enhanced_result.data[0] if enhanced_result.data else {}

                # Construir texto para embedding
                text = build_embedding_text(exp, enhanced)

                if not text.strip():
                    print(f"  ⚠️ Sin texto para {exp['id']}")
                    continue

                # Generar embedding
                embedding = generate_embedding(text)

                # Guardar en Supabase
                supabase.table("experiences").update(
                    {"vector_embedding": embedding}
                ).eq("id", exp["id"]).execute()

                processed += 1

            except Exception as e:
                print(f"  ❌ Error en {exp['id']}: {e}")
                errors += 1

        print(f"  Procesados: {processed}/{total} (errores: {errors})")

        # Rate limiting - OpenAI permite ~3000 RPM para embeddings
        time.sleep(1)

    print(f"\n✅ Completado: {processed} embeddings generados, {errors} errores")


if __name__ == "__main__":
    main()
