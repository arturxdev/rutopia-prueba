import copy
from datetime import datetime, timedelta
from fastapi import WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage, AIMessage

from app.agent.graph import agent
from app.agent.state import AgentState


class ConnectionManager:
    """Maneja las conexiones WebSocket y el estado de las sesiones."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.sessions: dict[str, AgentState] = {}
        self.session_last_active: dict[str, datetime] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

        if session_id not in self.sessions:
            self.sessions[session_id] = {"messages": [], "last_search_results": []}

        self.session_last_active[session_id] = datetime.now()

    def disconnect(self, session_id: str):
        self.active_connections.pop(session_id, None)

    def get_state(self, session_id: str) -> AgentState:
        default_state = {"messages": [], "last_search_results": []}
        state = self.sessions.get(session_id, default_state)
        # Return deep copy to avoid race conditions
        return copy.deepcopy(state)

    def update_state(self, session_id: str, state: AgentState):
        # Store deep copy to avoid external mutations
        self.sessions[session_id] = copy.deepcopy(state)
        self.session_last_active[session_id] = datetime.now()

    async def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Remove sessions that haven't been active and are disconnected."""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = [
            sid
            for sid, last_active in self.session_last_active.items()
            if last_active < cutoff and sid not in self.active_connections
        ]
        for sid in to_remove:
            self.sessions.pop(sid, None)
            self.session_last_active.pop(sid, None)


manager = ConnectionManager()


async def handle_chat_message(websocket: WebSocket, session_id: str, user_message: str):
    """Procesa un mensaje del usuario y envía respuestas por WebSocket."""

    state = manager.get_state(session_id)

    # Create clean input state without mutating the original
    input_state = {
        "messages": state["messages"] + [HumanMessage(content=user_message)],
        "last_search_results": state.get("last_search_results", []),
    }

    streamed_tokens = []
    final_state = None

    try:
        async for event in agent.astream_events(input_state, version="v2"):
            event_type = event["event"]

            # DEBUG: Ver todos los eventos
            print(f"Event: {event_type} | Keys: {event.keys()}")

            # Chat model start (thinking started)
            if event_type == "on_chat_model_start":
                await websocket.send_json({"type": "thinking_start"})

            # Token de texto (streaming)
            elif event_type == "on_chat_model_stream":
                chunk = event["data"].get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    if isinstance(chunk.content, str):
                        streamed_tokens.append(chunk.content)
                        await websocket.send_json(
                            {"type": "token", "content": chunk.content}
                        )

            # Chat model end (thinking finished)
            elif event_type == "on_chat_model_end":
                await websocket.send_json({"type": "thinking_end"})

            # Inicio de herramienta
            elif event_type == "on_tool_start":
                tool_name = event.get("name", "")
                print(f"🔧 Tool start: {tool_name}")
                await websocket.send_json(
                    {
                        "type": "tool_start",
                        "tool": tool_name,
                        "message": get_tool_message(tool_name),
                    }
                )

            # Fin de herramienta
            elif event_type == "on_tool_end":
                tool_name = event.get("name", "")
                print(f"🔧 Tool end: {tool_name}")
                await websocket.send_json({"type": "tool_end", "tool": tool_name})

            # Capture final state from graph
            elif event_type == "on_chain_end" and event.get("name") == "LangGraph":
                final_state = event["data"].get("output")
                print("✅ Captured final state from graph")

        # If graph didn't emit on_chain_end, reconstruct manually
        if final_state is None:
            print("⚠️  No final state from graph, reconstructing...")
            if streamed_tokens:
                ai_message = AIMessage(content="".join(streamed_tokens))
                final_state = {
                    "messages": input_state["messages"] + [ai_message],
                    "last_search_results": input_state.get("last_search_results", []),
                }
            else:
                # No tokens streamed, use input state as fallback
                final_state = input_state

        # Update with FINAL state (output, not input)
        if final_state:
            manager.update_state(session_id, final_state)

            # Send the complete message from the agent
            final_messages = final_state.get("messages", [])
            if final_messages:
                last_message = final_messages[-1]
                if hasattr(last_message, "content") and last_message.content:
                    # Extract text content from structured content
                    content = last_message.content
                    if isinstance(content, list):
                        # Content is list of blocks (e.g., [{'text': '...', 'type': 'text'}])
                        text_content = ""
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text_content += block.get("text", "")
                        content = text_content

                    if content:
                        await websocket.send_json({
                            "type": "message",
                            "content": content
                        })
                        print(f"📤 Sent complete message: {content[:100]}...")

            # Send experiences if they exist in final state
            if final_state.get("last_search_results"):
                # Check if results are new (different from input state)
                if final_state["last_search_results"] != state.get("last_search_results", []):
                    await websocket.send_json(
                        {"type": "experiences", "data": final_state["last_search_results"]}
                    )
                    print(f"✅ Sent {len(final_state['last_search_results'])} experiences to frontend")

        # Mensaje completado
        await websocket.send_json({"type": "done"})

    except Exception as e:
        print(f"❌ Error en chat: {e}")
        import traceback

        traceback.print_exc()
        await websocket.send_json({"type": "error", "message": str(e)})
        # Close WebSocket on error
        await websocket.close(code=1011)


def get_tool_message(tool_name: str) -> str:
    """Devuelve un mensaje amigable para cada herramienta."""
    messages = {
        "search_rutopia_experiences": "🔍 Buscando experiencias...",
        "get_experience_details": "📋 Obteniendo detalles...",
    }
    return messages.get(tool_name, "⏳ Procesando...")
