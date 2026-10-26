import os
import json
from openai import AsyncOpenAI
from app.services.tfnsw import fetch_tfnsw_trip
from datetime import datetime
import pytz

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is missing or blank!")

client = AsyncOpenAI(api_key=api_key)

def get_system_prompt(profile) -> dict:
    # Get current Sydney time
    sydney_tz = pytz.timezone('Australia/Sydney')
    current_time = datetime.now(sydney_tz).strftime("%I:%M %p on %A, %B %d, %Y")
    
    context = f"""
    USER CONTEXT:
    - Current System Time: {current_time}
    - Current Location: Marsden Park, NSW
    - Home Station: {profile.home_station if profile else 'Not set'}
    - Work Station: {profile.work_station if profile else 'Not set'}
    - Requires Wheelchair Access: {'Yes' if profile and profile.requires_wheelchair else 'No'}
    """
        
    return {
        "role": "system",
        "content": (
            "You are a strict, single-purpose Sydney public transit routing assistant. "
            "Your ONLY function is to help users plan trips using the get_trip_plan tool. "
            f"{context} "
            "If the user asks for a trip 'now', use the Current System Time for the tool call. "
            "If the user asks to go 'home' or to 'work', use the exact station names provided in their USER CONTEXT. "
            "You are STRICTLY PROHIBITED from answering general knowledge questions."
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

    print("[LLM INFERENCE 1] Evaluating user query with gpt-4o-mini...")
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools_schema,
        tool_choice="auto"
    )

    response_message = response.choices[0].message

    # Handle standard native tool calls
    if response_message.tool_calls:
        messages.append(response_message)

        for tool_call in response_message.tool_calls:
            if tool_call.function.name == "get_trip_plan":
                args = json.loads(tool_call.function.arguments)
                api_result = await fetch_tfnsw_trip(
                    origin=args.get("origin"),
                    destination=args.get("destination"),
                    time=args.get("time")
                )

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": api_result
                })

        print("[LLM INFERENCE 2] Synthesizing transit route into response...")
        final_response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return final_response.choices[0].message.content

    return response_message.content