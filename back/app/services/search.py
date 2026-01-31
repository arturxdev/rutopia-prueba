from app.services.supabase import get_client
from app.services.embeddings import generate_embedding
from app.models.schemas import Experience, SearchFilters


def extract_title_from_narrative(narrative_text: str) -> str:
    """Extrae el título del narrative_text."""
    if not narrative_text:
        return "Experiencia sin nombre"

    if "Title:" in narrative_text:
        start = narrative_text.find("Title:") + 6
        end = narrative_text.find("|", start)
        if end == -1:
            end = narrative_text.find("\n", start)
        if end == -1:
            end = start + 100
        return narrative_text[start:end].strip()

    return narrative_text[:100].strip()


def search_experiences(filters: SearchFilters, limit: int = 10) -> list[Experience]:
    """
    Búsqueda híbrida: genera embedding del query y llama a la función de Supabase.
    """
    supabase = get_client()

    # 1. Generar embedding del query semántico
    query_embedding = generate_embedding(filters.semantic_query)

    # 2. Llamar a la función de búsqueda híbrida en Supabase
    result = supabase.rpc(
        "search_experiences_hybrid",
        {
            "query_embedding": query_embedding,
            "filter_destination": filters.destination,
            "filter_city": filters.city,
            "filter_family_friendly": filters.family_friendly,
            "filter_intensity": filters.physical_intensity,
            "filter_max_duration": filters.max_duration_hours,
            "filter_environment": filters.environment_type,
            "filter_includes_food": filters.includes_food,
            "filter_experience_type": filters.experience_type,
            "match_count": limit,
        },
    ).execute()

    # 3. Transformar resultados a modelo Experience
    experiences = []
    for row in result.data:
        # Extraer highlights de unique_selling_points
        highlights = []
        if row.get("unique_selling_points"):
            usp = row["unique_selling_points"]
            if isinstance(usp, list):
                highlights = usp[:3]  # Máximo 3 highlights

        # Construir nombre
        name = row.get("one_line_summary") or extract_title_from_narrative(
            row.get("narrative_text", "")
        )

        # Construir ubicación
        location = row.get("city") or row.get("destination_name") or "México"

        experience = Experience(
            id=str(row["id"]),
            name=name,
            summary=row.get("one_line_summary") or row.get("narrative_text", "")[:200],
            lat=float(row["lat"]) if row.get("lat") else 0.0,
            lon=float(row["lon"]) if row.get("lon") else 0.0,
            duration=row.get("duration"),
            location=location,
            destination=row.get("destination_name"),
            highlights=highlights,
            type=row.get("primary_experience_type"),
            intensity=row.get("physical_intensity"),
            family_friendly=row.get("family_friendly"),
            includes_food=row.get("includes_food"),
            includes_transport=row.get("includes_transport"),
            similarity=row.get("similarity"),
        )
        experiences.append(experience)

    return experiences


def get_experience_by_id(experience_id: str) -> dict | None:
    """Obtiene los detalles completos de una experiencia por ID."""
    supabase = get_client()

    # Traer de experiences
    result = supabase.table("experiences").select("*").eq("id", experience_id).execute()

    if not result.data:
        return None

    experience = result.data[0]

    # Traer datos enhanced
    enhanced_result = (
        supabase.table("experiences_enhanced")
        .select("*")
        .eq("experience_id", experience_id)
        .execute()
    )

    enhanced = enhanced_result.data[0] if enhanced_result.data else {}

    # Combinar datos
    return {
        "id": experience["id"],
        "name": enhanced.get("one_line_summary")
        or extract_title_from_narrative(experience.get("narrative_text", "")),
        "narrative_text": experience.get("narrative_text"),
        "supplier_name": experience.get("supplier_name"),
        "city": experience.get("city"),
        "destination_name": experience.get("destination_name"),
        "duration": experience.get("duration"),
        "lat": experience.get("lat"),
        "lon": experience.get("lon"),
        "full_json": experience.get("full_json"),
        "environment_type": enhanced.get("environment_type"),
        "primary_experience_type": enhanced.get("primary_experience_type"),
        "physical_intensity": enhanced.get("physical_intensity"),
        "family_friendly": enhanced.get("family_friendly"),
        "includes_food": enhanced.get("includes_food"),
        "includes_transport": enhanced.get("includes_transport"),
        "semantic_tags": enhanced.get("semantic_tags"),
        "unique_selling_points": enhanced.get("unique_selling_points"),
        "one_line_summary": enhanced.get("one_line_summary"),
    }
