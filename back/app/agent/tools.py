from langchain_core.tools import tool
from app.services.search import search_experiences, get_experience_by_id
from app.models.schemas import SearchFilters


@tool
def search_rutopia_experiences(
    semantic_query: str,
    destination: str | None = None,
    city: str | None = None,
    family_friendly: bool | None = None,
    physical_intensity: str | None = None,
    max_duration_hours: float | None = None,
    environment_type: str | None = None,
    includes_food: bool | None = None,
    experience_type: str | None = None,
) -> list[dict]:
    """
    Busca experiencias turísticas en el catálogo de Rutopia.

    Args:
        semantic_query: Descripción en lenguaje natural de lo que busca el usuario.
                       Ejemplo: "nadar en aguas cristalinas con familia"
        destination: Región - 'Quintana Roo', 'Yucatan', 'Campeche Area', 'Chiapas', 'Puebla Area', 'Oaxaca'
        city: Ciudad específica - 'Tulum', 'Mérida', 'Playa del Carmen', 'Cancún', 'Bacalar', etc.
        family_friendly: True si debe ser apta para familias con niños
        physical_intensity: Nivel de esfuerzo físico - 'low', 'moderate', 'high'
        max_duration_hours: Duración máxima en horas (ejemplo: 4 para medio día)
        environment_type: Tipo de entorno - 'cenote', 'jungle', 'beach', 'city', 'desert', 'lake'
        includes_food: True si debe incluir comida
        experience_type: Tipo principal - 'culture', 'nature', 'adventure', 'wellness', 'gastronomy'

    Returns:
        Lista de experiencias con id, nombre, ubicación, coordenadas y detalles
    """
    print(
        f"Buscando experiencias con query: {semantic_query} {destination} {city} {family_friendly} {physical_intensity} {max_duration_hours} {environment_type} {includes_food} {experience_type}"
    )
    filters = SearchFilters(
        semantic_query=semantic_query,
        destination=destination,
        city=city,
        family_friendly=family_friendly,
        physical_intensity=physical_intensity,
        max_duration_hours=max_duration_hours,
        environment_type=environment_type,
        includes_food=includes_food,
        experience_type=experience_type,
    )

    results = search_experiences(filters, limit=8)

    # Convertir a dict para LangChain
    return [exp.model_dump() for exp in results]


@tool
def get_experience_details(experience_id: str) -> dict:
    """
    Obtiene información detallada de una experiencia específica.
    Usa esto cuando el usuario pregunte por más detalles, precios,
    qué incluye, o información específica de una experiencia ya mostrada.

    Args:
        experience_id: UUID de la experiencia (obtenido de búsquedas anteriores)

    Returns:
        Detalles completos incluyendo precios, descripción, qué incluye, contacto
    """
    result = get_experience_by_id(experience_id)

    if result is None:
        return {"error": "Experiencia no encontrada"}

    return result
