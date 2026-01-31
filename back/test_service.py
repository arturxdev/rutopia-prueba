import asyncio
import json
import websockets


async def test_websocket():
    uri = "ws://localhost:8000/ws/chat/test-session-123"

    print("🔌 Conectando al WebSocket...")

    async with websockets.connect(uri) as websocket:
        print("✅ Conectado!\n")

        # Enviar mensaje
        message = {
            "content": "Hola, busco cenotes para ir con mi familia cerca de Tulum"
        }
        print(f"📤 Enviando: {message['content']}\n")
        await websocket.send(json.dumps(message))

        # Recibir respuestas
        print("📥 Respuesta:\n")
        full_response = ""

        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=60)
                data = json.loads(response)

                if data["type"] == "token":
                    print(data["content"], end="", flush=True)
                    full_response += data["content"]

                elif data["type"] == "message":
                    # Complete message received at once
                    print(data["content"])
                    full_response = data["content"]

                elif data["type"] == "tool_start":
                    print(f"\n\n⏳ {data.get('message', 'Procesando...')}\n")

                elif data["type"] == "tool_end":
                    print(f"✅ {data['tool']} completado\n")

                elif data["type"] == "experiences":
                    print(
                        f"\n\n🗺️ {len(data['data'])} experiencias encontradas para el mapa"
                    )
                    for exp in data["data"]:
                        print(f"   • {exp['name']} ({exp['location']})")
                    print()

                elif data["type"] == "done":
                    print("\n\n✅ Mensaje completado")
                    break

                elif data["type"] == "error":
                    print(f"\n❌ Error: {data['message']}")
                    break

            except asyncio.TimeoutError:
                print("\n⏰ Timeout esperando respuesta")
                break


if __name__ == "__main__":
    asyncio.run(test_websocket())
