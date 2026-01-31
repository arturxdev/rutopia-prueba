from pydantic import BaseModel
from typing import Optional


class Experience(BaseModel):
    """Experiencia para mostrar en el chat y mapa."""

    id: str
    name: str
    summary: str
    lat: float
    lon: float
    duration: str | None
    location: str
    destination: str | None
    highlights: list[str]
    type: str | None
    intensity: str | None
    family_friendly: bool | None
    includes_food: bool | None
    includes_transport: bool | None
    similarity: float | None = None


class SearchFilters(BaseModel):
    """Filtros extraídos del query del usuario."""

    semantic_query: str
    destination: str | None = None
    city: str | None = None
    family_friendly: bool | None = None
    physical_intensity: str | None = None
    max_duration_hours: float | None = None
    environment_type: str | None = None
    includes_food: bool | None = None
    experience_type: str | None = None


class ChatMessage(BaseModel):
    """Mensaje en la conversación."""

    role: str  # "user" o "assistant"
    content: str


class WSMessage(BaseModel):
    """Mensaje enviado por WebSocket."""

    type: str  # "token", "tool_start", "tool_end", "experiences", "done", "error"
    content: str | None = None
    tool: str | None = None
    data: list[Experience] | None = None
    message: str | None = None
