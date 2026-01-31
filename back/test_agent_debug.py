from langchain_core.messages import HumanMessage
from app.agent.graph import agent
import asyncio
import json
from dotenv import load_dotenv

load_dotenv()


async def test():
    print("🤖 Probando agente con debug...\n")

    state = {
        "messages": [HumanMessage(content="Busco cenotes para familia en Tulum")],
        "last_search_results": [],
    }

    print("📡 Streaming eventos:\n")

    async for event in agent.astream_events(state, version="v2"):
        event_type = event["event"]

        if event_type == "on_tool_start":
            print(f"🔧 TOOL START: {event.get('name')}")
            print(f"   Input: {event.get('data', {}).get('input', {})}")

        elif event_type == "on_tool_end":
            print(f"\n🔧 TOOL END: {event.get('name')}")
            output = event.get("data", {}).get("output")
            print(f"   Output type: {type(output)}")

            # Intentar diferentes formas de acceder al contenido
            if output is not None:
                print(f"   Has 'content' attr: {hasattr(output, 'content')}")

                if hasattr(output, "content"):
                    content = output.content
                    print(f"   Content type: {type(content)}")
                    print(f"   Content preview: {str(content)[:200]}...")

                    # Intentar parsear
                    if isinstance(content, str):
                        try:
                            parsed = json.loads(content)
                            print(f"   Parsed type: {type(parsed)}")
                            print(
                                f"   Parsed length: {len(parsed) if isinstance(parsed, list) else 'N/A'}"
                            )
                        except:
                            print("   Could not parse as JSON")

                if hasattr(output, "artifact"):
                    print(f"   Has artifact: {output.artifact}")

        elif event_type == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                if isinstance(chunk.content, str) and chunk.content:
                    print(chunk.content, end="", flush=True)

    print("\n\n✅ Test completado")


if __name__ == "__main__":
    asyncio.run(test())
