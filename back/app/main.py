import uuid
import json
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.websocket import manager, handle_chat_message


async def periodic_cleanup():
    """Cleanup old sessions every hour."""
    while True:
        await asyncio.sleep(3600)  # Every hour
        await manager.cleanup_old_sessions(max_age_hours=24)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup: launch cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    yield
    # Shutdown: cancel cleanup task
    cleanup_task.cancel()


app = FastAPI(
    title="Rutopia Chatbot API",
    description="API para el chatbot de experiencias turísticas de Rutopia",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS para el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React default
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check."""
    return {"status": "ok", "service": "Rutopia Chatbot API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check detallado."""
    return {"status": "healthy", "active_sessions": len(manager.sessions)}


@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint para el chat.

    Mensajes que envía el cliente:
    - {"content": "mensaje del usuario"}

    Mensajes que envía el servidor:
    - {"type": "token", "content": "..."} - Token de texto (streaming)
    - {"type": "tool_start", "tool": "...", "message": "..."} - Inicio de herramienta
    - {"type": "tool_end", "tool": "..."} - Fin de herramienta
    - {"type": "experiences", "data": [...]} - Experiencias para el mapa
    - {"type": "done"} - Mensaje completado
    - {"type": "error", "message": "..."} - Error
    """
    await manager.connect(websocket, session_id)

    try:
        while True:
            # Recibir mensaje del usuario
            data = await websocket.receive_text()

            # Validate JSON
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
                continue

            # Validate message structure
            user_content = message.get("content", "")
            if not user_content:
                await websocket.send_json({
                    "type": "error",
                    "message": "Missing 'content' field"
                })
                continue

            await handle_chat_message(websocket, session_id, user_content)

    except WebSocketDisconnect:
        manager.disconnect(session_id)
        print(f"Session {session_id} disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close(code=1011)
    finally:
        manager.disconnect(session_id)
