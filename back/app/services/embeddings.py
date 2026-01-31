from openai import OpenAI
from app.config import settings

_client: OpenAI | None = None


def get_openai_client() -> OpenAI:
    """Obtiene o crea el cliente de OpenAI (singleton)."""
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def generate_embedding(text: str) -> list[float]:
    """Genera embedding usando OpenAI text-embedding-3-small."""
    client = get_openai_client()

    response = client.embeddings.create(model="text-embedding-3-small", input=text)

    return response.data[0].embedding
