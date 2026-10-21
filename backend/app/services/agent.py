import os
import json
from openai import AsyncOpenAI
from app.services.tfnsw import fetch_tfnsw_trip

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is missing or blank!")

client = AsyncOpenAI(api_key=api_key)

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a helpful Sydney public transit assistant. "
        "Use the get_trip_plan tool whenever the user asks for travel routes, trains, buses, or travel times in Sydney. "
        "For greetings, clarification, or general transit questions, respond directly with conversational text."
    )
}

tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_trip_plan",
            "description": "Get a public transit route between two locations in Sydney.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "Starting station or suburb (e.g. 'Parramatta')"
                    },
                    "destination": {
                        "type": "string",
                        "description": "Ending station or suburb (e.g. 'Central')"
                    },
                    "time": {
                        "type": "string",
                        "description": "Requested departure time in HH:MM format (24-hour)."
                    }
                },
                "required": ["origin", "destination", "time"]
            }
        }
    }
]

async def generate_chat_response(messages: list) -> str:
    conversation = [SYSTEM_PROMPT] + [m for m in messages if m.get("role") != "system"]

    print("[LLM INFERENCE 1] Evaluating user query with gpt-4o-mini...")
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation,
        tools=tools_schema,
        tool_choice="auto"
    )

    response_message = response.choices[0].message

    # Handle standard native tool calls
    if response_message.tool_calls:
        conversation.append(response_message)

        for tool_call in response_message.tool_calls:
            if tool_call.function.name == "get_trip_plan":
                args = json.loads(tool_call.function.arguments)
                api_result = await fetch_tfnsw_trip(
                    origin=args.get("origin"),
                    destination=args.get("destination"),
                    time=args.get("time")
                )

                conversation.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": api_result
                })

        print("[LLM INFERENCE 2] Synthesizing transit route into response...")
        final_response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation
        )
        return final_response.choices[0].message.content

    return response_message.content