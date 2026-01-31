import json
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage

from app.config import settings
from app.agent.state import AgentState
from app.agent.tools import search_rutopia_experiences, get_experience_details
from app.agent.prompts import SYSTEM_PROMPT


# Tools disponibles
tools = [search_rutopia_experiences, get_experience_details]

# Modelo con tools
model = ChatAnthropic(
    model="claude-sonnet-4-20250514", api_key=settings.anthropic_api_key, streaming=True
).bind_tools(tools)


def build_system_message(state: AgentState) -> SystemMessage:
    """Construye el system message con contexto de búsquedas anteriores."""
    content = SYSTEM_PROMPT

    # Agregar contexto de última búsqueda si existe
    if state.get("last_search_results"):
        content += "\n\n## Últimas experiencias mostradas al usuario:\n"
        for i, exp in enumerate(state["last_search_results"][:5], 1):
            content += f"{i}. {exp.get('name', 'Sin nombre')} (ID: {exp.get('id')}) - {exp.get('location', '')}\n"
        content += "\nSi el usuario dice 'el primero', 'el segundo', etc., refiere a estas experiencias."

    return SystemMessage(content=content)


async def agent_node(state: AgentState):
    """Nodo principal: el agente decide qué hacer."""
    system_message = build_system_message(state)
    messages = [system_message] + state["messages"]

    response = await model.ainvoke(messages)

    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    """Decide si continuar con tools o terminar."""
    last_message = state["messages"][-1]

    # Si hay tool_calls, ir al nodo de tools
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    # Si no, terminar
    return END


def process_tool_results(state: AgentState) -> dict:
    """Procesa resultados de tools y actualiza el estado."""
    updates = {}

    # Buscar el último ToolMessage
    for message in reversed(state["messages"]):
        if message.type == "tool":
            try:
                content = message.content
                if isinstance(content, str):
                    results = json.loads(content)
                else:
                    results = content

                # Si es una lista de experiencias, guardarla
                if isinstance(results, list) and len(results) > 0:
                    if isinstance(results[0], dict) and "lat" in results[0]:
                        updates["last_search_results"] = results
                        break
            except (json.JSONDecodeError, TypeError):
                pass

    return updates


def create_agent_graph():
    """Crea y compila el grafo del agente."""
    workflow = StateGraph(AgentState)

    # Nodos
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_node("process_results", process_tool_results)

    # Edges
    workflow.set_entry_point("agent")

    workflow.add_conditional_edges(
        "agent", should_continue, {"tools": "tools", END: END}
    )

    workflow.add_edge("tools", "process_results")
    workflow.add_edge("process_results", "agent")

    return workflow.compile()


# Instancia global del agente
agent = create_agent_graph()
