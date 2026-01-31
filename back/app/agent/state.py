from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Estado del agente conversacional."""

    messages: Annotated[list, add_messages]  # Historial de mensajes
    last_search_results: list[dict]  # Últimas experiencias mostradas
